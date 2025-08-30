#!/usr/bin/env python3
from pathlib import Path
import re
import json

BIB_FILE = Path("Publications/references.bib")     # <-- your single source of truth
OUT_MD   = Path("Publications/publications.md")
OUT_JSON = Path("assets/data/pubs.json")           # optional; handy later

def read_bib():
    try:
        import bibtexparser
        from bibtexparser.bparser import BibTexParser
        from bibtexparser.customization import convert_to_unicode
    except Exception:
        raise SystemExit("Missing bibtexparser. CI will install it; locally run: pip install bibtexparser")

    if not BIB_FILE.exists():
        raise SystemExit(f"Bib file not found: {BIB_FILE}")

    parser = BibTexParser(common_strings=True)
    parser.customization = convert_to_unicode
    with open(BIB_FILE, "r", encoding="utf-8") as f:
        db = bibtexparser.load(f, parser=parser)
    return db.entries or []

def etype(e): return (e.get("ENTRYTYPE") or e.get("entrytype") or "").lower()
def year(e):
    y = str(e.get("year") or "")
    m = re.search(r"\d{4}", y)
    return int(m.group(0)) if m else 0

def is_preprint(e: dict) -> bool:
    # entry type check
    t = (e.get("ENTRYTYPE") or e.get("entrytype") or "").lower()
    if t in ("preprint", "unpublished"):
        return True

    # textual hints
    note = ((e.get("note") or "") + " " + (e.get("howpublished") or "")).lower()
    if "preprint" in note:
        return True

    # host-based hints
    url = (e.get("url") or "").lower()
    if any(h in url for h in ("arxiv.org", "ssrn.com", "biorxiv.org", "medrxiv.org", "chemrxiv.org", "osf.io")):
        return True

    # arXiv metadata
    ap = (e.get("archiveprefix") or e.get("archivePrefix") or "").lower()
    return ap == "arxiv"


def is_journal_like(e: dict) -> bool:
    if is_preprint(e):
        return False
    return etype(e) == "article" or bool(e.get("journal") or e.get("journaltitle"))


def is_journal(e: dict) -> bool:
    return (not is_preprint(e)) and (etype(e) == "article" or bool(e.get("journal") or e.get("journaltitle")))

def is_chapter(e):
    return etype(e) == "incollection"

def is_conf(e):
    return etype(e) == "inproceedings"

def authors_str(e):
    a = str(e.get("author") or "").replace("\n"," ")
    parts = [p.strip() for p in a.split(" and ") if p.strip()]
    return ", ".join(parts)

def title_str(e):
    t = str(e.get("title") or "").strip().strip("{}")
    t = t.replace("``", '"').replace("''", '"')
    return t

def venue_str(e: dict, kind: str) -> str:
    if kind == "journal":
        return get_journal(e)
    if kind == "preprint":
        u   = (e.get("url") or "").lower()
        ap  = (e.get("archiveprefix") or e.get("archivePrefix") or "").lower()
        eid = (e.get("eprint") or "").strip()
        if ap == "arxiv" or "arxiv.org" in u:
            return "arXiv" + (f":{eid}" if eid else "")
        if "ssrn.com" in u:     return "SSRN"
        if "biorxiv.org" in u:  return "bioRxiv"
        if "medrxiv.org" in u:  return "medRxiv"
        if "chemrxiv.org" in u: return "ChemRxiv"
        # fallback if host not recognized
        return (e.get("note") or e.get("howpublished") or "Preprint").strip()
    # chapters/conf default: your existing logic
    return get_booktitle(e)



def link_str(e):
    url = str(e.get("url") or "").strip()
    if url: return f"[Link]({url})"
    doi = str(e.get("doi") or "").strip()
    if doi:
        if not doi.lower().startswith("http"):
            doi = "https://doi.org/" + doi
        return f"[Link]({doi})"
    return ""

def render_list(title, items, kind):
    lines = []
    lines.append(f"## {title}\n")
    if not items:
        lines.append("_No entries._\n")
        return lines
    items.sort(key=year, reverse=True)
    for i, e in enumerate(items, 1):
        au = authors_str(e)
        ti = title_str(e)
        ve = venue_str(e, kind)
        yr = year(e)
        ln = link_str(e)
        s = f"{i}. {au}, _{ti}_"
        if ve: s += f", **{ve}**"
        if yr: s += f", {yr}"
        if ln: s += f" {ln}"
        lines.append(s + "\n")
    return lines

def main():
    entries = read_bib()

    # buckets
    pre = [e for e in entries if is_preprint(e)]
    jnl = [e for e in entries if is_journal(e)]
    chp = [e for e in entries if is_chapter(e)]
    cnf = [e for e in entries if is_conf(e)]

    # page
    out = []
    out.append("---"); out.append("layout: page"); out.append("title: Publications"); out.append("---\n")
    out.extend(render_list("Preprint",       pre, "preprint"));  out.append("\n")
    out.extend(render_list("Journals",       jnl, "journal"));   out.append("\n")
    out.extend(render_list("Book Chapters",  chp, "chapter"));   out.append("\n")
    out.extend(render_list("Conferences",    cnf, "conf"))

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")

    # optional JSON export
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    def venue_for(e):
        if is_preprint(e): return venue_str(e, "preprint")
        if is_journal(e):  return venue_str(e, "journal")
        if is_chapter(e):  return venue_str(e, "chapter")
        if is_conf(e):     return venue_str(e, "conf")
        return ""
    json.dump([
        {
            "id": (e.get("ID") or e.get("id") or "").strip(),
            "type": etype(e),
            "title": title_str(e),
            "authors": [p.strip() for p in str(e.get("author") or "").split(" and ") if p.strip()],
            "year": year(e),
            "venue": venue_for(e),
            "url": (e.get("url") or ""),
        } for e in entries
    ], open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
