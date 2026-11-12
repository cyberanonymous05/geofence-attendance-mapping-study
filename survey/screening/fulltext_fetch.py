"""Download open-access full texts of audited papers into a scratch dir (NOT the repo; texts are not redistributed).
Each paper gets its own directory. PDFs go through pdftotext, HTML is tag-stripped. Writes fulltext_status.csv."""
import csv, json, re, subprocess, sys, urllib.request
from pathlib import Path
SCR = Path(sys.argv[1]); SCR.mkdir(parents=True, exist_ok=True)
meta = json.load(open("meta_cache.json"))
ver = {r["id"]: r for r in csv.DictReader(open("verification_log.csv")) if r["status"] == "verified"}
aud = [r["id"] for r in csv.DictReader(open("audit.csv"))]
out = []
for i in aud:
    doi = ver[i]["doi"].lower(); m = meta.get(doi) or {}
    rec = dict(id=i, doi=doi, status="no-oa", chars=0, url=m.get("pdf_url") or m.get("oa_url") or "")
    if m.get("is_oa") and rec["url"]:
        d = SCR / i; d.mkdir(exist_ok=True)
        try:
            req = urllib.request.Request(rec["url"], headers={"User-Agent": "Mozilla/5.0 (survey fulltext check)"})
            with urllib.request.urlopen(req, timeout=40) as r: raw = r.read(25_000_000)
            (d / "raw.bin").write_bytes(raw)
            if raw[:4] == b"%PDF":
                subprocess.run(["pdftotext", "-layout", str(d / "raw.bin"), str(d / "text.txt")], timeout=90, check=False)
                txt = (d / "text.txt").read_text(errors="ignore") if (d / "text.txt").exists() else ""
            else:
                h = raw.decode("utf-8", "ignore")
                h = re.sub(r"(?is)<(script|style|nav|header|footer)[^>]*>.*?</\1>", " ", h)
                txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)); (d / "text.txt").write_text(txt)
            rec["chars"] = len(txt); rec["status"] = "fulltext" if len(txt) > 8000 else "short"
        except Exception as e:
            rec["status"] = "error:" + type(e).__name__
    out.append(rec); print(i, rec["status"], rec["chars"], file=sys.stderr)
with open("fulltext_status.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
from collections import Counter
print(Counter(r["status"] for r in out))
