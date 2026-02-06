---
name: pdf-to-llm
description: Convert PDF documents into LLM-friendly formats with intelligent extraction
version: 1.1.0
author: chart-skills
tags: [pdf, conversion, summarization, data-extraction, tables]
---

# PDF to LLM Converter

Convert large PDF documents into structured formats optimized for language model processing.

## Features

- **Document metadata extraction** - Title, entity, date period, type
- **Section detection** - Identifies document sections and headers
- **Table extraction** - Preserves table structures with headers and rows
- **Key figure extraction** - Extracts numerical values with labels and units
- **Multiple output formats** - JSON, JSONL, Markdown

## Usage

```
/pdf-to-llm <path-or-url> [--format <format>] [--mode <mode>] [--pages <pages>]
```

### Arguments

- `path-or-url`: Local file path or URL to the PDF document
- `--format`: Output format - `json` (default), `jsonl`, or `markdown`
- `--mode`: Processing mode:
  - `auto` (default): Uses LLM if API key available, otherwise basic
  - `llm`: Requires ANTHROPIC_API_KEY for intelligent extraction
  - `basic`: No API key needed, uses pattern-based extraction
- `--pages`: Specific pages to process (e.g., "1,2,10-20,50")

## Instructions

When the user invokes this skill:

1. **Run the enhanced processing script**:
   ```bash
   python scripts/pdf_to_llm.py --file <path> --output output/<name>.json --mode auto
   ```
   Or for URLs:
   ```bash
   python scripts/pdf_to_llm.py --url <url> --output output/<name>.md --format markdown
   ```

2. **For LLM mode**, ensure ANTHROPIC_API_KEY is set:
   ```bash
   export ANTHROPIC_API_KEY=your-key-here
   python scripts/pdf_to_llm.py --file <path> --mode llm --output result.json
   ```

3. **Process specific pages** for faster testing:
   ```bash
   python scripts/pdf_to_llm.py --file <path> --pages "1,2,10-15" --output sample.json
   ```

## Output Structure

### JSON
```json
{
  "metadata": {
    "title": "LATAM Airlines Group Financial Statements",
    "document_type": "financial_report",
    "entity": "LATAM Airlines Group S.A.",
    "date_period": "December 31, 2025",
    "total_pages": 149,
    "source_file": "financial-statements.pdf",
    "processed_at": "2025-02-06T...",
    "executive_summary": "Consolidated financial statements showing...",
    "key_sections": ["Balance Sheet", "Income Statement", "Notes"]
  },
  "pages": [
    {
      "page_number": 1,
      "section": "Balance Sheet",
      "summary": "Total assets of $17.6 billion...",
      "key_figures": [
        {"label": "Total Assets", "value": "17,640,891", "unit": "ThUS$", "context": "As of Dec 31, 2025"}
      ],
      "tables": [
        {
          "title": "Assets",
          "headers": ["Item", "Note", "2025", "2024"],
          "rows": [["Cash", "6-7", "2,150,113", "1,957,788"]],
          "context": "Current and non-current assets"
        }
      ],
      "raw_text": "..."
    }
  ]
}
```

### JSONL
```jsonl
{"type": "metadata", "title": "...", "entity": "...", ...}
{"type": "page", "page_number": 1, "section": "...", "summary": "...", ...}
{"type": "page", "page_number": 2, "section": "...", "summary": "...", ...}
```

### Markdown
```markdown
---
title: "LATAM Airlines Group Financial Statements"
entity: "LATAM Airlines Group S.A."
document_type: financial_report
period: "December 31, 2025"
total_pages: 149
---

# Executive Summary

Consolidated financial statements showing...

---

# Balance Sheet

## Page 1

Summary of page content...

### Key Figures

- **Total Assets**: 17,640,891 ThUS$ (As of Dec 31, 2025)

### Assets

| Item | Note | 2025 | 2024 |
|------|------|------|------|
| Cash | 6-7 | 2,150,113 | 1,957,788 |
```

## Dependencies

- Python 3.8+
- `pdftotext` (poppler-utils)
- `anthropic` (optional, for LLM mode)

## Environment Variables

- `ANTHROPIC_API_KEY`: Required for LLM mode, enables intelligent extraction
