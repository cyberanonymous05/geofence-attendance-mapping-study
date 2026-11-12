"""Agreement between coder 1 (all 28 full-text papers) and coder 2 (an AI coder, blind, random 15 papers), computed BEFORE any adjudication."""
import csv, json
from collections import Counter
c1 = {r["id"]: r for r in csv.DictReader(open("fulltext_codes_coder1.csv"))}
mp = json.load(open("blind_mapping.json"))
c2 = {mp[r["paper"]]: r for r in csv.DictReader(open("fulltext_codes_coder2_blind_raw.csv"))}
Q = [f"Q{i}" for i in range(1, 8)]
def kappa(a, b):
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n
    pa = Counter(a); pb = Counter(b)
    pe = sum((pa[k] / n) * (pb[k] / n) for k in "YN")
    return (po - pe) / (1 - pe) if pe < 1 else float("nan"), po
ids_all = sorted(set(c2) & set(c1))   # 1251 (web-page boilerplate, no usable full text) was excluded by coder 1
# Only papers with a Creative Commons licence are analysed in the paper (PeerJ asks for permission before copyrighted text goes into an AI tool),
# so the agreement figures use the double-coded papers that carry a CC licence.
lic = {r["id"]: r["license"] for r in csv.DictReader(open("fulltext_licences.csv"))}
ids = [i for i in ids_all if lic.get(i, "").startswith("cc-")]
print("papers double-coded:", len(ids))
tot_a, tot_b = [], []
rows = []
for q in Q:
    a = [c1[i][q] for i in ids]; b = [c2[i][q] for i in ids]
    k, po = kappa(a, b); tot_a += a; tot_b += b
    rows.append((q, po, k, sum(x == "Y" for x in a), sum(x == "Y" for x in b)))
    print(f"{q}: agreement {100*po:.0f}%  kappa {k:.2f}  (Y by coder1={rows[-1][3]}, by coder2={rows[-1][4]})")
k, po = kappa(tot_a, tot_b); print(f"ALL: agreement {100*po:.0f}%  kappa {k:.2f}  over {len(tot_a)} judgements")
print("disagreements:")
for i in ids:
    for q in Q:
        if c1[i][q] != c2[i][q]: print(f"  paper {i} {q}: coder1={c1[i][q]} coder2={c2[i][q]}")
json.dump(dict(rows=rows, all_kappa=k, all_agree=po, n=len(ids), n_all=len(ids_all), n_judgements=len(tot_a)), open("agreement.json", "w"))
