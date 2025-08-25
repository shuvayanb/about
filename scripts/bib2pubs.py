#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import re
import sys

# ----- CONFIG -----
BIB_PATH = Path("reference.bib")                  # <- read ONLY this file
OUT_PATH = Path("Publications/publications.md")   # full page output
PAGE_TITLE = "Publications"
YOUR_NAME_PATTERNS = [
    r"\bBrahmachary,\s*Shuvayan\b",
    r"\bShuvayan\s+Brahmachary\b",
    r"\bBrahmachary,\s*S\.?\b",
    r"\bS\.?\s*Brahmachary\b",
]
# ------------------

def latex_to_text(s: str) -> str:
    try:
        from pylatexenc.latex2text import LatexNodes2Text  # type: ignore
        return LatexNodes2Text().latex_to_text(s or "")
    except Exception:
        s = (s or "")
        s = s.replace("{", "").replace("}", "")
        s = s.replace("\\&", "&").replace("\\%", "%").replace("\\_", "_")
        s = s.replace("``", '"').replace("''", '"')
        return s

def f(e: dict, key: str) -> str:
    return latex_to_text((e.get(key) or "").strip())

def bold_author_name(author_str: str) -> str:
    out = author_str
    for pat in YOUR_NAME_PATTERNS:
        out = re.sub(pat, lambda m: f"**{m.group(0)}**", out, flags=re.IGNORECASE)
    return out

def build_link(e: dict) -> str:
    url = (e.get("url") or "").strip().strip("{}")
    if url:
        return f"[Link]({url})"
    doi = (e.get("doi") or "").strip().strip("{}")
    if doi:
        if not doi.lower().startswith("http"):
            doi = f"https://doi.org/{doi}"
        return f"[Link]({doi})"
    return ""

def get_year(e: dict) -> int:
    y = f(e, "year")
    m = re.search(r"\d{4}", y)
    return int(m.group(0)) if m else 0

def get_journal(e: dict) -> str:
    return (f(e, "journal") or f(e, "journaltitle")).strip()

def get_booktitle(e: dict) -> str:
    return f(e, "booktitle").strip()

def is_journal_like(e: dict) -> bool:
    et = (e.get("ENTRYTYPE") or e.get("entrytype") or "").lower()
    return et == "article" or bool(e.get("journal") or e.get("journaltitle"))

def is_book_chapter(e: dict) -> bool:
    et = (e.get("ENTRYTYPE") or e.get("entrytype") or "").lower()
    return et == "incollection" or bool(e.get("booktitle"))

def load_bib(path: Path) -> list[dict]:
    print(f"[bib2pubs] Using BIB_PATH: {path.resolve()}")
    if not path.exists():
        print(f"[bib2pubs] ERROR: {path} not found", file=sys.stderr)
        return []
    try:
        import bibtexparser  # type: ignore
        from bibtexparser.bparser import BibTexParser  # type: ignore
        from bibtexparser.customization import convert_to_unicode  # type: ignore
        parser = BibTexParser(common_strings=True)
        parser.customization = convert_to_unicode
        with open(path, "r", encoding="utf-8") as f:
            db = bibtexparser.load(f, parser=parser)
        entries = db.entries or []
        print(f"[bib2pubs] parsed {len(entries)} total entries")
        return entries
    except Exception as ex:
        print(f"[bib2pubs] ERROR parsing bib: {ex}", file=sys.stderr)
        return []

def render_section(title_html: str, items: list[dict], journal_mode: bool) -> list[str]:
    lines = []
    lines.append(f'# <span style="color:blue">{title_html}</span>\n')
    if not items:
        lines.append("_No entries._\n")
        return lines

    items.sort(key=get_year, reverse=True)
    for idx, e in enumerate(items, start=1):
        authors = bold_author_name(f(e, "author").replace(" and ", ", "))
        title = f(e, "title").strip(' "{}')
        venue = get_journal(e) if journal_mode else get_booktitle(e)
        year = f(e, "year")
        link_md = build_link(e)

        item = f"{idx}. {authors}, _{title}_"
        if venue:
            item += f", **{venue}**"
        if year:
            item += f", {year}"
        if link_md:
            item += f" {link_md}"
        lines.append(item + "\n")
    return lines

def main():
    entries = load_bib(BIB_PATH)
    journals = [e for e in entries if is_journal_like(e)]
    chapters = [e for e in entries if is_book_chapter(e)]
    print(f"[bib2pubs] journals: {len(journals)}, chapters: {len(chapters)}")

    lines = []
    lines.append("---")
    lines.append("layout: page")
    lines.append(f"title: {PAGE_TITLE}")
    lines.append("---\n")

    lines.append("**Published**\n")
    lines.extend(render_section("Journals", journals, journal_mode=True))
    lines.append("\n")
    lines.extend(render_section("Book Chapters", chapters, journal_mode=False))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"[bib2pubs] wrote {OUT_PATH}")

if __name__ == "__main__":
    main()
