"""Reproducible literature search against the OpenAlex API (no login, no key).

Every query, its reported total hit count, and the retrieved records are written to disk so the
survey's search protocol can be audited. Re-running gives different numbers over time (OpenAlex is
updated continuously); the run date is logged.

Usage: python3 search_openalex.py            (writes raw/*.json and query_log.csv)
"""
import csv, json, os, sys, time, urllib.parse, urllib.request, urllib.error
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
RAW = HERE / "raw"
RAW.mkdir(exist_ok=True)

FROM_YEAR = 2005          # earliest year retained
PER_PAGE = 100
PAGES = 1                 # top-100 by relevance per query; documented limitation
SELECT = "id,doi,title,publication_year,type,cited_by_count,primary_location,abstract_inverted_index,language"

# (id, theme, query string). Quoted phrases are OpenAlex phrase matches.
QUERIES = [
    ("q01", "geofence-attendance",  'geofencing attendance'),
    ("q02", "geofence-attendance",  'geofence "attendance system"'),
    ("q03", "gps-attendance",       'GPS "attendance system"'),
    ("q04", "lora-attendance",      'LoRa attendance'),
    ("q05", "lora-tracking",        'LoRa GPS tracking'),
    ("q06", "lora-tracking",        'LoRaWAN "asset tracking"'),
    ("q07", "geofence-core",        'geofencing "location-based" service'),
    ("q08", "geofence-core",        'geofence boundary detection GPS error'),
    ("q09", "geofence-core",        'geofence "false" alarms hysteresis'),
    ("q10", "attendance-other",     'RFID "attendance system"'),
    ("q11", "attendance-other",     'Bluetooth "attendance" smartphone'),
    ("q12", "attendance-other",     'WiFi "attendance" localization'),
    ("q13", "attendance-other",     'face recognition "attendance system"'),
    ("q14", "attendance-other",     'IoT "smart attendance"'),
    ("q15", "lora-scaling",         'LoRaWAN scalability collisions capacity'),
    ("q16", "lora-scaling",         'LoRa spreading factor capture effect'),
    ("q17", "lora-scaling",         'LoRaWAN "ALOHA" uplink "packet delivery"'),
    ("q18", "gps-energy",           'adaptive GPS sampling energy mobile'),
    ("q19", "gps-energy",           'duty cycling GPS energy-efficient localization'),
    ("q20", "gps-accuracy",         'smartphone GPS accuracy urban canyon'),
    ("q21", "privacy",              'location privacy tracking students'),
    ("q22", "privacy",              'attendance monitoring privacy surveillance university'),
    ("q23", "security",             'LoRaWAN security vulnerabilities'),
    ("q24", "security",             'GPS spoofing detection'),
    ("q25", "presence-detection",   'presence detection geofence smartphone indoor outdoor'),
    ("q26", "campus-sensing",       'campus mobility smartphone sensing students dataset'),
    ("q27", "indoor-position",      'indoor localization WiFi fingerprint survey'),
    ("q28", "tracking-lora-sota",   'LoRa localization survey'),
    ("q29", "prior-surveys",        'attendance system survey review'),
    ("q30", "prior-surveys",        'automated attendance management systems review'),
    ("q31", "prior-surveys",        'geofencing survey'),
    ("q32", "prior-surveys",        'LPWAN survey LoRa NB-IoT Sigfox'),
    ("q33", "prior-surveys",        'LoRaWAN survey review'),
    ("q34", "attendance-other",     'NFC OR QR attendance system university'),
    ("q35", "attendance-other",     'deep learning face recognition attendance classroom'),
    ("q36", "attendance-other",     'BLE beacon attendance classroom'),
    ("q37", "attendance-other",     'fingerprint biometric attendance system'),
    ("q38", "presence-detection",   'occupancy detection building sensing survey'),
    ("q39", "gps-energy",           'GPS energy consumption smartphone location sensing'),
    ("q40", "geofence-core",        'geofence monitoring energy-efficient mobile'),
]


def fetch(url, tries=12):
    delay = 5
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "survey-search/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")
            if e.code == 400:                      # bad query: retrying cannot help
                raise RuntimeError("HTTP 400: " + body[:300])
            wait = delay
            try:
                wait = max(wait, int(json.loads(body).get("retryAfter", wait)) + 1)
            except Exception:
                pass
            print(f"  HTTP {e.code}, retry in {wait}s", file=sys.stderr)
            time.sleep(wait)
            delay = min(delay * 2, 90)
        except RuntimeError:
            raise
        except Exception as e:                       # network blip
            print(f"  {type(e).__name__}: {e}, retry in {delay}s", file=sys.stderr)
            time.sleep(delay)
            delay = min(delay * 2, 60)
    raise RuntimeError("giving up: " + url)


def main():
    today = date.today().isoformat()
    log_path = HERE / "query_log.csv"
    rows = []
    for qid, theme, q in QUERIES:
        out = RAW / f"{qid}.json"
        if out.exists():
            d = json.loads(out.read_text())
        else:
            params = {
                "search": q,
                "filter": f"from_publication_date:{FROM_YEAR}-01-01,type:article|review|preprint|book-chapter|conference-paper",
                "per-page": PER_PAGE, "page": 1, "select": SELECT,
            }
            if os.environ.get("OPENALEX_API_KEY"):          # optional; supplied by the user, never hard-coded
                params["api_key"] = os.environ["OPENALEX_API_KEY"]
            url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params, safe=":|,")
            print(qid, q, file=sys.stderr)
            try:
                d = fetch(url)
            except Exception as ex:
                print(f"  FAILED {qid}: {ex}", file=sys.stderr)
                rows.append(dict(qid=qid, theme=theme, query=q, run_date=today, total_hits=-1, retrieved=0))
                continue
            d["_query"] = q; d["_theme"] = theme; d["_run_date"] = today
            out.write_text(json.dumps(d))
            time.sleep(2)
        rows.append(dict(qid=qid, theme=theme, query=q, run_date=d.get("_run_date", today),
                         total_hits=d["meta"]["count"], retrieved=len(d["results"])))
    with open(log_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    for r in rows:
        print(f'{r["qid"]} {r["total_hits"]:>7} hits  {r["query"]}')


if __name__ == "__main__":
    main()
