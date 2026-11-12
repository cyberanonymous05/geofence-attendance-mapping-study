"""Import exports from proprietary databases that need institutional login (Scopus, Web of Science, IEEE Xplore).

We cannot and must not log in for you. Run the queries below in the database yourself, export with abstracts, and save the
files in search/external/ named <db>_<queryid>.<ext>, e.g. scopus_S1.csv, wos_W1.txt, ieee_I1.csv.
Then:  python3 import_exports.py   (writes raw_other/<db>_<queryid>.json)  ->  python3 merge_sources.py -> make tables -> make pdf.

  python3 import_exports.py --write-md      regenerates external_queries.md from the QUERIES table below
"""
import csv, io, json, re, sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
EXT = HERE / "external"; OUT = HERE / "raw_other"; OUT.mkdir(exist_ok=True)

# Query IDs are file-name prefixes: scopus_S1.csv ... Themes mirror the OpenAlex queries (Appendix of the survey).
QUERIES = {
 "scopus": {
   "S1": 'TITLE-ABS-KEY ( ( geofenc* OR "geo-fenc*" ) AND ( attendance OR "presence monitoring" OR "presence system" ) ) AND PUBYEAR > 2004',
   "S2": 'TITLE-ABS-KEY ( ( lora OR lorawan OR lpwan ) AND ( attendance OR "roll call" ) ) AND PUBYEAR > 2004',
   "S3": 'TITLE-ABS-KEY ( ( gps OR gnss ) AND "attendance system" ) AND PUBYEAR > 2004',
   "S4": 'TITLE-ABS-KEY ( ( lora OR lorawan ) AND ( geofenc* OR "geo-fenc*" ) ) AND PUBYEAR > 2004',
   "S5": 'TITLE-ABS-KEY ( geofenc* AND ( "location error" OR "gps error" OR "positioning error" OR uncertainty OR hysteresis OR "false alarm*" ) ) AND PUBYEAR > 2004',
   "S6": 'TITLE ( attendance ) AND TITLE-ABS-KEY ( survey OR review OR "systematic review" ) AND PUBYEAR > 2004',
   "S7": 'TITLE-ABS-KEY ( ( rfid OR "face recognition" OR bluetooth OR ble OR "qr code" OR nfc OR fingerprint ) AND "attendance system" ) AND PUBYEAR > 2017',
   "S8": 'TITLE-ABS-KEY ( ( lorawan OR lora ) AND ( scalab* OR collision* OR capacity ) ) AND DOCTYPE ( ar OR re ) AND PUBYEAR > 2014',
 },
 "wos": {
   "W1": 'TS=((geofenc* OR "geo-fenc*") AND (attendance OR "presence monitoring" OR "presence system")) AND PY=(2005-2026)',
   "W2": 'TS=((lora OR lorawan OR lpwan) AND (attendance OR "roll call")) AND PY=(2005-2026)',
   "W3": 'TS=((gps OR gnss) AND "attendance system") AND PY=(2005-2026)',
   "W4": 'TS=((lora OR lorawan) AND (geofenc* OR "geo-fenc*")) AND PY=(2005-2026)',
   "W5": 'TS=(geofenc* AND ("location error" OR "gps error" OR "positioning error" OR uncertainty OR hysteresis OR "false alarm*")) AND PY=(2005-2026)',
   "W6": 'TI=(attendance) AND TS=(survey OR review OR "systematic review") AND PY=(2005-2026)',
 },
 "ieee": {   # IEEE Xplore search is free to run; abstracts are visible without a subscription; export CSV (up to 2,000 per export)
   "I1": '("All Metadata":geofenc*) AND ("All Metadata":attendance)',
   "I2": '("All Metadata":lora OR "All Metadata":lorawan) AND ("All Metadata":attendance)',
   "I3": '("All Metadata":gps) AND ("All Metadata":"attendance system")',
   "I4": '("All Metadata":lora OR "All Metadata":lorawan) AND ("All Metadata":geofenc*)',
   "I5": '("All Metadata":geofenc*) AND ("All Metadata":"location error" OR "All Metadata":"gps error" OR "All Metadata":hysteresis)',
 },
}
NAMES = {"scopus": "Scopus", "wos": "Web of Science", "ieee": "IEEE Xplore"}
CLEAN_DOI = lambda d: re.sub(r"^https?://(dx\.)?doi\.org/", "", (d or "").strip(), flags=re.I).lower()


