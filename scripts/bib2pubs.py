#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import re
import sys
import json
from itertools import combinations

# ----- CONFIG -----
# Added root-level _bibliography path first so it wins
BIB_PATHS = [
    Path("_bibliography/references.bib"),   # <--- NEW (your Jekyll-Scholar location)
    Path("reference.bib"),
    Path("Publications/references.bib"),
]
OUT_PAGE  = Path("Publications/publications.md")
OUT_DIR   = Path("assets/data")
PUBS_JSON = OUT_DIR / "pubs.json"
GRAPH_JSON= OUT_DIR / "topic_graph.json"

TAGS_YAML   = Path("_data/pub_tags.yml")       # optional (stickers + domains/tags)
ALIASES_YAML= Path("_data/topic_aliases.yml")  # optional (topic synonym map)

PAGE_TITLE = "Publications"
YOUR_NAME_PATTERNS = [
    r"\bBrahmachary,\s*Shuvayan\b",
    r"\bShuvayan\s+Brahmachary\b",
    r"\bBrahmachary,\s*S\.?\b",
    r"\bS\.?\s*Brahmachary\b",
]

STICKER_CSS = """
<style>
.sticker-tag{
  display:inline-block; font-size:11px; line-height:1; font-weight:700;
  padding:3px 6px; border-radius:6px; margin-left:6px; vertical-align:middle;
}
.sticker-new{ background:#e6fffb; color:#006d75; border:1px solid #87e8de; }
.sticker-preprint{ background:#f6ffed; color:#237804; border:1px solid #b7eb8f; }
.sticker-award{ background:#fff7e6; color:#ad4e00; border:1px solid #ffd591; }
@media (prefers-color-scheme: dark){
  .sticker-new{ background:#003a3f; color:#c2fffb; border-color:#146b66; }
  .sticker-preprint{ background:#163a24; color:#bdf7a8; border-color:#2c6c45; }
  .sticker-award{ background:#3e2a00; color:#ffd8a8; border-color:#805500; }
}
</style>
"""
# ------------------ helpers (latex/text) ------------------

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
    # Prefer explicit URL
    url = (e.get("url") or "").strip().strip("{}")
    if url:
        return f"[Link]({url})"
    # arXiv via eprint+archiveprefix
    ap = (e.get("archiveprefix") or e.get("archivePrefix") or "").lower()
    eprint = (e.get("eprint") or "").strip()
    if ap == "arxiv" and eprint:
        return f"[Link](https://arxiv.org/abs/{eprint})"
    # DOI
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

def get_preprint_venue(e: dict) -> str:
    ap = (e.get("archiveprefix") or e.get("archivePrefix") or "").lower()
    eprint = (e.get("eprint") or "").strip()
    url = (e.get("url") or "").lower()
    if ap == "arxiv" or "arxiv.org" in url:
        return "arXiv" + (f":{eprint}" if eprint else "")
    if "ssrn.com" in url:
        return "SSRN"
    if "biorxiv.org" in url:
        return "bioRxiv"
    if "medrxiv.org" in url:
        return "medRxiv"
    if "chemrxiv.org" in url:
        return "ChemRxiv"
    return (e.get("note") or "").strip() or (e.get("howpublished") or "").strip() or (e.get("journal") or "").strip()

def etype(e: dict) -> str:
    return (e.get("ENTRYTYPE") or e.get("entrytype") or "").lower()

def is_preprint(e: dict) -> bool:
    t = etype(e)
    if t in ("preprint", "unpublished"):
        return True
    note = (e.get("note") or "").lower()
    if "preprint" in note:
        return True
    url = (e.get("url") or "").lower()
    if any(dom in url for dom in ("arxiv.org","ssrn.com","biorxiv.org","medrxiv.org","chemrxiv.org","osf.io")):
        return True
    ap = (e.get("archiveprefix") or e.get("archivePrefix") or "").lower()
    if ap == "arxiv":
        return True
    return False

def is_journal_like(e: dict) -> bool:
    # never classify a preprint as a journal, even if it has a 'journal' field
    if is_preprint(e):
        return False
    return etype(e) == "article" or bool(e.get("journal") or e.get("journaltitle"))

def is_book_chapter(e: dict) -> bool:
    return etype(e) == "incollection" or (bool(e.get("booktitle")) and etype(e) not in ("inproceedings",))

def is_conference(e: dict) -> bool:
    return etype(e) == "inproceedings"

# ------------------ bib loading (primary + fallback) ------------------

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

# ------------------ tags / domains loading ------------------

