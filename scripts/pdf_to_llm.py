#!/usr/bin/env python3
"""
pdf_to_llm.py
=============

Enhanced PDF processor that uses LLM (Claude) to intelligently extract
and structure content from PDF documents for downstream LLM consumption.

Features:
- Intelligent table detection and structured extraction
- Section/heading identification
- Key data point extraction (numbers, dates, entities)
- Document-level metadata and summary
- Multiple output formats (JSON, JSONL, Markdown)

Usage:
    python pdf_to_llm.py --file <PDF_PATH> --output result.json
    python pdf_to_llm.py --url <PDF_URL> --output result.md --format markdown

Environment:
    ANTHROPIC_API_KEY: Required for LLM processing (optional - falls back to basic mode)

Modes:
    --mode llm      : Use Claude for intelligent extraction (requires API key)
    --mode basic    : Use frequency-based extraction (no API key needed)
    --mode auto     : Use LLM if available, fall back to basic (default)
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from urllib import request as urllib_request
except ImportError:
    import urllib.request as urllib_request

import string

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

# Stopwords for basic mode summarization
STOPWORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an',
    'and', 'any', 'are', 'as', 'at', 'be', 'because', 'been', 'before',
    'being', 'below', 'between', 'both', 'but', 'by', 'can', 'could', 'did',
    'do', 'does', 'doing', 'down', 'during', 'each', 'few', 'for', 'from',
    'further', 'had', 'has', 'have', 'having', 'he', 'her', 'here', 'hers',
    'herself', 'him', 'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is',
    'it', 'its', 'itself', 'me', 'more', 'most', 'my', 'myself', 'no', 'nor',
    'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'our', 'ours',
    'ourselves', 'out', 'over', 'own', 'same', 'she', 'should', 'so', 'some',
    'such', 'than', 'that', 'the', 'their', 'theirs', 'them', 'themselves',
    'then', 'there', 'these', 'they', 'this', 'those', 'through', 'to', 'too',
    'under', 'until', 'up', 'very', 'was', 'we', 'were', 'what', 'when',
    'where', 'which', 'while', 'who', 'whom', 'why', 'with', 'would', 'you',
    'your', 'yours', 'yourself', 'yourselves'
}


@dataclass
class TableData:
    """Represents an extracted table."""
    title: str
    headers: List[str]
    rows: List[List[str]]
    context: str = ""


@dataclass
class KeyFigure:
    """Represents an important numerical value."""
    label: str
    value: str
    unit: str = ""
    context: str = ""


@dataclass
class PageContent:
    """Processed content from a single page."""
    page_number: int
    section: str = ""
    summary: str = ""
    key_figures: List[KeyFigure] = field(default_factory=list)
    tables: List[TableData] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class DocumentMetadata:
    """Document-level metadata."""
    title: str = ""
    document_type: str = ""
    entity: str = ""
    date_period: str = ""
    total_pages: int = 0
    source_file: str = ""
    processed_at: str = ""
    executive_summary: str = ""
    key_sections: List[str] = field(default_factory=list)


@dataclass
class ProcessedDocument:
    """Complete processed document."""
    metadata: DocumentMetadata
    pages: List[PageContent]


def download_pdf(url: str, dest_path: str) -> str:
    """Download a PDF from a URL."""
    with urllib_request.urlopen(url) as response, open(dest_path, 'wb') as out_file:
        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            out_file.write(chunk)
    return dest_path


def pdf_to_text(pdf_path: str) -> str:
    """Convert PDF to text using pdftotext."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp:
        txt_path = tmp.name
    try:
        result = subprocess.run(
            ['pdftotext', '-layout', pdf_path, txt_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"pdftotext failed: {result.stderr.decode('utf-8', errors='ignore')}"
            )
        with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    finally:
        try:
            os.remove(txt_path)
        except OSError:
            pass
    return text


def split_into_pages(text: str) -> List[str]:
    """Split text into pages using form feed character."""
    pages = text.split('\f')
    return [p.strip() for p in pages if p.strip()]


# ============================================================================
# Basic Mode Processing (no LLM required)
# ============================================================================

def extract_numbers_basic(text: str) -> List[KeyFigure]:
    """Extract key numerical values from text using regex patterns."""
    figures = []

    # Pattern for labeled numbers: "Label: 1,234,567" or "Label 1,234,567"
    patterns = [
        # Currency amounts with labels
        r'([A-Za-z][A-Za-z\s]+?)[\s:]+\$?\s*([\d,]+(?:\.\d+)?)\s*(ThUS\$|MUS\$|US\$|USD|EUR|BRL)?',
        # Percentages
        r'([A-Za-z][A-Za-z\s]+?)[\s:]+(\d+(?:\.\d+)?)\s*(%)',
        # Numbers in parentheses (often financial negatives)
        r'([A-Za-z][A-Za-z\s]+?)[\s:]+\(([\d,]+(?:\.\d+)?)\)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text[:3000])  # Limit search
        for match in matches[:10]:  # Limit results per pattern
            if len(match) >= 2:
                label = match[0].strip()
                value = match[1].strip()
                unit = match[2] if len(match) > 2 else ""
                if label and value and len(label) < 50:
                    figures.append(KeyFigure(label=label, value=value, unit=unit))

    return figures[:15]  # Limit total figures


def detect_section_basic(text: str) -> str:
    """Detect section header from page text."""
    lines = text.split('\n')

    # Look for common section patterns
    section_patterns = [
        r'^NOTE\s+\d+\s*[-–:]\s*(.+)$',
        r'^(\d+\.?\s+[A-Z][A-Za-z\s]+)$',
        r'^([A-Z][A-Z\s]+)$',  # ALL CAPS headers
        r'^(CONSOLIDATED\s+.+)$',
    ]

    for line in lines[:15]:
        line = line.strip()
        if not line or len(line) > 100:
            continue
        for pattern in section_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1).strip() if match.lastindex else line

    return ""


def summarize_basic(text: str, ratio: float = 0.3) -> str:
    """Basic extractive summarization using frequency scoring."""
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s) > 20]

    if not sentences:
        return text[:500]

    # Build word frequency
    translator = str.maketrans('', '', string.punctuation)
    freq = {}
    for sent in sentences:
        words = sent.translate(translator).lower().split()
        for word in words:
            if word not in STOPWORDS and len(word) > 2:
                freq[word] = freq.get(word, 0) + 1

    # Score sentences
    scored = []
    for i, sent in enumerate(sentences):
        words = sent.translate(translator).lower().split()
        score = sum(freq.get(w, 0) for w in words if w not in STOPWORDS)
        if words:
            score /= len(words)
        scored.append((i, sent, score))

    # Select top sentences
    n = max(1, int(len(sentences) * ratio))
    top = sorted(scored, key=lambda x: x[2], reverse=True)[:n]
    top.sort(key=lambda x: x[0])  # Restore order

    return ' '.join(s[1] for s in top)


