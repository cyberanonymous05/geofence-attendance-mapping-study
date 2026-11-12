"""Merge OpenAlex corpus with Crossref / arXiv / Semantic Scholar results into corpus_all.csv.
New records without an abstract get one from OpenAlex (by DOI) when available. Writes per-source counts to sources_counts.json."""
import csv, glob, json, re, sys, time, urllib.parse, urllib.request, urllib.error
from collections import defaultdict
from pathlib import Path
HERE = Path(__file__).parent
norm = lambda t: re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()
base = list(csv.DictReader(open(HERE / "corpus.csv")))
fields = list(base[0].keys())
by_doi = {r["doi"]: r for r in base if r["doi"]}; by_title = {norm(r["title"]): r for r in base}
for r in base: r["sources"] = "openalex"
stats = defaultdict(lambda: dict(retrieved=0, in_openalex=0, new=0, queries=set()))
new = {}
for f in sorted(glob.glob(str(HERE / "raw_other/*.json"))):
    d = json.load(open(f)); src = d["_source"]
    stats[src]["queries"].add(Path(f).stem)
    for w in d["results"]:
        if not w.get("title"): continue
        stats[src]["retrieved"] += 1
        doi = (w.get("doi") or "").lower(); nt = norm(w["title"])
        hit = by_doi.get(doi) if doi else None
        hit = hit or by_title.get(nt) or new.get(doi or "t:" + nt)
        if hit is not None and hit in base:
            stats[src]["in_openalex"] += 1; hit["sources"] = ";".join(sorted(set(hit["sources"].split(";")) | {src})); continue
        key = doi or "t:" + nt
        if key in new:
            new[key]["sources"] = ";".join(sorted(set(new[key]["sources"].split(";")) | {src})); continue
        stats[src]["new"] += 1
        new[key] = dict(key=key, doi=doi, title=w["title"], year=w.get("year") or "", type=w.get("type") or "", cited_by=w.get("cited_by") or 0,
                        venue=w.get("venue") or "", language=w.get("language") or "en", abstract=w.get("abstract") or "", queries=f"{src}:{Path(f).stem}", sources=src)
# abstracts for new records lacking one (OpenAlex batch by DOI)
need = [r["doi"] for r in new.values() if r["doi"] and not r["abstract"]]
def inv(i):
    if not i: return ""
    pos = {p: w for w, ps in i.items() for p in ps}; return " ".join(pos[p] for p in sorted(pos))
got = 0
for k in range(0, len(need), 40):
    b = need[k:k + 40]
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode({"filter": "doi:" + "|".join("https://doi.org/" + x for x in b), "per-page": 50, "select": "doi,abstract_inverted_index"}, safe=":|/")
    for t in range(8):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "survey-merge/1.0"}), timeout=60) as r: j = json.load(r); break
        except urllib.error.HTTPError as e:
            if e.code == 400: j = None; break
            time.sleep(10 * (t + 1))
        except Exception: time.sleep(10)
    else: j = None
    for w in (j or {}).get("results", []):
        d = (w.get("doi") or "").replace("https://doi.org/", "").lower()
        if d in new and not new[d]["abstract"]: new[d]["abstract"] = inv(w.get("abstract_inverted_index")); got += bool(new[d]["abstract"])
    time.sleep(2)
allr = base + list(new.values())
for r in allr: r.setdefault("queries", "")
with open(HERE / "corpus_all.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields + ["sources"], extrasaction="ignore"); w.writeheader(); w.writerows(allr)
out = {k: dict(v, queries=len(v["queries"])) for k, v in stats.items()}
out["openalex"] = dict(retrieved=json.load(open(HERE / "prisma_counts.json"))["records_retrieved"], unique=len(base))
out["union"] = dict(unique=len(allr), new_from_other_sources=len(new), abstracts_filled_from_openalex=got)
(HERE / "sources_counts.json").write_text(json.dumps(out, indent=1)); print(json.dumps(out))
