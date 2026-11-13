"""Extra analyses for the survey, all from screening files (same regex definitions applied to every group):
 1. reporting practice by sensing modality (non-geofence attendance systems)
 2. geofence systems vs other attendance systems
 3. venue split of the audit (OpenAlex core flag, source type, open access)
 4. geofencing application map (domain of every geofence-titled record)
Outputs gen/tab_modality.tex, tab_compare.tex, tab_venue.tex, tab_domain.tex, stats_extra.tex."""
import csv, json, re, statistics as st
from pathlib import Path
S = Path(__file__).parent; G = S / "gen"
stage1 = list(csv.DictReader(open(S / "screening/stage1.csv")))
if not any(r["abstract"] for r in stage1):   # the public deposit has no abstract text; refuse to overwrite gen/ with wrong values
    raise SystemExit("No abstract text here: publishers' abstracts are not redistributed. Fetch them again with `make search corpus` (newer data, so counts will differ), or use the tables in gen/ as published.")
audit = list(csv.DictReader(open(S / "screening/audit.csv")))
meta = json.load(open(S / "screening/meta_cache.json"))
ver = {r["id"]: r for r in csv.DictReader(open(S / "screening/verification_log.csv"))}
fmt = lambda n: f"{n:,}".replace(",", "{,}")
rx = lambda p, t: re.search(p, t, re.I) is not None
FIELDS = {
 "number":   r"\d+(\.\d+)?\s?%|accuracy|precision|recall|f1|false (accept|reject)",
 "sample":   r"\b\d+\s+(students|users|subjects|participants|employees|persons|people|images|faces|samples|trials|sessions|respondents|classes|scenarios|tests)\b",
 "spoof":    r"spoof|liveness|proxy|buddy|impersonat|fraud|cheat|fake",
 "privacy":  r"privacy|gdpr|consent|data protection",
}
ACC = [re.compile(r"accura\w*[^.%\d]{0,50}?(\d{1,3}(?:\.\d+)?)\s?%", re.I), re.compile(r"(\d{1,3}(?:\.\d+)?)\s?%\s+(?:\w+\s+){0,2}accura\w*", re.I)]
def accs(t):
    v = [float(m.group(1)) for r in ACC for m in r.finditer(t)]
    return [x for x in v if 50 <= x <= 100]
REVIEW = re.compile(r"\breview\b|survey|systematic|retracted|overview", re.I)
MOD = [("Face recognition", r"face|facial"), ("Fingerprint, iris, voice", r"fingerprint|biometric|iris|voice"), ("RFID", r"rfid"),
       ("NFC, smart card", r"\bnfc\b|smart ?card"), ("BLE, Bluetooth", r"bluetooth|\bble\b|beacon"), ("QR code", r"\bqr\b|barcode"), ("Wi-Fi", r"wi-?fi")]
def modality(r):
    t = r["title"] + " " + r["abstract"][:300]
    for name, p in MOD:
        if rx(p, r["title"]): return name
    for name, p in MOD:
        if rx(p, t): return name
    return "Unspecified"
others = [r for r in stage1 if "attendance" in r["buckets"].split(";") and "geofence" not in r["buckets"].split(";") and not REVIEW.search(r["title"])
          and r["year"] and 2005 <= int(r["year"]) and r["abstract"]]
for r in others: r["mod"] = modality(r)
mc = {}
for r in others: mc.setdefault(r["mod"], []).append(r)
MKEY = {"Face recognition": "Face", "Fingerprint, iris, voice": "Bio", "RFID": "Rfid", "NFC, smart card": "Nfc", "BLE, Bluetooth": "Ble", "QR code": "Qr", "Wi-Fi": "Wifi", "Unspecified": "Unspec"}
macros = {"nOthers": len(others)}

# --- 1 modality table
tab = [r"\begin{table}[tbp]\centering\footnotesize",
       r"\caption{Reporting practice by sensing modality among \nOthers{} non-geofence attendance systems in the corpus (abstract level). ``Accuracy'' = abstracts giving an accuracy percentage; the median and range are of those values. These are reported figures on different data sets and are \emph{not} comparable performance rankings.}\label{tab:modality}",
       r"\resizebox{\linewidth}{!}{\begin{tabular}{@{}lrrrrrr@{}}\toprule Modality & Systems & Report accuracy & Median (range) \% & Report sample size & Mention spoofing & Mention privacy \\ \midrule"]
