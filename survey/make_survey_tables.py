"""Generate every number, table and figure used by the survey from the screening files.
Outputs (in ./gen): stats.tex (macros), tab_audit.tex, tab_appendix.tex, tab_prior.tex, fig_year.pdf."""
import csv, json, re
from collections import Counter
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

S = Path(__file__).parent; G = S / "gen"; G.mkdir(exist_ok=True)
prisma = json.load(open(S / "search/prisma_counts.json"))
stage1 = list(csv.DictReader(open(S / "screening/stage1.csv")))
if not any(r["abstract"] for r in stage1):   # the public deposit has no abstract text; refuse to overwrite gen/ with wrong values
    raise SystemExit("No abstract text here: publishers' abstracts are not redistributed. Fetch them again with `make search corpus` (newer data, so counts will differ), or use the tables in gen/ as published.")
inc = list(csv.DictReader(open(S / "screening/included.csv")))
ver = {r["id"]: r for r in csv.DictReader(open(S / "screening/verification_log.csv"))}
audit = list(csv.DictReader(open(S / "screening/audit.csv")))
cand = [r["id"] for r in csv.DictReader(open(S / "screening/audit_candidates.csv"))]
by1 = {r["id"]: r for r in stage1}
keys = {i: r["key"] for i, r in ver.items() if r["status"] == "verified"}
n_ver = len(keys)
json.dump(keys, open(S / 'screening/keys.json', 'w'), indent=0)   # build_tex.py reads this; it used to go stale when selections changed
keys.update(json.load(open(S / 'screening/aliases.json')))   # same work already in refs_paper.bib
fmt = lambda n: f"{n:,}".replace(",", "{,}")

# ---------- macros ----------
bk = Counter(b for r in stage1 for b in r["buckets"].split(";"))
N = len(audit)
macros = {
 "nQueries": len({k.split("_")[0] for k in prisma["per_query"]}), "nPages": prisma["queries"], "nRetrieved": fmt(prisma["records_retrieved"]), "nUnique": fmt(prisma["unique_records"]),
 "nWithAbs": fmt(prisma["with_abstract"]), "nStageOne": fmt(len(stage1)), "nSelected": len(inc), "nVerified": n_ver,
 "nDropped": len(inc) - n_ver, "nAudit": N, "nAuditCand": len(cand), "nAuditDropped": len(cand) - N,
 "nGeofenceBucket": fmt(bk["geofence"]), "nAttBucket": fmt(bk["attendance"]), "nLpwanBucket": fmt(bk["lpwan"]),
 "nRescreen": sum(1 for r in inc if r["category"] == "rescreen"), "nRescreenVer": sum(1 for r in inc if r["category"] == "rescreen" and r["id"] in keys),
 "nAuditLang": json.load(open(S / "screening/audit_stats.json"))["excluded_nonenglish"], "nPriorSel": sum(1 for r in inc if r["category"] == "prior_review" and r["id"] in keys),
}
sc = json.load(open(S / "search/sources_counts.json"))
NAMES = {"openalex": "OpenAlex", "crossref": "Crossref", "arxiv": "arXiv", "semanticscholar": "Semantic Scholar", "scopus": "Scopus", "wos": "Web of Science", "ieee": "IEEE Xplore"}
SHORT = dict(NAMES, semanticscholar="S2")
ALL = [k for k in NAMES if k in sc and (sc[k].get("retrieved", 0) > 0)]
EXT = [k for k in ("scopus", "wos", "ieee") if k in ALL]
join = lambda xs: (", ".join(xs[:-1]) + " and " + xs[-1]) if len(xs) > 1 else (xs[0] if xs else "")
_tot = sum(sc[k]["retrieved"] for k in ALL)
_nq = lambda k: macros["nQueries"] if k == "openalex" else sc[k]["queries"]
missing = [NAMES[k] for k in ("scopus", "wos", "ieee") if k not in EXT]
ext_names = [NAMES[k] for k in EXT]
verb = lambda xs: "was" if len(xs) == 1 else "were"
if not EXT:
    srcPhrase = "four open sources (OpenAlex, Crossref, arXiv and Semantic Scholar)"
    srcMissing = r"We did \emph{not} search Scopus, IEEE Xplore or Web of Science, which need institutional access; this is a limitation."
    srcThreat = "Proprietary databases are missing."
