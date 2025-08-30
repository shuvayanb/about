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

def is_preprint(e):
    if etype(e) in ("preprint","unpublished"): return True
    if "preprint" in str(e.get("note") or "").lower(): return True
    url = str(e.get("url") or "").lower()
    if any(x in url for x in ("arxiv.org","ssrn.com","biorxiv.org","medrxiv.org","chemrxiv.org","osf.io")):
        return True
    if (e.get("archiveprefix") or e.get("archivePrefix") or "").lower() == "arxiv":
        return True
    return False

def is_journal(e):
    return etype(e) == "article" and not is_preprint(e)

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

def venue_str(e, kind):
    if kind == "preprint":
        url = str(e.get("url") or "").lower()
        ap = (e.get("archiveprefix") or e.get("archivePrefix") or "").lower()
        eprint = str(e.get("eprint") or "").strip()
        if ap == "arxiv" or "arxiv.org" in url:
            return "arXiv" + (f":{eprint}" if eprint else "")
        if "ssrn.com" in url: return "SSRN"
        if "biorxiv.org" in url: return "bioRxiv"
        if "medrxiv.org" in url: return "medRxiv"
        if "chemrxiv.org" in url: return "ChemRxiv"
        return str(e.get("note") or "").strip() or str(e.get("howpublished") or "").strip()
    if kind == "journal":
        return str(e.get("journaltitle") or e.get("journal") or "").strip()
    if kind == "chapter" or kind == "conf":
        return str(e.get("booktitle") or "").strip()
    return ""

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
    pre  = [e for e in entries if is_preprint(e)]
    jnl  = [e for e in entries if is_journal(e)]
    chp  = [e for e in entries if is_chapter(e)]
    cnf  = [e for e in entries if is_conf(e)]

    out = []
    out.append("---"); out.append("layout: page"); out.append("title: Publications"); out.append("---\n")
    out.extend(render_list("Preprint",   pre,  "preprint"));  out.append("\n")
    out.extend(render_list("Journals",   jnl,  "journal"));   out.append("\n")
    out.extend(render_list("Book Chapters", chp, "chapter")); out.append("\n")
    out.extend(render_list("Conferences", cnf, "conf"))

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")

    # optional JSON export
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    def venue_for(e):
        if is_preprint(e): return venue_str(e,"preprint")
        if is_journal(e):  return venue_str(e,"journal")
        if is_chapter(e):  return venue_str(e,"chapter")
        if is_conf(e):     return venue_str(e,"conf")
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
    print(f"Wrote {OUT_MD} — preprints:{len(pre)} journals:{len(jnl)} chapters:{len(chp)} conf:{len(cnf)}")

if __name__ == "__main__":
    main()