def safe_yaml_load(path: Path):
    try:
        import yaml  # PyYAML is available on runners; we’ll also pin in CI
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as ex:
        print(f"[bib2pubs] WARN: YAML load failed for {path}: {ex}", file=sys.stderr)
        return None

def load_alias_map() -> dict[str, str]:
    if not ALIASES_YAML.exists():
        print("[bib2pubs] no _data/topic_aliases.yml (aliases optional)")
        return {}
    data = safe_yaml_load(ALIASES_YAML) or {}
    out = {}
    if isinstance(data, dict):
        for k, v in data.items():
            out[str(k).strip().lower()] = str(v).strip()
    print(f"[bib2pubs] loaded {len(out)} topic aliases")
    return out

def load_domains_map() -> dict[str, list[str]]:
    """
    From _data/pub_tags.yml accept either:
      ID: [list of stickers]             # ignored for domains
      ID: { domains: [...], tags: [...] } # we merge both
    """
    if not TAGS_YAML.exists():
        print("[bib2pubs] no _data/pub_tags.yml (stickers/domains optional)")
        return {}
    raw = safe_yaml_load(TAGS_YAML) or {}
    out: dict[str, list[str]] = {}
    if not isinstance(raw, dict):
        return out
    for k, v in raw.items():
        topics: list[str] = []
        if isinstance(v, dict):
            if "domains" in v and isinstance(v["domains"], list):
                topics += [str(x) for x in v["domains"]]
            if "tags" in v and isinstance(v["tags"], list):
                topics += [str(x) for x in v["tags"]]
        elif isinstance(v, list):
            pass
        out[k] = topics
    print(f"[bib2pubs] loaded domains/tags for {sum(bool(v) for v in out.values())} entries from pub_tags.yml")
    return out

def normalize_topics(items: list[str], alias_map: dict[str, str]) -> list[str]:
    norm = []
    seen = set()
    for t in items:
        t0 = str(t).strip()
        if not t0:
            continue
        key = t0.lower()
        canon = alias_map.get(key, t0)  # replace if alias known
        if canon not in seen:
            seen.add(canon)
            norm.append(canon)
    return norm

def topics_for_entry(e: dict, domains_map: dict[str, list[str]], alias_map: dict[str, str]) -> list[str]:
    bid = (e.get("ID") or e.get("id") or "").strip()
    topics: list[str] = []
    topics += domains_map.get(bid, [])
    kw = (e.get("keywords") or e.get("keyword") or "")
    if kw:
        parts = re.split(r"[;,]", kw)
        topics += [p for p in (pp.strip() for pp in parts) if p]
    return normalize_topics(topics, alias_map)

# ------------------ sticker tags (existing) ------------------

def load_sticker_map() -> dict[str, list[str]]:
    if not TAGS_YAML.exists():
        return {}
    raw = safe_yaml_load(TAGS_YAML) or {}
    out: dict[str, list[str]] = {}
    if not isinstance(raw, dict):
        return out
    for k, v in raw.items():
        if isinstance(v, list):
            out[k] = [str(x).lower() for x in v]
        elif isinstance(v, dict):
            stickers = v.get("stickers") if isinstance(v.get("stickers"), list) else []
            out[k] = [str(x).lower() for x in stickers]
        else:
            out[k] = []
    return out

def render_badges(stickers: list[str], force_preprint: bool=False) -> str:
    # Always show a Preprint sticker if this is a preprint entry
    if force_preprint and "preprint" not in stickers:
        stickers = list(stickers) + ["preprint"]
    if not stickers:
        return ""
    label_map = {"new": "NEW", "preprint": "Preprint", "award": "Best Paper"}
    cls_map = {"new": "sticker-new", "preprint": "sticker-preprint", "award": "sticker-award"}
    spans = []
    for t in stickers:
        label = label_map.get(t)
        cls = cls_map.get(t)
        if label and cls:
            spans.append(f'<span class="sticker-tag {cls}">{label}</span>')
    return " " + "".join(spans) if spans else ""

# ------------------ render page ------------------

