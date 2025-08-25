
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import re
import sys

# ---------- Config ----------
BIB_PATH = Path("reference.bib")                          # your .bib at repo root
OUT_PATH = Path("Publications/publications.md")           # full page written here
UNDER_REVIEW_MD = Path("_data/under_review.md")           # optional: manual block
YOUR_NAME_PATTERNS = [
    r"\bBrahmachary,\s*Shuvayan\b",
    r"\bShuvayan\s+Brahmachary\b",
    r"\bBrahmachary,\s*S\.?\b",
    r"\bS\.?\s*Brahmachary\b",
]
PAGE_TITLE = "Publications"
# ----------------------------

def latex_to_text(s: str) -> str:
    """Convert basic LaTeX to text; keep it simple & safe."""
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

def load_bib_entries(path: Path):
    """Load with pinned bibtexparser v1 API (see workflow)."""
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

def is_journal_like(entry: dict) -> bool:
    et = (entry.get("ENTRYTYPE") or entry.get("entrytype") or "").lower()
    if et == "article":
        return True
    if entry.get("journal") or entry.get("journaltitle"):
        return True
    return False

def render_under_review() -> str:
    """If _data/under_review.md exists, include it verbatim under an **Under Review** header."""
    if not UNDER_REVIEW_MD.exists():
        return ""
    txt = UNDER_REVIEW_MD.read_text(encoding="utf-8").strip()
    if not txt:
        return ""
    # If the user already put a header inside, just return it.
    if txt.lstrip().startswith("**Under Review**"):
        return txt + "\n\n"
    return "**Under Review**\n\n" + txt + "\n\n"

def main():
    entries = load_bib_entries(BIB_PATH)
    journals = [e for e in entries if is_journal_like(e)]
    journals.sort(key=get_year, reverse=True)

    page_lines = []
    # Front matter
    page_lines.append("---")
    page_lines.append("layout: page")
    page_lines.append(f"title: {PAGE_TITLE}")
    page_lines.append("---\n")

    # Optional "Under Review" block (pure Markdown from _data/under_review.md)
    under_review_block = render_under_review()
    if under_review_block:
        page_lines.append(under_review_block)

    # Published / Journals
    page_lines.append("**Published**\n")
    page_lines.append('# <span style="color:blue">Journals</span>\n')

    if not journals:
        page_lines.append("_No journal entries found in reference.bib._\n")
    else:
        for idx, e in enumerate(journals, start=1):
            # Authors: "A and B and C" -> "A, B, C", then bold your name
            authors_raw = get_field(e, "author")
            authors = bold_author_name(authors_raw.replace(" and ", ", "))

            # Clean title (remove surrounding quotes/braces)
            title = get_field(e, "title").strip(' "{}')
            journal = get_journal(e)
            year = get_field(e, "year")
            link_md = build_link(e)

            # Final line: number. Authors, _Title_, **Journal**, Year [Link](...)
            item = f"{idx}. {authors}, _{title}_"
            if journal:
                item += f", **{journal}**"
            if year:
                item += f", {year}"
            if link_md:
                item += f" {link_md}"
            page_lines.append(item + "\n")

    # Write file
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(page_lines).rstrip() + "\n", encoding="utf-8")
    print(f"[bib2pubs] wrote {OUT_PATH} with {len(journals)} journal items")

if __name__ == "__main__":
    main()
