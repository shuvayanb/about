#!/usr/bin/env python3
from pathlib import Path
import re
import json
import os
import sys
import traceback
from collections import Counter

DEBUG = os.getenv("DEBUG_BIB2PUBS", "1") != "0"

def log(*a):
    if DEBUG:
        print("[bib2pubs]", *a, flush=True)

BIB_FILE = Path("Publications/references.bib")
OUT_MD   = Path("Publications/publications.md")
OUT_JSON = Path("assets/data/pubs.json")
OUT_GRAPH= Path("assets/data/topic_graph.json")

def tags_from_keywords(e: dict) -> list[str]:
    """
    Parse keywords into a flat list of tags for pubs.json.
    Supports hierarchy with '>' and grouped children in {...} with '|' or ','.
    Examples:
      "CFD > {immersed boundary | RANS}; surrogate"
      -> ["CFD", "immersed boundary", "RANS", "surrogate"]
    """
    s = (e.get("keywords") or e.get("keyword") or "")
    tokens = []
    depth = 0
    buf = []
    items = []
    # split top-level items on ';' or ',' but NOT inside {...}
    for ch in s:
        if ch == '{': depth += 1
        if ch == '}': depth = max(0, depth-1)
        if (ch in ';,' and depth == 0):
            it = "".join(buf).strip()
            if it: items.append(it)
            buf = []
        else:
            buf.append(ch)
    tail = "".join(buf).strip()
    if tail: items.append(tail)

    seen = set()
    for raw in items:
        part = raw.strip()
        if not part: continue
        # if hierarchical item, flatten all levels and groups
        if '>' in part:
            levels = [p.strip() for p in part.split('>') if p.strip()]
            for lvl in levels:
                if lvl.startswith('{') and lvl.endswith('}'):
                    body = lvl[1:-1]
                    kids = [t.strip() for t in re.split(r'[|,]', body) if t.strip()]
                    for k in kids:
                        if k.lower() not in seen:
                            tokens.append(k); seen.add(k.lower())
                else:
                    if lvl.lower() not in seen:
                        tokens.append(lvl); seen.add(lvl.lower())
        else:
            # plain item may still contain comma-separated tags
            for t in [p.strip() for p in part.split(',') if p.strip()]:
                if t.lower() not in seen:
                    tokens.append(t); seen.add(t.lower())
    return tokens

def _split_top_level_items(s: str) -> list[str]:
    # Split keywords string into top-level items by ';' or ',' respecting {...}
    items, buf, depth = [], [], 0
    for ch in s:
        if ch == '{': depth += 1
        elif ch == '}': depth = max(0, depth-1)
        if (ch in ';,' and depth == 0):
            it = "".join(buf).strip()
            if it: items.append(it)
            buf = []
        else:
            buf.append(ch)
    tail = "".join(buf).strip()
    if tail: items.append(tail)
    return items

def _parse_hier_item(item: str) -> list[list[str]]:
    """
    Parse one hierarchical item like:
      'A > {B|C} > {D,E}'  ->  [['A'], ['B','C'], ['D','E']]
      'A > B'              ->  [['A'], ['B']]
    """
    levels = []
    for seg in [p.strip() for p in item.split('>') if p.strip()]:
        if seg.startswith('{') and seg.endswith('}'):
            body = seg[1:-1]
            kids = [t.strip() for t in re.split(r'[|,]', body) if t.strip()]
            levels.append(kids)
        else:
            levels.append([seg])
    return levels

