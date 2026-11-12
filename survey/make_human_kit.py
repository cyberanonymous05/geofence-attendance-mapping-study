"""Build the blind human re-coding kit (human_coding/): a stratified random sample of audited abstracts and ALL coded full-text papers.
The key that links neutral ids to papers is written OUTSIDE human_coding/ (screening/human_key.json); the human must not open it.
Stratification: rare properties (geofence measured / location error handled / adversarial test) are over-sampled so agreement on them is testable."""
import csv, json, random
from pathlib import Path
S = Path(__file__).parent; D = S / "screening"; H = S / "human_coding"; H.mkdir(exist_ok=True)
rows = {r["id"]: r for r in csv.DictReader(open(D / "stage1.csv"))}
aud = list(csv.DictReader(open(D / "audit.csv")))
ft = {r["id"]: r for r in csv.DictReader(open(D / "fulltext_codes_final.csv"))}
meta = json.load(open(D / "meta_cache.json")); ver = {r["id"]: r for r in csv.DictReader(open(D / "verification_log.csv"))}
rng = random.Random(11)
# abstracts: 15 = all-rare-property papers (up to 6) + random others
rare = [a["id"] for a in aud if a["geo_metric"] == "1" or a["loc_err_handled"] == "1"]
pick_a = rng.sample(rare, min(6, len(rare)))
others = [a["id"] for a in aud if a["id"] not in pick_a]
pick_a += rng.sample(others, 15 - len(pick_a)); rng.shuffle(pick_a)
# full texts: ALL coded papers (28), in random order, so every reported full-text code has a human second look.
# (An earlier version sampled 15 of the 28; the abstract sample above is unchanged because it is drawn first from the same seed.)
pick_f = list(ft); rng.shuffle(pick_f)
key = {"abstracts": {f"P{k:02d}": i for k, i in enumerate(pick_a, 1)}, "fulltext": {f"F{k:02d}": i for k, i in enumerate(pick_f, 1)}}
(D / "human_key.json").write_text(json.dumps(key))
A = ["A1_second_factor", "A2_boundary_shape", "A3_proxy_fraud_spoofing", "A4_reports_a_number", "A5_geofence_decision_or_position_error_measured", "A6_location_error_handled", "A7_privacy_mentioned", "A8_uses_LoRa_or_LPWAN"]
with open(H / "coding_sheet_abstracts.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["paper", "title", "year", "doi", "abstract"] + A)
    for p, i in key["abstracts"].items(): w.writerow([p, rows[i]["title"], rows[i]["year"], ver[i]["doi"], rows[i]["abstract"]] + [""] * len(A))
Q = [f"Q{k}" for k in range(1, 8)]
with open(H / "coding_sheet_fulltext.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["paper", "title", "year", "doi", "open_access_link"] + Q + ["notes"])
    for p, i in key["fulltext"].items():
        m = meta.get(ver[i]["doi"].lower()) or {}
        w.writerow([p, rows[i]["title"], rows[i]["year"], ver[i]["doi"], m.get("pdf_url") or m.get("oa_url") or ""] + [""] * len(Q) + [""])
print(len(pick_a), "abstracts;", len(pick_f), "full texts; key ->", D / "human_key.json")
