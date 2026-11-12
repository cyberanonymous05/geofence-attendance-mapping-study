"""Estimate GPS-error statistics from stationary segments of real GeoLife tracks.

A segment is 'stationary' if, over a window of W seconds at ~1 Hz, every fix lies within `radius_m`
of the window median. Residuals from the median then approximate measurement error (they also include
any slow true motion within the radius, so the estimate is an UPPER bound on sigma).
"""
import sys, json
import numpy as np
from geosim import geolife

W, RADIUS = 300, 25.0
rng = np.random.default_rng(0)
tracks = geolife.list_tracks()
rng.shuffle(tracks)
tracks = tracks[:3000]
sig, ac10, ac30, outl, nseg = [], [], [], [], 0
for p in tracks:
    try:
        lat, lon, t = geolife.load_track(p)
    except Exception:
        continue
    for x, y in geolife.to_1hz_segments(lat, lon, t, max_gap=3.0, min_len=W):
        for s in range(0, len(x) - W, W):
            xs, ys = x[s:s + W], y[s:s + W]
            mx, my = np.median(xs), np.median(ys)
            rx, ry = xs - mx, ys - my
            if np.hypot(rx, ry).max() > RADIUS:
                continue
            nseg += 1
            res = np.r_[rx, ry]
            sig.append(res.std())
            for lag, store in ((10, ac10), (30, ac30)):
                store.append(np.mean([np.corrcoef(r[:-lag], r[lag:])[0, 1] for r in (rx, ry)]))
            outl.append(np.mean(np.hypot(rx, ry) > 3 * np.hypot(rx, ry).std() + 1e-9))
sig = np.array(sig)
out = dict(n_tracks_scanned=len(tracks), n_stationary_windows=int(nseg),
           sigma_per_axis_median=float(np.median(sig)), sigma_p25=float(np.percentile(sig, 25)),
           sigma_p75=float(np.percentile(sig, 75)), sigma_p95=float(np.percentile(sig, 95)),
           autocorr_lag10_median=float(np.nanmedian(ac10)), autocorr_lag30_median=float(np.nanmedian(ac30)),
           frac_fixes_beyond_3sigma_median=float(np.median(outl)))
# AR(1) correlation time from lag-10 autocorrelation: rho = exp(-lag/tau)
r10 = float(np.nanmedian(ac10))
out["tau_s_from_lag10"] = float(-10 / np.log(r10)) if 0 < r10 < 1 else None
print(json.dumps(out, indent=1))
json.dump(out, open("results/gps_calibration_geolife.json", "w"), indent=1)
