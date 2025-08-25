#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import re
import sys

# -------- Output destination (writes the full page) --------
OUT_PATH = Path("Publications/publications.md")

# -------- Your name bolding patterns --------
YOUR_NAME_PATTERNS = [
    r"\bBrahmachary,\s*Shuvayan\b",
    r"\bShuvayan\s+Brahmachary\b",
    r"\bBrahmachary,\s*S\.?\b",
    r"\bS\.?\s*Brahmachary\b",
]

PAGE_TITLE = "Publications"

# -------- LaTeX cleanup --------
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

def get_field(entry: dict, key: str) -> str:
    return latex_to_text((entry.get(key) or "").strip())

def get_journal(entry: dict) -> str:
    # BibTeX vs BibLaTeX
    j = entry.get("journal") or entry.get("journaltitle") or ""
    return latex_to_text(j.strip())

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

def is_journal_like(entry: dict) -> bool:
    et = (entry.get("ENTRYTYPE") or entry.get("entrytype") or "").lower()
    if et == "article":
        return True
    if entry.get("journal") or entry.get("journaltitle"):
        return True
    return False

def find_best_bib() -> tuple[list[dict], Path | None]:
    """
    Try common locations first; if none succeed, scan for any .bib and pick the
    one that yields the most entries.
    """
    preferred = [
        Path("reference.bib"),
        Path("Publications/reference.bib"),
        Path("_data/reference.bib"),
        Path("references.bib"),
    ]
    # Try preferred paths
    for p in preferred:
        if p.exists():
            entries = load_bib_entries(p)
            if entries:
                (Path(".") / ".bib2pubs_last_bib.txt").write_text(str(p), encoding="utf-8")
                return entries, p

    # Fallback: scan repo for any .bib
    candidates = []
    for p in Path(".").rglob("*.bib"):
        if any(seg in p.parts for seg in (".git", "_site", "node_modules")):
            continue
        candidates.append(p)

    best_entries: list[dict] = []
    best_path: Path | None = None
    for p in candidates:
        entries = load_bib_entries(p)
        if len(entries) > len(best_entries):
            best_entries, best_path = entries, p

    if best_path:
        (Path(".") / ".bib2pubs_last_bib.txt").write_text(str(best_path), encoding="utf-8")
    else:
        (Path(".") / ".bib2pubs_last_bib.txt").write_text("NO_BIB_FOUND", encoding="utf-8")

    return best_entries, best_path

def main():
    # Locate and load a bib with entries
    all_entries, bib_path = find_best_bib()

    # Keep journal-like only (still ok if year missing)
    journals = [e for e in all_entries if is_journal_like(e)]
    journals.sort(key=get_year, reverse=True)

    # Build the full page (front matter + content)
    lines = []
    lines.append("---")
    lines.append("layout: page")
    lines.append(f"title: {PAGE_TITLE}")
    lines.append("---\n")

    lines.append("**Published**\n")
    lines.append('# <span style="color:blue">Journals</span>\n')

    if not journals:
        if bib_path is None:
            lines.append("_No .bib file found in the repo._\n")
        else:
            lines.append(f"_No journal entries found in {bib_path.name}._\n")
    else:
        for idx, e in enumerate(journals, start=1):
            # Authors
            authors_raw = get_field(e, "author")
            authors = bold_author_name(authors_raw.replace(" and ", ", "))

            # Title / venue / year / link
            title = get_field(e, "title").strip(' "{}')
            journal = get_journal(e)
            year = get_field(e, "year")
            link_md = build_link(e)

            item = f"{idx}. {authors}, _{title}_"
            if journal:
                item += f", **{journal}**"
            if year:
                item += f", {year}"
            if link_md:
                item += f" {link_md}"
            lines.append(item + "\n")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"[bib2pubs] wrote {OUT_PATH} with {len(journals)} journal items")

if __name__ == "__main__":
    main()