def read_text(p):
    raw = Path(p).read_bytes()
    for enc in ("utf-8-sig", "utf-16", "latin-1"):
        try: return raw.decode(enc)
        except UnicodeError: continue
    return raw.decode("utf-8", "ignore")


def to_int(x):
    try: return int(float(str(x).strip()))
    except Exception: return 0


def parse(db, text):
    """Return normalised records from the text of one export file."""
    out = []
    if db == "scopus":
        for r in csv.DictReader(io.StringIO(text)):
            out.append(dict(doi=CLEAN_DOI(r.get("DOI")), title=r.get("Title", ""), year=to_int(r.get("Year")) or None, type=r.get("Document Type", ""),
                            cited_by=to_int(r.get("Cited by")), venue=r.get("Source title", ""),
                            language=(r.get("Language of Original Document") or "English")[:2].lower() if r.get("Language of Original Document") else "en",
                            abstract=re.sub(r"^\[No abstract available\]$", "", r.get("Abstract", "")).strip()))
    elif db == "wos":   # tab-delimited "plain text" export, field tags in the header
        for r in csv.DictReader(io.StringIO(text), delimiter="\t", quoting=csv.QUOTE_NONE):
            out.append(dict(doi=CLEAN_DOI(r.get("DI")), title=r.get("TI", ""), year=to_int(r.get("PY")) or None, type=r.get("DT", ""),
                            cited_by=to_int(r.get("TC")), venue=r.get("SO", ""), language=(r.get("LA") or "English")[:2].lower(), abstract=(r.get("AB") or "").strip()))
    elif db == "ieee":
        for r in csv.DictReader(io.StringIO(text)):
            out.append(dict(doi=CLEAN_DOI(r.get("DOI")), title=r.get("Document Title", ""), year=to_int(r.get("Publication Year")) or None, type=r.get("Content Type", ""),
                            cited_by=to_int(r.get("Article Citation Count")), venue=r.get("Publication Title", ""), language="en", abstract=(r.get("Abstract") or "").strip()))
    else:
        raise ValueError(db)
    return [o for o in out if o["title"]]


def lang_code(x):   # scopus/wos give 'English' -> 'en'; keep unknowns as given (stage 1 drops non-English)
    return {"en": "en", "ch": "zh", "sp": "es", "ge": "de", "fr": "fr", "po": "pt", "ru": "ru"}.get(x, x)


def main():
    if "--write-md" in sys.argv:
        md = ["# Queries for databases that need institutional access", "",
              "Run each query, export **with abstracts**, save in `search/external/` as `<db>_<id>.<ext>` and run `python3 import_exports.py`.", "",
              "- **Scopus** (library login): Advanced search, paste the query, Export > CSV, select *Citation information* and *Abstract & keywords*. Up to 20,000 records per export.",
              "- **Web of Science** (library login): Advanced search, paste the query, Export > Tab-delimited file (Win, UTF-8), record content *Full Record*, up to 1,000 records per file (export in batches).",
              "- **IEEE Xplore** (free to search, no login needed for abstracts): Command search, paste the query, Export > CSV (Citations and abstracts), up to 2,000 per export.",
              "- ScienceDirect and ACM DL block automated access and have no useful bulk export; skip them or add a few records by hand.", ""]
        for db, qs in QUERIES.items():
            md += [f"## {NAMES[db]}", ""] + [f"- `{db}_{q}`: `{t}`" for q, t in qs.items()] + [""]
        (HERE / "external_queries.md").write_text("\n".join(md)); print("wrote external_queries.md"); return
    n_files = 0
    for p in sorted(EXT.glob("*")):
        m = re.match(r"(scopus|wos|ieee)_([A-Za-z0-9]+)\.", p.name, re.I)
        if not m: continue
        db, qid = m.group(1).lower(), m.group(2).upper()
        recs = parse(db, read_text(p))
        for r in recs: r["language"] = lang_code(r["language"])
        (OUT / f"{db}_{qid}.json").write_text(json.dumps(dict(_source=db, _query=QUERIES[db].get(qid, p.name), total=len(recs), results=recs, _run_date=date.today().isoformat())))
        print(f"{p.name}: {len(recs)} records"); n_files += 1
    if not n_files: print("no files found in", EXT, "(nothing to import)")


if __name__ == "__main__":
    main()