def build_topic_graph_with_hierarchy(entries: list[dict], policy: str = "adjacent") -> dict:
    """
    Build a topic graph using explicit hierarchy:
      - Items with '>' add parent↔child edges.
      - Grouped children are supported with {...} and '|' or ','.
      - Plain (non-hierarchical) tags connect pairwise among themselves.
    policy:
      * 'adjacent' (default): for levels [L0, L1, L2] add all pairs in L0×L1 and L1×L2
      * 'tail'             : for levels [.., Lk-2, Lk-1] add only pairs in Lk-2×Lk-1
    """
    tag_set = set()
    edge_w  = {}

    for e in entries:
        raw = (e.get("keywords") or e.get("keyword") or "")
        items = _split_top_level_items(raw)

        # collect all tokens (for nodes) + track which tags participate in hierarchy
        hier_levels_list = []
        hier_members = set()
        plain_candidates = []

        for it in items:
            if '>' in it:
                levels = _parse_hier_item(it)
                hier_levels_list.append(levels)
                for lvl in levels:
                    for tag in lvl:
                        tag_set.add(tag.strip().lower())
                        hier_members.add(tag.strip().lower())
            else:
                # may contain comma-separated plain tags
                for t in [p.strip() for p in it.split(',') if p.strip()]:
                    tag_set.add(t.strip().lower())
                    plain_candidates.append(t.strip().lower())

        # add hierarchy edges
        for levels in hier_levels_list:
            if len(levels) < 2:
                continue
            if policy == "tail" and len(levels) >= 2:
                left = [a.strip().lower() for a in levels[-2]]
                right = [b.strip().lower() for b in levels[-1]]
                for a in left:
                    for b in right:
                        if a != b:
                            key = tuple(sorted((a,b)))
                            edge_w[key] = edge_w.get(key, 0) + 1
            else:  # 'adjacent'
                for i in range(len(levels)-1):
                    left = [a.strip().lower() for a in levels[i]]
                    right= [b.strip().lower() for b in levels[i+1]]
                    for a in left:
                        for b in right:
                            if a != b:
                                key = tuple(sorted((a,b)))
                                edge_w[key] = edge_w.get(key, 0) + 1

        # add plain edges among plain tags ONLY (exclude any tag that was in a hierarchy item)
        plain = [t for t in plain_candidates if t not in hier_members]
        for i in range(len(plain)):
            for j in range(i+1, len(plain)):
                key = tuple(sorted((plain[i], plain[j])))
                edge_w[key] = edge_w.get(key, 0) + 1

    nodes = [{"id": t} for t in sorted(tag_set)]
    links = [{"source": a, "target": b, "weight": w} for (a,b), w in edge_w.items()]
    print(f"[hier] nodes={len(nodes)} links={len(links)} policy={policy}")
    return {"nodes": nodes, "links": links}


def build_topic_graph(pubs: list[dict]) -> dict:
    # Co-occurrence from lower-cased unique tags per paper
    tag_set = set()
    edge_w  = {}
    for p in pubs:
        t = [str(s).strip().lower() for s in (p.get("tags") or []) if str(s).strip()]
        t = sorted(set(t))
        for a in t: tag_set.add(a)
        for i in range(len(t)):
            for j in range(i+1, len(t)):
                key = (t[i], t[j])
                edge_w[key] = edge_w.get(key, 0) + 1

    nodes = [{"id": t} for t in sorted(tag_set)]
    links = [{"source": a, "target": b, "weight": w} for (a,b), w in edge_w.items()]
    log(f"build_topic_graph: nodes={len(nodes)} links={len(links)}")
    return {"nodes": nodes, "links": links}

# ---------- NEW: enrichment with prints + hard fallbacks ----------
def enrich_topic_graph(graph: dict, pubs: list[dict]) -> dict:
    log("enrich_topic_graph: start")
    # counts from pubs
    tag_count = Counter()
    for p in pubs:
        for t in (p.get("tags") or []):
            k = str(t).strip().lower()
            if k: tag_count[k] += 1
    log(f" counts: unique_tags={len(tag_count)} sample={tag_count.most_common(5)}")

    # weighted degree from links
    deg_w = Counter()
    for l in (graph.get("links") or []):
        s = str(l.get("source"))
        t = str(l.get("target"))
        try:
            w = int(l.get("weight") or 1)
        except Exception:
            w = 1
        deg_w[s] += w; deg_w[t] += w
    log(f" degree_w: computed for {len(deg_w)} nodes")

    # community detection (optional)
    partition = {}
    try:
        import networkx as nx  # type: ignore
        try:
            import community as community_louvain  # python-louvain
        except Exception as e:
            log(" community: python-louvain import failed:", e)
            community_louvain = None

        if community_louvain is not None:
            G = nx.Graph()
            for n in (graph.get("nodes") or []):
                G.add_node(str(n["id"]))
            for l in (graph.get("links") or []):
                G.add_edge(str(l["source"]), str(l["target"]),
                           weight=int(l.get("weight") or 1))
            partition = community_louvain.best_partition(G, weight="weight", random_state=42)
            log(f" community: detected {len(set(partition.values()))} communities")
        else:
            raise RuntimeError("community lib unavailable")
    except Exception as e:
        log(" community: FALLBACK to single community (reason below)")
        if DEBUG: traceback.print_exc()
        for n in (graph.get("nodes") or []):
            partition[str(n["id"])] = 0

    # renumber communities for stability (0..K-1 by size)
    comm_bins = {}
    for nid, cid in partition.items():
        comm_bins.setdefault(int(cid), []).append(nid)

    order = sorted(comm_bins.keys(),
                   key=lambda c: (-sum(tag_count.get(n,0) for n in comm_bins[c]),
                                  -sum(deg_w.get(n,0) for n in comm_bins[c]),
                                  c))
    remap = {old:i for i, old in enumerate(order)}
    log(f" community: remapped ids={remap}")

    # finalize nodes
    new_nodes = []
    for n in (graph.get("nodes") or []):
        orig = str(n["id"])
        low  = orig.strip().lower()
        new_nodes.append({
            "id": orig,
            "count": int(tag_count.get(low, 0)),
            "degree_w": int(deg_w.get(orig, 0) or deg_w.get(low, 0) or 0),
            "community": int(remap.get(int(partition.get(orig, partition.get(low, 0))), 0)),
        })

    log("enrich_topic_graph: done")
    return {"nodes": new_nodes, "links": graph.get("links", [])}

