"""Stage 3: selected records -> Crossref lookup -> verified BibTeX.
A record is kept only if the Crossref title matches the OpenAlex title (difflib ratio >= 0.85).
Outputs: included.csv (selection + category), ../refs_survey.bib, verification_log.csv."""
import csv, difflib, html, json, re, sys, time, urllib.parse, urllib.request, urllib.error
from pathlib import Path

rows = {r["id"]: r for r in csv.DictReader(open("stage1.csv"))}
aud_ids = [r["id"] for r in csv.DictReader(open("audit_candidates.csv"))]
SEL = {
 "prior_review":   "166 275 495 515 518 728 797 1021 1065 1074 1200 1213 1337 1360 1465 1510 1694 3013 3025 3218 3345 3483 3743 3803 3979 3987 4102 4109 4289 4293 4296 4297 4298 4318",   # 3013, 3025 found only through the IEEE Xplore / Web of Science searches; 3218-4318 only through Scopus (those without a DOI are dropped by the DOI check)
 "geofence":       "175 187 207 410 507 521 659 751 990 754 1018 1019 857 902 933 1755 856 976 1457 1596 700 977 357 1235 1870 684 385",
 "geofence_att":   " ".join(aud_ids),
 "att_tech":       "16 33 36 47 61 65 71 78 80 86 159 165 167 168 209 210 225 226 242 250 270 287 300 142",
 "lpwan_survey":   "3 4 12 19 22 26 67 90 94 129 198 237 255 311 313 465 466 191",
 "lpwan_primary":  "10 15 17 18 24 44 51 54 55 62 82 96 103 112 123 138 146 148 156 206 220",
 "gps":            "11 115 147 152 30 39 27 223 195 1592 114",
 "privacy":        "43 75 278 312 1641 21 8 645",
 "localization":   "0 74",
 "lpwan_attendance": "850 851 1000 1353 1354 1355",
 "rescreen":       "1 3162 6 7 3165 3166 13 3168 14 20 25 29 34 37 3255 128 174 41 2061 2093 332",   # added 2026-11-11 after the Scopus/WoS/IEEE exports: unselected on-topic LPWAN, GNSS and privacy records with high citation counts (rule in the Method section)
 "geofence_apps":  "95 185 336 349 394 731 307 604 306 753 701",
}
inc, seen = [], set()
for cat, ids in SEL.items():
    for i in ids.split():
        if i in seen or i not in rows: continue
        seen.add(i); inc.append((i, cat))
with open("included.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["id", "category"]); w.writerows(inc)
print("selected:", len(inc))

def get(url, tries=4):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "survey-verify/1.0"})
            with urllib.request.urlopen(req, timeout=40) as r: return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(3 * (k + 1))
        except Exception: time.sleep(3 * (k + 1))
    return None

def clean(s): return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html.unescape(html.unescape(s or "")))).strip()

def csl(doi):
    """Fallback for DOIs not held by Crossref (DataCite, regional agencies): content negotiation at doi.org."""
    try:
        req = urllib.request.Request("https://doi.org/" + urllib.parse.quote(doi),
                                     headers={"Accept": "application/vnd.citationstyles.csl+json", "User-Agent": "survey-verify/1.0"})
        with urllib.request.urlopen(req, timeout=40) as r: j = json.load(r)
    except Exception: return None
    t = j.get("title"); c = j.get("container-title")
    tmap = {"paper-conference": "proceedings-article", "article-journal": "journal-article"}
    return {"title": [t] if isinstance(t, str) else (t or [""]), "author": j.get("author") or [],
            "issued": j.get("issued") or {}, "container-title": [c] if isinstance(c, str) else (c or [""]),
            "volume": j.get("volume"), "issue": j.get("issue"), "page": j.get("page"),
            "type": tmap.get(j.get("type"), j.get("type", ""))}

def norm(s): return re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower()).split()
def sim(a, b): return difflib.SequenceMatcher(None, " ".join(norm(a)), " ".join(norm(b))).ratio()
def esc(s): return (s or "").replace("&", r"\&").replace("%", r"\%").replace("_", r"\_").replace("#", r"\#")

log, bib, keys = [], [], set()
for i, cat in inc:
    r = rows[i]; doi = r["doi"]
    rec = dict(id=i, category=cat, doi=doi, openalex_title=r["title"][:90], status="", ratio="")
    if not doi:
        rec["status"] = "no-doi"; log.append(rec); continue
    d = get("https://api.crossref.org/works/" + urllib.parse.quote(doi))
    time.sleep(0.4)
    src = "crossref"
    if d: m = d["message"]
    else:
        m = csl(doi); src = "doi.org"; time.sleep(0.4)
        if not m: rec["status"] = "unresolved"; log.append(rec); continue
    rec["source"] = src
    title = clean((m.get("title") or [""])[0])
    ratio = sim(title, clean(r["title"])); rec["ratio"] = f"{ratio:.2f}"
    if ratio < 0.85:
        rec["status"] = "title-mismatch"; rec["crossref_title"] = title[:90]; log.append(rec); continue
    au = m.get("author") or []
    names = " and ".join(f"{a.get('family','')}, {a.get('given','')}".strip(", ") for a in au if a.get("family")) or "Anonymous"
    year = (m.get("issued", {}).get("date-parts") or [[r["year"]]])[0][0]
    fam = re.sub(r"[^a-z]", "", (au[0].get("family", "x") if au else "anon").lower()) or "anon"
    first = next((w for w in norm(title) if len(w) > 3), "w")
    key = f"{fam}{year}{first}"
    n = 0
    while key in keys: n += 1; key = f"{fam}{year}{first}{chr(97+n)}"
    keys.add(key)
    ctype = m.get("type", "")
    cont = (m.get("container-title") or [""])[0]
    kind = "inproceedings" if "proceedings" in ctype else ("article" if ctype in ("journal-article",) and cont else "misc")
    fld = {"author": names, "title": "{" + esc(title) + "}", "year": str(year), "doi": doi}
    if cont and kind != "misc": fld["booktitle" if kind == "inproceedings" else "journal"] = esc(clean(cont))
    elif kind == "misc": fld["howpublished"] = "arXiv preprint" if doi.startswith("10.48550") else ("Zenodo" if doi.startswith("10.5281") else esc(clean(cont)) or "online")
    for src, dst in (("volume", "volume"), ("issue", "number"), ("page", "pages")):
        if m.get(src): fld[dst] = str(m[src]).replace("-", "--") if dst == "pages" else str(m[src])
    bib.append(f"@{kind}{{{key},\n" + ",\n".join(f"  {k} = {{{v}}}" if k != 'title' else f"  title = {v}" for k, v in fld.items()) + "\n}\n")
    rec["status"] = "verified"; rec["key"] = key; log.append(rec)
Path("../refs_survey.bib").write_text("\n".join(bib))
fn = ["id", "category", "doi", "status", "source", "ratio", "key", "openalex_title", "crossref_title"]
with open("verification_log.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fn, extrasaction="ignore"); w.writeheader(); w.writerows(log)
from collections import Counter
print(Counter(r["status"] for r in log))
