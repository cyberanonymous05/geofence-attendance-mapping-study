"""Run all experiments. Usage: python3 run_experiments.py [n_days]. Writes results/*.csv and *.png.
All numbers produced here are SIMULATED."""
import sys, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from geosim import mobility, gps, detector, sampler, node, energy, lora, packet, security
from geosim import params as P

N = int(sys.argv[1]) if len(sys.argv) > 1 else 100
OUT = "results"
HEARTBEAT_S = 3600
PL = packet.PAYLOAD_BYTES
RAW_PAYLOAD = 16


def make_days(n, seed0=1000, sigma_deg=None, **over):
    """over: overrides for geosim.params attributes during GPS error generation, e.g. GPS_CORR_TAU_S=79."""
    days = []
    if sigma_deg is not None:
        over["GPS_SIGMA_DEGRADED_M"] = sigma_deg
    for s in range(n):
        rng = np.random.default_rng(seed0 + s)
        x, y = mobility.generate_day(rng)
        old = {k: getattr(P, k) for k in over}
        for k, v in over.items():
            setattr(P, k, v)
        ex, ey = gps.gps_error(rng, x, y)
        for k, v in old.items():
            setattr(P, k, v)
        days.append((x, y, ex, ey, node.truth_transitions(x, y)))
    return days


CONFIGS = {
    "plain+fixed5s":      lambda: (detector.PlainRadius(), sampler.Fixed(5), False),
    "plain+adaptive":     lambda: (detector.PlainRadius(), sampler.Adaptive(), False),
    "hyst+fixed5s":       lambda: (detector.Hysteresis(), sampler.Fixed(5), True),
    "hyst+fixed30s":      lambda: (detector.Hysteresis(), sampler.Fixed(30), True),
    "hyst+fixed60s":      lambda: (detector.Hysteresis(), sampler.Fixed(60), True),
    "hyst+fixed300s":     lambda: (detector.Hysteresis(), sampler.Fixed(300), True),
    "hyst+adaptive":      lambda: (detector.Hysteresis(), sampler.Adaptive(), True),
}


def evaluate(days, make):
    rows = []
    for x, y, ex, ey, truth in days:
        det, smp, filt = make()
        ev, fixes = node.run_node(x, y, ex, ey, det, smp, use_filter=filt)
        delays, missed, spur = node.match_events(truth, ev, init_state=bool(np.hypot(x[0], y[0]) <= P.FENCE_RADIUS_M))
        rows.append(dict(fixes=fixes, events=len(ev), truth=len(truth), missed=missed, spurious=spur,
                         delay_mean=np.mean(delays) if delays else np.nan,
                         delay_max=np.max(delays) if delays else np.nan))
    return pd.DataFrame(rows)


def ci95(s):
    s = s.dropna()
    return 1.96 * s.std(ddof=1) / np.sqrt(len(s)) if len(s) > 1 else np.nan


def exp_detection(days, tag="main"):
    res = []
    for name, mk in CONFIGS.items():
        df = evaluate(days, mk)
        tx = df["events"].mean() + 86400 / HEARTBEAT_S
        life = energy.battery_life_days(df["fixes"].mean(), tx, PL)
        res.append(dict(config=name, fixes_per_day=df["fixes"].mean(), spurious_per_day=df["spurious"].mean(),
                        spurious_ci=ci95(df["spurious"]), missed_per_day=df["missed"].mean(),
                        delay_mean_s=df["delay_mean"].mean(), delay_ci=ci95(df["delay_mean"]),
                        delay_max_s=df["delay_max"].max(), events_per_day=df["events"].mean(),
                        battery_days=life))
    out = pd.DataFrame(res)
    out.to_csv(f"{OUT}/exp1_detection_{tag}.csv", index=False)
    return out


def exp_energy():
    rows = []
    for dt in [1, 2, 5, 10, 30, 60, 300]:
        rows.append(dict(policy=f"fixed {dt}s", fixes=86400 / dt,
                         life=energy.battery_life_days(86400 / dt, 10, PL),
                         life_raw=energy.battery_life_days(86400 / dt, 86400 / dt, RAW_PAYLOAD)))
    pd.DataFrame(rows).to_csv(f"{OUT}/exp2_energy_fixed.csv", index=False)
    return pd.DataFrame(rows)


