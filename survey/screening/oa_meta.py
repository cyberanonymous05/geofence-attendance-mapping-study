"""Fetch open-access links and venue flags from OpenAlex for a list of DOIs (batches of 40). Cached in meta_cache.json."""
import json, sys, time, urllib.parse, urllib.request, urllib.error
from pathlib import Path
CACHE = Path(__file__).parent / "meta_cache.json"
SEL = "doi,open_access,best_oa_location,primary_location,cited_by_count,publication_year,type"

def fetch(url, tries=10):
    d = 5
    for _ in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "survey-meta/1.0"}), timeout=60) as r: return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 400: return None
            time.sleep(d); d = min(d * 2, 60)
        except Exception: time.sleep(d); d = min(d * 2, 60)
    return None

def get_meta(dois):
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    todo = [d for d in dois if d and d.lower() not in cache]
    for i in range(0, len(todo), 40):
        b = todo[i:i + 40]
        p = {"filter": "doi:" + "|".join("https://doi.org/" + d for d in b), "per-page": 50, "select": SEL}
        j = fetch("https://api.openalex.org/works?" + urllib.parse.urlencode(p, safe=":|/"))
        got = set()
        for w in (j or {}).get("results", []):
            doi = (w.get("doi") or "").replace("https://doi.org/", "").lower()
            src = (w.get("primary_location") or {}).get("source") or {}
            bo = w.get("best_oa_location") or {}
            cache[doi] = dict(is_oa=(w.get("open_access") or {}).get("is_oa"), oa_url=bo.get("pdf_url") or bo.get("landing_page_url"), pdf_url=bo.get("pdf_url"),
                              src_type=src.get("type"), src_core=src.get("is_core"), src_doaj=src.get("is_in_doaj"), src_name=src.get("display_name"),
                              cited_by=w.get("cited_by_count"), year=w.get("publication_year"))
            got.add(doi)
        for d in b:
            if d.lower() not in got: cache[d.lower()] = None
        CACHE.write_text(json.dumps(cache)); time.sleep(2)
    return {d: cache.get(d.lower()) for d in dois}

if __name__ == "__main__":
    import csv
    ver = {r["id"]: r for r in csv.DictReader(open("verification_log.csv")) if r["status"] == "verified"}
    aud = [r["id"] for r in csv.DictReader(open("audit.csv"))]
    m = get_meta([ver[i]["doi"] for i in aud])
    ok = [d for d, v in m.items() if v]
    print("meta for", len(ok), "of", len(m), "; OA:", sum(1 for d in ok if m[d]["is_oa"]), "; core venues:", sum(1 for d in ok if m[d]["src_core"]))
