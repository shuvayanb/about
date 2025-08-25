#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import re
import sys

# ---------- Config ----------
OUT_PATH = Path("Publications/publications.md")   # writes the full page

YOUR_NAME_PATTERNS = [
    r"\bBrahmachary,\s*Shuvayan\b",
    r"\bShuvayan\s+Brahmachary\b",
    r"\bBrahmachary,\s*S\.?\b",
    r"\bS\.?\s*Brahmachary\b",
]

PAGE_TITLE = "Publications"
# ----------------------------

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

def bold_author_name(author_str: str) -> str:
    out = author_str
    for pat in YOUR_NAME_PATTERNS:
        out = re.sub(pat, lambda m: f"**{m.group(0)}**", out, flags=re.IGNORECASE)
    return out

def build_link(entry: dict) -> str:
    """Prefer URL; fall back to DOI as a URL. Render as [Link](...)."""
    url = (entry.get("url") or "").strip().strip("{}")
    if url:
        return f"[Link]({url})"
    doi = (entry.get("doi") or "").strip().strip("{}")
    if doi:
        if not doi.lower().startswith("http"):
            doi = f"https://doi.org/{doi}"
        return f"[Link]({doi})"
    return ""

def get_year(entry: dict) -> int:
    y = (entry.get("year") or "").strip()
    m = re.search(r"\d{4}", y)
    return int(m.group(0)) if m else 0

def f(entry: dict, key: str) -> str:
    return latex_to_text((entry.get(key) or "").strip())

def get_journal(entry: dict) -> str:
    return latex_to_text((entry.get("journal") or entry.get("journaltitle") or "").strip())

def get_booktitle(entry: dict) -> str:
    return latex_to_text((entry.get("booktitle") or "").strip())

# -------- Bib loading (pinned to bibtexparser v1 API in CI) --------
def load_bib_entries(path: Path):
    try:
        import bibtexparser  # type: ignore
        from bibtexparser.bparser import BibTexParser  # type: ignore
        from bibtexparser.customization import convert_to_unicode  # type: ignore
    except Exception as ex:
        print(f"[bib2pubs] ERROR importing bibtexparser: {ex}", file=sys.stderr)
        return []

    try:
        parser = BibTexParser(common_strings=True)
        parser.customization = convert_to_unicode
        with open(path, "r", encoding="utf-8") as f:
            db = bibtexparser.load(f, parser=parser)
        entries = db.entries or []
        print(f"[bib2pubs] parsed {len(entries)} entries from {path}")
        return entries
    except Exception as ex:
        print(f"[bib2pubs] ERROR parsing {path}: {ex}", file=sys.stderr)
        return []

def is_journal_like(e: dict) -> bool:
    et = (e.get("ENTRYTYPE") or e.get("entrytype") or "").lower()
    return et == "article" or bool(e.get("journal") or e.get("journaltitle"))

def is_book_chapter(e: dict) -> bool:
    et = (e.get("ENTRYTYPE") or e.get("entrytype") or "").lower()
    return et == "incollection" or bool(e.get("booktitle"))

def find_best_bib() -> tuple[list[dict], Path | None]:
    preferred = [
        Path("reference.bib"),
        Path("Publications/reference.bib"),
        Path("_data/reference.bib"),
        Path("references.bib"),
    ]
    for p in preferred:
        if p.exists():
            entries = load_bib_entries(p)
            if entries:
                (Path(".") / ".bib2pubs_last_bib.txt").write_text(str(p), encoding="utf-8")
                return entries, p

    best_entries: list[dict] = []
    best_path: Path | None = None
    for p in Path(".").rglob("*.bib"):
        if any(seg in p.parts for seg in (".git", "_site", "node_modules")):
            continue
        entries = load_bib_entries(p)
        if len(entries) > len(best_entries):
            best_entries, best_path = entries, p

    if best_path:
        (Path(".") / ".bib2pubs_last_bib.txt").write_text(str(best_path), encoding="utf-8")
    else:
        (Path(".") / ".bib2pubs_last_bib.txt").write_text("NO_BIB_FOUND", encoding="utf-8")

    return best_entries, best_path

def render_section(title_html: str, items: list[dict], is_journal: bool) -> list[str]:
    """Render a numbered list section. For journals use journal name; for chapters use booktitle."""
    lines = []
    lines.append(f'# <span style="color:blue">{title_html}</span>\n')
    if not items:
        lines.append("_No entries._\n")
        return lines

    # Sort newest first
    items.sort(key=get_year, reverse=True)

    for idx, e in enumerate(items, start=1):
        authors = bold_author_name(f(e, "author").replace(" and ", ", "))
        title = f(e, "title").strip(' "{}')
        venue = get_journal(e) if is_journal else get_booktitle(e)
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
    entries, bib_path = find_best_bib()

    journals = [e for e in entries if is_journal_like(e)]
    chapters = [e for e in entries if is_book_chapter(e)]

    lines = []
    lines.append("---")
    lin
