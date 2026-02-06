# Chart Skills

A repository for packaging and versioning Claude skills for both **Claude Code** (CLI) and **claude.ai** (web) environments.

## Structure

```
chart-skills/
├── skills/
│   ├── shared/           # Skills that work in both environments
│   ├── claude-code/      # CLI-specific skills
│   └── claude-ai/        # Web-specific skills
├── scripts/              # Build and conversion tools
├── schema/               # Validation schemas
└── output/               # Processed outputs (gitignored)
```

## Skills

### pdf-to-llm

Converts PDF documents into LLM-friendly formats (Markdown, JSON, JSONL) with intelligent chunking and metadata extraction.

**Formats:**
- **Markdown** - Human-readable with frontmatter metadata
- **JSON** - Structured data with sections and chunks
- **JSONL** - Line-delimited JSON for streaming/batch processing

## Usage

### Claude Code
```
/pdf-to-llm path/to/document.pdf --format markdown
```

### claude.ai
Upload PDF and use the skill instructions from `skills/shared/pdf-to-llm/skill.claude.txt`

## Versioning

Skills follow semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes to skill interface
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes

## License

MIT
