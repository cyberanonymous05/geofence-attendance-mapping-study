"""Human-factor keyword counts for the audited geofence attendance abstracts (strict patterns only; a keyword scan, not coding of meaning).
Output: gen/stats_human.tex (macros hfConsent, hfDevBind, hfN)."""
import csv, re
from pathlib import Path
S = Path(__file__).parent
stage1 = {r["id"]: r for r in csv.DictReader(open(S / "screening/stage1.csv"))}
audit = list(csv.DictReader(open(S / "screening/audit.csv")))
PAT = {
    # explicit mention of consent or an opt-in / opt-out choice for the person being tracked
    "hfConsent": r"\bconsent\b|opt-?in\b|opt-?out\b",
    # binding the attendance record to a device identity (IMEI, device id, hardware id, MAC address)
    "hfDevBind": r"\bimei\b|device[ -](id|identifier|binding)|hardware id|mac address",
}
mac = {"hfN": len(audit)}
for k, p in PAT.items():
    mac[k] = sum(1 for a in audit if re.search(p, stage1[a["id"]]["title"] + " " + stage1[a["id"]]["abstract"], re.I))
(S / "gen/stats_human.tex").write_text("\n".join(f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in mac.items()) + "\n")
print(mac)
