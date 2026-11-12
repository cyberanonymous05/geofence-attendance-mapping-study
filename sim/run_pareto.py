"""Detector Pareto study: false-toggle rate of a student standing on the fence (worst case) versus mean detection
delay of a walker crossing at 1.4 m/s, for the hysteresis family and the excess-area (CUSUM-style) family.
SIMULATED. Fixed 5 s sampling, AR(1) GPS error."""
import math, sys, numpy as np, pandas as pd
from scipy.signal import lfilter
from geosim import detector

DT = 5.0
CASES = [(5.3, 79.0), (8.0, 30.0)]
V = 1.4

def ar1(rng, n, sigma, Tc):
    phi = math.exp(-DT / Tc)
    return sigma * lfilter([math.sqrt(1 - phi ** 2)], [1, -phi], rng.standard_normal(n))

def false_rate(make, sigma, Tc, hours, seed=1):
    n = int(hours * 3600 / DT)
    e = ar1(np.random.default_rng(seed), n, sigma, Tc)
    d = 300.0 + e
    det = make(); det.reset(inside=True)
    prev, cnt = True, 0
    for i in range(n):
        st = det.update(i * DT, d[i])
        if st != prev: cnt += 1; prev = st
    return cnt / hours

def walker_delay(make, sigma, Tc, trials=1500, seed=7):
    rng = np.random.default_rng(seed)
    delays, miss = [], 0
    t_pre = 60.0 / V                      # starts 60 m inside
    T = int((60.0 + 250.0) / V / DT) + 1  # walks to 250 m outside
    for _ in range(trials):
        e = ar1(rng, T + 40, sigma, Tc)
        e = e[20:20 + T]                  # decorrelate from start
        t = np.arange(T) * DT
        d = 240.0 + V * t + e             # true distance, crosses 300 at t_pre
        det = make(); det.reset(inside=True)
        hit = None
        for i in range(T):
            if det.update(t[i], d[i]) is False:
                hit = t[i]; break
        if hit is None: miss += 1
        else: delays.append(hit - t_pre)
    if not delays: return float('nan'), float('nan'), miss / trials
    return float(np.mean(delays)), float(np.percentile(delays, 95)), miss / trials

fams = {}
for h in np.arange(5, 35.1, 2.5):
    for dw in (0, 5, 10, 20, 30, 45, 60):
        fams[("hyst", float(h), dw)] = lambda h=h, dw=dw: detector.Hysteresis(h=h, k=2, dwell_s=dw)
for h in np.arange(0, 30.1, 2.5):
    for A in (25, 50, 75, 100, 150, 200, 300, 400, 600, 800, 1200, 1600):
        fams[("excess", float(h), A)] = lambda h=h, A=A: detector.ExcessArea(h=h, A=A)

rows = []
for sigma, Tc in CASES:
    for (fam, p1, p2), mk in fams.items():
        # adaptive horizon: enough hours for ~ >=150 expected toggles, capped
        r0 = false_rate(mk, sigma, Tc, 100)
        hours = float(min(2500, max(100, 150 / max(r0, 1e-3))))
        r = false_rate(mk, sigma, Tc, hours) if hours > 100 else r0
        md, p95, ms = walker_delay(mk, sigma, Tc)
        rows.append(dict(sigma=sigma, Tc=Tc, family=fam, p1=p1, p2=p2, false_per_h=r, hours=hours, delay_mean=md, delay_p95=p95, miss=ms))
        print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv("results/exp19_detector_pareto.csv", index=False)
