"""Figure: share of the full-text-coded papers (Creative Commons licence only) that meet each reporting item R1-R7.
Reads screening/fulltext_codes_final.csv and screening/fulltext_licences.csv and keeps the papers whose open-access copy carries a Creative
Commons licence (the same scope as make_fulltext_table.py). Writes gen/fig_reporting.pdf and gen/fig_reporting.png (300 dpi, as PeerJ asks).
Colour is slot 1 of the validated categorical palette (blue); one series, so no legend is needed and the title names it."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

S = Path(__file__).parent
G = S / "gen"
D = S / "screening"
ft = {r["id"]: r for r in csv.DictReader(open(D / "fulltext_codes_final.csv"))}
lic = {r["id"]: r["license"] for r in csv.DictReader(open(D / "fulltext_licences.csv"))}
ft = {i: r for i, r in ft.items() if lic[i].startswith("cc-")}
n = len(ft)
items = [("R1", "Q1", "Location error handled"), ("R2", "Q2", "Geofence decision measured"),
         ("R3", "Q3", "Attack on the location factor tested"), ("R4", "Q4", "Sampling policy stated"),
         ("R5", "Q5", "Energy measured or modelled"), ("R6", "Q6", "Privacy discussed"), ("R7", "Q7", "Fence parameters stated")]
BLUE, INK, MUTED = "#2a78d6", "#0b0b0b", "#52514e"

fig, ax = plt.subplots(figsize=(6.2, 3.2))
for i, (rid, q, label) in enumerate(items):
    y = len(items) - 1 - i
    a = sum(1 for r in ft.values() if r[q] == "Y")
    ax.barh(y, 100 * a / n, height=0.55, color=BLUE, edgecolor="white", linewidth=0.6)
    ax.text(100 * a / n + 1.2, y, f"{a} of {n}", va="center", ha="left", fontsize=8, color=INK)
ax.set_yticks(range(len(items)))
ax.set_yticklabels([f"{rid}  {label}" for rid, _, label in reversed(items)], fontsize=8, color=INK)
ax.set_xlim(0, 50)
ax.set_xlabel(f"Share of the {n} Creative Commons full texts that meet the item (%)", fontsize=8, color=MUTED)
ax.tick_params(axis="x", labelsize=7, colors=MUTED, length=2)
ax.tick_params(axis="y", length=0)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#c9c8c2")
ax.xaxis.grid(True, color="#e6e5e0", linewidth=0.6)
ax.set_axisbelow(True)
fig.tight_layout()
fig.savefig(G / "fig_reporting.pdf")
fig.savefig(G / "fig_reporting.png", dpi=300)
print("wrote gen/fig_reporting.pdf and .png")