def detect_table_basic(text: str) -> List[TableData]:
    """Attempt to detect and extract tables from text."""
    tables = []
    lines = text.split('\n')

    # Look for lines with multiple whitespace-separated columns
    table_lines = []
    for line in lines:
        # Count columns by splitting on multiple spaces
        parts = re.split(r'\s{2,}', line.strip())
        if len(parts) >= 3 and all(len(p) < 50 for p in parts):
            table_lines.append(parts)
        elif table_lines and len(table_lines) >= 2:
            # End of table
            if len(table_lines) >= 3:
                tables.append(TableData(
                    title="",
                    headers=table_lines[0],
                    rows=table_lines[1:],
                    context=""
                ))
            table_lines = []

    return tables[:5]  # Limit tables


def process_page_basic(page_text: str, page_number: int) -> PageContent:
    """Process a page using basic extraction (no LLM)."""
    return PageContent(
        page_number=page_number,
        section=detect_section_basic(page_text),
        summary=summarize_basic(page_text, ratio=0.4),
        key_figures=extract_numbers_basic(page_text),
        tables=detect_table_basic(page_text),
        raw_text=page_text[:2000]
    )


def generate_metadata_basic(
    first_pages: str,
    total_pages: int,
    source_file: str
) -> DocumentMetadata:
    """Generate document metadata using basic extraction."""
    lines = first_pages.split('\n')

    # Try to find title (usually in first few lines, often in caps)
    title = "Unknown Document"
    for line in lines[:20]:
        line = line.strip()
        if line and len(line) > 10 and len(line) < 100:
            if line.isupper() or re.match(r'^[A-Z][A-Za-z\s]+$', line):
                title = line
                break

    # Try to find entity/company name
    entity = ""
    entity_patterns = [
        r'([\w\s]+(?:S\.A\.|Inc\.|Corp\.|Ltd\.|LLC|Group))',
        r'([\w\s]+Airlines)',
        r'([\w\s]+Company)',
    ]
    for pattern in entity_patterns:
        match = re.search(pattern, first_pages[:2000])
        if match:
            entity = match.group(1).strip()
            break

    # Try to find date
    date_period = ""
    date_patterns = [
        r'(December\s+\d{1,2},?\s+\d{4})',
        r'(Q[1-4]\s+\d{4})',
        r'(Year\s+ended\s+.+?\d{4})',
        r'(\d{4}\s+Annual)',
    ]
    for pattern in date_patterns:
        match = re.search(pattern, first_pages[:3000], re.IGNORECASE)
        if match:
            date_period = match.group(1)
            break

    return DocumentMetadata(
        title=title,
        document_type="financial_report" if "financial" in first_pages.lower() else "other",
        entity=entity,
        date_period=date_period,
        total_pages=total_pages,
        source_file=source_file,
        processed_at=datetime.now().isoformat(),
        executive_summary=summarize_basic(first_pages[:3000], ratio=0.2),
        key_sections=[]
    )