else:
    srcPhrase = f"{len(ALL)} sources: four open ones (OpenAlex, Crossref, arXiv and Semantic Scholar) and {join(ext_names)}"
    import json as _json, datetime as _dt
    _dates = sorted({_json.load(open(f))["_run_date"] for k in EXT for f in (S / "search/raw_other").glob(f"{k}_*.json")})
    _when = " on " + " and ".join(_dt.date.fromisoformat(d).strftime("%-d %B %Y") for d in _dates) if _dates else ""
    srcMissing = (f"{join(ext_names)} {verb(ext_names)} searched through exports{_when} (institutional access or free search); " + (f"{join(missing)} {verb(missing)} not, which is a limitation." if missing else "none of the three major proprietary indexes is missing."))
    srcThreat = (f"{join(missing)} {verb(missing)} not searched." if missing else "Coverage of the proprietary databases depends on our queries and on the exports we obtained.")
macros['nSources'] = len(ALL)
srcQueryExtra = "".join(f", {_nq(k)} {NAMES[k]}" for k in EXT)
srcRecordsExtra = "".join(f", {fmt(sc[k]['retrieved'])} {NAMES[k]}" for k in EXT)
srcFlow = ", ".join(f"{SHORT[k]} {fmt(sc[k]['retrieved'])}" for k in ALL)
_st = {r["id"]: r for r in stage1}
macros.update(srcPhrase=srcPhrase, srcMissing=srcMissing, srcThreat=srcThreat, srcQueryExtra=srcQueryExtra, srcRecordsExtra=srcRecordsExtra, srcFlow=srcFlow,
              srcOA=fmt(sc["openalex"]["retrieved"]), srcCR=fmt(sc["crossref"]["retrieved"]), srcAX=fmt(sc["arxiv"]["retrieved"]), srcSS=fmt(sc["semanticscholar"]["retrieved"]),
              nQueriesOA=macros["nQueries"], nQueriesCR=sc["crossref"]["queries"], nQueriesAX=sc["arxiv"]["queries"], nQueriesSS=sc["semanticscholar"]["queries"],
              nQueriesAll=sum(_nq(k) for k in ALL),
              totRetrieved=fmt(_tot), unionUnique=fmt(sc["union"]["unique"]), newOther=fmt(sc["union"]["new_from_other_sources"]), dupRemoved=fmt(_tot - sc["union"]["unique"]),
              exclStageOne=fmt(sc["union"]["unique"] - len(stage1)), exclStageTwo=fmt(len(stage1) - len(inc)),
              nAuditOnlyOther=sum(1 for r in audit if "openalex" not in (_st[r["id"]].get("sources") or "openalex").split(";")))
def cnt(f): return sum(1 for r in audit if f(r))
def pct(n): return f"{100*n/N:.0f}"
facts = {
 "second": cnt(lambda r: r["face"] == "1" or r["biometric"] == "1" or r["qr"] == "1" or r["rfid_ble"] == "1" or r["imei_dev"] == "1"),
 "face": cnt(lambda r: r["face"] == "1"), "bio": cnt(lambda r: r["biometric"] == "1"), "qr": cnt(lambda r: r["qr"] == "1"),
 "rfid": cnt(lambda r: r["rfid_ble"] == "1"), "circle": cnt(lambda r: r["circle"] == "1"), "poly": cnt(lambda r: r["polygon"] == "1"),
 "spoof": cnt(lambda r: r["spoof"] == "1"), "quant": cnt(lambda r: r["quant"] == "1"), "metric": cnt(lambda r: r["geo_metric"] == "1"),
 "locerr": cnt(lambda r: r["loc_err_handled"] == "1"), "priv": cnt(lambda r: r["privacy"] == "1"), "lpwan": cnt(lambda r: r["lpwan"] == "1"),
 "deployed": cnt(lambda r: r["deployed"] == "1"),
}
for k, v in facts.items():
    macros["a" + k.capitalize()] = v; macros["p" + k.capitalize()] = pct(v)
years = Counter(int(r["year"]) for r in audit)
macros["aEarly"] = sum(v for y, v in years.items() if y <= 2022)
macros["aYtwentythree"] = years[2023]; macros["aYtwentyfour"] = years[2024]; macros["aYtwentyfive"] = years[2025]; macros["aYtwentysix"] = years[2026]
macros["aRecent"] = years[2025] + years[2026]
macros["pRecent"] = pct(years[2025] + years[2026])
(G / "stats.tex").write_text("\n".join(f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in macros.items()) + "\n")
json.dump({k: str(v) for k, v in macros.items()}, open(G / "stats.json", "w"), indent=1)

