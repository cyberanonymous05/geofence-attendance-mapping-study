"""Record the licence of the open-access copy of each coded full text (as OpenAlex lists it).
Why: PeerJ's AI policy asks for permission from copyright holders before copyrighted material is put into an AI tool,
so the paper reports how many of the coded full texts carry a Creative Commons licence and how many are free to read with no licence recorded.
Output: fulltext_licences.csv (id, doi, oa_status, license, host). Needs network. Usage: python3 -I fulltext_licences.py"""
import csv, json, time, urllib.parse, urllib.request
from pathlib import Path
D = Path(__file__).parent
status = [r for r in csv.DictReader(open(D / "fulltext_status.csv")) if r["status"] == "fulltext"]
coded = {r["id"] for r in csv.DictReader(open(D / "fulltext_codes_final.csv"))}
out = []
for r in status:
    if r["id"] not in coded:
        continue
    url = "https://api.openalex.org/works/doi:" + urllib.parse.quote(r["doi"]) + "?select=doi,title,best_oa_location,open_access"
    lic = host = oa = ""
    for k in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "survey-licence-check/1.0"})
            j = json.load(urllib.request.urlopen(req, timeout=30))
            b = j.get("best_oa_location") or {}
            lic = b.get("license") or ""
            host = (b.get("source") or {}).get("display_name") or ""
            oa = (j.get("open_access") or {}).get("oa_status", "")
            break
        except Exception:
            time.sleep(2)
    out.append((r["id"], r["doi"], oa, lic, host))
with open(D / "fulltext_licences.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["id", "doi", "oa_status", "license", "host"]); w.writerows(out)
print(len(out), "papers;", sum(1 for o in out if o[3].startswith("cc-")), "with a Creative Commons licence")
