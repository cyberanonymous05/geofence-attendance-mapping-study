"""Robustness of the GeoLife replay: fence radius and placement, plus paired bootstrap of plain vs proposed.
Real fixes are measurements; truth is the smoothed-track proxy. Pedestrian segments only."""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy.signal import medfilt
from scipy.ndimage import uniform_filter1d
from geosim import geolife, detector, sampler, node
from geosim.stats import cluster_indices

rng = np.random.default_rng(42)
tracks = geolife.list_tracks(); rng.shuffle(tracks)
segs = []
for p in tracks:
    if len(segs) >= 800: break
    try: lat, lon, t = geolife.load_track(p)
    except Exception: continue
    for x, y in geolife.to_1hz_segments(lat, lon, t, max_gap=10.0, min_len=1800):
        xs = uniform_filter1d(medfilt(x, 61), 31); ys = uniform_filter1d(medfilt(y, 61), 31)
        if np.percentile(np.hypot(np.diff(xs), np.diff(ys)), 95) <= 3.0:
            segs.append((x, y, xs, ys, p.split("/")[-3]))
print("pedestrian segments:", len(segs))

def run(R, frac):
    rows = []
    for x, y, xs, ys, user in segs:
        i0 = int(len(x) * frac); cx, cy = x[i0], y[i0]
        xm, ym, xt, yt = x - cx, y - cy, xs - cx, ys - cy
        truth = node.truth_transitions(xt, yt, R=R)
        if len(truth) < 2: continue
        init = bool(np.hypot(xm[0], ym[0]) <= R); z = np.zeros_like(xm); hrs = len(xm) / 3600
        for name, mk in (("plain", lambda: (detector.PlainRadius(R=R), sampler.Fixed(5), False)),
                         ("proposed", lambda: (detector.Hysteresis(R=R), sampler.Adaptive(R=R), True))):
            det, smp, filt = mk()
            ev, fx = node.run_node(xm, ym, z, z, det, smp, use_filter=filt)
            dl, ms, sp = node.match_events(truth, ev, init_state=init)
            rows.append(dict(config=name, user=user, hours=hrs, fixes=fx, spurious=sp, missed=ms, truth=len(truth), dsum=sum(dl), dn=len(dl)))
    return pd.DataFrame(rows)

out = []
for R, frac in [(300, .25), (300, .5), (300, .75), (100, .5), (500, .5)]:
    df = run(R, frac)
    pl, pr = df[df.config == "plain"].reset_index(drop=True), df[df.config == "proposed"].reset_index(drop=True)
    n = len(pl); H = pl.hours.sum()
    diffs = []
    for sd in range(300):
        i = cluster_indices(pl.user.values, np.random.default_rng(sd))
        diffs.append((pl.spurious.iloc[i].sum() - pr.spurious.iloc[i].sum()) / pl.hours.iloc[i].sum())
    out.append(dict(R=R, placement=frac, segments=n, hours=H,
                    plain_spur_h=pl.spurious.sum() / H, prop_spur_h=pr.spurious.sum() / H,
                    reduction_pct=100 * (1 - pr.spurious.sum() / max(pl.spurious.sum(), 1)),
                    diff_ci_lo=np.percentile(diffs, 2.5), diff_ci_hi=np.percentile(diffs, 97.5),
                    missed_pct=100 * pr.missed.sum() / pr.truth.sum(),
                    fix_reduction=pl.fixes.sum() / pr.fixes.sum(),
                    delay_s=pr.dsum.sum() / max(pr.dn.sum(), 1)))
    print(out[-1])
pd.DataFrame(out).to_csv("results/exp15_realtrace_robustness.csv", index=False)
