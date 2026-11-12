"""Extra experiments for review robustness: smoothing baselines, GPS cold-start energy, capture-aware capacity.
All simulated except the real-trace part of exp10, which replays GeoLife (proxy truth)."""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy.signal import medfilt
from scipy.ndimage import uniform_filter1d
import run_experiments as E
from geosim import detector, sampler, node, energy, capacity, geolife
from geosim import params as P
from geosim.stats import cluster_indices

R = "results/"
BASE = {
 "plain+fixed5s":   lambda: (detector.PlainRadius(), sampler.Fixed(5), False),
 "movavg5+fixed5s": lambda: (detector.MovingAverage(n=5), sampler.Fixed(5), False),
 "kalman+fixed5s":  lambda: (detector.KalmanRadius(), sampler.Fixed(5), False),
 "hyst+fixed5s":    lambda: (detector.Hysteresis(), sampler.Fixed(5), True),
 "hyst+adaptive":   lambda: (detector.Hysteresis(), sampler.Adaptive(), True),
}

# ---- exp10: baselines, simulated + real replay ----
days = E.make_days(100)
rows = []
for name, mk in BASE.items():
    df = E.evaluate(days, mk)
    rows.append(dict(data="simulated", config=name, spurious=df.spurious.mean(), spurious_ci=E.ci95(df.spurious),
                     missed=df.missed.mean(), delay=df.delay_mean.mean(), fixes=df.fixes.mean(), unit="per day"))
rng = np.random.default_rng(42)
tracks = geolife.list_tracks(); rng.shuffle(tracks)
acc = {k: [] for k in BASE}; usr = {k: [] for k in BASE}; nseg = 0
for p in tracks:
    if nseg >= 600: break
    try: lat, lon, t = geolife.load_track(p)
    except Exception: continue
    for x, y in geolife.to_1hz_segments(lat, lon, t, max_gap=10.0, min_len=1800):
        i0 = len(x) // 4; xm, ym = x - x[i0], y - y[i0]
        xs = uniform_filter1d(medfilt(xm, 61), 31); ys = uniform_filter1d(medfilt(ym, 61), 31)
        if np.percentile(np.hypot(np.diff(xs), np.diff(ys)), 95) > 3.0: continue
        truth = node.truth_transitions(xs, ys)
        if len(truth) < 2: continue
        nseg += 1; z = np.zeros_like(xm); init = bool(np.hypot(xm[0], ym[0]) <= P.FENCE_RADIUS_M)
        for name, mk in BASE.items():
            det, smp, filt = mk()
            ev, fixes = node.run_node(xm, ym, z, z, det, smp, use_filter=filt)
            dl, ms, sp = node.match_events(truth, ev, init_state=init)
            acc[name].append((len(xm) / 3600, fixes, sp, ms, len(truth), sum(dl), len(dl))); usr[name].append(p.split('/')[-3])
    if nseg >= 600: break
for name, a in acc.items():
    a = np.array(a); H = a[:, 0].sum()
    boot = [a[cluster_indices(usr[name], np.random.default_rng(s))] for s in range(300)]
    sp = [b[:, 2].sum() / b[:, 0].sum() for b in boot]
    rows.append(dict(data="GeoLife replay", config=name, spurious=a[:, 2].sum() / H,
                     spurious_ci=1.96 * np.std(sp), missed=a[:, 3].sum() / a[:, 4].sum(),
                     delay=a[:, 5].sum() / max(a[:, 6].sum(), 1), fixes=a[:, 1].sum() / H, unit="per hour"))
pd.DataFrame(rows).to_csv(R + "exp10_baselines.csv", index=False)
print(pd.DataFrame(rows).to_string())

# ---- exp11: GPS fix-time (cold-start) sensitivity on battery life ----
det = pd.read_csv(R + "exp1_detection_main.csv").set_index("config")
rows = []
for fix_s in (2, 5, 15, 30):
    old = P.GPS_FIX_TIME_S; P.GPS_FIX_TIME_S = fix_s
    for cfg in ("hyst+fixed5s", "hyst+fixed30s", "hyst+fixed60s", "hyst+adaptive"):
        r = det.loc[cfg]
        rows.append(dict(fix_time_s=fix_s, config=cfg,
                         battery_days=energy.battery_life_days(r.fixes_per_day, r.events_per_day + 24, 10)))
    P.GPS_FIX_TIME_S = old
pd.DataFrame(rows).to_csv(R + "exp11_fixtime.csv", index=False)
print(pd.DataFrame(rows).pivot(index="fix_time_s", columns="config", values="battery_days").round(1).to_string())

# ---- exp12: capture-aware, multi-channel capacity ----
rate = (det.loc["hyst+adaptive"].events_per_day + 24) / 86400.0
rows = []
for D in (300.0, 1000.0):
    for ch in (1, 3, 8):
        for cap_db, lab in ((1e9, "no capture"), (6.0, "capture 6 dB")):
            caps = [capacity.capacity(rate, channels=ch, D=D, capture_db=cap_db, seed=s) for s in range(3)]
            rows.append(dict(disc_radius_m=D, channels=ch, model=lab, students_per_gateway=int(np.median(caps))))
pd.DataFrame(rows).to_csv(R + "exp12_capacity_capture.csv", index=False)
print(pd.DataFrame(rows).to_string())