for name in [m for m, _ in MOD] + ["Unspecified"]:
    rs = mc.get(name, [])
    if not rs: continue
    a = [accs(r["abstract"])[0] for r in rs if accs(r["abstract"])]
    n = len(rs); k = lambda f: sum(1 for r in rs if rx(FIELDS[f], r["title"] + " " + r["abstract"]))
    med = f"{st.median(a):.1f} ({min(a):.0f}--{max(a):.0f})" if len(a) >= 5 else ("--" if not a else "n$<$5")
    tab.append(f"{name} & {n} & {len(a)} ({100*len(a)/n:.0f}\\%) & {med} & {k('sample')} ({100*k('sample')/n:.0f}\\%) & {k('spoof')} ({100*k('spoof')/n:.0f}\\%) & {k('privacy')} ({100*k('privacy')/n:.0f}\\%) \\\\")
    macros["mod" + MKEY[name]] = n; macros["modAccN" + MKEY[name]] = len(a); macros["modAccMed" + MKEY[name]] = (f"{st.median(a):.1f}" if len(a) >= 5 else "--"); macros["modAccPct" + MKEY[name]] = round(100 * len(a) / n); macros["modSpoofPct" + MKEY[name]] = round(100 * k("spoof") / n)
tab.append(r"\bottomrule\end{tabular}}\end{table}")
(G / "tab_modality.tex").write_text("\n".join(tab) + "\n")

# --- 2 geofence vs others
def share(rs, f): return 100 * sum(1 for r in rs if rx(FIELDS[f], r["title"] + " " + r["abstract"])) / len(rs)
geo_abs = {r["id"]: r for r in stage1}
geo = [geo_abs[a["id"]] for a in audit]
oth = [r for r in others if int(r["year"]) >= 2018]
oth_acc = 100 * sum(1 for r in oth if accs(r["abstract"])) / len(oth)
geo_acc = 100 * sum(1 for r in geo if accs(r["abstract"])) / len(geo)
rows = [("Reports an accuracy percentage", geo_acc, oth_acc), ("Reports a sample size (users, images, trials)", share(geo, "sample"), share(oth, "sample")),
        ("Mentions spoofing, proxy or fraud", share(geo, "spoof"), share(oth, "spoof")), ("Mentions privacy or data protection", share(geo, "privacy"), share(oth, "privacy"))]
cmp = [r"\begin{table}[tbp]\centering\small",
       r"\caption{Geofence attendance systems (\nAudit{}) compared with other attendance systems from 2018 onward (" + str(len(oth)) + r"), by the same abstract-level rules. Shares are percentages of systems.}\label{tab:compare}",
       r"\begin{tabular}{@{}lrr@{}}\toprule Property in the abstract & Geofence & Other \\ \midrule"]
for a, g, o in rows: cmp.append(f"{a} & {g:.0f} & {o:.0f} \\\\")
cmp += [r"\bottomrule\end{tabular}\end{table}"]
(G / "tab_compare.tex").write_text("\n".join(cmp) + "\n")
macros["nOthersRecent"] = len(oth)
for (a, g, o), k in zip(rows, ("acc", "sample", "spoof", "priv")): macros["cmpG" + k] = f"{g:.0f}"; macros["cmpO" + k] = f"{o:.0f}"

# --- 3 venue split
def vinfo(a):
    m = meta.get(ver[a["id"]]["doi"].lower()) or {}
    return m
V = [vinfo(a) for a in audit]
core = sum(1 for m in V if m.get("src_core")); oa = sum(1 for m in V if m.get("is_oa"))
types = {}
for m in V: types[m.get("src_type") or "unknown"] = types.get(m.get("src_type") or "unknown", 0) + 1
def stat(sub):
    n = len(sub)
    if not n: return "--", "--", "--"
    f = lambda k: sum(1 for a in sub if a[k] == "1")
    return n, f("quant"), f("geo_metric")
ven = [r"\begin{table}[tbp]\centering\small", r"\caption{Venue type of the audited systems (OpenAlex source metadata) and the share that report any number or a geofence-decision measurement.}\label{tab:venue}",
       r"\begin{tabular}{@{}lrL{2.2cm}L{2.6cm}@{}}\toprule Group & Systems & Report any number & Geofence measurement \\ \midrule"]
groups = [("OpenAlex core source", [a for a, m in zip(audit, V) if m.get("src_core")]), ("Other journal", [a for a, m in zip(audit, V) if not m.get("src_core") and m.get("src_type") == "journal"]),
          ("Conference (not core)", [a for a, m in zip(audit, V) if not m.get("src_core") and m.get("src_type") == "conference"]), ("Repository (Zenodo, arXiv)", [a for a, m in zip(audit, V) if not m.get("src_core") and m.get("src_type") == "repository"])]
