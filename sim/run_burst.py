"""exp20-22: synchronised-crossing bursts, jittered / back-dated / encrypted uplink, timing leakage.
Timetable parameters are ASSUMED; detector latency is drawn from the simulated hysteresis detector."""
import math, sys, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy.signal import lfilter
from geosim import detector, burst
OUT = "results"
DT, V = 5.0, 1.4


def detector_delays(n=3000, sigma=5.3, Tc=79.0, seed=3):
    """Mean detector latency distribution for a 1.4 m/s walker crossing the fence (simulated hysteresis, 5 s fixes)."""
    rng = np.random.default_rng(seed); phi = math.exp(-DT / Tc)
    T = int((60 + 250) / V / DT) + 1; t = np.arange(T) * DT; t_pre = 60 / V; out = []
    for _ in range(n):
        e = sigma * lfilter([math.sqrt(1 - phi ** 2)], [1, -phi], rng.standard_normal(T + 40))[20:20 + T]
        det = detector.Hysteresis(); det.reset(True)
        for i in range(T):
            if det.update(t[i], 240 + V * t[i] + e[i]) is False:
                out.append(t[i] - t_pre); break
    return np.array(out)


def exp20(seeds=3):
    dl = detector_delays()
    print("detector latency: mean %.1f s, p5 %.1f, p95 %.1f" % (dl.mean(), *np.percentile(dl, [5, 95])), flush=True)
    rows = []
    for sw in (15, 30, 60, 120, 300):
        for J, rep in ((0, 1), (60, 1), (240, 1), (240, 2)):
            for n in (250, 500, 1000, 1500, 2000, 3000, 4500, 7000):
                r = [burst.burst_delivery(n, sw, J, rep, dl, seed=s) for s in range(seeds)]
                rows.append(dict(sigma_w_s=sw, jitter_s=J, repeats=rep, n=n,
                                 event_delivery=np.mean([x["event_delivery"] for x in r]),
                                 packet_pdr=np.mean([x["packet_pdr"] for x in r]),
                                 peak_pkts_per_min=np.mean([x["peak_pkts_per_min"] for x in r])))
        print("sigma_w", sw, flush=True)
    df = pd.DataFrame(rows); df.to_csv(f"{OUT}/exp20_burst_capacity.csv", index=False)
    caps = []
    for (sw, J, rep), g in df.groupby(["sigma_w_s", "jitter_s", "repeats"]):
        g = g.sort_values("n"); ln, y = np.log(g.n.values), g.event_delivery.values
        if y[0] < 0.95: cap = float("nan")
        elif y[-1] >= 0.95: cap = float(g.n.values[-1])
        else:
            i = int(np.argmax(y < 0.95)); f = (y[i - 1] - 0.95) / (y[i - 1] - y[i])
            cap = float(np.exp(ln[i - 1] + f * (ln[i] - ln[i - 1])))
        caps.append(dict(sigma_w_s=sw, jitter_s=J, repeats=rep, students_at_95pct=cap))
    pd.DataFrame(caps).to_csv(f"{OUT}/exp20_burst_capacity_summary.csv", index=False)
    print(pd.DataFrame(caps).pivot_table(index="sigma_w_s", columns=["jitter_s", "repeats"], values="students_at_95pct").round(0))
    return dl