def exp_capacity(events_per_node_day):
    rows = []
    rate = (events_per_node_day + 86400 / HEARTBEAT_S) / 86400.0
    for sf in range(7, 13):
        toa = lora.time_on_air(PL, sf=sf)
        for n in [50, 100, 250, 500, 1000, 2000, 5000]:
            rows.append(dict(sf=sf, n=n, toa_ms=toa * 1000, pdr=lora.aloha_success_prob(n, rate, toa)))
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/exp3_capacity.csv", index=False)
    cap = []
    for sf in range(7, 13):
        toa = lora.time_on_air(PL, sf=sf)
        n = 1
        while lora.aloha_success_prob(n, rate, toa) >= 0.95 and n < 10**7:
            n *= 1.02; n = int(n) + 1
        cap.append(dict(sf=sf, toa_ms=toa * 1000, students_per_gateway_pdr95=n,
                        duty_cycle_pct_per_node=100 * rate * toa))
    pd.DataFrame(cap).to_csv(f"{OUT}/exp3_capacity_summary.csv", index=False)
    return df, pd.DataFrame(cap)


def exp_privacy(fixes_per_day, events_per_day):
    # coordinate-bearing transmissions per day and bytes/day
    rows = [dict(scheme="raw streaming (every fix)", coord_tx=fixes_per_day, bytes_day=fixes_per_day * RAW_PAYLOAD),
            dict(scheme="proposed (state events + heartbeat)", coord_tx=0,
                 bytes_day=(events_per_day + 86400 / HEARTBEAT_S) * PL)]
    pd.DataFrame(rows).to_csv(f"{OUT}/exp4_privacy.csv", index=False)
    return pd.DataFrame(rows)


def exp_security(days, rng):
    rows = []
    # RSSI consistency: spoofer claims to be inside (d_claim<=R) while truly at d_true
    for k in (1.5, 2.0, 2.5, 3.0):
        far = []
        for d_true in (400, 600, 1000, 1500, 2500):
            claim = rng.uniform(10, P.FENCE_RADIUS_M, 20000)
            far.append((d_true, security.rssi_flag(rng, np.full(20000, float(d_true)), claim, k=k).mean()))
        honest_d = rng.uniform(10, P.FENCE_RADIUS_M, 20000)
        fa = security.rssi_flag(rng, honest_d, honest_d, k=k).mean()
        for d_true, p in far:
            rows.append(dict(test="rssi_spoof", k=k, d_true_m=d_true, detect_rate=p, false_alarm=fa))
    # static-device flag: false alarms on honest simulated days
    for w_h in (6, 12, 18):
        fa = np.mean([security.static_flag(x, y, w_h * 3600) for x, y, *_ in days])
        rows.append(dict(test="static_device", window_h=w_h, false_alarm=fa))
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/exp5_security.csv", index=False)
    return df


def exp_sensitivity(n):
    rows = []
    for sd in (4.0, 8.0, 16.0):
        d = make_days(n, seed0=5000, sigma_deg=sd)
        for name in ("plain+fixed5s", "hyst+adaptive"):
            df = evaluate(d, CONFIGS[name])
            rows.append(dict(sigma_deg=sd, config=name, spurious=df["spurious"].mean(), missed=df["missed"].mean(),
                             delay=df["delay_mean"].mean(), fixes=df["fixes"].mean()))
    pd.DataFrame(rows).to_csv(f"{OUT}/exp6_sensitivity_sigma.csv", index=False)
    return pd.DataFrame(rows)


def exp_calibrated_and_sweeps(n):
    """GeoLife-calibrated GPS error (sigma 5.3 m open, 8.4 m degraded, tau 79 s) and one-at-a-time sweeps."""
    rows = []
    scen = [("baseline(assumed)", {}),
            ("GeoLife-calibrated", dict(GPS_SIGMA_OPEN_M=5.3, GPS_SIGMA_DEGRADED_M=8.4, GPS_CORR_TAU_S=79.0)),
            ("tau=10s", dict(GPS_CORR_TAU_S=10.0)), ("tau=150s", dict(GPS_CORR_TAU_S=150.0)),
            ("outlier p=0.0", dict(GPS_OUTLIER_P=0.0)), ("outlier p=0.02", dict(GPS_OUTLIER_P=0.02)),
            ("sigma_open=4m", dict(GPS_SIGMA_OPEN_M=4.0)), ("sigma_open=8m", dict(GPS_SIGMA_OPEN_M=8.0))]
    cfgs = dict(CONFIGS); cfgs["hyst25+adaptive"] = lambda: (detector.Hysteresis(h=25.0), sampler.Adaptive(), True)
    for name, over in scen:
        d = make_days(n, seed0=7000, **over)
        for cn in ("plain+fixed5s", "hyst+adaptive", "hyst25+adaptive"):
            df = evaluate(d, cfgs[cn])
            rows.append(dict(scenario=name, config=cn, spurious=df["spurious"].mean(), spurious_ci=ci95(df["spurious"]),
                             missed=df["missed"].mean(), delay=df["delay_mean"].mean(), fixes=df["fixes"].mean()))
    out = pd.DataFrame(rows); out.to_csv(f"{OUT}/exp8_calibrated_sweeps.csv", index=False)
    return out


