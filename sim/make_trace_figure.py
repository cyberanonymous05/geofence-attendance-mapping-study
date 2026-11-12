"""Illustrative trace: plain radius flaps near the fence, hysteresis does not. SIMULATED data."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from geosim import mobility, gps, detector, sampler, node
from geosim import params as P

best = None
for seed in range(1000, 1100):
    rng = np.random.default_rng(seed)
    x, y = mobility.generate_day(rng)
    ex, ey = gps.gps_error(rng, x, y)
    ev_p, _ = node.run_node(x, y, ex, ey, detector.PlainRadius(), sampler.Fixed(5), use_filter=False)
    ev_h, _ = node.run_node(x, y, ex, ey, detector.Hysteresis(), sampler.Fixed(5), use_filter=True)
    if len(ev_p) >= 12 and best is None or (best and len(ev_p) > len(best[3]) and len(ev_h) <= 4):
        best = (seed, (x, y, ex, ey), ev_h, ev_p)
seed, (x, y, ex, ey), ev_h, ev_p = best
t_ev = [t for t, _ in ev_p]
# window around densest plain-flap cluster
c = max(t_ev, key=lambda t: sum(abs(u - t) < 300 for u in t_ev))
a, b = int(c - 400), int(c + 400)
r = np.hypot(x, y); rm = np.hypot(x + ex, y + ey)
def step(ev, init=True):
    ts, st = [a], []
    cur = init
    for t, s in ev:
        if t <= a: cur = s
    st = [cur]
    for t, s in ev:
        if a < t < b:
            ts.append(t); st.append(s)
    ts.append(b); st.append(st[-1])
    return ts, st
plt.rcParams.update({"font.size": 8})
fig, ax = plt.subplots(2, 1, figsize=(3.45, 3.3), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
tt = np.arange(a, b)
ax[0].plot(tt, r[a:b], "k-", lw=1, label="true distance")
ax[0].plot(tt[::5], rm[a:b:5], ".", ms=2.5, color="tab:orange", label="GPS fix")
ax[0].axhline(P.FENCE_RADIUS_M, color="tab:blue", ls="--", lw=0.8, label="fence $R$")
ax[0].axhspan(P.FENCE_RADIUS_M - 15, P.FENCE_RADIUS_M + 15, color="tab:blue", alpha=0.12, label="hysteresis band")
ax[0].set_ylabel("Distance (m)"); ax[0].legend(fontsize=6, loc="best")
for nm, ev, col, off in (("plain radius", ev_p, "tab:red", 1.0), ("hysteresis", ev_h, "tab:green", 0.0)):
    ts, st = step(ev)
    ax[1].step(ts, np.array(st, float) * 0.8 + off * 1.2, where="post", color=col, label=nm)
ax[1].set_yticks([0.4, 1.6]); ax[1].set_yticklabels(["hyst.", "plain"]); ax[1].set_ylim(-0.2, 2.4)
ax[1].set_xlabel("Time (s)"); ax[1].set_ylabel("State\n(up=inside)")
fig.tight_layout(); fig.savefig("../paper/figs/fig_trace.pdf"); fig.savefig("../paper/figs/fig_trace.png", dpi=200)
print("seed", seed, "plain events", len(ev_p), "hyst events", len(ev_h), "window", a, b)
