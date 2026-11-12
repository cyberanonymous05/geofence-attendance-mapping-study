"""Graphical abstract for the journal submission (Elsevier encourages one; minimum 1328 x 531 px, readable at 5 x 13 cm).
Every number is read from the generated data files; nothing is typed in. Output: submission/graphical_abstract.png
Design: one series, one hue, direct labels, no legend needed, recessive track behind each bar."""
import csv, json, re
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

S = Path(__file__).parent
OUT = S / "submission"; OUT.mkdir(exist_ok=True)
ft = list(csv.DictReader(open(S / "screening/fulltext_codes_final.csv")))
N = len(ft)
mac = {}
for f in ("gen/stats.tex", "gen/stats_human.tex", "gen/stats_ft.tex"):
    for k, v in re.findall(r"\\newcommand\{\\(\w+)\}\{([^}]*)\}", (S / f).read_text()): mac[k] = v
audit_n = int(mac["nAudit"]); lpwan = int(mac["aLpwan"]); consent = int(mac["hfConsent"]); hf_n = int(mac["hfN"])
LABELS = [("Q1", "R1  Location error handled"), ("Q2", "R2  Decision measured"), ("Q3", "R3  Attack tested"), ("Q4", "R4  Sampling policy"),
          ("Q5", "R5  Energy reported"), ("Q6", "R6  Privacy discussed"), ("Q7", "R7  Fence parameters")]
counts = [sum(1 for r in ft if r[q] == "Y") for q, _ in LABELS]
none_met = sum(1 for r in ft if all(r[q] != "Y" for q, _ in LABELS))

INK, MUTED, TRACK, BAR = "#1f2328", "#57606a", "#e3e6ea", "#1f5fa8"
fig = plt.figure(figsize=(6.64, 2.75), dpi=300, facecolor="white")

# title across the top, then three columns: scope | one bar per checklist item | headline numbers
fig.text(0.03, 0.94, "Geofence attendance papers: what do they report?", fontsize=9.5, fontweight="bold", color=INK, va="center")
fig.text(0.03, 0.70, f"{audit_n} systems audited\nfrom abstracts", fontsize=8.5, color=MUTED, va="top", linespacing=1.3)
fig.text(0.03, 0.46, f"{N} open-access full\ntexts coded", fontsize=8.5, color=MUTED, va="top", linespacing=1.3)

ax = fig.add_axes([0.48, 0.08, 0.26, 0.70])
ys = list(range(len(LABELS)))[::-1]
for y, c, (_, lab) in zip(ys, counts, LABELS):
    ax.barh(y, N, height=0.46, color=TRACK, linewidth=0)
    if c: ax.barh(y, c, height=0.46, color=BAR, linewidth=0)
    ax.text(N + 0.8, y, str(c), va="center", ha="left", fontsize=8.5, color=INK)
    ax.text(-0.8, y, lab, va="center", ha="right", fontsize=8, color=INK)
ax.set_xlim(0, N + 4); ax.set_ylim(-0.6, len(LABELS) - 0.4)
ax.axis("off")
fig.text(0.26, 0.83, f"Papers meeting each reporting item (of {N})", fontsize=8, color=MUTED, va="center")

def stat(y, big, small):
    fig.text(0.79, y, big, fontsize=16, fontweight="bold", color=BAR, va="center", ha="left")
    fig.text(0.79, y - 0.08, small, fontsize=7.8, color=MUTED, va="top", ha="left", linespacing=1.25)
stat(0.72, f"{none_met} of {N}", "meet none of the\nseven items")
stat(0.46, f"{lpwan} of {audit_n}", "audited systems\nuse LoRa")
stat(0.20, f"{consent} of {hf_n}", "abstracts mention\nconsent")

fig.savefig(OUT / "graphical_abstract.png", dpi=300, facecolor="white")
print("graphical_abstract.png", fig.get_size_inches() * 300, "px;", dict(none_met=none_met, counts=counts, audit_n=audit_n, lpwan=lpwan, consent=consent))
