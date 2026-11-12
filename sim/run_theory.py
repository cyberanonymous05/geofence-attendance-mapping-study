"""Validate the analytic flapping model against Monte Carlo of the actual detector, and tabulate the design rule.
Stationary student near the fence, AR(1) GPS error (no outliers, no plausibility filter). All SIMULATED."""
import math, numpy as np, pandas as pd
from scipy.signal import lfilter
from geosim import analysis as A, detector

DT, K, DWELL = 5.0, 2, 20.0
CASES = [(8.0, 30.0), (5.3, 79.0)]          # (sigma, Tc): assumed vs GeoLife-calibrated
rows = []

def ar1(rng, n, sigma, Tc):
    phi = math.exp(-DT / Tc)
    return sigma * lfilter([math.sqrt(1 - phi ** 2)], [1, -phi], rng.standard_normal(n))

def mc_plain(delta, sigma, Tc, hours, seed):
    n = int(hours * 3600 / DT)
    e = ar1(np.random.default_rng(seed), n, sigma, Tc)
    s = np.sign(e - delta)
    return np.sum(s[1:] != s[:-1]) / hours

def mc_hyst(delta, h, sigma, Tc, hours, seed):
    n = int(hours * 3600 / DT)
    e = ar1(np.random.default_rng(seed), n, sigma, Tc)
    d = 300.0 - delta + e
    det = detector.Hysteresis(R=300.0, h=h, k=K, dwell_s=DWELL)
    det.reset(inside=True)
    prev, cnt = True, 0
    for i in range(n):
        st = det.update(i * DT, d[i])
        if st != prev:
            cnt += 1; prev = st
    return cnt / hours

for sigma, Tc in CASES:
    for delta in (0.0, 5.0, 10.0):
        an = A.plain_toggles_per_hour(delta, sigma, Tc, DT)
        mc = mc_plain(delta, sigma, Tc, 200, 1)
        rows.append(dict(detector="plain", sigma=sigma, Tc=Tc, delta=delta, h=np.nan, analytic=an, monte_carlo=mc, hours=200))
    for h in (5.0, 8.0, 10.0, 15.0):
        an = A.hyst_toggles_per_hour(0.0, h, sigma, Tc, DT, K, DWELL)
        hours = float(min(6000, max(300, 400 / max(an, 1e-9))))
        mc = mc_hyst(0.0, h, sigma, Tc, hours, 2)
        rows.append(dict(detector="hysteresis", sigma=sigma, Tc=Tc, delta=0.0, h=h, analytic=an, monte_carlo=mc, hours=hours))
val = pd.DataFrame(rows)
val["rel_err_pct"] = 100 * (val.monte_carlo - val.analytic) / val.analytic
val.to_csv("results/exp13_theory_validation.csv", index=False)
print(val.to_string())

drows = []
for sigma, Tc in [(2.1, 30.0), (5.3, 79.0), (8.0, 30.0), (8.0, 79.0), (16.0, 30.0)]:
    for dwell in (10.0, 20.0, 40.0):
        for eps in (0.1, 0.01):
            h = A.design_h(eps, sigma, Tc, DT, K, dwell)
            drows.append(dict(sigma=sigma, Tc=Tc, dwell=dwell, eps_per_hour=eps, h_star=h,
                              pred_delay_s=A.predicted_delay(h, 1.4, dwell, DT)))
des = pd.DataFrame(drows)
des.to_csv("results/exp14_design_rule.csv", index=False)
print(des.to_string())
