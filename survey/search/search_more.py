"""Second search pass: deeper pages for the geofence-attendance queries plus two variant queries.
Same API, filter and logging as search_openalex.py; results saved as raw/<qid>_p<N>.json."""
import json, sys, time, urllib.parse
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from search_openalex import fetch, RAW, FROM_YEAR, PER_PAGE, SELECT

JOBS = [("q01", "geofencing attendance", range(2, 6)), ("q02", 'geofence "attendance system"', range(2, 3)),
        ("q03", 'GPS "attendance system"', range(2, 4)),
        ("q41", "geo-fencing attendance mobile application", range(1, 4)),
        ("q42", "location-based attendance smartphone GPS", range(1, 4))]
today = date.today().isoformat()
for qid, q, pages in JOBS:
    for pg in pages:
        out = RAW / (f"{qid}_p{pg}.json" if pg > 1 else f"{qid}.json")
        if out.exists(): continue
        params = {"search": q, "filter": f"from_publication_date:{FROM_YEAR}-01-01,type:article|review|preprint|book-chapter|conference-paper",
                  "per-page": PER_PAGE, "page": pg, "select": SELECT}
        d = fetch("https://api.openalex.org/works?" + urllib.parse.urlencode(params, safe=":|,"))
        d["_query"] = q; d["_theme"] = "geofence-attendance-deep"; d["_run_date"] = today
        out.write_text(json.dumps(d)); print(qid, pg, len(d["results"]), file=sys.stderr); time.sleep(2)
