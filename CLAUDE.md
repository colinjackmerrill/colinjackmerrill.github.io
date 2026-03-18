# colinmerrill.com — Claude Code Briefing

## About the Site
Personal site for Colin Merrill — writer, literary blogger, Director of Business Development at Emerald Inc. Hosted on GitHub Pages at colinjackmerrill.github.io. Hand-coded HTML/CSS, no build system, no Jekyll.

## Fonts
- Cormorant Garamond (headings)
- Crimson Pro (body)
- Loaded via Google Fonts

## Site Structure
- `index.html` — homepage
- `about.html` — about page
- `essays.html` — essays hub
- `reading.html` — reading/books page
- `writing.html` — writing page
- `writing-tools.html` — writing tools hub
- `writing-resources.html` — writing resources
- `tools/` — individual writing tools
  - `character-psychology.html`
  - `book-rater.html`
- `essays/` — individual essay files
- `footer.html` — shared footer loaded via fetch()
- `style.css` — global styles
- `script.js` — global scripts

## Conventions
- Footer is loaded dynamically via `fetch('/footer.html')` — never hardcode the footer in a page
- New pages should follow the structure of existing pages
- File names are lowercase with hyphens
- No em dashes anywhere in copy
- Writing is clean, minimal, purposeful — no ornate or formulaic language

## Writing Tools
- Tools live in `/tools/`
- Tools use typeable fields, not pure generators
- Tools have static "Help me think" guide panels
- Tools have "Suggest one" fallback buttons
- Tools follow the writer-first design philosophy

## Book Reviews
Four-paragraph format: hook, craft analysis, critical placement, rating justification
- No spoilers beyond publisher description
- Tight length
- Varied structure across reviews

## Style Preferences
- Minimal formatting
- No em dashes
- Clean and purposeful over ornate
