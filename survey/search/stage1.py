"""Stage 1: topic buckets by title/abstract regex (transparent, reproducible). Writes ../screening/stage1.csv."""
import csv, os, re
rows = list(csv.DictReader(open("corpus_all.csv" if os.path.exists("corpus_all.csv") else "corpus.csv")))
T = lambda r, p: re.search(p, r["title"].lower()) is not None
A = lambda r, p: re.search(p, (r["title"] + " " + r["abstract"]).lower()) is not None
BUCKETS = {
 "geofence":   lambda r: T(r, r"geofenc|geo-fenc|geo fenc"),
 "attendance": lambda r: T(r, r"attendance|roll[- ]call") and A(r, r"system|automat|smart|iot|monitor|track|detect"),
 "lpwan":      lambda r: T(r, r"\blora\b|lorawan|lpwan|low[- ]power wide|nb-iot|sigfox"),
 "gps-energy": lambda r: T(r, r"\bgps\b|\bgnss\b|location sensing|localization|positioning") and A(r, r"energy|battery|duty|power consumption"),
 "gps-error":  lambda r: T(r, r"\bgps\b|\bgnss\b") and T(r, r"accura|spoof|urban|error|multipath|jamm"),
 "privacy":    lambda r: T(r, r"location privacy|location tracking|surveillance|student privacy|facial recognition"),
}
out = []
for r in rows:
    if r["language"] not in ("en", "", None): continue
    if not r["abstract"]: continue
    b = [k for k, f in BUCKETS.items() if f(r)]
    if b:
        r = dict(r); r["buckets"] = ";".join(b); out.append(r)
import json, os
MAP = "../screening/id_map.json"          # ids are frozen across re-runs so hand-coded sets stay valid
idmap = json.load(open(MAP)) if os.path.exists(MAP) else {}
nxt = max(idmap.values(), default=-1) + 1
for r in sorted(out, key=lambda r: -(int(r["cited_by"] or 0))):
    if r["key"] not in idmap:
        idmap[r["key"]] = nxt; nxt += 1
    r["id"] = idmap[r["key"]]
json.dump(idmap, open(MAP, "w"))
fields = ["id", "key", "sources", "buckets", "year", "cited_by", "type", "venue", "title", "doi", "queries", "abstract"]
with open("../screening/stage1.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader()
    w.writerows(sorted(out, key=lambda r: int(r["id"])))
from collections import Counter
c = Counter(b for r in out for b in r["buckets"].split(";"))
print(len(out), dict(c))