# ---------- existing bib parsing ----------
def read_bib() -> list[dict]:
    bib_path = BIB_FILE
    txt = bib_path.read_text(encoding="utf-8")

    entries_rx: list[dict] = []
    entry_re = re.compile(r'@(\w+)\s*{\s*([^,]+)\s*,(.*?)\n}\s*', re.S | re.I)
    field_re = re.compile(r'([A-Za-z][A-Za-z0-9_-]*)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|"[^"]*")\s*,?', re.S)

    for m in entry_re.finditer(txt):
        etype = m.group(1).strip().lower()
        key   = m.group(2).strip()
        body  = m.group(3)
        d = {"ENTRYTYPE": etype, "ID": key}
        for fm in field_re.finditer(body):
            k = fm.group(1).lower()
            v = fm.group(2).strip()
            if (v.startswith("{") and v.endswith("}")) or (v.startswith('"') and v.endswith('"')):
                v = v[1:-1]
            d[k] = v.strip()
        entries_rx.append(d)

    # bibtexparser parse
    entries_bp: list[dict] = []
    try:
        import bibtexparser
        from bibtexparser.bparser import BibTexParser
        parser = BibTexParser(common_strings=True)
        db = bibtexparser.loads(txt, parser=parser)
        entries_bp = db.entries or []
    except Exception as e:
        log("bibtexparser load failed:", e)

    def keyfn(e: dict):
        return ((e.get("ENTRYTYPE") or e.get("entrytype") or "").lower(),
                (e.get("ID") or e.get("id") or "").lower())

    out: list[dict] = []
    seen = set()
    for e in entries_bp + entries_rx:
        k = keyfn(e)
        if k in seen: continue
        seen.add(k); out.append(e)

    log(f"[read_bib] merged entries: total={len(out)} (bibtexparser={len(entries_bp)} regex={len(entries_rx)})")
    return out

def etype(e): return (e.get("ENTRYTYPE") or e.get("entrytype") or "").lower()
def year(e):
    y = str(e.get("year") or "")
    m = re.search(r"\d{4}", y)
    return int(m.group(0)) if m else 0
def is_preprint(e: dict) -> bool:
    t = (e.get("ENTRYTYPE") or e.get("entrytype") or "").lower()
    if t in ("preprint", "unpublished"): return True
    note = ((e.get("note") or "") + " " + (e.get("howpublished") or "")).lower()
    if "preprint" in note: return True
    url = (e.get("url") or "").lower()
    if any(h in url for h in ("arxiv.org","ssrn.com","biorxiv.org","medrxiv.org","chemrxiv.org","osf.io")):
        return True
    ap = (e.get("archiveprefix") or e.get("archivePrefix") or "").lower()
    return ap == "arxiv"
def is_journal(e: dict) -> bool:
    return (not is_preprint(e)) and (etype(e) == "article" or bool(e.get("journal") or e.get("journaltitle")))
def is_chapter(e): return etype(e) == "incollection"
def is_conf(e):    return etype(e) == "inproceedings"

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
        return (e.get("journal") or e.get("journaltitle") or "").strip()
    if kind == "preprint":
        u   = (e.get("url") or "").lower()
        ap  = (e.get("archiveprefix") or e.get("archivePrefix") or "").lower()
        eid = (e.get("eprint") or "").strip()
        if ap == "arxiv" or "arxiv.org" in u: return "arXiv" + (f":{eid}" if eid else "")
        if "ssrn.com" in u:     return "SSRN"
        if "biorxiv.org" in u:  return "bioRxiv"
        if "medrxiv.org" in u:  return "medRxiv"
        if "chemrxiv.org" in u: return "ChemRxiv"
        return ((e.get("note") or e.get("howpublished") or "Preprint")).strip()
    if kind in ("chapter", "conf"): return (e.get("booktitle") or "").strip()
    return ""
