---
name: pdf-to-llm
description: Convert PDF documents into LLM-friendly formats with intelligent summarization
version: 1.0.0
author: chart-skills
tags: [pdf, conversion, summarization, data-extraction]
---

# PDF to LLM Converter

Convert large PDF documents into formats optimized for language model processing.

## Usage

```
/pdf-to-llm <path-or-url> [--format <format>] [--ratio <ratio>]
```

### Arguments

- `path-or-url`: Local file path or URL to the PDF document
- `--format`: Output format - `json` (default), `jsonl`, or `markdown`
- `--ratio`: Summary ratio per page (0.1-1.0, default: 0.3)

## Instructions

When the user invokes this skill:

1. **Locate the PDF processing script** at `scripts/pdf_digestible.py`

2. **Run the script** with appropriate arguments:
   ```bash
   python scripts/pdf_digestible.py --file <path> --output output/<name>.json --ratio <ratio>
   ```
   Or for URLs:
   ```bash
   python scripts/pdf_digestible.py --url <url> --output output/<name>.json --ratio <ratio>
   ```

3. **Convert to requested format** if not JSON:
   - For JSONL: Convert JSON array to newline-delimited JSON objects
   - For Markdown: Generate structured markdown with frontmatter

4. **Output structure** should include:
   - Document metadata (source, pages, processing date)
   - Per-page summaries with page numbers
   - Key information extracted (tables, figures mentioned)

## Output Formats

### JSON
```json
{
  "metadata": {
    "source": "document.pdf",
    "pages": 149,
    "processed_at": "2025-02-06T..."
  },
  "content": [
    {"page": 1, "summary": "..."},
    {"page": 2, "summary": "..."}
  ]
}
```

### JSONL
```jsonl
{"page": 1, "summary": "..."}
{"page": 2, "summary": "..."}
```

### Markdown
```markdown
---
source: document.pdf
pages: 149
---

# Document Summary

## Page 1
...

## Page 2
...
```

## Dependencies

- Python 3.8+
- `pdftotext` (poppler-utils)
