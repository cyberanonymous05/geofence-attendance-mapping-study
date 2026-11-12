"""Abstract-level coding of geofence-based attendance/presence systems (stage 2).
Inclusion: geofence bucket AND attendance/presence term in title or first 400 chars of abstract AND the
paper proposes/evaluates a system (not a review). Coding is by regex on the abstract only; absence in an
abstract does NOT mean absence in the paper. Output: audit.csv + printed counts."""
import csv, json, re
rows = list(csv.DictReader(open("stage1.csv")))
ATT = re.compile(r"attendance|presence (system|monitoring|recognition|verification|tracking|detection|validation|application|record)|(teacher|employee|staff|student|professor|lecturer|worker)s?'? presence|presensi|absensi|kehadiran|truancy|working hours|check-in|roll call", re.I)
STOP_EN = set("the of and to in is a for that with on as by are this be an or from at it which can was were has have not their these also using used based system".split())
def is_english(text):
    tk = re.findall(r"[a-z]+", text.lower())
    return len(tk) >= 20 and sum(t in STOP_EN for t in tk) / len(tk) >= 0.15
VER = {r["id"]: r for r in csv.DictReader(open("verification_log.csv")) if r["status"] == "verified"}
sel = [r for r in rows if "geofence" in r["buckets"].split(";") and ATT.search(r["title"] + " " + r["abstract"][:400])]
REVIEWISH = re.compile(r"\breview\b|survey|scoping", re.I)
sel = [r for r in sel if not REVIEWISH.search(r["title"])]
open("audit_candidates.csv", "w").write("id\n" + "\n".join(r["id"] for r in sel) + "\n")   # input of build_bib.py
n_loose = len(sel)
excl_lang = [r for r in sel if not is_english(r["abstract"])]
sel = [r for r in sel if is_english(r["abstract"])]
json.dump(dict(candidates=len(sel), excluded_nonenglish=len(excl_lang), excluded_ids=[r["id"] for r in excl_lang]), open("audit_stats.json", "w"))
open("audit_candidates.csv", "w").write("id\n" + "\n".join(r["id"] for r in sel) + "\n")
print("candidates (before DOI verification):", len(sel), "| dropped, abstract not in English:", len(excl_lang))
sel = [r for r in sel if r["id"] in VER]
F = {
 "face":      r"face|facial|liveness",
 "biometric": r"fingerprint|biometric|voice|iris",
 "qr":        r"\bqr\b|barcode",
 "rfid_ble":  r"rfid|\bnfc\b|bluetooth|beacon|\bble\b",
 "imei_dev":  r"imei|device id|device binding",
 "quant":     r"\d+(\.\d+)?\s?%|accuracy of|\d+\s+(students|users|employees|respondents|participants|scenarios|tests|trials|samples|sessions)|\bsus\b|system usability|precision|recall|f1",
 "gps_err":   r"gps (error|accuracy|drift|noise|inaccura)|(accuracy|error|inaccuracy|uncertainty) of (the )?(gps|location)|location (error|uncertainty|accuracy)|uncertaint|tolerance|hysteresis|multipath|jitter|signal (loss|strength|quality)|buffer zone",
 "spoof":     r"spoof|mock location|fake gps|fake location|fraud|proxy|buddy|manipulat|cheat",
 "polygon":   r"polygon|winding number|ray[- ]cast",
 "circle":    r"haversine|circular|radius|distance formula",
 "privacy":   r"privacy|gdpr|consent|data protection|encrypt",
 "deployed":  r"deployed|implemented at|case study|pilot|field test|real[- ]world|in situ|at pt|school|police|hospital",
 "lpwan":     r"\blora\b|lorawan",
}
# Hand-coded after reading the abstracts (regexes cannot judge these):
GEO_DECISION_METRIC = {"739", "992", "1242", "1249", "1280", "1992"}   # reports a measurement of the geofence in/out decision or position error
LOC_ERROR_HANDLED   = {"1244", "1247", "1249", "1260"}          # abstract states that location error/uncertainty is handled or modelled
out = []
for r in sorted(sel, key=lambda r: int(r["year"] or 0)):
    t = r["title"] + " " + r["abstract"]
    row = dict(id=r["id"], year=r["year"], venue=r["venue"][:50], type=r["type"], title=r["title"][:90], doi=r["doi"])
    for k, p in F.items():
        row[k] = int(re.search(p, t, re.I) is not None)
    row["geo_metric"] = int(r["id"] in GEO_DECISION_METRIC)
    row["loc_err_handled"] = int(r["id"] in LOC_ERROR_HANDLED)
    row["key"] = VER[r["id"]]["key"]
    row["polygon"] = int(re.search(F["polygon"] + r"|aabb|bounding box", t, re.I) is not None)
    out.append(row)
with open("audit.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
n = len(out)
print("N =", n, " years:", min(int(r["year"]) for r in out), "-", max(int(r["year"]) for r in out))
for k in list(F) + ["geo_metric", "loc_err_handled"]:
    c = sum(r[k] for r in out)
    print(f"{k:10s} {c:3d}  {100*c/n:4.0f}%")
by = {}
for r in out: by.setdefault(r["year"], 0); by[r["year"]] += 1
print("by year:", dict(sorted(by.items())))
print("any 2nd factor (face/biometric/qr/rfid_ble/imei):", sum(1 for r in out if r["face"] or r["biometric"] or r["qr"] or r["rfid_ble"] or r["imei_dev"]))