for name, sub in groups:
    n, q, g = stat(sub); ven.append(f"{name} & {n} & {q} & {g} \\\\")
ven.append(r"\bottomrule\end{tabular}\end{table}")
(G / "tab_venue.tex").write_text("\n".join(ven) + "\n")
macros.update(nCore=core, nOA=oa)

# --- 4 application map
DOM = [("Attendance, presence, workforce", r"attendance|presence|presensi|absensi|kehadiran|workforce|employee|check-in|working hours|truancy"),
       ("Health, COVID-19, elderly care", r"covid|quarantine|patient|health|alzheimer|dementia|elderly|hospital|clinical|dental|hiv"),
       ("Livestock, wildlife, farming", r"livestock|cattle|wildlife|elephant|animal|farm|crop|agricultur|soybean|turtle|deer|pet"),
       ("Aviation, drones, UAV", r"drone|uav|unmanned|aircraft|airspace|aviation|flight"),
       ("Vehicles, transport, logistics", r"vehicle|traffic|fleet|bus\b|road|cargo|toll|ambulance|logistic|micromobil|railway|vessel|boat|driver"),
       ("Marketing, tourism, location services", r"marketing|advertis|tourist|tourism|museum|retail|shopping|location-based|point-of-interest|notif|reminder|audio"),
       ("Safety, security, access control", r"safety|security|child|theft|intruder|lock|surveillance|emergency|construction")]
DKEY = {"Attendance, presence, workforce": "Att", "Health, COVID-19, elderly care": "Health", "Livestock, wildlife, farming": "Live", "Aviation, drones, UAV": "Avi", "Vehicles, transport, logistics": "Veh", "Marketing, tourism, location services": "Mkt", "Safety, security, access control": "Safe", "Other or unclear": "Other"}
geo_all = [r for r in stage1 if "geofence" in r["buckets"].split(";")]
dm = {}
for r in geo_all:
    t = r["title"] + " " + r["abstract"][:500]
    d = next((n for n, p in DOM if rx(p, r["title"])), None) or next((n for n, p in DOM if rx(p, t)), "Other or unclear")
    dm.setdefault(d, []).append(r)
macros["nGeoAll"] = len(geo_all)
macros["domLoraTotal"] = sum(1 for r in geo_all if rx(r"lora|lpwan", r["title"] + " " + r["abstract"]))
macros["domLoraLive"] = sum(1 for r in dm.get("Livestock, wildlife, farming", []) if rx(r"lora|lpwan", r["title"] + " " + r["abstract"]))
dtab = [r"\begin{table}[tbp]\centering\footnotesize", r"\caption{Application domains of the \nGeoAll{} geofence-titled records in the corpus (title and abstract rules, first match wins). Shares are of records in the row; abstract-level.}\label{tab:domain}",
        r"\resizebox{\linewidth}{!}{\begin{tabular}{@{}lrrrrr@{}}\toprule Domain & Records & Share & Mention LoRa/LPWAN & Mention energy & Mention location error or uncertainty \\ \midrule"]
for name in [n for n, _ in DOM] + ["Other or unclear"]:
    rs = dm.get(name, [])
    if not rs: continue
    n = len(rs); c = lambda p: sum(1 for r in rs if rx(p, r["title"] + " " + r["abstract"]))
    dtab.append(f"{name} & {n} & {100*n/len(geo_all):.0f}\\% & {c(r'lora|lpwan')} & {c(r'energy|battery|power consumption')} & {c(r'(gps|location|position\w*) (error|inaccura|uncertain|accuracy|drift|noise)|uncertaint|inaccurate')} \\\\")
    macros["dom" + DKEY[name]] = n; macros["domPct" + DKEY[name]] = round(100 * n / len(geo_all))
dtab.append(r"\bottomrule\end{tabular}}\end{table}")
(G / "tab_domain.tex").write_text("\n".join(dtab) + "\n")
_fmtv = lambda v: f"{v:,}".replace(",", "{,}") if isinstance(v, int) and v >= 1000 else v   # thousands separators, as in the other macro files
(G / "stats_extra.tex").write_text("\n".join(f"\\newcommand{{\\{k}}}{{{_fmtv(v)}}}" for k, v in macros.items()) + "\n")
print(json.dumps(macros))
