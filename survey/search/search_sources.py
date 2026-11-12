"""Second and third open sources: Crossref and arXiv (plus Semantic Scholar if it answers).
All are free and need no login. Results are normalised to one schema and cached in raw_other/.
Scopus, IEEE Xplore and Web of Science need institutional access and were NOT searched."""
import json, re, sys, time, urllib.parse, urllib.request, urllib.error
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "raw_other"; OUT.mkdir(exist_ok=True)
UA = {"User-Agent": "survey-search/1.0"}
FROM = "2005-01-01"

# (id, query). Same topics as the OpenAlex run, simplified (these engines have no phrase operators in the same form).
QUERIES = [
    ("c01", "geofencing attendance"), ("c02", "geofence attendance system mobile application"),
    ("c03", "GPS based attendance system"), ("c04", "LoRa attendance system"), ("c05", "LoRa GPS tracking geofence"),
    ("c06", "LoRaWAN geofencing"), ("c07", "attendance system review survey"), ("c08", "RFID attendance system"),
    ("c09", "BLE beacon attendance"), ("c10", "face recognition attendance system"), ("c11", "QR code attendance system"),
    ("c12", "geofence location error false alarm"), ("c13", "adaptive GPS sampling energy geofence"),
    ("c14", "LoRaWAN scalability collisions capacity"), ("c15", "location privacy attendance students"),
    ("c16", "geofencing survey review"), ("c17", "LPWAN survey review"), ("c18", "smart campus attendance IoT LoRa"),
]
ARXIV_Q = [("a01", "all:geofence AND all:attendance"), ("a02", "all:geofencing AND all:LoRa"), ("a03", "all:attendance AND all:LoRa"),
           ("a04", "all:geofence AND all:GPS AND all:accuracy"), ("a05", "all:attendance AND all:smartphone AND all:GPS"),
           ("a06", "all:LoRaWAN AND all:scalability")]


def get(url, accept="application/json", tries=6):
    d = 5
    for _ in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={**UA, "Accept": accept}), timeout=60) as r:
                return r.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            if e.code in (400, 404): return None
            time.sleep(d); d = min(d * 2, 60)
        except Exception:
            time.sleep(d); d = min(d * 2, 60)
    return None


def crossref(qid, q, pages=1):
    res, total = [], 0
    for pg in range(pages):
        p = {"query.bibliographic": q, "rows": 100, "offset": pg * 100,
             "filter": f"from-pub-date:{FROM},type:journal-article,type:proceedings-article,type:posted-content,type:book-chapter",
             "select": "DOI,title,container-title,issued,type,abstract,is-referenced-by-count"}
        t = get("https://api.crossref.org/works?" + urllib.parse.urlencode(p, safe=":,"))
        if not t: break
        m = json.loads(t)["message"]; total = m.get("total-results", 0)
        for w in m["items"]:
            ab = re.sub(r"<[^>]+>", " ", w.get("abstract") or "")
            res.append(dict(doi=(w.get("DOI") or "").lower(), title=(w.get("title") or [""])[0], year=(w.get("issued", {}).get("date-parts") or [[None]])[0][0],
                            type=w.get("type"), cited_by=w.get("is-referenced-by-count", 0), venue=(w.get("container-title") or [""])[0],
                            language="en", abstract=re.sub(r"\s+", " ", ab).strip()))
        time.sleep(1)
    return dict(_source="crossref", _query=q, total=total, results=res)


def arxiv(qid, q):
    t = get("http://export.arxiv.org/api/query?" + urllib.parse.urlencode({"search_query": q, "max_results": 100, "sortBy": "relevance"}), "application/atom+xml")
    if not t: return None
    ns = {"a": "http://www.w3.org/2005/Atom"}; root = ET.fromstring(t); res = []
    tot = root.find("{http://a9.com/-/spec/opensearch/1.1/}totalResults")
    for e in root.findall("a:entry", ns):
        idu = e.find("a:id", ns).text.strip(); aid = idu.split("/abs/")[-1]
        aid_nov = re.sub(r"v\d+$", "", aid)
        res.append(dict(doi=f"10.48550/arxiv.{aid_nov}".lower(), title=re.sub(r"\s+", " ", e.find("a:title", ns).text).strip(),
                        year=int(e.find("a:published", ns).text[:4]), type="posted-content", cited_by=0, venue="arXiv", language="en",
                        abstract=re.sub(r"\s+", " ", e.find("a:summary", ns).text).strip()))
    time.sleep(3)
    return dict(_source="arxiv", _query=q, total=int(tot.text) if tot is not None else len(res), results=res)


def s2(qid, q):
    p = {"query": q, "limit": 100, "year": "2005-", "fields": "title,year,externalIds,abstract,venue,citationCount,publicationTypes"}
    t = get("https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode(p), tries=4)
    if not t: return None
    j = json.loads(t); res = []
    for w in j.get("data", []):
        doi = ((w.get("externalIds") or {}).get("DOI") or "").lower()
        res.append(dict(doi=doi, title=w.get("title") or "", year=w.get("year"), type=",".join(w.get("publicationTypes") or []), cited_by=w.get("citationCount", 0),
                        venue=w.get("venue") or "", language="en", abstract=w.get("abstract") or ""))
    time.sleep(3)
    return dict(_source="semanticscholar", _query=q, total=j.get("total", len(res)), results=res)


def main():
    today = date.today().isoformat()
    jobs = [("crossref", qid, q) for qid, q in QUERIES] + [("arxiv", qid, q) for qid, q in ARXIV_Q] + [("s2", f"s{qid[1:]}", q) for qid, q in QUERIES[:8]]
    only = sys.argv[1] if len(sys.argv) > 1 else None   # e.g. "crossref" to run one source
    for src, qid, q in jobs:
        if only and src != only: continue
        f = OUT / f"{src}_{qid}.json"
        if f.exists(): continue
        pages = 3 if (src == "crossref" and qid in ("c01", "c02", "c03")) else 1
        d = crossref(qid, q, pages) if src == "crossref" else (arxiv(qid, q) if src == "arxiv" else s2(qid, q))
        if d is None:
            print("FAILED", src, qid, file=sys.stderr); continue
        d["_run_date"] = today; f.write_text(json.dumps(d)); print(src, qid, len(d["results"]), "of", d["total"], file=sys.stderr)


if __name__ == "__main__":
    main()
