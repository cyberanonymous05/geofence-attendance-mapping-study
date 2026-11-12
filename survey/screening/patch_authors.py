"""Post-process refs_survey.bib: where Crossref has no author or year, take them from OpenAlex (same DOI)."""
import json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path
b = Path("../refs_survey.bib"); t = b.read_text()
ents = re.split(r"\n(?=@)", t); out = []
for e in ents:
    if "author = {Anonymous}" in e or "year = {None}" in e:
        doi = re.search(r"doi = \{([^}]+)\}", e).group(1)
        url = "https://api.openalex.org/works/doi:" + urllib.parse.quote(doi) + "?select=authorships,publication_year"
        j = None
        for k in range(6):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "survey-verify/1.0"}), timeout=40) as r: j = json.load(r); break
            except Exception: time.sleep(8)
        if j:
            names = [a["author"]["display_name"] for a in j.get("authorships", []) if a.get("author", {}).get("display_name")]
            if names and "author = {Anonymous}" in e:
                def flip(n):
                    p = n.split(); return f"{p[-1]}, {' '.join(p[:-1])}" if len(p) > 1 else n
                e = e.replace("author = {Anonymous}", "author = {" + " and ".join(flip(n) for n in names) + "}")
            if j.get("publication_year") and "year = {None}" in e:
                e = e.replace("year = {None}", f"year = {{{j['publication_year']}}}")
            print("patched", doi, names[:2], j.get("publication_year"), file=sys.stderr)
    out.append(e)
# COMMA_LIST: Crossref sometimes returns one author string "A B, C D, E F" (no "and"); BibTeX needs "and" between names
def fix_commas(e):
    m = re.search(r"author = \{([^{}]*)\}", e)
    if m and " and " not in m.group(1) and m.group(1).count(",") >= 2:
        names = [x.strip() for x in m.group(1).split(",") if x.strip()]
        e = e.replace(m.group(0), "author = {" + " and ".join(names) + "}")
    return e
# LATEXIFY: BibTeX makes initials from the first BYTE, which cuts a UTF-8 letter in half (invalid UTF-8 in main.bbl); write accented author letters as LaTeX accents
import unicodedata
ACC = {"\u0308": '"', "\u0301": "'", "\u0300": "`", "\u0302": "^", "\u0303": "~", "\u0304": "=", "\u030a": "r ", "\u0327": "c ", "\u030c": "v ", "\u0306": "u "}
def latexify(e):
    def one(m):
        out_ = []
        for ch in m.group(1):
            d = unicodedata.normalize("NFD", ch)
            if ord(ch) > 127 and len(d) == 2 and d[1] in ACC and d[0].isascii(): out_.append("{\\" + ACC[d[1]] + d[0] + "}")
            else: out_.append(ch)
        return "author = {" + "".join(out_) + "}"
    return re.sub(r"author = \{([^{}]*)\}", one, e)
# AMPERSAND: some sources join authors with " & "; a bare & breaks LaTeX in styles that do not escape it
def fix_amp(e):
    return re.sub(r"author = \{([^{}]*)\}", lambda m: "author = {" + m.group(1).replace(" & ", " and ") + "}", e)
# INITIAL_FAMILY: some sources register South-Indian names as "Initial, Given" or "Given Initial" (for example "J., Dakshayani", "Revanth D"),
# so BibTeX takes the initial as the family name and a name-year citation prints "J. et al.". Keep exactly the tokens the source gave, but
# brace-protect the whole name so it prints as written ("Dakshayani J."). No name is invented or guessed.
def protect_initial_names(e):
    def one(m):
        names = re.split(r"\s+and\s+", m.group(1)); fixed = []
        for n in names:
            n = n.strip()
            if "," in n:
                fam, giv = [x.strip() for x in n.split(",", 1)]
                if re.fullmatch(r"(?:[A-Z]\.?){1,3}", fam.replace(" ", "")) and giv and not giv.startswith("{"):
                    n = "{" + giv + " " + fam + "}"
            elif not n.startswith("{") and len(n.split()) > 1 and re.fullmatch(r"[A-Z]{1,2}\.?", n.split()[-1]):
                n = "{" + n + "}"
            fixed.append(n)
        return "author = {" + " and ".join(fixed) + "}"
    return re.sub(r"author = \{([^{}]*)\}", one, e)
out = [protect_initial_names(fix_amp(latexify(fix_commas(e)))) for e in out]
# INVISIBLE: strip zero-width and directional marks (LaTeX stops on U+200F etc.)
b.write_text(re.sub("[\u200b-\u200f\u202a-\u202e\u2060\ufeff]", "", "\n".join(out)))
