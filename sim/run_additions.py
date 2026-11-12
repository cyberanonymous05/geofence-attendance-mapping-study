"""Additional experiments for the paper: exp16 detector ablation, exp17 polygon fences on real GeoLife
pedestrian tracks, exp18 end-to-end attendance accuracy with lossy uplink.
Usage: python3 run_additions.py [16|17|18 ...]. All synthetic numbers are SIMULATED; exp17 uses real
GeoLife fixes with a proxy truth (see paper)."""
import sys, warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from run_experiments import make_days, ci95, HEARTBEAT_S
from geosim import detector, sampler, node
from geosim import params as P
from geosim.stats import cluster_indices

OUT = "results"
which = set(sys.argv[1:]) or {"16", "17", "18"}


# ---------------------------------------------------------------- exp16: detector ablation
def exp16(n=100):
    days = make_days(n)
    cfgs = {
        "none (plain radius)":     dict(h=0, k=1, dw=0, filt=False),
        "plausibility filter":     dict(h=0, k=1, dw=0, filt=True),
        "hysteresis band only":    dict(h=15, k=1, dw=0, filt=False),
        "k-of-n only (k=2)":       dict(h=0, k=2, dw=0, filt=False),
        "dwell only (20 s)":       dict(h=0, k=1, dw=20, filt=False),
        "band + k-of-n":           dict(h=15, k=2, dw=0, filt=False),
        "band + dwell":            dict(h=15, k=1, dw=20, filt=False),
        "band + k + dwell":        dict(h=15, k=2, dw=20, filt=False),
        "full (band+k+dwell+filter)": dict(h=15, k=2, dw=20, filt=True),
    }
    rows = []
    for (dt, name), c in [((dt, nm), c) for dt in (5, 60) for nm, c in cfgs.items()]:
        sp, ms, dl = [], [], []
        for x, y, ex, ey, truth in days:
            det = detector.Hysteresis(h=c["h"], k=c["k"], dwell_s=c["dw"])
            ev, fx = node.run_node(x, y, ex, ey, det, sampler.Fixed(dt), use_filter=c["filt"])
            d, m, s = node.match_events(truth, ev, init_state=bool(np.hypot(x[0], y[0]) <= P.FENCE_RADIUS_M))
            sp.append(s); ms.append(m); dl.append(np.mean(d) if d else np.nan)
        sp, ms, dl = pd.Series(sp), pd.Series(ms), pd.Series(dl)
        rows.append(dict(interval_s=dt, config=name, spurious_per_day=sp.mean(), spurious_ci=ci95(sp), missed_per_day=ms.mean(),
                         delay_mean_s=dl.mean(), delay_ci=ci95(dl)))
        print(rows[-1], flush=True)
    pd.DataFrame(rows).to_csv(f"{OUT}/exp16_ablation.csv", index=False)