def exp24(seeds=3):
    """Trace-driven burst study with REAL crossing times (StudentLife, Dartmouth 2013; see geosim/studentlife.py)."""
    from geosim import studentlife as S
    df = S.load("data/studentlife/dataset_rds/sensing/wifi_location.Rds")
    homes = S.home_of(df); ev = S.events(df, homes)
    ev.to_csv(f"{OUT}/exp24_studentlife_events.csv", index=False)
    wk = ev[ev.dow < 5]
    pools = {"all weekdays": wk, "Mon/Wed/Fri": wk[wk.dow.isin([0, 2, 4])], "Tue/Thu": wk[wk.dow.isin([1, 3])]}
    dl = detector_delays()
    rows, stats = [], []
    for pname, p in pools.items():
        sdays = [g.sod.values for _, g in p.groupby(["uid", "day"])]
        per_min = np.bincount((p.sod.values // 60).astype(int), minlength=1440)
        peak_min_frac = per_min.max() / len(sdays)          # events in busiest minute per student-day
        peak5 = np.convolve(per_min, np.ones(5), "valid").max() / len(sdays)
        stats.append(dict(pool=pname, student_days=len(sdays), events_per_day=len(p) / len(sdays),
                          peak_minute_events_per_student=peak_min_frac, peak_5min_events_per_student=peak5))
        gen = burst.empirical_crossings(sdays)
        for J, rep in ((0, 1), (60, 1), (240, 1), (240, 2)):
            for n in (500, 1000, 1500, 2000, 3000, 4500, 7000, 10000):
                r = [burst.burst_delivery(n, 0, J, rep, dl, seed=s, crossing_fn=gen) for s in range(seeds)]
                rows.append(dict(pool=pname, jitter_s=J, repeats=rep, n=n, event_delivery=np.mean([x["event_delivery"] for x in r]),
                                 peak_pkts_per_min=np.mean([x["peak_pkts_per_min"] for x in r])))
        print(pname, flush=True)
    df_ = pd.DataFrame(rows); df_.to_csv(f"{OUT}/exp24_real_burst_delivery.csv", index=False)
    pd.DataFrame(stats).to_csv(f"{OUT}/exp24_real_burst_stats.csv", index=False)
    caps = []
    for (pn, J, rep), g in df_.groupby(["pool", "jitter_s", "repeats"]):
        g = g.sort_values("n"); ln, y = np.log(g.n.values), g.event_delivery.values
        if y[0] < 0.95: cap = float("nan")
        elif y[-1] >= 0.95: cap = float(g.n.values[-1])
        else:
            i = int(np.argmax(y < 0.95)); f = (y[i - 1] - 0.95) / (y[i - 1] - y[i]); cap = float(np.exp(ln[i - 1] + f * (ln[i] - ln[i - 1])))
        caps.append(dict(pool=pn, jitter_s=J, repeats=rep, students_at_95pct=cap))
    cp = pd.DataFrame(caps); cp.to_csv(f"{OUT}/exp24_real_burst_capacity.csv", index=False)
    print(pd.DataFrame(stats).round(4).to_string()); print(cp.pivot_table(index="pool", columns=["jitter_s", "repeats"], values="students_at_95pct").round(0))


def _cap_model(lam, J, rep, st, pout, target=0.95):
    from geosim import burst_model as M
    lo, hi = 1, 2
    while M.event_delivery(lam, hi, J, rep, stats=st, p_out=pout) >= target and hi < 200000: lo, hi = hi, hi * 2
    for _ in range(18):
        mid = (lo + hi) // 2
        if M.event_delivery(lam, mid, J, rep, stats=st, p_out=pout) >= target: lo = mid
        else: hi = mid
    return lo


def exp25(seeds=3):
    """Closed-form burst model vs Monte Carlo (Gaussian and real StudentLife profiles) and the worst-case bound."""
    from geosim import burst_model as M, studentlife as S
    st, pout = M.link_stats()
    ev = pd.read_csv(f"{OUT}/exp24_studentlife_events.csv"); wk = ev[ev.dow < 5]
    sdays = [g.sod.values for _, g in wk.groupby(["uid", "day"])]
    lam_real = M.profile_from_events(wk.sod.values, len(sdays))
    gen = burst.empirical_crossings(sdays)
    rows = []
    cases = [("Gaussian 30 s", M.profile_from_gauss([8.5, 13, 14, 17.5], 0.9, 30), dict(sigma=30)),
             ("Gaussian 120 s", M.profile_from_gauss([8.5, 13, 14, 17.5], 0.9, 120), dict(sigma=120)),
             ("Gaussian 300 s", M.profile_from_gauss([8.5, 13, 14, 17.5], 0.9, 300), dict(sigma=300)),
             ("real (StudentLife)", lam_real, dict(real=True))]
    for name, lam, kw in cases:
        for J, rep in ((0, 1), (240, 1), (240, 2)):
            for n in (1000, 2000, 4000, 8000):
                a = M.event_delivery(lam, n, J, rep, stats=st, p_out=pout)
                mc = np.mean([(burst.burst_delivery(n, 0, J, rep, np.full(50, 33.0), seed=s, crossing_fn=gen) if kw.get("real")
                               else burst.burst_delivery(n, kw["sigma"], J, rep, np.full(50, 33.0), seed=s))["event_delivery"] for s in range(seeds)])
                rows.append(dict(profile=name, jitter_s=J, repeats=rep, n=n, model=a, monte_carlo=mc, abs_err_pts=100 * abs(a - mc)))
        print(name, flush=True)
    pd.DataFrame(rows).to_csv(f"{OUT}/exp25_burst_model_validation.csv", index=False)
    # worst case: all students cross exactly at the four bells (sigma_w = 0)
    lam0 = M.profile_from_gauss([8.5, 13, 14, 17.5], 0.9, 0)
    wc = []
    for J, rep in ((0, 1), (60, 1), (120, 1), (240, 1), (240, 2)):
        cm = _cap_model(lam0, J, rep, st, pout)
        mcd = [burst.burst_delivery(n, 0, J, rep, np.full(50, 33.0), seed=0)["event_delivery"] for n in (int(cm * 0.8) or 1, cm, int(cm * 1.25) + 1)]
        wc.append(dict(jitter_s=J, repeats=rep, capacity_model=cm, mc_delivery_at_0p8x=mcd[0], mc_delivery_at_1x=mcd[1], mc_delivery_at_1p25x=mcd[2]))
        print(wc[-1], flush=True)
    pd.DataFrame(wc).to_csv(f"{OUT}/exp25_worst_case.csv", index=False)
    v = pd.DataFrame(rows)
    print(v.groupby("profile").abs_err_pts.agg(["mean", "max"]).round(2))
    print(v[v.repeats == 1].abs_err_pts.agg(["mean", "max"]).round(2), v[v.repeats == 2].abs_err_pts.agg(["mean", "max"]).round(2))


def exp25b():
    """Real profile vs uniform-in-time arrivals (closed-form model), and Monte-Carlo worst-case capacity with repetition."""
    from geosim import burst_model as M
    st, pout = M.link_stats()
    ev = pd.read_csv(f"{OUT}/exp24_studentlife_events.csv"); wk = ev[ev.dow < 5]
    n_sd = wk.groupby(["uid", "day"]).ngroups
    lam = M.profile_from_events(wk.sod.values, n_sd)
    uni = np.full(86400, lam.sum() / 86400)
    rows = []
    for name, l in (("uniform in time", uni), ("real profile", lam)):
        rows.append(dict(profile=name, capacity_J0=_cap_model(l, 0, 1, st, pout), capacity_J240=_cap_model(l, 240, 1, st, pout)))
    pd.DataFrame(rows).to_csv(f"{OUT}/exp25_real_vs_uniform.csv", index=False)
    pk = np.convolve(lam, np.ones(60), "valid").max() / (lam.sum() / 1440)
    pd.DataFrame([dict(peak_to_mean_per_minute=pk, events_per_student_day=lam.sum())]).to_csv(f"{OUT}/exp25_real_profile_stats.csv", index=False)
    scan = []
    for n in (1000, 1250, 1500, 1750, 2000, 2250, 2500):
        scan.append(dict(n=n, mc_delivery=np.mean([burst.burst_delivery(n, 0, 240, 2, np.full(50, 33.0), seed=s)["event_delivery"] for s in range(4)])))
    sc = pd.DataFrame(scan); sc.to_csv(f"{OUT}/exp25_worst_case_rep2_scan.csv", index=False)
    y, x = sc.mc_delivery.values, sc.n.values
    i = int(np.argmax(y < 0.95)); cap = x[i - 1] + (y[i - 1] - 0.95) / (y[i - 1] - y[i]) * (x[i] - x[i - 1])
    pd.DataFrame([dict(mc_capacity_rep2_worst=cap)]).to_csv(f"{OUT}/exp25_worst_case_rep2_cap.csv", index=False)
    print(pd.DataFrame(rows).to_string(), pk, cap)


def _events_days(days):
    from geosim import sampler, node
    from geosim import params as P
    out = []
    for x, y, ex, ey, truth in days:
        det, smp = detector.Hysteresis(), sampler.Adaptive()
        cand = []
        ev, fx = node.run_node(x, y, ex, ey, det, smp, use_filter=True, cand_out=cand)
        init = bool(np.hypot(x[0], y[0]) <= P.FENCE_RADIUS_M)
        out.append((ev, cand, init, truth, x, y))
    return out


def _match(truth, ev, cand):
    """Pair each detector event with the truth transition it confirms (same new state, within [t-60, next truth))."""
    pairs = []
    used = set()
    for i, (tt, ts) in enumerate(truth):
        t_end = truth[i + 1][0] if i + 1 < len(truth) else 1e18
        for j, (te, es) in enumerate(ev):
            if j not in used and es == ts and tt - 60 <= te < t_end:
                used.add(j); pairs.append((tt, te, cand[j])); break
    return pairs


def exp21(days):
    """Timing leakage to a passive eavesdropper who sees packet times (payload encrypted) and filters out heartbeats."""
    ed = _events_days(days)
    rng = np.random.default_rng(11)
    pr = [p for ev, cand, init, truth, x, y in ed for p in _match(truth, ev, cand)]
    tt = np.array([p[0] for p in pr]); te = np.array([p[1] for p in pr]); n = len(pr)
    rows = []
    for J in (0, 30, 60, 120, 240):
        arr = te + (rng.uniform(0, J, n) if J else 0.0)
        off = arr - tt; err = np.abs(off - np.median(off))
        rows.append(dict(scheme=f"event-driven, jitter U(0,{J} s)" if J else "event-driven, no jitter", median_err_s=np.median(err),
                         p90_err_s=np.percentile(err, 90), within60_pct=100 * np.mean(err <= 60)))
    for P_ in (900, 3600):
        arr = tt + rng.uniform(0, P_, n)
        off = arr - tt; err = np.abs(off - np.median(off))
        rows.append(dict(scheme=f"heartbeat only, period {P_} s", median_err_s=np.median(err), p90_err_s=np.percentile(err, 90),
                         within60_pct=100 * np.mean(err <= 60)))
    df = pd.DataFrame(rows); df.to_csv(f"{OUT}/exp21_timing_leakage.csv", index=False)
    print(df.round(1).to_string()); print("events matched:", n)


def _server_belief(pk, init, T=86400):
    """pk: list of (t_tx, key, state). Packets are applied in transmit (= counter) order; each sets the state from
    `key` (its back-dated or arrival time) onward, so a later-transmitted event overrides an earlier heartbeat."""
    belief = np.full(T, init, bool)
    for t_tx, key, st in sorted(pk, key=lambda p: p[0]):
        k = int(min(max(key, 0), T - 1))
        belief[k:] = st
    return belief


def _state_at(ev, init, t):
    st = init
    for te, es in ev:
        if te <= t: st = es
        else: break
    return st


def exp22(days, hb=900, tol=20.0):
    """Roll-call accuracy: server timeline by arrival time (real time) or by back-dated time (age field)."""
    ed = _events_days(days)
    rows = []
    for J in (0, 120, 240):
        for pdr in (1.0, 0.95):
            for mode in ("real-time", "back-dated"):
                rng = np.random.default_rng(21)
                strict, tolr, errs = [], [], []
                for (ev, cand, init, truth, x, y) in ed:
                    pk = []
                    for (te, es), c in zip(ev, cand):
                        if rng.random() >= pdr: continue
                        ttx = te + (rng.uniform(0, J) if J else 0.0)
                        age = min(round((ttx - (c if c is not None else te)) / 2) * 2, 254)
                        pk.append((ttx, (ttx if mode == "real-time" else ttx - age), es))
                    for th in np.arange(rng.uniform(0, hb), 86400, hb):
                        if rng.random() < pdr: pk.append((th, th, _state_at(ev, init, th)))
                    b = _server_belief(pk, init)
                    r = np.hypot(x, y); ts = r <= 300.0; amb = np.abs(r - 300.0) <= tol
                    ok = b == ts; strict.append(ok.mean()); tolr.append((ok | amb).mean())
                rows.append(dict(jitter_s=J, pdr=pdr, mode=mode, acc_strict_pct=100 * np.mean(strict), acc_tol_pct=100 * np.mean(tolr)))
        print(J, flush=True)
    # log timestamp error of the back-dated estimate (pdr=1, no jitter effect by construction)
    errs = [(c if c is not None else te) - tt for ev, cand, init, truth, x, y in ed for tt, te, c in _match(truth, ev, cand)]
    errs = np.array(errs)
    df = pd.DataFrame(rows); df.to_csv(f"{OUT}/exp22_backdating_accuracy.csv", index=False)
    pd.DataFrame([dict(median_err_s=np.median(errs), mae_s=np.mean(np.abs(errs)), p90_abs_s=np.percentile(np.abs(errs), 90), n=len(errs))]
                 ).to_csv(f"{OUT}/exp22_backdating_timestamp_error.csv", index=False)
    print(df.round(2).to_string()); print("timestamp error: median %.1f MAE %.1f p90 %.1f (n=%d)" % (np.median(errs), np.mean(np.abs(errs)), np.percentile(np.abs(errs), 90), len(errs)))


if __name__ == "__main__":
    which = set(sys.argv[1:]) or {"20", "21", "22"}
    if "20" in which: exp20()
    if "24" in which: exp24()
    if "25" in which: exp25()
    if "25b" in which: exp25b()
    if which & {"21", "22"}:
        from run_experiments import make_days
        days = make_days(100)
        if "21" in which: exp21(days)
        if "22" in which: exp22(days)
