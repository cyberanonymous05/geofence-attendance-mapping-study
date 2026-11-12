"""Agreement between the human coder and the first coder. Usage:
   python3 human_agreement.py human_coding/coding_sheet_abstracts_done.csv human_coding/coding_sheet_fulltext_done.csv
Writes screening/human_agreement.json (used by the manuscript macros) and prints disagreements."""
import csv, json, sys
from collections import Counter
from pathlib import Path
S = Path(__file__).parent; D = S / "screening"
ab_path, ft_path = sys.argv[1], sys.argv[2]
key = json.load(open(D / "human_key.json"))
aud = {r["id"]: r for r in csv.DictReader(open(D / "audit.csv"))}
fin = {r["id"]: r for r in csv.DictReader(open(D / "fulltext_codes_final.csv"))}
yn = lambda x: "Y" if str(x).strip().upper().startswith("Y") else ("N" if str(x).strip().upper().startswith("N") and str(x).strip().upper() != "NA" else None)
def kappa(a, b):
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = Counter(a), Counter(b); pe = sum((pa[k] / n) * (pb[k] / n) for k in set(a) | set(b))
    return (po - pe) / (1 - pe) if pe < 1 else None, po
first = {  # first-coder value for each abstract field, from audit.csv (regex rules + two hand-coded fields)
 "A1_second_factor": lambda r: "Y" if any(r[k] == "1" for k in ("face", "biometric", "qr", "rfid_ble", "imei_dev")) else "N",
 "A2_boundary_shape": lambda r: "P" if r["polygon"] == "1" else ("C" if r["circle"] == "1" else "N"),
 "A3_proxy_fraud_spoofing": lambda r: "Y" if r["spoof"] == "1" else "N",
 "A4_reports_a_number": lambda r: "Y" if r["quant"] == "1" else "N",
 "A5_geofence_decision_or_position_error_measured": lambda r: "Y" if r["geo_metric"] == "1" else "N",
 "A6_location_error_handled": lambda r: "Y" if r["loc_err_handled"] == "1" else "N",
 "A7_privacy_mentioned": lambda r: "Y" if r["privacy"] == "1" else "N",
 "A8_uses_LoRa_or_LPWAN": lambda r: "Y" if r["lpwan"] == "1" else "N"}
res = {"abstract_fields": {}, "fulltext_fields": {}}
H1 = {r["paper"]: r for r in csv.DictReader(open(ab_path, encoding="utf-8-sig"))}
H2 = {r["paper"]: r for r in csv.DictReader(open(ft_path, encoding="utf-8-sig"))}
tot_a, tot_b, bad = [], [], []
for fld, f in first.items():
    a, b = [], []
    for p, i in key["abstracts"].items():
        h = (H1[p].get(fld) or "").strip().upper()[:1]
        if not h: continue
        a.append(f(aud[i])); b.append(h)
        if a[-1] != b[-1]: bad.append((fld, p, i, a[-1], b[-1]))
    k, po = kappa(a, b) if a else (None, None)
    res["abstract_fields"][fld] = dict(n=len(a), agree=po, kappa=k); tot_a += a; tot_b += b
for q in [f"Q{k}" for k in range(1, 8)]:
    a, b = [], []
    for p, i in key["fulltext"].items():
        h = yn(H2[p].get(q, ""))
        if h is None: continue
        a.append(fin[i][q]); b.append(h)
        if a[-1] != b[-1]: bad.append((q, p, i, a[-1], b[-1]))
    k, po = kappa(a, b) if a else (None, None)
    res["fulltext_fields"][q] = dict(n=len(a), agree=po, kappa=k); tot_a += a; tot_b += b
# pooled agreement per section
def pool(section):
    A, B = [], []
    if section == "abstract":
        for fld, f in first.items():
            for p, i in key["abstracts"].items():
                h = (H1[p].get(fld) or "").strip().upper()[:1]
                if h: A.append(f(aud[i])); B.append(h)
    else:
        for q in [f"Q{k}" for k in range(1, 8)]:
            for p, i in key["fulltext"].items():
                h = yn(H2[p].get(q, ""))
                if h: A.append(fin[i][q]); B.append(h)
    k, po = kappa(A, B) if A else (None, None)
    return dict(n_judgements=len(A), agree=po, kappa=k)
res["abstract_pooled"] = pool("abstract"); res["fulltext_pooled"] = pool("fulltext")
res["n_abstract_papers"] = len(key["abstracts"]); res["n_fulltext_papers"] = len(key["fulltext"])
(D / "human_agreement.json").write_text(json.dumps(res, indent=1))
for sec in ("abstract_fields", "fulltext_fields"):
    for f, v in res[sec].items(): print(f"{f}: n={v['n']} agree={v['agree'] if v['agree'] is None else round(100*v['agree'])}% kappa={v['kappa'] if v['kappa'] is None else round(v['kappa'], 2)}")
print("pooled abstracts:", res["abstract_pooled"]); print("pooled full texts:", res["fulltext_pooled"])
print("disagreements (field, sheet id, record id, first coder, human):"); [print("  ", x) for x in bad]