# ============================================================================
# LLM Mode Processing
# ============================================================================

def process_page_with_llm(
    client: 'anthropic.Anthropic',
    page_text: str,
    page_number: int,
    model: str = "claude-sonnet-4-20250514"
) -> PageContent:
    """Process a single page using Claude to extract structured content."""

    prompt = f"""Analyze this page from a document and extract structured information.

<page_content>
{page_text[:12000]}
</page_content>

Respond with a JSON object containing:
{{
    "section": "The section/heading this content belongs to (e.g., 'Note 3 - Financial Risk Management', 'Balance Sheet', etc.)",
    "summary": "A concise summary preserving all key facts, numbers, and relationships. Be specific with values.",
    "key_figures": [
        {{"label": "Revenue", "value": "14,265,056", "unit": "ThUS$", "context": "For year ended Dec 31, 2025"}}
    ],
    "tables": [
        {{
            "title": "Table title or description",
            "headers": ["Column1", "Column2", "Column3"],
            "rows": [["val1", "val2", "val3"], ["val4", "val5", "val6"]],
            "context": "What this table shows"
        }}
    ]
}}

Important:
- Extract ALL numerical values with their labels and units
- Preserve table structures completely - every row and column
- Keep exact numbers, don't round or approximate
- If no tables exist, return empty array
- Section should identify the document section this belongs to"""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text

        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = {"section": "", "summary": response_text, "key_figures": [], "tables": []}

        return PageContent(
            page_number=page_number,
            section=data.get("section", ""),
            summary=data.get("summary", ""),
            key_figures=[KeyFigure(**kf) for kf in data.get("key_figures", [])],
            tables=[TableData(**t) for t in data.get("tables", [])],
            raw_text=page_text[:2000]  # Keep truncated raw text for reference
        )

    except Exception as e:
        print(f"  Warning: LLM processing failed for page {page_number}: {e}", file=sys.stderr)
        return PageContent(
            page_number=page_number,
            summary=page_text[:500],
            raw_text=page_text[:2000]
        )


def generate_document_metadata(
    client: 'anthropic.Anthropic',
    first_pages_text: str,
    total_pages: int,
    source_file: str,
    model: str = "claude-sonnet-4-20250514"
) -> DocumentMetadata:
    """Generate document-level metadata from first few pages."""

    prompt = f"""Analyze the beginning of this document and extract metadata.

<document_start>
{first_pages_text[:8000]}
</document_start>

Total pages in document: {total_pages}

Respond with a JSON object:
{{
    "title": "Full document title",
    "document_type": "financial_report|annual_report|research_paper|legal_document|other",
    "entity": "Company or organization name",
    "date_period": "The period covered (e.g., 'Q4 2025', 'Year ended December 31, 2025')",
    "executive_summary": "2-3 sentence summary of what this document contains and its key findings",
    "key_sections": ["List of main sections/chapters in the document"]
}}"""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text
        json_match = re.search(r'\{[\s\S]*\}', response_text)

        if json_match:
            data = json.loads(json_match.group())
        else:
            data = {}

        return DocumentMetadata(
            title=data.get("title", "Unknown Document"),
            document_type=data.get("document_type", "other"),
            entity=data.get("entity", ""),
            date_period=data.get("date_period", ""),
            total_pages=total_pages,
            source_file=source_file,
            processed_at=datetime.now().isoformat(),
            executive_summary=data.get("executive_summary", ""),
            key_sections=data.get("key_sections", [])
        )

    except Exception as e:
        print(f"Warning: Metadata extraction failed: {e}", file=sys.stderr)
        return DocumentMetadata(
            title="Unknown Document",
            total_pages=total_pages,
            source_file=source_file,
            processed_at=datetime.now().isoformat()
        )


