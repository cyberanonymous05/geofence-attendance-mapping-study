"""Replay real GeoLife tracks through the node pipeline. Real fixes are the MEASUREMENTS (no injected error).
Ground truth is unknown, so a proxy truth is used: median(61 s)+moving-average(31 s) smoothed track,
Schmitt trigger +-10 m on its distance. Results are REAL-TRACE (proxy-truth), not simulated mobility.
Fence: circle R=300 m centred on the track position at 25% of the segment (so tracks cross it)."""
import numpy as np, pandas as pd
from scipy.signal import medfilt
from scipy.ndimage import uniform_filter1d
from geosim import geolife, detector, sampler, node, energy
from geosim import params as P
from geosim.stats import cluster_indices

rng = np.random.default_rng(42)
tracks = geolife.list_tracks(); rng.shuffle(tracks)
import warnings; warnings.filterwarnings('ignore')
CFG = {
 "plain+fixed5s":   lambda: (detector.PlainRadius(), sampler.Fixed(5), False),
 "plain+adaptive":  lambda: (detector.PlainRadius(), sampler.Adaptive(), False),
 "hyst+fixed5s":    lambda: (detector.Hysteresis(), sampler.Fixed(5), True),
 "hyst+fixed30s":   lambda: (detector.Hysteresis(), sampler.Fixed(30), True),
 "hyst+fixed60s":   lambda: (detector.Hysteresis(), sampler.Fixed(60), True),
 "hyst+adaptive":   lambda: (detector.Hysteresis(), sampler.Adaptive(), True),
 "hyst25+adaptive": lambda: (detector.Hysteresis(h=25.0), sampler.Adaptive(), True),
}
rows, nseg = [], 0
for p in tracks:
    if nseg >= 600: break
    try:
        lat, lon, t = geolife.load_track(p)
    except Exception:
        continue
    for x, y in geolife.to_1hz_segments(lat, lon, t, max_gap=10.0, min_len=1800):
        i0 = len(x) // 4
        cx, cy = x[i0], y[i0]
        xm, ym = x - cx, y - cy
        xs = uniform_filter1d(medfilt(xm, 61), 31); ys = uniform_filter1d(medfilt(ym, 61), 31)
        spd = np.hypot(np.diff(xs), np.diff(ys))
        if np.percentile(spd, 95) > 3.0:      # keep pedestrian segments only (matches student use case)
            continue
        truth = node.truth_transitions(xs, ys)
        truth20 = node.truth_transitions(xs, ys, tol=20.0)
        if len(truth) < 2: continue
        nseg += 1
        z = np.zeros_like(xm)
        hours = len(xm) / 3600.0
        init = bool(np.hypot(xm[0], ym[0]) <= P.FENCE_RADIUS_M)
        for name, mk in CFG.items():
            det, smp, filt = mk()
            ev, fixes = node.run_node(xm, ym, z, z, det, smp, use_filter=filt)
            delays, missed, spur = node.match_events(truth, ev, init_state=init)
            _, missed20, _ = node.match_events(truth20, ev, init_state=init)
            rows.append(dict(config=name, user=p.split('/')[-3], hours=hours, fixes=fixes, events=len(ev), truth=len(truth),
                             truth20=len(truth20), missed20=missed20,
                             missed=missed, spurious=spur, delay_sum=float(np.sum(delays)), delay_n=len(delays)))
        if nseg >= 600: break
df = pd.DataFrame(rows)
res = []
for name, g in df.groupby("config", sort=False):
    H = g.hours.sum()
    g = g.reset_index(drop=True)
    boot = [g.iloc[cluster_indices(g.user.values, np.random.default_rng(s))] for s in range(300)]
    sp = [b.spurious.sum() / b.hours.sum() for b in boot]
    fx = [b.fixes.sum() / b.hours.sum() for b in boot]
    res.append(dict(config=name, segments=len(g), track_hours=H,
                    fixes_per_hour=g.fixes.sum() / H, spurious_per_hour=g.spurious.sum() / H,
                    spur_ci_lo=np.percentile(sp, 2.5), spur_ci_hi=np.percentile(sp, 97.5),
                    missed_frac=g.missed.sum() / g.truth.sum(),
                    missed_frac_tol20=g.missed20.sum() / max(g.truth20.sum(), 1),
                    delay_mean_s=g.delay_sum.sum() / max(g.delay_n.sum(), 1),
                    true_transitions_per_hour=g.truth.sum() / H))
out = pd.DataFrame(res)
out["battery_days"] = [energy.battery_life_days(r.fixes_per_hour * 24, (r.true_transitions_per_hour * 24) + 24, 10) for r in out.itertuples()]
out.to_csv("results/exp7_realtrace_geolife.csv", index=False)
print(out.to_string())
