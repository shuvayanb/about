#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import re
import sys

# Optional deps are installed in the GH Action
try:
    import bibtexparser  # type: ignore
except Exception as e:
    print("Please install bibtexparser (pip install bibtexparser)", file=sys.stderr)
    raise

# Optional LaTeX→Unicode cleanup for titles/authors
try:
    from pylatexenc.latex2text import LatexNodes2Text  # type: ignore
    L2T = LatexNodes2Text()
    def latex_to_text(s: str) -> str:
        return L2T.latex_to_text(s or "")
except Exception:
    def latex_to_text(s: str) -> str:
        # minimal cleanup if pylatexenc unavailable
        s = (s or "").replace("{", "").replace("}", "")
        s = s.replace("\\&", "&").replace("\\%", "%").replace("\\_", "_")
        return s

# ---------- config ----------
BIB_PATH = Path("Publications/references.bib")   
OUT_PATH = Path("_includes/publications_list.md")
YOUR_NAME_PATTERNS = [
    r"\bBrahmachary,\s*Shuvayan\b",
    r"\bShuvayan\s+Brahmachary\b",
    r"\bBrahmachary,\s*S\.\b",
    r"\bS\.\s*Brahmachary\b",
]
# ----------------------------

def bold_your_name(author_str: str) -> str:
    out = author_str
    for pat in YOUR_NAME_PATTERNS:
        out = re.sub(pat, lambda m: f"**{m.group(0)}**", out, flags=re.IGNORECASE)
    return out

def build_link(entry: dict) -> str:
    doi = entry.get("doi", "").strip()
    url = entry.get("url", "").strip()
    if doi:
        doi = doi.lstrip().rstrip()
        if not doi.lower().startswith("http"):
            return f"https://doi.org/{doi}"
        return doi
    return url

def get_field(entry: dict, key: str) -> str:
    return latex_to_text(entry.get(key, "")).strip()

def build_link(entry: dict) -> str:
    # Prefer URL if present; otherwise fall back to DOI as a URL
    url = entry.get("url", "").strip().strip("{}")
    if url:
        return url
    doi = entry.get("doi", "").strip().strip("{}")
    if doi:
        return doi if doi.lower().startswith("http") else f"https://doi.org/{doi}"
    return ""


def main():
    if not BIB_PATH.exists():
        print(f"ERROR: {BIB_PATH} not found.", file=sys.stderr)
        sys.exit(1)

    with open(BIB_PATH, "r", encoding="utf-8") as f:
        db = bibtexparser.load(f)

    # keep only @article
    articles = [e for e in db.entries if e.get("ENTRYTYPE", "").lower() == "article"]

    # sort by year desc (missing year → 0)
    def year_of(e):
        try:
            return int(re.findall(r"\d{4}", e.get("year", ""))[0])
        except Exception:
            return 0
    articles.sort(key=year_of, reverse=True)

    lines = []
    # Header block (matches your current style)
    lines.append("**Published**\n")
    lines.append('# <span style="color:blue">Journals</span>\n')

    for idx, e in enumerate(articles, start=1):
        authors = get_field(e, "author")
        authors = authors.replace(" and ", ", ")
        authors = bold_your_name(authors)

        title = get_field(e, "title")
        # strip surrounding quotes/braces if present
        title = title.strip(' "{}')

        journal = get_field(e, "journal")
        year = get_field(e, "year")
        link = build_link(e)

        # Build one-line item. Keep it minimal & consistent with your commented template.
        # Example:
        # 1. Author list, _Title_, **Journal**, 2024 [DOI-Link](...)
        item = f"{idx}. {authors}, _{title}_, **{journal}**"
        if year:
            item += f", {year}"
        link = build_link(e)
        if link:
            item += f" [Link]({link})"

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH}")

if __name__ == "__main__":
    main()
