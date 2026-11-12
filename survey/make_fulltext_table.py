"""Full-text check table: adjudicated full-text codes vs abstract-level codes for the same papers; coverage and agreement macros."""
import csv, json
from collections import Counter
from pathlib import Path
S = Path(__file__).parent; D = S / "screening"; G = S / "gen"
ft_all = {r["id"]: r for r in csv.DictReader(open(D / "fulltext_codes_final.csv"))}   # every paper the first coder read (28)
# Scope: only papers whose open-access copy carries a Creative Commons licence are analysed. PeerJ asks for permission from the copyright holders before
# copyrighted material is put into an AI tool, and the authors have no person to code the other papers. Codes of the other papers are not used anywhere.
lic_all = {r["id"]: r for r in csv.DictReader(open(D / "fulltext_licences.csv"))}
ft = {i: r for i, r in ft_all.items() if lic_all[i]["license"].startswith("cc-")}
aud = {r["id"]: r for r in csv.DictReader(open(D / "audit.csv"))}
st = list(csv.DictReader(open(D / "fulltext_status.csv")))
ag = json.load(open(D / "agreement.json"))
n = len(ft)
assert all(sum(1 for r in ft.values() if r[q] == "Y") == 0 for q in ("Q4", "Q5", "Q6")), "prose says none for Q4-Q6 (sampling policy, energy, privacy); update main.src.tex and build_peerj.py"
cnt = lambda q: sum(1 for r in ft.values() if r[q] == "Y")
abs_ = {"Q1": sum(1 for i in ft if aud[i]["loc_err_handled"] == "1"), "Q2": sum(1 for i in ft if aud[i]["geo_metric"] == "1"),
        "Q3": sum(1 for i in ("1306", "1249") if i in ft),   # abstracts reporting an adversarial outcome (hand-checked in Section 5); 1240 has no full text
        "Q6": sum(1 for i in ft if aud[i]["privacy"] == "1")}
labels = {"Q1": "Location error handled or analysed", "Q2": "Geofence decision or position error measured", "Q3": "Adversarial test with an outcome",
          "Q4": "Location sampling policy stated", "Q5": "Energy measured or modelled", "Q6": "Privacy or data protection discussed", "Q7": "Fence parameters stated"}
t = [r"\begin{table}[tbp]\centering\small",
     r"\caption{Full-text check of the \ftN{} audited papers whose open-access copy carries a Creative Commons licence: papers with the property, by full-text coding and by abstract-level coding of the same papers (``--'' = not coded at abstract level). Full-text codes are adjudicated; see Section~\ref{sec:fulltext}.}\label{tab:fulltext}",
     r"\begin{tabular}{@{}lrr@{}}\toprule Property & Full text & Abstract only \\ \midrule"]
for q in ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7"):
    t.append(f"{labels[q]} & {cnt(q)} & {abs_.get(q, '--')} \\\\")
t.append(r"\bottomrule\end{tabular}\end{table}")
(G / "tab_fulltext.tex").write_text("\n".join(t) + "\n")

# --- reporting checklist (proposal) scored on the same adjudicated full-text codes; items R1-R7 = codebook Q1-Q7, no "not applicable" option was used
QS = ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7")
ITEMS = [  # (item, codebook question, what to report, applies to)
    ("R1", "Q1", "Position error of the sensing method under the test conditions (for example median and 95th percentile), and how the decision rule copes with it.", "Location-based"),
    ("R2", "Q2", "Error of the presence decision itself against ground truth: false entries, false exits, missed events, delay.", "All modalities"),
    ("R3", "Q3", "At least one attack on the presence factor (mock location, forwarded or relayed token, photo or replay, shared device) and its outcome.", "All modalities"),
    ("R4", "Q4", "When and how often the person or tag is sampled, and what triggers a sample.", "Location-based"),
    ("R5", "Q5", "Energy per day or battery life, measured or modelled with the fix or read time stated.", "Battery-powered"),
    ("R6", "Q6", "Personal data collected, retention period, legal basis or consent route, and who can read the log.", "All modalities"),
    ("R7", "Q7", "Fence shape and size, thresholds, dwell or confirmation rule, and the values used in the test.", "Geofence"),
]
cl = [r"\begin{table}[tbp]\centering\footnotesize",
      r"\caption{Proposed minimum reporting checklist for presence-sensing papers, with the number of the \ftN{} full-text-coded geofence attendance papers (Creative Commons licence) that meet each item. Items R1--R7 are the codebook questions of Section~\ref{sec:fulltext}; no item was scored as not applicable, so counts for R4, R5 and R7 are low for papers where an item arguably does not apply. The codebook definitions of R1 and R6 are looser than the wording here (``handled or analysed'', ``discussed''), so the counts for those two overstate compliance.}\label{tab:checklist}",
      r"\begin{tabular}{@{}lL{7.4cm}L{2.2cm}r@{}}\toprule Item & Report & Applies to & Met \\ \midrule"]