def process_document(
    pdf_path: str,
    mode: str = "auto",
    model: str = "claude-sonnet-4-20250514",
    max_workers: int = 5,
    sample_pages: Optional[List[int]] = None
) -> ProcessedDocument:
    """Process entire PDF document.

    Args:
        pdf_path: Path to PDF file
        mode: Processing mode - 'llm', 'basic', or 'auto'
        model: Claude model to use (for LLM mode)
        max_workers: Number of parallel workers
        sample_pages: Specific pages to process (1-indexed)
    """
    # Determine actual mode
    use_llm = False
    if mode == "llm":
        if not HAS_ANTHROPIC:
            raise RuntimeError("anthropic package not installed. Run: pip install anthropic")
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY environment variable not set")
        use_llm = True
    elif mode == "auto":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if HAS_ANTHROPIC and api_key:
            use_llm = True
            print("Using LLM mode (API key detected)")
        else:
            print("Using basic mode (no API key - set ANTHROPIC_API_KEY for LLM mode)")
    else:  # basic mode
        print("Using basic mode")

    client = None
    if use_llm:
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    print("Extracting text from PDF...")
    full_text = pdf_to_text(pdf_path)
    pages = split_into_pages(full_text)
    total_pages = len(pages)
    print(f"Found {total_pages} pages")

    # Generate document metadata from first few pages
    print("Generating document metadata...")
    first_pages = '\n\n---PAGE BREAK---\n\n'.join(pages[:5])

    if use_llm:
        metadata = generate_document_metadata(
            client, first_pages, total_pages, os.path.basename(pdf_path), model
        )
    else:
        metadata = generate_metadata_basic(
            first_pages, total_pages, os.path.basename(pdf_path)
        )
    print(f"Document: {metadata.title}")

    # Determine which pages to process
    if sample_pages:
        pages_to_process = [(i, pages[i-1]) for i in sample_pages if i <= total_pages]
    else:
        pages_to_process = list(enumerate(pages, start=1))

    # Process pages
    mode_name = "LLM" if use_llm else "basic extraction"
    print(f"Processing {len(pages_to_process)} pages with {mode_name}...")
    processed_pages: List[PageContent] = []

    if use_llm:
        def process_single(args):
            page_num, page_text = args
            return process_page_with_llm(client, page_text, page_num, model)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_single, p): p[0] for p in pages_to_process}

            for i, future in enumerate(as_completed(futures), 1):
                page_num = futures[future]
                try:
                    result = future.result()
                    processed_pages.append(result)
                    print(f"  Processed page {page_num} ({i}/{len(pages_to_process)})")
                except Exception as e:
                    print(f"  Error on page {page_num}: {e}", file=sys.stderr)
    else:
        # Basic mode - process sequentially
        for i, (page_num, page_text) in enumerate(pages_to_process, 1):
            result = process_page_basic(page_text, page_num)
            processed_pages.append(result)
            if i % 10 == 0 or i == len(pages_to_process):
                print(f"  Processed {i}/{len(pages_to_process)} pages")

    # Sort pages by page number
    processed_pages.sort(key=lambda p: p.page_number)

    return ProcessedDocument(metadata=metadata, pages=processed_pages)