# ---------------------------------------------------------------- exp17: polygon fences, real tracks
def exp17(max_segs=500):
    from scipy.signal import medfilt
    from scipy.ndimage import uniform_filter1d
    from geosim import geolife
    from geosim.polygon import PolygonFence, rectangle, l_shape
    rng = np.random.default_rng(42)
    tracks = geolife.list_tracks(); rng.shuffle(tracks)
    segs = []
    for p in tracks:
        if len(segs) >= max_segs: break
        try: lat, lon, t = geolife.load_track(p)
        except Exception: continue
        for x, y in geolife.to_1hz_segments(lat, lon, t, max_gap=10.0, min_len=1800):
            xs = uniform_filter1d(medfilt(x, 61), 31); ys = uniform_filter1d(medfilt(y, 61), 31)
            if np.percentile(np.hypot(np.diff(xs), np.diff(ys)), 95) <= 3.0:
                segs.append((x, y, xs, ys, p.split('/')[-3]))
    print("pedestrian segments:", len(segs))
    shapes = {"circle R=300": None, "rectangle 600x400": rectangle(600, 400), "L-shape 700 (notch 350)": l_shape()}
    out = []
    for sname, verts in shapes.items():
        fence = PolygonFence(verts, R0=P.FENCE_RADIUS_M) if verts else None
        recs = []
        for x, y, xs, ys, user in segs:
            i0 = int(len(x) * 0.25)
            xm, ym, xt, yt = x - x[i0], y - y[i0], xs - x[i0], ys - y[i0]
            if fence:
                rt = fence.equiv_series(xt, yt); df = fence.equiv
            else:
                rt = None; df = None
            truth = node.truth_transitions(xt, yt, r=rt)
            if len(truth) < 2: continue
            r0 = df(xm[0], ym[0]) if df else np.hypot(xm[0], ym[0])
            init = bool(r0 <= P.FENCE_RADIUS_M); z = np.zeros_like(xm); hrs = len(xm) / 3600
            for name, mk in (("plain", lambda: (detector.PlainRadius(), sampler.Fixed(5), False)),
                             ("proposed", lambda: (detector.Hysteresis(), sampler.Adaptive(), True))):
                det, smp, filt = mk()
                ev, fx = node.run_node(xm, ym, z, z, det, smp, use_filter=filt, dist_fn=df)
                dl, ms, sp = node.match_events(truth, ev, init_state=init)
                recs.append(dict(config=name, user=user, hours=hrs, fixes=fx, spurious=sp, missed=ms, truth=len(truth), dsum=sum(dl), dn=len(dl)))
        d = pd.DataFrame(recs)
        pl, pr = d[d.config == "plain"].reset_index(drop=True), d[d.config == "proposed"].reset_index(drop=True)
        n = len(pl); H = pl.hours.sum(); diffs = []
        for sd in range(300):
            i = cluster_indices(pl.user.values, np.random.default_rng(sd))
            diffs.append((pl.spurious.iloc[i].sum() - pr.spurious.iloc[i].sum()) / pl.hours.iloc[i].sum())
        out.append(dict(fence=sname, segments=n, hours=H, plain_spur_h=pl.spurious.sum() / H, prop_spur_h=pr.spurious.sum() / H,
                        reduction_pct=100 * (1 - pr.spurious.sum() / max(pl.spurious.sum(), 1)),
                        diff_ci_lo=np.percentile(diffs, 2.5), diff_ci_hi=np.percentile(diffs, 97.5),
                        missed_pct=100 * pr.missed.sum() / pr.truth.sum(), fix_reduction=pl.fixes.sum() / pr.fixes.sum(),
                        delay_s=pr.dsum.sum() / max(pr.dn.sum(), 1)))
        print(out[-1], flush=True)
    pd.DataFrame(out).to_csv(f"{OUT}/exp17_polygon.csv", index=False)


# ---------------------------------------------------------------- exp18: end-to-end attendance accuracy
def _state_at(events, init, t):
    st = init
    for te, es in events:
        if te <= t: st = es
        else: break
    return st


def server_state_series(events, init, heartbeat, pdr, rng, T=86400):
    """Server's belief, per second. Packets (events + heartbeats) each arrive with prob pdr.
    heartbeat: period in s (None = no heartbeat). Belief starts at the known overnight state."""
    pk = [(te, es) for te, es in events if rng.random() < pdr]
    if heartbeat:
        ph = rng.uniform(0, heartbeat)
        for th in np.arange(ph, T, heartbeat):
            if rng.random() < pdr:
                pk.append((th, _state_at(events, init, th)))
    pk.sort()
    belief = np.empty(T, bool); st = init; j = 0
    for t in range(T):
        while j < len(pk) and pk[j][0] <= t:
            st = pk[j][1]; j += 1
        belief[t] = st
    return belief


def exp18(n=100, tol=20.0):
    days = make_days(n)
    cfgs = {"plain+fixed5s": lambda: (detector.PlainRadius(), sampler.Fixed(5), False),
            "hyst+fixed60s": lambda: (detector.Hysteresis(), sampler.Fixed(60), True),
            "hyst+adaptive": lambda: (detector.Hysteresis(), sampler.Adaptive(), True)}
    rows = []
    for cname, mk in cfgs.items():
        evs = []
        for x, y, ex, ey, truth in days:
            det, smp, filt = mk()
            ev, fx = node.run_node(x, y, ex, ey, det, smp, use_filter=filt)
            evs.append((ev, bool(np.hypot(x[0], y[0]) <= P.FENCE_RADIUS_M)))
        for pdr in (1.0, 0.95, 0.9, 0.8):
            for hb in (None, 3600, 900):
                rng = np.random.default_rng(5)
                strict, tolerant = [], []
                for (x, y, ex, ey, truth), (ev, init) in zip(days, evs):
                    r = np.hypot(x, y); tstate = r <= P.FENCE_RADIUS_M
                    amb = np.abs(r - P.FENCE_RADIUS_M) <= tol
                    b = server_state_series(ev, init, hb, pdr, rng)
                    ok = b == tstate
                    strict.append(ok.mean()); tolerant.append((ok | amb).mean())
                s, tl = pd.Series(strict), pd.Series(tolerant)
                rows.append(dict(config=cname, pdr=pdr, heartbeat_s=hb if hb else 0,
                                 acc_strict_pct=100 * s.mean(), acc_tol_pct=100 * tl.mean(), acc_tol_ci=100 * ci95(tl),
                                 wrong_min_per_day=(1 - s.mean()) * 1440))
        print(cname, flush=True)
    pd.DataFrame(rows).to_csv(f"{OUT}/exp18_attendance_accuracy.csv", index=False)


