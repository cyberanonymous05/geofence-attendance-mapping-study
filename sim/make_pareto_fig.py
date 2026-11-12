"""Figure: false-toggle rate vs detection delay for the hysteresis and excess-area (CUSUM-style) families."""
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
d = pd.read_csv("results/exp19_detector_pareto.csv")
fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
for ax, (s, tc) in zip(axs, [(5.3, 79.0), (8.0, 30.0)]):
    g = d[(d.sigma == s) & (d.Tc == tc) & (d.miss < 0.05)].copy()
    g["fr"] = g.false_per_h.clip(lower=3e-4)
    for fam, c, mk, lab in (("hyst", "#1f77b4", "o", "hysteresis (band $h$, dwell)"), ("excess", "#d62728", "^", "excess-area (CUSUM-style)")):
        a = g[g.family == fam]
        ax.scatter(a.fr, a.delay_mean, s=14, c=c, marker=mk, alpha=0.35, linewidths=0)
        a = a.sort_values("fr"); best = 1e9; fx, fy = [], []
        for _, r in a.iterrows():
            if r.delay_mean < best: best = r.delay_mean; fx.append(r.fr); fy.append(r.delay_mean)
        ax.step(fx, fy, where="post", c=c, lw=1.6, label=lab)
    dflt = g[(g.family == "hyst") & (g.p1 == 15) & (g.p2 == 20)].iloc[0]
    ax.scatter([max(dflt.false_per_h, 3e-4)], [dflt.delay_mean], s=70, facecolors="none", edgecolors="k", lw=1.5, zorder=5, label="paper default ($h{=}15$, 20 s)")
    ax.set_xscale("log"); ax.set_xlabel("False toggles per hour (student on the fence)")
    ax.set_title(f"$\\sigma$ = {s:g} m, $T_c$ = {tc:g} s", fontsize=9); ax.set_xlim(2e-4, 60); ax.set_ylim(5, 50); ax.grid(alpha=0.3)
axs[0].set_ylabel("Mean detection delay (s)"); axs[0].legend(fontsize=6.5, loc="upper right")
fig.tight_layout(); fig.savefig("../paper/figs/fig_pareto.pdf"); fig.savefig("../paper/figs/fig_pareto.png", dpi=200)
