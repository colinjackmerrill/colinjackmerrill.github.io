#!/usr/bin/env python3
"""
Generate the reading pages for colinmerrill.com from a Goodreads export.

Reads  data/goodreads_library_export.csv
Writes reading-log.html, book-reviews.html, reviews/<slug>.html, sitemap.xml

Re-export from Goodreads (My Books > Import and Export > Export Library),
drop the file into data/, and run this again. Everything regenerates.
"""
import csv, html, os, re, sys
from collections import defaultdict, Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV  = os.path.join(ROOT, "data", "goodreads_library_export.csv")
REVIEW_DIR = os.path.join(ROOT, "reviews")

# ---------------------------------------------------------------- helpers

HEADER = '''  <header class="site-header">
  <a href="/" class="site-title">
    Colin Merrill
    <svg width="20" height="18" viewBox="0 0 40 36" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M20 4 C20 4 12 2 4 4 L4 32 C12 30 20 32 20 32"/>
      <path d="M20 4 C20 4 28 2 36 4 L36 32 C28 30 20 32 20 32"/>
      <line x1="20" y1="4" x2="20" y2="32"/>
    </svg>
  </a>
</header>
'''

FOOTER = '''  <div id="footer-placeholder"></div>
<script>
  fetch('/footer.html')
    .then(res => res.text())
    .then(html => {
      document.getElementById('footer-placeholder').innerHTML = html;
      const link = document.getElementById('footer-main-link');
      if (window.location.pathname === '/about.html' || window.location.pathname === '/about') {
        link.textContent = 'Home';
        link.href = '/';
      }
    });
</script>
'''

def page(title, description, main, css_prefix=""):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <link rel="icon" href="/favicon.ico">
  <meta name="description" content="{html.escape(description, quote=True)}">
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="{css_prefix}style.css" />
</head>
<body>