def render_section(title_html: str, items: list[dict], mode: str, sticker_map: dict[str, list[str]]) -> list[str]:
    lines = []
    lines.append(f'# <span style="color:blue">{title_html}</span>\n')
    if not items:
        lines.append("_No entries._\n")
        return lines

    items.sort(key=get_year, reverse=True)
    for idx, e in enumerate(items, start=1):
        authors = bold_author_name(f(e, "author").replace(" and ", ", "))
        title = f(e, "title").strip(' "{}')
        if mode == "journal":
            venue = get_journal(e)
        elif mode == "chapter":
            venue = get_booktitle(e)
        elif mode == "preprint":
            venue = get_preprint_venue(e)
        else:
            venue = get_booktitle(e) or get_journal(e)

        year = f(e, "year")
        link_md = build_link(e)
        bid = (e.get("ID") or e.get("id") or "").strip()

        force_pre = (mode == "preprint")
        badges = render_badges(sticker_map.get(bid, []), force_preprint=force_pre)

        item = f"{idx}. {authors}, _{title}_"
        if venue:
            item += f", **{venue}**"
        if year:
            item += f", {year}"
        if link_md:
            item += f" {link_md}"
        item += badges
        lines.append(item + "\n")
    return lines

# ------------------ JSON export ------------------

def build_pubs_json(entries: list[dict], domains_map: dict[str, list[str]], alias_map: dict[str, str]) -> list[dict]:
    out = []
    for e in entries:
        bid = (e.get("ID") or e.get("id") or "").strip()
        title = f(e, "title").strip(' "{}')
        authors = [a.strip() for a in f(e, "author").replace("\n"," ").split(" and ") if a.strip()]
        year = get_year(e)
        typ = etype(e)
        if is_journal_like(e):
            venue = get_journal(e)
        elif is_book_chapter(e):
            venue = get_booktitle(e)
        elif is_preprint(e):
            venue = get_preprint_venue(e)
        else:
            venue = get_booktitle(e) or get_journal(e)
        url = (e.get("url") or "").strip() or (("https://doi.org/" + e.get("doi").strip()) if e.get("doi") else "")
        topics = topics_for_entry(e, domains_map, alias_map)
        out.append({
            "id": bid, "type": typ, "title": title, "authors": authors,
            "year": year, "venue": venue, "url": url, "tags": topics
        })
    return out

def build_topic_graph(pubs: list[dict]) -> dict:
    topic_set = set()
    link_weights: dict[tuple[str,str], int] = {}
    for p in pubs:
        tags = [t for t in p.get("tags", []) if t]
        tags = sorted(set(tags))
        for t in tags:
            topic_set.add(t)
        for a, b in combinations(tags, 2):
            key = (a, b) if a < b else (b, a)
            link_weights[key] = link_weights.get(key, 0) + 1
    nodes = [{"id": t} for t in sorted(topic_set)]
    links = [{"source": s, "target": t, "weight": w} for (s, t), w in link_weights.items()]
    return {"nodes": nodes, "links": links}

# ------------------ main ------------------

def main():
    alias_map   = load_alias_map()
    domains_map = load_domains_map()
    sticker_map = load_sticker_map()

    entries = load_all(BIB_PATHS)

    # --- classify ---
    preprints   = [e for e in entries if is_preprint(e)]
    journals    = [e for e in entries if is_journal_like(e) and not is_preprint(e)]
    chapters    = [e for e in entries if is_book_chapter(e)]
    conferences = [e for e in entries if is_conference(e)]
    print(f"[bib2pubs] preprints: {len(preprints)}, journals: {len(journals)}, chapters: {len(chapters)}, conferences: {len(conferences)}")

    # --- write page ---
    lines = []
    lines.append("---")
    lines.append("layout: page")
    lines.append(f"title: {PAGE_TITLE}")
    lines.append("---\n")
    lines.append(STICKER_CSS.strip() + "\n\n")

    # NEW: Preprint section first
    lines.extend(render_section("Preprint", preprints, mode="preprint", sticker_map=sticker_map))
    lines.append("\n")

    lines.append("**Published**\n")
    lines.extend(render_section("Journals",      journals,    mode="journal",  sticker_map=sticker_map))
    lines.append("\n")
    lines.extend(render_section("Book Chapters", chapters,    mode="chapter",  sticker_map=sticker_map))
    lines.append("\n")
    lines.extend(render_section("Conferences",   conferences, mode="conf",     sticker_map=sticker_map))

    OUT_PAGE.parent.mkdir(parents=True, exist_ok=True)
    OUT_PAGE.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"[bib2pubs] wrote {OUT_PAGE}")

    # --- write JSON ---
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pubs = build_pubs_json(entries, domains_map, alias_map)
    PUBS_JSON.write_text(json.dumps(pubs, ensure_ascii=False, indent=2), encoding="utf-8")
    graph = build_topic_graph(pubs)
    GRAPH_JSON.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[bib2pubs] wrote {PUBS_JSON} ({len(pubs)} items) and {GRAPH_JSON} "
          f"({len(graph.get('nodes',[]))} topics, {len(graph.get('links',[]))} links)")

if __name__ == "__main__":
    main()
