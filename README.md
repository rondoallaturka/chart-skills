# Chart Skills

A repository for packaging and versioning Claude skills for both **Claude Code** (CLI) and **claude.ai** (web) environments.

## Structure

```
chart-skills/
├── skills/
│   ├── shared/           # Skills that work in both environments
│   ├── claude-code/      # CLI-specific skills
│   └── claude-ai/        # Web-specific skills
├── scripts/              # Processing scripts
├── schema/               # Validation schemas
└── output/               # Processed outputs (gitignored)
```

## Skills

### pdf-to-llm (v1.1.0)

Converts PDF documents into LLM-friendly formats with intelligent extraction.

**Features:**
- Document metadata extraction (title, entity, date, type)
- Section detection and heading identification
- Table extraction with preserved structure
- Key figure extraction with labels and units
- Multiple output formats (JSON, JSONL, Markdown)

**Processing Modes:**
- `auto` - Uses LLM if API key available, otherwise basic extraction
- `llm` - Intelligent extraction using Claude (requires ANTHROPIC_API_KEY)
- `basic` - Pattern-based extraction (no API key required)

**Usage:**

```bash
# Basic mode (no API key required)
python scripts/pdf_to_llm.py --file document.pdf --mode basic --output result.json

# LLM mode (requires API key)
export ANTHROPIC_API_KEY=your-key
python scripts/pdf_to_llm.py --file document.pdf --mode llm --output result.md --format markdown

# Process specific pages
python scripts/pdf_to_llm.py --file document.pdf --pages "1,2,10-20" --output sample.json
```

### census-data (v1.0.0)

Fetch US Census Bureau data via the public API with iterative discovery of endpoints, variables, and geography.

**Features:**
- Iterative discovery workflow (probe endpoints, find variable names, adjust)
- Covers ACS 1-Year, 5-Year, Subject Tables, Data Profiles, Selected Population Profiles, Decennial Census, County Business Patterns
- Variable search by keyword
- POPGROUP code discovery for population subgroups
- Common variable cheat sheet and 10 documented pitfalls

**Usage:**

```bash
# Search for variable names
python scripts/census_fetch.py search 2023 acs5 "median household income"

# Fetch median household income by state
python scripts/census_fetch.py fetch 2023 acs5 "NAME,B19013_001E" "state:*" -o output.csv

# Fetch poverty rate by county in Texas
python scripts/census_fetch.py fetch 2023 acs5_subject "NAME,S1701_C03_001E" "county:*" --in "state:48"

# Discover POPGROUP codes
python scripts/census_fetch.py popgroups 2024 "mexican"
```

### Claude Code
```
/census-data median household income by state
/pdf-to-llm path/to/document.pdf --format markdown --mode auto
```

### claude.ai
Upload PDF and use the skill instructions from `skills/shared/pdf-to-llm/skill.claude.txt`

## Output Formats

| Format | Description |
|--------|-------------|
| **JSON** | Structured data with metadata, pages, tables, and key figures |
| **JSONL** | Line-delimited JSON for streaming/batch processing |
| **Markdown** | Human-readable with frontmatter and formatted tables |

## Versioning

Skills follow semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes to skill interface
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes

## Dependencies

- Python 3.8+
- `requests`: `pip install requests`
- `pdftotext` (poppler-utils): `apt install poppler-utils`
- `anthropic` (optional, for LLM mode): `pip install anthropic`

## License

MIT