{HEADER}
{main}
{FOOTER}
</body>
</html>
'''

SLUG_RE = re.compile(r"[^a-z0-9]+")
def slugify(*parts):
    s = SLUG_RE.sub("-", " ".join(parts).lower()).strip("-")
    return s[:80].strip("-")

def clean_title(t):
    """Drop the trailing series parenthetical Goodreads appends."""
    return re.sub(r"\s*\([^()]*#[^()]*\)\s*$", "", t).strip()

ALLOWED = {"br", "i", "b", "em", "strong"}
TAG_RE = re.compile(r"<\s*/?\s*([a-zA-Z0-9]+)[^>]*>")

def safe_review_html(raw):
    """Goodreads review text carries some inline HTML. Keep a small safe set,
    escape the rest, and split blank-line-separated blocks into paragraphs."""
    placeholders = {}
    def keep(m):
        tag = m.group(1).lower()
        if tag in ALLOWED:
            key = f"\x00{len(placeholders)}\x00"
            placeholders[key] = "<br>" if tag == "br" else m.group(0)
            return key
        return ""
    stashed = TAG_RE.sub(keep, raw)
    escaped = html.escape(stashed)
    for key, val in placeholders.items():
        escaped = escaped.replace(html.escape(key), val)
    escaped = escaped.replace("<br><br>", "\n\n")
    paras = [p.strip() for p in re.split(r"\n\s*\n", escaped) if p.strip()]
    return "\n".join(f"        <p>{p}</p>" for p in paras)

def stars(rating):
    try: r = int(float(rating))
    except (TypeError, ValueError): return ""
    return "★" * r + "☆" * (5 - r) if r else ""

MONTHS = ["January","February","March","April","May","June",
          "July","August","September","October","November","December"]
def pretty_date(d):
    m = re.match(r"(\d{4})/(\d{2})/(\d{2})", d or "")
    if not m: return ""
    y, mo, day = m.groups()
    return f"{MONTHS[int(mo)-1]} {int(day)}, {y}"

# ---------------------------------------------------------------- load

def load():
    if not os.path.exists(CSV):
        sys.exit(f"No export found at {CSV}\nDownload it from Goodreads: My Books > Import and Export > Export Library.")
    with open(CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    books = []
    for r in rows:
        if r.get("Exclusive Shelf") != "read":
            continue
        title = clean_title(r["Title"])
        books.append({
            "id": r["Book Id"],
            "title": title,
            "author": r["Author"].strip(),
            "rating": r["My Rating"],
            "date_read": r["Date Read"],
            "year": (r["Date Read"] or "")[:4],
            "review": r["My Review"].strip(),
            "spoiler": (r.get("Spoiler") or "").strip().lower() == "true",
            "pages": r["Number of Pages"],
            "slug": slugify(title, r["Author"].split()[-1] if r["Author"] else ""),
        })
    return books

# ---------------------------------------------------------------- pages

def build_reading_log(books):
    dated = [b for b in books if b["year"].isdigit()]
    undated = [b for b in books if not b["year"].isdigit()]
    by_year = defaultdict(list)
    for b in dated:
        by_year[b["year"]].append(b)
    years = sorted(by_year, reverse=True)

    nav = " ".join(f'<a href="#y{y}">{y}</a>' for y in years)
    out = ['  <main class="reading-log-page">', "    <h1>Annual Reading Log</h1>",
           f'    <p class="log-intro">Every book I have finished since I started keeping track. '
           f'{len(books)} books, {sum(int(b["pages"]) for b in books if b["pages"].isdigit()):,} pages.</p>',
           f'    <p class="log-nav">{nav}</p>']

    for y in years:
        items = sorted(by_year[y], key=lambda b: b["date_read"], reverse=True)
        out.append(f'    <section class="log-year" id="y{y}">')
        out.append(f'      <h2>{y} <span class="log-count">{len(items)} books</span></h2>')
        out.append('      <ul class="log-list">')
        for b in items:
            link = f'/reviews/{b["slug"]}.html' if b["review"] else None
            name = (f'<a href="{link}" class="log-title">{html.escape(b["title"])}</a>'
                    if link else f'<span class="log-title">{html.escape(b["title"])}</span>')
            out.append('        <li class="log-item">')
            out.append(f'          {name}')
            out.append(f'          <span class="log-author">{html.escape(b["author"])}</span>')
            if stars(b["rating"]):
                out.append(f'          <span class="log-rating">{stars(b["rating"])}</span>')
            out.append('        </li>')
        out.append("      </ul>")
        out.append("    </section>")

    if undated:
        out.append('    <section class="log-year" id="yundated">')
        out.append(f'      <h2>Undated <span class="log-count">{len(undated)} books</span></h2>')
        out.append('      <p class="log-intro">Read before I started logging dates.</p>')
        out.append('      <ul class="log-list">')
        for b in sorted(undated, key=lambda b: b["title"]):
            out.append('        <li class="log-item">')
            out.append(f'          <span class="log-title">{html.escape(b["title"])}</span>')
            out.append(f'          <span class="log-author">{html.escape(b["author"])}</span>')
            if stars(b["rating"]):
                out.append(f'          <span class="log-rating">{stars(b["rating"])}</span>')
            out.append('        </li>')
        out.append("      </ul>")
        out.append("    </section>")

    out.append("  </main>")
    return page("Annual Reading Log — Colin Merrill".replace("—","-"),
                f"A chronological record of every book Colin Merrill has read, {years[-1]} to {years[0]}.",
                "\n".join(out))

def build_reviews(books):
    reviewed = [b for b in books if b["review"] and not b["spoiler"]]
    reviewed.sort(key=lambda b: (b["date_read"] or "0000"), reverse=True)

    # individual pages
    seen = Counter()
    for b in reviewed:
        seen[b["slug"]] += 1
        if seen[b["slug"]] > 1:
            b["slug"] = f'{b["slug"]}-{seen[b["slug"]]}'
        body = safe_review_html(b["review"])
        meta = []
        if stars(b["rating"]): meta.append(f'<span class="review-rating">{stars(b["rating"])}</span>')
        if pretty_date(b["date_read"]): meta.append(f'<span class="review-date">Read {pretty_date(b["date_read"])}</span>')
        main = f'''  <main class="review-page">
    <p class="review-back"><a href="/book-reviews.html">Book Reviews</a></p>
    <article>
      <h1>{html.escape(b["title"])}</h1>
      <p class="review-author">{html.escape(b["author"])}</p>
      <p class="review-meta">{" ".join(meta)}</p>
      <div class="review-body">
{body}
      </div>
      <p class="review-source"><a href="https://www.goodreads.com/book/show/{b["id"]}" rel="nofollow">This book on Goodreads</a></p>
    </article>
  </main>'''
        desc = re.sub(r"<[^>]+>", "", body).strip().replace("\n", " ")[:155]
        with open(os.path.join(REVIEW_DIR, f'{b["slug"]}.html'), "w", encoding="utf-8") as f:
            f.write(page(f'{b["title"]} by {b["author"]} - Colin Merrill', desc, main, css_prefix="/"))

    # index
    by_year = defaultdict(list)
    for b in reviewed:
        by_year[b["year"] if b["year"].isdigit() else "Undated"].append(b)
    years = sorted([y for y in by_year if y != "Undated"], reverse=True)
    if "Undated" in by_year: years.append("Undated")

    out = ['  <main class="reviews-page">', "    <h1>Book Reviews</h1>",
           f'    <p class="log-intro">Considered responses to books I have finished. {len(reviewed)} reviews so far.</p>']
    for y in years:
        out.append('    <section class="log-year">')
        out.append(f'      <h2>{y} <span class="log-count">{len(by_year[y])} reviews</span></h2>')
        out.append('      <ul class="review-list">')
        for b in by_year[y]:
            out.append('        <li class="review-item">')
            out.append(f'          <a href="/reviews/{b["slug"]}.html" class="review-title">{html.escape(b["title"])}</a>')
            out.append(f'          <span class="review-author-inline">{html.escape(b["author"])}</span>')
            if stars(b["rating"]):
                out.append(f'          <span class="log-rating">{stars(b["rating"])}</span>')
            out.append('        </li>')
        out.append("      </ul>")
        out.append("    </section>")
    out.append("  </main>")
    return page("Book Reviews - Colin Merrill",
                f"{len(reviewed)} book reviews by Colin Merrill, covering literary fiction, classics, debuts and small press titles.",
                "\n".join(out)), len(reviewed)

# ---------------------------------------------------------------- sitemap

SITE = "https://colinmerrill.com"

def build_sitemap(review_slugs, review_dates):
    """Every page on the site, so search engines can find the reviews."""
    static = []
    for name in sorted(os.listdir(ROOT)):
        if name.endswith(".html") and name not in ("footer.html",) and not name.startswith("google"):
            static.append("/" if name == "index.html" else f"/{name}")
    for sub in ("essays", "writing-resources", "tools"):
        d = os.path.join(ROOT, sub)
        if not os.path.isdir(d):
            continue
        for dirpath, _, files in os.walk(d):
            for name in sorted(files):
                if name.endswith(".html"):
                    rel = os.path.relpath(os.path.join(dirpath, name), ROOT)
                    static.append("/" + rel.replace(os.sep, "/"))

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    def url(loc, lastmod=None, priority=None):
        out.append("  <url>")
        out.append(f"    <loc>{SITE}{loc}</loc>")
        if lastmod:
            out.append(f"    <lastmod>{lastmod}</lastmod>")
        if priority:
            out.append(f"    <priority>{priority}</priority>")
        out.append("  </url>")

    for loc in static:
        url(loc, priority="0.8" if loc in ("/", "/reading.html", "/book-reviews.html") else None)
    for slug in review_slugs:
        d = review_dates.get(slug, "")
        lastmod = d.replace("/", "-") if re.match(r"\d{4}/\d{2}/\d{2}", d) else None
        url(f"/reviews/{slug}.html", lastmod=lastmod, priority="0.7")
    out.append("</urlset>")
    return "\n".join(out) + "\n"

ROBOTS = f"""User-agent: *
Allow: /

Sitemap: {SITE}/sitemap.xml
"""

# ---------------------------------------------------------------- main

def main():
    books = load()
    os.makedirs(REVIEW_DIR, exist_ok=True)
    for old in os.listdir(REVIEW_DIR):
        if old.endswith(".html"):
            os.remove(os.path.join(REVIEW_DIR, old))

    with open(os.path.join(ROOT, "reading-log.html"), "w", encoding="utf-8") as f:
        f.write(build_reading_log(books))
    reviews_html, n = build_reviews(books)
    with open(os.path.join(ROOT, "book-reviews.html"), "w", encoding="utf-8") as f:
        f.write(reviews_html)

    slugs = [b["slug"] for b in books if b["review"] and not b["spoiler"]]
    dates = {b["slug"]: b["date_read"] for b in books}
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(build_sitemap(slugs, dates))
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(ROBOTS)

    skipped = sum(1 for b in books if b["review"] and b["spoiler"])
    print(f"reading-log.html   {len(books)} books")
    print(f"book-reviews.html  {n} reviews  ({len(os.listdir(REVIEW_DIR))} pages in reviews/)")
    urls = open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read().count("<loc>")
    print(f"sitemap.xml        {urls} urls")
    print(f"robots.txt         written")
    if skipped:
        print(f"skipped            {skipped} review(s) flagged as spoilers on Goodreads")

if __name__ == "__main__":
    main()
