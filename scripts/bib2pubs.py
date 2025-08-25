#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import re
import sys

# ----- CONFIG -----
# Read BOTH bib files (if present)
BIB_PATHS = [Path("Publications/references.bib")]
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

def etype(e: dict) -> str:
    return (e.get("ENTRYTYPE") or e.get("entrytype") or "").lower()

def is_journal_like(e: dict) -> bool:
    return etype(e) == "article" or bool(e.get("journal") or e.get("journaltitle"))

def is_book_chapter(e: dict) -> bool:
    return etype(e) == "incollection" or (bool(e.get("booktitle")) and etype(e) not in ("inproceedings",))

def is_conference(e: dict) -> bool:
    return etype(e) == "inproceedings"

# ---------- primary parser (bibtexparser v1) ----------
def load_bib_with_bibtexparser(path: Path) -> list[dict]:
    try:
        import bibtexparser  # type: ignore
        from bibtexparser.bparser import BibTexParser  # type: ignore
        from bibtexparser.customization import convert_to_unicode  # type: ignore
        ver = getattr(bibtexparser, "__version__", "unknown")
        print(f"[bib2pubs] bibtexparser version: {ver}")
        parser = BibTexParser(common_strings=True)
        parser.customization = convert_to_unicode
        with open(path, "r", encoding="utf-8") as f:
            db = bibtexparser.load(f, parser=parser)
        entries = db.entries or []
        print(f"[bib2pubs] parsed {len(entries)} entries with bibtexparser from {path}")
        return entries
    except Exception as ex:
        print(f"[bib2pubs] WARN: bibtexparser failed on {path}: {ex}", file=sys.stderr)
        return []

# ---------- fallback parser (regex) ----------
FIELD_RE = re.compile(
    r'(?mi)^\s*([A-Za-z][A-Za-z0-9_-]*)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|"[^"]*")\s*,?\s*$'
)
ENTRY_RE = re.compile(
    r'@(?P<type>\w+)\s*{\s*(?P<id>[^,]+)\s*,(?P<body>.*?)\n}\s*',
    re.DOTALL | re.IGNORECASE,
)

def strip_braces_quotes(v: str) -> str:
    v = v.strip().strip(",")
    if (v.startswith("{") and v.endswith("}")) or (v.startswith('"') and v.endswith('"')):
        v = v[1:-1]
    return v.strip()

def parse_bib_fallback(text: str, src: Path) -> list[dict]:
    entries = []
    for m in ENTRY_RE.finditer(text):
        et = m.group("type").strip()
        eid = m.group("id").strip()
        body = m.group("body")
        d = {"ENTRYTYPE": et, "ID": eid}
        for fm in FIELD_RE.finditer(body):
            key = fm.group(1).lower()
            val = strip_braces_quotes(fm.group(2))
            d[key] = val
        entries.append(d)
    print(f"[bib2pubs] fallback parsed {len(entries)} entries from {src}")
    return entries

def load_one(path: Path) -> list[dict]:
    if not path.exists():
        print(f"[bib2pubs] NOTE: {path} not found, skipping")
        return []
    print(f"[bib2pubs] Using BIB: {path.resolve()}")
    entries = load_bib_with_bibtexparser(path)
    if entries:
        return entries
    # fallback
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        text = path.read_text(errors="replace")
    return parse_bib_fallback(text, path)

def dedupe(entries: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for e in entries:
        key = (etype(e), (e.get("ID") or e.get("id") or "").lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out

def load_all(paths: list[Path]) -> list[dict]:
    all_entries: list[dict] = []
    for p in paths:
        all_entries.extend(load_one(p))
    all_entries = dedupe(all_entries)
    print(f"[bib2pubs] total entries combined: {len(all_entries)}")
    return all_entries

def render_section(title_html: str, items: list[dict], mode: str) -> list[str]:
    """
    mode: 'journal' | 'chapter' | 'conf'
    journal -> use journal/journaltitle
    chapter/conf -> use booktitle
    """
    lines = []
    lines.append(f'# <span style="color:blue">{title_html}</span>\n')
    if not items:
        lines.append("_No entries._\n")
        return lines

    items.sort(key=get_year, reverse=True)
    for idx, e in enumerate(items, start=1):
        authors = bold_author_name(f(e, "author").replace(" and ", ", "))
        title = f(e, "title").strip(' "{}')
        venue = get_journal(e) if mode == "journal" else get_booktitle(e)
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
    entries = load_all(BIB_PATHS)

    journals   = [e for e in entries if is_journal_like(e)]
    chapters   = [e for e in entries if is_book_chapter(e)]
    conferences= [e for e in entries if is_conference(e)]
    print(f"[bib2pubs] journals: {len(journals)}, chapters: {len(chapters)}, conferences: {len(conferences)}")

    lines = []
    lines.append("---")
    lines.append("layout: page")
    lines.append(f"title: {PAGE_TITLE}")
    lines.append("---\n")

    lines.append("**Published**\n")
    # Journals
    lines.extend(render_section("Journals", journals, mode="journal"))
    lines.append("\n")
    # Book Chapters
    lines.extend(render_section("Book Chapters", chapters, mode="chapter"))
    lines.append("\n")
    # Conferences
    lines.extend(render_section("Conferences", conferences, mode="conf"))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"[bib2pubs] wrote {OUT_PATH}")

if __name__ == "__main__":
    main()
