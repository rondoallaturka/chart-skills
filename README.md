# Chart Skills

A collection of reusable Claude skills for data fetching, document processing, and chart generation. Skills work in both **Claude Code** (CLI) and **claude.ai** (web).

## What is a skill?

A skill is a packaged set of instructions and tools that teach Claude how to perform a specific task — fetching Census data, converting PDFs, generating charts, etc. Each skill includes:

- **`skill.md`** — Instructions for Claude Code (invoked via `/skill-name`)
- **`skill.claude.txt`** — Instructions for claude.ai (paste or upload)
- **`metadata.json`** — Version, tags, dependencies, changelog

Skills can optionally include supporting Python scripts in `scripts/`.

## Repository Structure

```
chart-skills/
├── skills/
│   ├── shared/              # Skills that work in both environments
│   │   ├── census-data/      # Census Bureau API data fetching
│   │   └── pdf-to-llm/      # PDF to LLM-friendly format conversion
│   ├── claude-code/         # CLI-specific skills
│   └── claude-ai/           # Web-specific skills
├── scripts/                 # Supporting Python scripts
│   ├── census_fetch.py      # Census API helper (search, fetch, discover)
│   ├── pdf_to_llm.py        # PDF extraction with LLM mode
│   └── pdf_digestible.py    # Legacy PDF extraction
└── output/                  # Generated files (gitignored)
```

## Skills

### census-data (v1.0.0)

Fetch US Census Bureau data via the public API. The Census API is powerful but quirky — variable names shift between years, endpoints differ by table type, and parameter codes change. This skill encodes the knowledge needed to navigate that iteratively.

**Covers:** ACS 1-Year, ACS 5-Year, Subject Tables, Data Profiles, Selected Population Profiles, Decennial Census, County Business Patterns

**Key feature:** An iterative discovery workflow that expects API calls to fail on first attempt and guides you through probe-and-adjust cycles.

```bash
# Claude Code
/census-data median household income by state

# Script: search for variables
python scripts/census_fetch.py search 2023 acs5 "median household income"

# Script: fetch data
python scripts/census_fetch.py fetch 2023 acs5 "NAME,B19013_001E" "state:*" -o output.csv

# Script: discover population subgroup codes
python scripts/census_fetch.py popgroups 2024 "mexican"
```

### pdf-to-llm (v1.1.0)

Convert PDF documents into structured formats optimized for language model processing.

**Modes:** `auto` (LLM if API key available, else basic), `llm` (requires ANTHROPIC_API_KEY), `basic` (pattern-based, no key needed)

**Output formats:** JSON, JSONL, Markdown

```bash
# Claude Code
/pdf-to-llm document.pdf --format markdown --mode auto

# Script
python scripts/pdf_to_llm.py --file document.pdf --mode basic --output result.json
```

## Creating a New Skill

### 1. Create the skill directory

```bash
mkdir -p skills/shared/my-skill
```

### 2. Write `metadata.json`

```json
{
  "name": "my-skill",
  "version": "1.0.0",
  "description": "What the skill does in one sentence",
  "author": "chart-skills",
  "license": "MIT",
  "compatibility": {
    "claude-code": true,
    "claude-ai": true
  },
  "tags": ["relevant", "tags"],
  "dependencies": {
    "python": ">=3.8",
    "required": ["requests"],
    "optional": ["anthropic"]
  },
  "files": {
    "claude-code": "skill.md",
    "claude-ai": "skill.claude.txt",
    "script": "../../scripts/my_script.py"
  },
  "changelog": [
    {
      "version": "1.0.0",
      "date": "2026-01-01",
      "changes": ["Initial release"]
    }
  ]
}
```

### 3. Write `skill.md` (Claude Code instructions)

Use YAML frontmatter for metadata, then write the instructions Claude Code should follow when the skill is invoked:

```markdown
---
name: my-skill
description: What the skill does
version: 1.0.0
tags: [relevant, tags]
---

# My Skill

## Usage
/my-skill <arguments>

## Instructions
When the user invokes this skill:
1. Step one...
2. Step two...
```

### 4. Write `skill.claude.txt` (claude.ai instructions)

Same guidance but adapted for the web environment (no file system access, no script execution). Focus on generating code the user can copy-paste or guiding them through manual steps.

### 5. Add supporting scripts (optional)

Place reusable Python scripts in `scripts/`. Design them to work both as CLI tools and importable modules.

### Design principles for skills

- **Expect iteration.** External APIs change. Document known failure modes and how to recover.
- **Encode tribal knowledge.** The value of a skill is the gotchas, pitfalls, and workarounds that took time to discover.
- **Keep scripts generic.** A skill's Python script should be a reusable tool, not a one-off query. Parameterize everything.
- **Document what you verified.** Note which endpoints/variables/parameters you actually tested and when.

## Versioning

Skills follow semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes to skill interface
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes

## Dependencies

- Python 3.8+
- `requests`: `pip install requests`
- `pdftotext` (poppler-utils): `apt install poppler-utils` (pdf-to-llm only)
- `anthropic` (optional, for LLM mode): `pip install anthropic`

## License

MIT
