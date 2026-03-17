# Enhanced doc_create_pdf — Design Spec

**Date:** 2026-03-17
**Status:** Approved

## Problem

The current `doc_create_pdf` tool uses reportlab with plain paragraph rendering. It lacks:
- Markdown support (headings, lists, tables, code blocks)
- Styling/theming options
- Page layout controls (size, orientation, margins)
- Robust content passing (current triple-quote f-string interpolation breaks on edge cases)

## Solution

Replace reportlab with WeasyPrint (HTML/CSS → PDF) and pre-bake HTML/CSS templates into the sandbox Docker image.

### Pipeline

```
content (markdown) → write to /tmp/_doc_content.md
                   → script reads file
                   → markdown lib → HTML
                   → inject into base.html template with selected CSS theme
                   → WeasyPrint → PDF
```

### New Schema

```json
{
  "content": "string (required) — markdown/text content",
  "output_path": "string — default /workspace/output.pdf",
  "title": "string — optional document title",
  "style": "string — default|report|article|minimal (default: default)",
  "custom_css": "string — optional CSS overrides appended after theme",
  "page_size": "string — A4|letter|legal (default: A4)",
  "orientation": "string — portrait|landscape (default: portrait)"
}
```

### Template Files (baked into Docker image)

```
/opt/doc_templates/
  base.html          — HTML wrapper with {title}, {content}, {css} placeholders
  styles/
    default.css      — Clean professional: system fonts, balanced margins
    report.css       — Formal: header/footer, page numbers, serif fonts
    article.css      — Article: wider margins, large body text, drop caps
    minimal.css      — Stripped-down: no decoration, max content density
```

### Files Changed

| File | Change |
|------|--------|
| `sandbox/Dockerfile.default` | Add weasyprint system deps + python packages, COPY templates |
| `sandbox/doc_templates/base.html` | New: HTML wrapper |
| `sandbox/doc_templates/styles/default.css` | New |
| `sandbox/doc_templates/styles/report.css` | New |
| `sandbox/doc_templates/styles/article.css` | New |
| `sandbox/doc_templates/styles/minimal.css` | New |
| `backend/agent/tools/sandbox/doc_gen.py` | Rewrite DocCreatePDF |
| `backend/tests/test_doc_gen.py` | Update PDF tests |

### Unchanged

- DocCreateDOCX, DocCreateXLSX, DocCreatePPTX — untouched
- _run_doc_script helper — still used
- Tool registration in api/main.py — no changes
- SandboxTool base class — compatible

### Content Passing Strategy

Write content as a separate file (`/tmp/_doc_content.md`) via `session.write_file()`. The generation script reads from this file. Eliminates all string escaping issues.

### Markdown Features

Via `markdown` library with extensions:
- `tables` — pipe tables
- `fenced_code` — triple-backtick code blocks
- `codehilite` — syntax highlighting via Pygments
- `toc` — table of contents generation
- `attr_list` — custom attributes on elements