def link_str(e):
    url = str(e.get("url") or "").strip()
    if url: return f"[Link]({url})"
    doi = str(e.get("doi") or "").strip()
    if doi:
        if not doi.lower().startswith("http"): doi = "https://doi.org/" + doi
        return f"[Link]({doi})"
    return ""
def render_list(title, items, kind):
    lines = [f"## {title}\n"]
    if not items:
        lines.append("_No entries._\n"); return lines
    items.sort(key=year, reverse=True)
    for i, e in enumerate(items, 1):
        au = authors_str(e); ti = title_str(e); ve = venue_str(e, kind); yr = year(e); ln = link_str(e)
        s = f"{i}. {au}, _{ti}_"
        if ve: s += f", **{ve}**"
        if yr: s += f", {yr}"
        if ln: s += f" {ln}"
        lines.append(s + "\n")
    return lines

def main():
    log(f"Python {sys.version}")
    log(f"cwd={Path.cwd()}")

    entries = read_bib()
    log("entries sample:", [ (e.get("ENTRYTYPE"), e.get("ID")) for e in entries[:3] ])

    # buckets
    pre = [e for e in entries if is_preprint(e)]
    jnl = [e for e in entries if is_journal(e)]
    chp = [e for e in entries if is_chapter(e)]
    cnf = [e for e in entries if is_conf(e)]
    log(f"buckets: pre={len(pre)} jnl={len(jnl)} chp={len(chp)} cnf={len(cnf)}")

    # page
    out = ["---","layout: page","title: Publications","---\n"]
    out.extend(render_list("Preprint",       pre, "preprint"));  out.append("\n")
    out.extend(render_list("Journals",       jnl, "journal"));   out.append("\n")
    out.extend(render_list("Book Chapters",  chp, "chapter"));   out.append("\n")
    out.extend(render_list("Conferences",    cnf, "conf"))

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    log(f"Wrote {OUT_MD}")

    # pubs.json
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    pubs_out = []
    for e in entries:
        pubs_out.append({
            "id":      (e.get("ID") or e.get("id") or "").strip(),
            "type":    (e.get("ENTRYTYPE") or e.get("entrytype") or "").lower(),
            "title":   title_str(e),
            "authors": [p.strip() for p in str(e.get("author") or "").split(" and ") if p.strip()],
            "year":    year(e),
            "venue":   venue_str(e, "preprint") if is_preprint(e) else
                       venue_str(e, "journal")  if is_journal(e)  else
                       venue_str(e, "chapter")  if is_chapter(e)  else
                       venue_str(e, "conf")     if is_conf(e)     else "",
            "url":     (e.get("url") or ""),
            "tags":    tags_from_keywords(e),
        })
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(pubs_out, f, ensure_ascii=False, indent=2)
    log(f"Wrote {OUT_JSON} (papers={len(pubs_out)})")

    # topic_graph.json (hierarchy-aware + enriched; safe fallback on any error)
    OUT_GRAPH.parent.mkdir(parents=True, exist_ok=True)
    try:
        # Detect hierarchy usage and choose policy
        HIER_POLICY = (os.getenv("HIER_EDGE_POLICY") or "adjacent").strip().lower()  # 'adjacent' or 'tail'
        has_hier = any(('>' in str(e.get("keywords") or e.get("keyword") or "")) for e in entries)

        if has_hier:
            log(f"Hierarchy detected in keywords; policy={HIER_POLICY}")
            # requires build_topic_graph_with_hierarchy(...) to be defined above
            base_graph = build_topic_graph_with_hierarchy(entries, policy=HIER_POLICY)
        else:
            base_graph = build_topic_graph(pubs_out)

        graph = enrich_topic_graph(base_graph, pubs_out)
        graph["_meta"] = {"enriched": True, "hierarchy": {"detected": has_hier, "policy": HIER_POLICY}}
        with open(OUT_GRAPH, "w", encoding="utf-8") as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)
        log(f"Wrote {OUT_GRAPH} (ENRICHED, hier={has_hier})")

    except Exception as e:
        log("ENRICH/HIER FAILED — writing BASE graph. Reason below.")
        traceback.print_exc()
        base_graph = build_topic_graph(pubs_out)
        base_graph["_meta"] = {"enriched": False, "error": str(e)}
        with open(OUT_GRAPH, "w", encoding="utf-8") as f:
            json.dump(base_graph, f, ensure_ascii=False, indent=2)
        log(f"Wrote {OUT_GRAPH} (BASE)")


if __name__ == "__main__":
    main()