for it, q, what, ap in ITEMS:
    cl.append(f"{it} & {what} & {ap} & {cnt(q)} of \\ftN{{}} \\\\")
cl.append(r"\bottomrule\end{tabular}\end{table}")
(G / "tab_checklist.tex").write_text("\n".join(cl) + "\n")
score = {k: sum(1 for q in QS if r[q] == "Y") for k, r in ft.items()}
sc = Counter(score.values())
best = [k for k, v in score.items() if v == max(score.values())]
bestkeys = [aud[k]["key"] for k in best]
c = Counter(r["status"] for r in st)
mac = dict(ftN=n, ftTried=len(st), ftNoOA=c["no-oa"], ftShort=c["short"] + 1, ftErr=sum(v for k, v in c.items() if k.startswith("error")),
           ftPct=round(100 * len(ft_all) / len(st)), ftAllN=len(ft_all), ftCodes=7 * n, ftCcPct=round(100 * n / len(st)), ftQone=cnt("Q1"), ftQtwo=cnt("Q2"), ftQthree=cnt("Q3"), ftQfour=cnt("Q4"), ftQfive=cnt("Q5"), ftQsix=cnt("Q6"), ftQseven=cnt("Q7"),
           ftAbsQone=abs_["Q1"], ftAbsQtwo=abs_["Q2"],
           ftScoreZero=sc[0], ftScoreOne=sc[1], ftScoreTwo=sc[2], ftScoreThree=sum(v for k, v in sc.items() if k >= 3), ftScoreMax=max(score.values()),
           ftScoreAtLeastTwo=sum(v for k, v in sc.items() if k >= 2), ftBestCites="\\cite{" + ",".join(sorted(bestkeys)) + "}",
           agN=ag["n"], agNAll=ag["n_all"], agJ=ag["n_judgements"], agPct=round(100 * ag["all_agree"]), agKappa=f"{ag['all_kappa']:.2f}")
# licences come from screening/fulltext_licences.py (OpenAlex's recorded licence of the open-access copy)
mac["ftLicCC"] = n
mac["ftLicNone"] = len(ft_all) - n
hp = D / "human_agreement.json"
if hp.exists():
    h = json.load(open(hp)); a, f = h["abstract_pooled"], h["fulltext_pooled"]
    mac["humanSentence"] = (f" A human coder, independent of the authors of the rules, also re-coded {h['n_abstract_papers']} abstracts and {h['n_fulltext_papers']} full texts without seeing our codes: "
                            f"pooled agreement was {round(100*a['agree'])}\\% on abstract properties ($\\kappa={a['kappa']:.2f}$) and {round(100*f['agree'])}\\% on full-text questions ($\\kappa={f['kappa']:.2f}$).")
    mac["humanThreat"] = "The first coder applied all rules; the second full-text coder was an AI model that saw only snippets, and a human independent of the rule authors re-coded " + ("all the full texts and a sample of abstracts" if h["n_fulltext_papers"] >= mac["ftN"] else "a sample") + " (Section~\\ref{sec:fulltext})."
    mac["coderAbs"] = (f"A human independent of the rule authors also re-coded {h['n_abstract_papers']} abstracts and {h['n_fulltext_papers']} full texts without seeing our codes (pooled agreement {round(100*a['agree'])}\\% on abstract properties, $\\kappa={a['kappa']:.2f}$; {round(100*f['agree'])}\\% on full-text questions, $\\kappa={f['kappa']:.2f}$).")
else:
    mac["humanSentence"] = ""
    mac["humanThreat"] = "The first coder applied all rules and the second coder was an AI model that saw only snippets. One author (LHP) then read each of the \\ftN{} full texts and checked every full-text code against the paper, changing none of the \\ftCodes{} codes; because that author is one of us and saw the codes first, this is a check and not an independent second coding, and no person outside the author team re-coded the papers. The abstract-level codes were not re-checked by a person."
    mac["coderAbs"] = "The first coder applied all rules and a second coder, also an AI model, re-coded a sample of full texts from snippets; one author then checked all \\ftN{} full-text codes against the papers and changed none of them, and no person outside the author team re-coded them."
(G / "stats_ft.tex").write_text("\n".join(f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in mac.items()) + "\n")
print(mac)