# ---------------------------------------------------------------- exp23: Pareto-suggested tuning on the full pipeline
def exp23(n=100, max_segs=500):
    from scipy.signal import medfilt
    from scipy.ndimage import uniform_filter1d
    from geosim import geolife
    cfg = {"default (h=15, dwell 20)": lambda: detector.Hysteresis(h=15, k=2, dwell_s=20),
           "tuned (h=25, no dwell)":   lambda: detector.Hysteresis(h=25, k=2, dwell_s=0),
           "tuned (h=20, no dwell)":   lambda: detector.Hysteresis(h=20, k=2, dwell_s=0)}
    rows = []
    days = make_days(n)
    for name, mk in cfg.items():
        sp, ms, dl, fx = [], [], [], []
        for x, y, ex, ey, truth in days:
            ev, f = node.run_node(x, y, ex, ey, mk(), sampler.Adaptive(), use_filter=True)
            d, m, s_ = node.match_events(truth, ev, init_state=bool(np.hypot(x[0], y[0]) <= P.FENCE_RADIUS_M))
            sp.append(s_); ms.append(m); dl.append(np.mean(d) if d else np.nan); fx.append(f)
        sp, dl = pd.Series(sp), pd.Series(dl)
        rows.append(dict(data="simulated (per day)", config=name, spurious=sp.mean(), spurious_ci=ci95(sp), missed=np.mean(ms),
                         delay=dl.mean(), fixes=np.mean(fx)))
    rng = np.random.default_rng(42)
    tracks = geolife.list_tracks(); rng.shuffle(tracks); segs = []
    for p in tracks:
        if len(segs) >= max_segs: break
        try: lat, lon, t = geolife.load_track(p)
        except Exception: continue
        for x, y in geolife.to_1hz_segments(lat, lon, t, max_gap=10.0, min_len=1800):
            xs = uniform_filter1d(medfilt(x, 61), 31); ys = uniform_filter1d(medfilt(y, 61), 31)
            if np.percentile(np.hypot(np.diff(xs), np.diff(ys)), 95) <= 3.0: segs.append((x, y, xs, ys))
    for name, mk in cfg.items():
        H = SP = MS = TR = DS = DN = FX = 0
        for x, y, xs, ys in segs:
            i0 = int(len(x) * 0.25); xm, ym, xt, yt = x - x[i0], y - y[i0], xs - x[i0], ys - y[i0]
            truth = node.truth_transitions(xt, yt)
            if len(truth) < 2: continue
            z = np.zeros_like(xm)
            ev, f = node.run_node(xm, ym, z, z, mk(), sampler.Adaptive(), use_filter=True)
            d, m, s_ = node.match_events(truth, ev, init_state=bool(np.hypot(xm[0], ym[0]) <= P.FENCE_RADIUS_M))
            H += len(xm) / 3600; SP += s_; MS += m; TR += len(truth); DS += sum(d); DN += len(d); FX += f
        rows.append(dict(data="GeoLife replay (per hour)", config=name, spurious=SP / H, spurious_ci=np.nan, missed=100 * MS / TR,
                         delay=DS / max(DN, 1), fixes=FX / H))
    df = pd.DataFrame(rows); df.to_csv(f"{OUT}/exp23_tuned_default.csv", index=False); print(df.round(3).to_string())


if __name__ == "__main__":
    if "23" in which: exp23()
    which = which - {"23"}
    if "16" in which: exp16()
    if "17" in which: exp17()
    if "18" in which: exp18()