# ---------- audit aggregate table ----------
def row(label, n): return f"{label} & {n} & {pct(n)}\\% \\\\"
agg = [
 r"\begin{table}[tbp]\centering\small",
 r"\caption{Abstract-level audit of \nAudit{} geofence-based attendance and presence systems (counts overlap). Coding rules are in Section~\ref{sec:method}.}\label{tab:audit}",
 r"\begin{tabular}{@{}L{0.70\linewidth}rr@{}}\toprule", r"Property found in the abstract & Systems & Share \\ \midrule",
 row("Adds a second factor (face, biometric, QR, RFID/NFC/BLE, device ID)", facts["second"]),
 row("\\quad face recognition or liveness", facts["face"]),
 row("\\quad fingerprint, voice, iris or generic biometric", facts["bio"]),
 row("\\quad QR code", facts["qr"]),
 row("\\quad RFID, NFC or BLE", facts["rfid"]),
 row("Mentions proxy attendance, fraud or spoofing", facts["spoof"]),
 row("Boundary stated as circle (Haversine or radius)", facts["circle"]),
 row("Boundary stated as polygon or box", facts["poly"]),
 row("Reports any number (accuracy, latency, usability, sample size)", facts["quant"]),
 row("\\quad of which measures the geofence decision or position error", facts["metric"]),
 row("States that location error or uncertainty is handled", facts["locerr"]),
 row("Mentions privacy or data protection", facts["priv"]),
 row("Uses LoRa or another LPWAN", facts["lpwan"]),
 r"\bottomrule\end{tabular}\end{table}",
]
(G / "tab_audit.tex").write_text("\n".join(agg) + "\n")

# ---------- appendix list ----------
ap = [r"\begin{longtable}{@{}llllcc@{}}",
      r"\caption{Geofence-based attendance and presence systems in the audit (\nAudit{}). Factor: F face/liveness, B other biometric, Q QR, R RFID/NFC/BLE. Boundary: C circle, P polygon/box, -- not stated in abstract. M: abstract reports a geofence-decision or position-error measurement. E: abstract states that location error is handled.}\label{tab:appendix}\\",
      r"\toprule Ref. & Year & Factor & Boundary & M & E \\ \midrule \endfirsthead",
      r"\toprule Ref. & Year & Factor & Boundary & M & E \\ \midrule \endhead"]
for r in audit: r['key'] = keys.get(r['id'], r['key'])
for r in sorted(audit, key=lambda r: (int(r["year"]), r["key"])):
    f = "".join(c for c, k in (("F", "face"), ("B", "biometric"), ("Q", "qr"), ("R", "rfid_ble")) if r[k] == "1") or "--"
    b = "P" if r["polygon"] == "1" else ("C" if r["circle"] == "1" else "--")
    ap.append(f"\\cite{{{r['key']}}} & {r['year']} & {f} & {b} & {'$\\checkmark$' if r['geo_metric']=='1' else ''} & {'$\\checkmark$' if r['loc_err_handled']=='1' else ''} \\\\")
ap.append(r"\bottomrule\end{longtable}")
(G / "tab_appendix.tex").write_text("\n".join(ap) + "\n")

# ---------- prior reviews ----------
FOCUS = {"166": "Biometric (hardware)", "275": "RFID", "495": "Face recognition", "515": "Fingerprint, iris, RFID, GPS", "518": "Biometrics, RFID, BLE, GPS, QR",
         "728": "General", "797": "Face recognition", "1021": "General", "1065": "QR code", "1074": "Smart campus, general", "1200": "Smart card",
         "1213": "General", "1337": "AppSheet apps", "1360": "General (class attendance)", "1465": "RFID", "1694": "QR + geofencing; performance",
         "3013": "NFC", "3025": "Geolocation, geofencing (short narrative)",
         "3218": "Face recognition", "3345": "IoT, blockchain, AI", "3483": "Employee, cloud-based", "3743": "General (real-time automated)",
         "3803": "Computer vision, biometrics", "3979": "Neural network (lecture)", "3987": "Face recognition", "4102": "Hostel", "4109": "Computer vision",
         "4289": "Bluetooth", "4293": "Machine learning", "4296": "Face recognition", "4297": "Face recognition", "4298": "Facial biometrics", "4318": "Face recognition"}