def to_dict(obj: Any) -> Any:
    """Convert dataclass objects to dictionaries recursively."""
    if hasattr(obj, '__dataclass_fields__'):
        return {k: to_dict(v) for k, v in asdict(obj).items()}
    elif isinstance(obj, list):
        return [to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    return obj


def output_json(doc: ProcessedDocument, output_path: str):
    """Output as structured JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(to_dict(doc), f, indent=2, ensure_ascii=False)


def output_jsonl(doc: ProcessedDocument, output_path: str):
    """Output as JSONL (one page per line)."""
    with open(output_path, 'w', encoding='utf-8') as f:
        # First line is metadata
        f.write(json.dumps({"type": "metadata", **to_dict(doc.metadata)}, ensure_ascii=False) + '\n')
        # Following lines are pages
        for page in doc.pages:
            f.write(json.dumps({"type": "page", **to_dict(page)}, ensure_ascii=False) + '\n')


def output_markdown(doc: ProcessedDocument, output_path: str):
    """Output as Markdown with frontmatter."""
    lines = []

    # Frontmatter
    lines.append("---")
    lines.append(f"title: \"{doc.metadata.title}\"")
    lines.append(f"entity: \"{doc.metadata.entity}\"")
    lines.append(f"document_type: {doc.metadata.document_type}")
    lines.append(f"period: \"{doc.metadata.date_period}\"")
    lines.append(f"total_pages: {doc.metadata.total_pages}")
    lines.append(f"processed_at: {doc.metadata.processed_at}")
    lines.append(f"source: {doc.metadata.source_file}")
    lines.append("---")
    lines.append("")

    # Executive Summary
    lines.append("# Executive Summary")
    lines.append("")
    lines.append(doc.metadata.executive_summary)
    lines.append("")

    # Key Sections
    if doc.metadata.key_sections:
        lines.append("## Document Structure")
        lines.append("")
        for section in doc.metadata.key_sections:
            lines.append(f"- {section}")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Pages
    current_section = ""
    for page in doc.pages:
        # Section header if changed
        if page.section and page.section != current_section:
            lines.append(f"# {page.section}")
            lines.append("")
            current_section = page.section

        lines.append(f"## Page {page.page_number}")
        lines.append("")

        # Summary
        if page.summary:
            lines.append(page.summary)
            lines.append("")

        # Key Figures
        if page.key_figures:
            lines.append("### Key Figures")
            lines.append("")
            for kf in page.key_figures:
                unit = f" {kf.unit}" if kf.unit else ""
                context = f" ({kf.context})" if kf.context else ""
                lines.append(f"- **{kf.label}**: {kf.value}{unit}{context}")
            lines.append("")

        # Tables
        for table in page.tables:
            if table.title:
                lines.append(f"### {table.title}")
            if table.context:
                lines.append(f"*{table.context}*")
            lines.append("")

            if table.headers:
                lines.append("| " + " | ".join(table.headers) + " |")
                lines.append("| " + " | ".join(["---"] * len(table.headers)) + " |")
                for row in table.rows:
                    # Pad row if needed
                    padded = row + [""] * (len(table.headers) - len(row))
                    lines.append("| " + " | ".join(padded[:len(table.headers)]) + " |")
                lines.append("")

        lines.append("---")
        lines.append("")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(
        description='Convert PDF to LLM-friendly format with intelligent extraction.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic mode (no API key required)
  python pdf_to_llm.py --file document.pdf --mode basic --output result.json

  # LLM mode (requires ANTHROPIC_API_KEY)
  python pdf_to_llm.py --file document.pdf --mode llm --output result.md --format markdown

  # Auto mode (uses LLM if API key available, otherwise basic)
  python pdf_to_llm.py --url https://example.com/report.pdf --output result.json

  # Process specific pages only
  python pdf_to_llm.py --file document.pdf --pages "1,2,10-15,50" --output sample.json
"""
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--url', type=str, help='URL of the PDF to process')
    group.add_argument('--file', type=str, help='Path to a local PDF file')

    parser.add_argument('--output', type=str, default='output.json',
                        help='Output file path')
    parser.add_argument('--format', type=str, choices=['json', 'jsonl', 'markdown'],
                        default='json', help='Output format')
    parser.add_argument('--mode', type=str, choices=['llm', 'basic', 'auto'],
                        default='auto',
                        help='Processing mode: llm (requires API key), basic (no API), auto (default)')
    parser.add_argument('--model', type=str, default='claude-sonnet-4-20250514',
                        help='Claude model to use (for LLM mode)')
    parser.add_argument('--workers', type=int, default=5,
                        help='Number of parallel workers for page processing')
    parser.add_argument('--pages', type=str, default=None,
                        help='Specific pages to process (e.g., "1,2,5-10,15")')

    args = parser.parse_args()

    # Parse page ranges if specified
    sample_pages = None
    if args.pages:
        sample_pages = []
        for part in args.pages.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                sample_pages.extend(range(start, end + 1))
            else:
                sample_pages.append(int(part))

    # Get PDF path
    if args.url:
        filename = os.path.basename(args.url.split('?')[0]) or 'downloaded.pdf'
        pdf_path = os.path.join(tempfile.gettempdir(), filename)
        print(f'Downloading PDF from {args.url}...')
        download_pdf(args.url, pdf_path)
    else:
        pdf_path = args.file
        if not os.path.isfile(pdf_path):
            print(f'File not found: {pdf_path}', file=sys.stderr)
            sys.exit(1)

    # Process document
    doc = process_document(
        pdf_path,
        mode=args.mode,
        model=args.model,
        max_workers=args.workers,
        sample_pages=sample_pages
    )

    # Output in requested format
    output_funcs = {
        'json': output_json,
        'jsonl': output_jsonl,
        'markdown': output_markdown
    }

    output_funcs[args.format](doc, args.output)
    print(f"\nOutput saved to {args.output}")
    print(f"Processed {len(doc.pages)} pages from '{doc.metadata.title}'")


if __name__ == '__main__':
    main()