def exp_pathloss_sweep(rng):
    rows = []
    for n_exp in (2.4, 2.9, 3.4):
        for sig in (4.0, 6.0, 8.0):
            far = security.rssi_flag(rng, np.full(20000, 1000.0), rng.uniform(10, P.FENCE_RADIUS_M, 20000), k=2.0, n=n_exp, sigma=sig).mean()
            near = security.rssi_flag(rng, np.full(20000, 400.0), rng.uniform(10, P.FENCE_RADIUS_M, 20000), k=2.0, n=n_exp, sigma=sig).mean()
            hd = rng.uniform(10, P.FENCE_RADIUS_M, 20000)
            fa = security.rssi_flag(rng, hd, hd, k=2.0, n=n_exp, sigma=sig).mean()
            rows.append(dict(pathloss_exp=n_exp, shadow_sigma=sig, detect_1000m=far, detect_400m=near, false_alarm=fa))
    out = pd.DataFrame(rows); out.to_csv(f"{OUT}/exp9_pathloss_sweep.csv", index=False)
    return out


def plots(det, en, cap, sec):
    plt.rcParams.update({"font.size": 8, "figure.figsize": (3.4, 2.4)})
    fig, ax = plt.subplots(); ax.bar(det["config"], det["spurious_per_day"], yerr=det["spurious_ci"], capsize=2)
    ax.set_ylabel("Spurious events / day"); plt.xticks(rotation=25, ha="right"); fig.tight_layout(); fig.savefig(f"{OUT}/fig_spurious.png", dpi=300)
    fig, ax = plt.subplots(); ax.bar(det["config"], det["battery_days"])
    ax.set_ylabel("Battery life (days)"); plt.xticks(rotation=25, ha="right"); fig.tight_layout(); fig.savefig(f"{OUT}/fig_battery.png", dpi=300)
    fig, ax = plt.subplots()
    for sf, g in cap.groupby("sf"): ax.plot(g["n"], g["pdr"], label=f"SF{sf}")
    ax.set_xscale("log"); ax.set_xlabel("Students per gateway"); ax.set_ylabel("Packet delivery ratio"); ax.legend(ncol=2, fontsize=6)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_capacity.png", dpi=300)
    fig, ax = plt.subplots(); ax.semilogx(en["fixes"].map(lambda f: 86400 / f), en["life"], "o-", label="event-driven uplink")
    ax.semilogx(en["fixes"].map(lambda f: 86400 / f), en["life_raw"], "s--", label="raw streaming")
    ax.set_xlabel("Fixed GPS interval (s)"); ax.set_ylabel("Battery life (days)"); ax.legend(); fig.tight_layout(); fig.savefig(f"{OUT}/fig_energy_fixed.png", dpi=300)


if __name__ == "__main__":
    import os; os.makedirs(OUT, exist_ok=True)
    days = make_days(N)
    det = exp_detection(days); print(det.to_string())
    en = exp_energy(); print(en.to_string())
    best = det[det.config == "hyst+adaptive"].iloc[0]
    cap, capsum = exp_capacity(best["events_per_day"]); print(capsum.to_string())
    print(exp_privacy(best["fixes_per_day"], best["events_per_day"]).to_string())
    sec = exp_security(days[:30], np.random.default_rng(7)); print(sec.to_string())
    print(exp_sensitivity(max(N // 2, 20)).to_string())
    print(exp_calibrated_and_sweeps(max(N // 2, 20)).to_string())
    print(exp_pathloss_sweep(np.random.default_rng(11)).to_string())
    plots(det, en, cap, sec)