gp = re.compile(r"geofenc|geo-fenc|\bgps\b", re.I)
pr = [r"\begin{table}[tbp]\centering\footnotesize",
      r"\caption{Earlier attendance reviews found by the search. ``GPS/geofence'' = the abstract mentions it. One review \cite{gupta2025geolocation} is centred on geolocation-based attendance; it was returned only by IEEE Xplore and Scopus, its abstract mentions neither GPS nor geofencing, and its text on the publisher's page has four sections and no stated search protocol. No other review in this set is centred on geofencing, GPS or LPWAN presence sensing.}\label{tab:prior}",
      r"\begin{tabular}{@{}L{3.3cm}llL{4.0cm}c@{}}\toprule Ref. & Year & Type & Focus & GPS/geofence \\ \midrule"]
rows = []
for r in inc:
    if r["category"] != "prior_review" or r["id"] not in keys: continue
    s = by1[r["id"]]; typ = "systematic" if re.search(r"systematic", s["title"], re.I) else "review"
    rows.append((int(s["year"]), keys[r["id"]], typ, FOCUS.get(r["id"], "General"), "yes" if gp.search(s["abstract"]) else "no"))
for y, k, t, f, g in sorted(rows):
    pr.append(f"\\cite{{{k}}} & {y} & {t} & {f} & {g} \\\\")
pr.append(r"\bottomrule\end{tabular}\end{table}")
(G / "tab_prior.tex").write_text("\n".join(pr) + "\n")
macros_prior_gps = sum(1 for x in rows if x[4] == "yes")
(G / "stats.tex").write_text((G / "stats.tex").read_text() + f"\\newcommand{{\\nPriorGps}}{{{macros_prior_gps}}}\n")

# ---------- query appendix (all sources) ----------
import glob
esc = lambda x: x.replace("&", r"\\&").replace("_", r"\\_").replace('"', "'")
qs = {}
for k, v in prisma["per_query"].items():
    q = k.split("_")[0]
    if q not in qs: qs[q] = ("OpenAlex", v["query"], v["total_hits"], v["theme"])
for f in sorted(glob.glob(str(S / "search/raw_other/*.json"))):
    d = json.load(open(f)); q = Path(f).stem.split("_", 1)[1]
    qs[q] = (NAMES.get(d["_source"], d["_source"]), d["_query"], d["total"], "")
ql = [r"{\footnotesize\setlength{\tabcolsep}{3pt}\begin{longtable}{@{}llL{0.40\linewidth}rL{0.17\linewidth}@{}}", r"\caption{Search queries (open sources 4 November 2026; Scopus, Web of Science and IEEE Xplore 11 November 2026). Hits are the totals the source reports for its relevance-ranked query, not the number screened (top 100 per page; Section~\ref{sec:method}); Crossref and Semantic Scholar match loosely, so their totals are very large. Double quotes in the original queries are shown as single quotes.}\label{tab:queries}\\",
      r"\toprule ID & Source & Query & Hits & Theme \\ \midrule \endfirsthead", r"\toprule ID & Source & Query & Hits & Theme \\ \midrule \endhead"]
for q, (src, qq, hits, th) in sorted(qs.items()):
    ql.append(f"{q} & {src} & {esc(qq)} & {fmt(hits)} & {esc(th)} " + chr(92) + chr(92))
ql.append(r"\bottomrule\end{longtable}}")
(G / "tab_queries.tex").write_text("\n".join(ql) + "\n")

# ---------- figure: systems per year ----------
ys = list(range(2018, 2027)); vals = [years[y] for y in ys]
fig, ax = plt.subplots(figsize=(5.2, 2.5))
bars = ax.bar([str(y) for y in ys], vals, color="#2a6f97", width=0.65)
bars[-1].set_hatch("//"); bars[-1].set_facecolor("#9fc3d9"); bars[-1].set_edgecolor("#2a6f97")
for b, v in zip(bars, vals): ax.text(b.get_x() + b.get_width() / 2, v + 0.4, str(v), ha="center", va="bottom", fontsize=8)
ax.set_ylabel("Systems in the audit", fontsize=8); ax.tick_params(labelsize=8)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.set_ylim(0, max(vals) * 1.18); ax.text(0.99, 0.95, "2026: partial year (search run Nov 2026)", transform=ax.transAxes, ha="right", va="top", fontsize=7, color="#555")
fig.tight_layout(); fig.savefig(G / "fig_year.pdf"); fig.savefig(G / "fig_year.png", dpi=200)
print(json.dumps({k: str(v) for k, v in macros.items()}))
