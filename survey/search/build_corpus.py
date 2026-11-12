"""Merge raw OpenAlex results into one deduplicated corpus for screening.

Reads raw/q*.json, removes duplicates (DOI, else normalised title), reconstructs abstracts from the
inverted index, and writes corpus.csv plus prisma_counts.json (identification-stage numbers for the
PRISMA-style flow in the survey).
"""
import csv, json, re
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent


def abstract(inv):
    if not inv:
        return ""
    pos = {}
    for w, idxs in inv.items():
        for i in idxs:
            pos[i] = w
    return " ".join(pos[i] for i in sorted(pos))


def norm_title(t):
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


def main():
    recs = {}
    hits = defaultdict(set)
    n_raw = 0
    per_query = {}
    for p in sorted((HERE / "raw").glob("q*.json")):
        d = json.loads(p.read_text())
        qid = p.stem
        per_query[qid] = dict(total_hits=d["meta"]["count"], retrieved=len(d["results"]),
                              theme=d.get("_theme"), query=d.get("_query"))
        for w in d["results"]:
            n_raw += 1
            doi = (w.get("doi") or "").replace("https://doi.org/", "").lower()
            key = doi or "t:" + norm_title(w.get("title"))
            hits[key].add(qid)
            if key not in recs:
                loc = (w.get("primary_location") or {}).get("source") or {}
                recs[key] = dict(
                    key=key, doi=doi, title=w.get("title") or "", year=w.get("publication_year"),
                    type=w.get("type"), cited_by=w.get("cited_by_count"), venue=loc.get("display_name") or "",
                    language=w.get("language"), abstract=abstract(w.get("abstract_inverted_index")),
                )
    # second-pass dedupe by normalised title across DOI/no-DOI variants
    seen_t, out = {}, []
    for k, r in recs.items():
        nt = norm_title(r["title"])
        if nt and nt in seen_t:
            hits[seen_t[nt]] |= hits[k]
            continue
        seen_t[nt] = k
        r["queries"] = ";".join(sorted(hits[k]))
        out.append(r)
    out.sort(key=lambda r: (-(r["cited_by"] or 0)))
    with open(HERE / "corpus.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader(); w.writerows(out)
    stats = dict(queries=len(per_query), records_retrieved=n_raw, unique_records=len(out),
                 with_abstract=sum(1 for r in out if r["abstract"]), per_query=per_query)
    (HERE / "prisma_counts.json").write_text(json.dumps(stats, indent=1))
    print({k: v for k, v in stats.items() if k != "per_query"})


if __name__ == "__main__":
    main()
