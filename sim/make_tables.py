"""Generate LaTeX tables from results/*.csv so the paper never contains hand-typed numbers."""
import pandas as pd
R = "results/"
d = pd.read_csv(R + "exp1_detection_main.csv")
names = {"plain+fixed5s": "Plain radius, fixed 5\\,s", "plain+adaptive": "Plain radius, adaptive",
         "hyst+fixed5s": "Hysteresis, fixed 5\\,s", "hyst+fixed30s": "Hysteresis, fixed 30\\,s", "hyst+fixed60s": "Hysteresis, fixed 60\\,s", "hyst+fixed300s": "Hysteresis, fixed 300\\,s", "hyst+adaptive": "\\textbf{Hysteresis, adaptive (proposed)}"}
o = []
o.append("\\begin{table*}[!t]\\centering\\caption{Detection quality, GPS cost and battery life over 100 simulated student-days (mean $\\pm$ 95\\% CI where shown). All values are simulated.}\\label{tab:detect}")
o.append("\\begin{tabular}{lrrrrrr}\\toprule")
o.append("Configuration & Fixes/day & Spurious/day & Missed/day & Mean delay (s) & Max delay (s) & Battery (days)\\\\\\midrule")
for _, r in d.iterrows():
    o.append(f"{names[r.config]} & {r.fixes_per_day:,.0f} & {r.spurious_per_day:.2f}$\\pm${r.spurious_ci:.2f} & {r.missed_per_day:.2f} & {r.delay_mean_s:.1f}$\\pm${r.delay_ci:.1f} & {r.delay_max_s:.0f} & {r.battery_days:.1f}\\\\")
o.append("\\bottomrule\\end{tabular}\\end{table*}")
c = pd.read_csv(R + "exp3_capacity_summary.csv")
o.append("\\begin{table}[!t]\\centering\\caption{Gateway capacity at 95\\% packet delivery (pure ALOHA, one channel, one SF, 10-byte payload).}\\label{tab:cap}")
o.append("\\begin{tabular}{rrrr}\\toprule SF & Airtime (ms) & Students/gateway & Duty cycle/node (\\%)\\\\\\midrule")
for _, r in c.iterrows():
    o.append(f"{int(r.sf)} & {r.toa_ms:.1f} & {int(r.students_per_gateway_pdr95):,} & {r.duty_cycle_pct_per_node:.4f}\\\\")
o.append("\\bottomrule\\end{tabular}\\end{table}")
p = pd.read_csv(R + "exp4_privacy.csv")
o.append("\\begin{table}[!t]\\centering\\caption{Uplink volume and location exposure per node per day.}\\label{tab:priv}")
o.append("\\begin{tabular}{lrr}\\toprule Scheme & Coordinate packets/day & Bytes/day\\\\\\midrule")
for _, r in p.iterrows():
    o.append(f"{r.scheme.replace('&','\\&')} & {r.coord_tx:,.0f} & {r.bytes_day:,.0f}\\\\")
o.append("\\bottomrule\\end{tabular}\\end{table}")
s = pd.read_csv(R + "exp5_security.csv")
rs = s[(s.test == "rssi_spoof") & (s.k == 2.0)]
o.append("\\begin{table}[!t]\\centering\\caption{Gateway RSSI-consistency check ($k=2$): detection of a node that claims to be inside the fence from true distance $d$. False-alarm rate for honest nodes: " + f"{rs.false_alarm.iloc[0]*100:.1f}" + "\\%.}\\label{tab:spoof}")
o.append("\\begin{tabular}{rr}\\toprule True distance (m) & Detection rate (\\%)\\\\\\midrule")
for _, r in rs.iterrows():
    o.append(f"{r.d_true_m:.0f} & {r.detect_rate*100:.1f}\\\\")
o.append("\\bottomrule\\end{tabular}\\end{table}")
st = s[s.test == "static_device"]
o.append("\\begin{table}[!t]\\centering\\caption{Static-device flag: false-alarm rate on honest simulated days (30 days).}\\label{tab:static}")
o.append("\\begin{tabular}{rr}\\toprule Window (h) & False alarms (\\%)\\\\\\midrule")
for _, r in st.iterrows():
    o.append(f"{r.window_h:.0f} & {r.false_alarm*100:.1f}\\\\")
o.append("\\bottomrule\\end{tabular}\\end{table}")
v = pd.read_csv(R + "exp6_sensitivity_sigma.csv")
o.append("\\begin{table}[!t]\\centering\\caption{Sensitivity to GPS error near the fence (degraded-zone $\\sigma$), 50 simulated days each.}\\label{tab:sens}\\footnotesize")
o.append("\\begin{tabular}{rlrrr}\\toprule $\\sigma$ (m) & Configuration & Spurious/day & Missed/day & Delay (s)\\\\\\midrule")
for _, r in v.iterrows():
    o.append(f"{r.sigma_deg:.0f} & {"Plain, fixed 5\\,s" if r.config.startswith("plain") else "Proposed"} & {r.spurious:.2f} & {r.missed:.2f} & {r.delay:.1f}\\\\")
o.append("\\bottomrule\\end{tabular}\\end{table}")

rt = pd.read_csv(R + "exp7_realtrace_geolife.csv")
rn = {"plain+fixed5s": "Plain, fixed 5\\,s", "plain+adaptive": "Plain, adaptive", "hyst+fixed5s": "Hyst., fixed 5\\,s",
      "hyst+fixed30s": "Hyst., fixed 30\\,s", "hyst+fixed60s": "Hyst., fixed 60\\,s", "hyst+adaptive": "\\textbf{Hyst., adaptive (proposed)}",
      "hyst25+adaptive": "Hyst.\\ $h{=}25$\\,m, adaptive"}
seg = int(rt.segments.iloc[0]); hrs = rt.track_hours.iloc[0]
o.append("\\begin{table*}[!t]\\centering\\caption{Replay of real GeoLife pedestrian tracks (" + str(seg) + " segments, " + f"{hrs:.0f}" + " track-hours). Real fixes are the measurements; ground truth is a smoothed-track proxy. Spurious events per track-hour with cluster-bootstrap (by user) 95\\% interval; missed fraction at $\\pm$10\\,m and $\\pm$20\\,m truth tolerance.}\\label{tab:real}")
o.append("\\begin{tabular}{lrrrrrr}\\toprule")
o.append("Configuration & Fixes/h & Spurious/h [95\\% CI] & Missed (10\\,m) & Missed (20\\,m) & Mean delay (s) & Battery (days)\\\\\\midrule")
for _, r in rt.iterrows():
    o.append(f"{rn[r.config]} & {r.fixes_per_hour:.0f} & {r.spurious_per_hour:.3f} [{r.spur_ci_lo:.3f}, {r.spur_ci_hi:.3f}] & {r.missed_frac*100:.1f}\\% & {r.missed_frac_tol20*100:.1f}\\% & {r.delay_mean_s:.1f} & {r.battery_days:.1f}\\\\")
o.append("\\bottomrule\\end{tabular}\\end{table*}")
cs = pd.read_csv(R + "exp8_calibrated_sweeps.csv")
o.append("\\begin{table}[!t]\\centering\\caption{One-at-a-time sweeps of GPS-error parameters (50 simulated days each). Spurious events per day for the plain test (fixed 5\\,s) and the proposed detector with $h{=}15$ and $25$\\,m (adaptive); mean delay of the proposed detector.}\\label{tab:sweeps}\\footnotesize\\setlength{\\tabcolsep}{2.5pt}")
o.append("\\begin{tabular}{lrrrrr}\\toprule Scenario & Plain & $h{=}15$ & $h{=}25$ & Delay 15 & Delay 25\\\\\\midrule")
for sc, g in cs.groupby("scenario", sort=False):
    g = g.set_index("config")
    nm = sc.replace("(assumed)", " (assumed)").replace("=", "{=}").replace("_", "\\_")
    o.append(f"{nm} & {g.loc['plain+fixed5s','spurious']:.1f} & {g.loc['hyst+adaptive','spurious']:.2f} & {g.loc['hyst25+adaptive','spurious']:.2f} & {g.loc['hyst+adaptive','delay']:.1f} & {g.loc['hyst25+adaptive','delay']:.1f}\\\\")
o.append("\\bottomrule\\end{tabular}\\end{table}")
pl = pd.read_csv(R + "exp9_pathloss_sweep.csv")
o.append("\\begin{table}[!t]\\centering\\caption{RSSI-check sensitivity to path-loss exponent $n$ and shadowing $\\sigma_s$ (dB), $k{=}2$. Detection of a spoofer at the stated true distance, and false alarms on honest nodes.}\\label{tab:plsweep}\\footnotesize\\setlength{\\tabcolsep}{3pt}")
o.append("\\begin{tabular}{rrrrr}\\toprule $n$ & $\\sigma_s$ & Det.\\ 1\\,km & Det.\\ 400\\,m & False al.\\\\\\midrule")
for _, r in pl.iterrows():
    o.append(f"{r.pathloss_exp:.1f} & {r.shadow_sigma:.0f} & {r.detect_1000m*100:.1f}\\% & {r.detect_400m*100:.1f}\\% & {r.false_alarm*100:.1f}\\%\\\\")
o.append("\\bottomrule\\end{tabular}\\end{table}")

bl = pd.read_csv(R + "exp10_baselines.csv")
bn = {"plain+fixed5s": "Plain radius", "movavg5+fixed5s": "Moving average (5 fixes)", "kalman+fixed5s": "Kalman filter (1-D, CV)",
      "hyst+fixed5s": "Hysteresis detector", "hyst+adaptive": "\\textbf{Hysteresis + adaptive}"}
o.append("\\begin{table}[!t]\\centering\\caption{Comparison with smoothing baselines (all fixed 5\\,s except the last row). Spurious events per day (simulation, 100 days) and per track-hour (GeoLife replay); $\\pm$ is the 95\\% interval.}\\label{tab:base}\\footnotesize\\setlength{\\tabcolsep}{2.5pt}")
o.append("\\begin{tabular}{lrrrr}\\toprule & \\multicolumn{2}{c}{Simulated (/day)} & \\multicolumn{2}{c}{GeoLife (/hour)}\\\\\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}Detector & Spurious & Delay (s) & Spurious & Delay (s)\\\\\\midrule")
for k in bn:
    a = bl[(bl.config == k) & (bl.data == "simulated")].iloc[0]; b = bl[(bl.config == k) & (bl.data == "GeoLife replay")].iloc[0]
    o.append(f"{bn[k]} & {a.spurious:.2f}$\\pm${a.spurious_ci:.2f} & {a.delay:.1f} & {b.spurious:.3f}$\\pm${b.spurious_ci:.3f} & {b.delay:.1f}\\\\")
o.append("\\bottomrule\\end{tabular}\\end{table}")
ft = pd.read_csv(R + "exp11_fixtime.csv").pivot(index="fix_time_s", columns="config", values="battery_days")
o.append("\\begin{table}[!t]\\centering\\caption{Modelled battery life (days) versus GPS time per fix. Short times need hot starts (retained ephemeris and backup power).}\\label{tab:fixtime}\\footnotesize\\setlength{\\tabcolsep}{3pt}")
o.append("\\begin{tabular}{rrrrr}\\toprule Fix time (s) & Fixed 5\\,s & Fixed 30\\,s & Fixed 60\\,s & Adaptive\\\\\\midrule")
for fs, r in ft.iterrows():
    o.append(f"{fs} & {r['hyst+fixed5s']:.1f} & {r['hyst+fixed30s']:.1f} & {r['hyst+fixed60s']:.1f} & \\textbf{{{r['hyst+adaptive']:.1f}}}\\\\")
o.append("\\bottomrule\\end{tabular}\\end{table}")
cc = pd.read_csv(R + "exp12_capacity_capture.csv")
o.append("\\begin{table}[!t]\\centering\\caption{Students per gateway at 95\\% delivery from Monte-Carlo simulation with distance-based SF assignment, by number of channels, with and without a 6\\,dB capture effect. Nodes uniform in a disc of radius 300\\,m or 1\\,km.}\\label{tab:capcap}\\footnotesize\\setlength{\\tabcolsep}{3pt}")
o.append("\\begin{tabular}{rrrr}\\toprule Disc (m) & Channels & No capture & Capture 6\\,dB\\\\\\midrule")
for (D, ch), g in cc.groupby(["disc_radius_m", "channels"]):
    g = g.set_index("model")
    o.append(f"{D:.0f} & {ch} & {g.loc['no capture','students_per_gateway']:,} & {g.loc['capture 6 dB','students_per_gateway']:,}\\\\")
o.append("\\bottomrule\\end{tabular}\\end{table}")

tv = pd.read_csv(R + "exp13_theory_validation.csv")
o.append("\\begin{table}[!t]\\centering\\caption{Analytic model versus Monte Carlo of the actual detector for a stationary student at offset $\\delta$ inside the fence ($\\Delta{=}5$\\,s, $k{=}2$, dwell 20\\,s). Toggles per hour; error is (MC $-$ analytic)/analytic.}\\label{tab:theory}\\footnotesize\\setlength{\\tabcolsep}{2.5pt}")
o.append("\\begin{tabular}{llrrrr}\\toprule Detector & $(\\sigma,T_c)$ & $\\delta$ or $h$ (m) & Analytic & Monte Carlo & Error (\\%)\\\\\\midrule")
for _, r in tv.iterrows():
    if r.detector == "plain":
        lab, par = "Plain", f"$\\delta{{=}}{r.delta:.0f}$"
    else:
        if r.h == 8.0: continue
        lab, par = "Hysteresis", f"$h{{=}}{r.h:.0f}$"
    o.append(f"{lab} & ({r.sigma:g}\\,m, {r.Tc:g}\\,s) & {par} & {r.analytic:.3g} & {r.monte_carlo:.3g} & {r.rel_err_pct:+.1f}\\\\")
o.append("\\bottomrule\\end{tabular}\\end{table}")
dr = pd.read_csv(R + "exp14_design_rule.csv")
o.append("\\begin{table}[!t]\\centering\\caption{Design rule: smallest hysteresis half-width $h^*$ (m) keeping the worst-case false-toggle rate of a stationary student at the fence below $\\epsilon{=}0.01$ per hour, for three dwell times, and the predicted delay of a 1.4\\,m/s walker at 20\\,s dwell.}\\label{tab:design}\\footnotesize\\setlength{\\tabcolsep}{3pt}")
o.append("\\begin{tabular}{rrrrrr}\\toprule $\\sigma$ (m) & $T_c$ (s) & $h^*$, 10\\,s & $h^*$, 20\\,s & $h^*$, 40\\,s & Delay (s)\\\\\\midrule")
for (sg, tc), g in dr[dr.eps_per_hour == 0.01].groupby(["sigma", "Tc"]):
    g = g.set_index("dwell")
    o.append(f"{sg:g} & {tc:g} & {g.loc[10.0,'h_star']:.1f} & {g.loc[20.0,'h_star']:.1f} & {g.loc[40.0,'h_star']:.1f} & {g.loc[20.0,'pred_delay_s']:.0f}\\\\")
o.append("\\bottomrule\\end{tabular}\\end{table}")

rb = pd.read_csv(R + "exp15_realtrace_robustness.csv")
o.append("\\begin{table}[!t]\\centering\\caption{Robustness of the GeoLife replay to fence radius $R$ and placement (fraction of the segment at which the fence is centred). Plain test (fixed 5\\,s) versus proposed scheme; the interval is a paired bootstrap 95\\% interval of the reduction in spurious events per track-hour, resampled by user.}\\label{tab:robust}\\footnotesize\\setlength{\\tabcolsep}{2pt}")
o.append("\\begin{tabular}{rrrrrrrr}\\toprule $R$ (m) & Place & Seg. & Plain/h & Prop./h & Red.\\ [95\\% CI] & Miss & Fixes\\\\\\midrule")
for _, r in rb.iterrows():
    o.append(f"{r.R:.0f} & {r.placement:.2f} & {r.segments:.0f} & {r.plain_spur_h:.3f} & {r.prop_spur_h:.3f} & {r.reduction_pct:.0f}\\% [{r.diff_ci_lo:.2f}, {r.diff_ci_hi:.2f}] & {r.missed_pct:.1f}\\% & {r.fix_reduction:.1f}$\\times$\\\\")
o.append("\\bottomrule\\end{tabular}\\end{table}")

ab = pd.read_csv(R + "exp16_ablation.csv")
o.append("\\begin{table}[!t]\\centering\\caption{Ablation of the detector components (100 simulated days, fixed sampling). Spurious events per day and mean delay; $h{=}15$\\,m, $k{=}2$, dwell 20\\,s where enabled.}\\label{tab:ablate}\\footnotesize\\setlength{\\tabcolsep}{2.5pt}")
o.append("\\begin{tabular}{lrrrr}\\toprule & \\multicolumn{2}{c}{Fixed 5\\,s} & \\multicolumn{2}{c}{Fixed 60\\,s}\\\\\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}Components & Spur./day & Delay (s) & Spur./day & Delay (s)\\\\\\midrule")
for nm in ab[ab.interval_s == 5].config:
    a = ab[(ab.interval_s == 5) & (ab.config == nm)].iloc[0]; b = ab[(ab.interval_s == 60) & (ab.config == nm)].iloc[0]
    o.append(f"{nm} & {a.spurious_per_day:.2f} & {a.delay_mean_s:.1f} & {b.spurious_per_day:.2f} & {b.delay_mean_s:.1f}\\\\")
o.append("\\bottomrule\\end{tabular}\\end{table}")
pg = pd.read_csv(R + "exp17_polygon.csv")
o.append("\\begin{table}[!t]\\centering\\caption{Polygon fences on real GeoLife pedestrian tracks (fence centred at 25\\% of each segment, nominal size matching $R{=}300$\\,m). Plain test (fixed 5\\,s) versus proposed scheme; interval is a paired cluster-bootstrap (by user) 95\\% interval of the reduction in spurious events per track-hour.}\\label{tab:poly}\\footnotesize\\setlength{\\tabcolsep}{2pt}")
o.append("\\begin{tabular}{lrrrrrr}\\toprule Fence & Seg. & Plain/h & Prop./h & Red.\\ [95\\% CI] & Miss & Fixes\\\\\\midrule")
for _, r in pg.iterrows():
    nm = {"circle R=300": "Circle", "rectangle 600x400": "Rect.\\ 600$\\times$400", "L-shape 700 (notch 350)": "L-shape 700"}[r.fence]
    o.append(f"{nm} & {r.segments:.0f} & {r.plain_spur_h:.3f} & {r.prop_spur_h:.3f} & {r.reduction_pct:.0f}\\% [{r.diff_ci_lo:.2f}, {r.diff_ci_hi:.2f}] & {r.missed_pct:.1f}\\% & {r.fix_reduction:.1f}$\\times$\\\\")
o.append("\\bottomrule\\end{tabular}\\end{table}")
aa = pd.read_csv(R + "exp18_attendance_accuracy.csv")
def g(cfg, pdr, hb): return aa[(aa.config == cfg) & (aa.pdr == pdr) & (aa.heartbeat_s == hb)].iloc[0].acc_tol_pct
o.append("\\begin{table}[!t]\\centering\\caption{Attendance accuracy: percentage of random roll-call instants at which the server state matches the true state (instants within 20\\,m of the fence are not counted as errors), versus packet delivery ratio and heartbeat period (100 simulated days). Plain = plain test, fixed 5\\,s, 1\\,h heartbeat; the other columns are the proposed scheme.}\\label{tab:attend}\\footnotesize\\setlength{\\tabcolsep}{3pt}")
o.append("\\begin{tabular}{rrrrr}\\toprule PDR & Plain & Prop., no hb. & Prop., 1\\,h hb. & Prop., 15\\,min hb.\\\\\\midrule")
for pdr in (1.0, 0.95, 0.9, 0.8):
    o.append(f"{pdr:.2f} & {g('plain+fixed5s', pdr, 3600):.1f} & {g('hyst+adaptive', pdr, 0):.1f} & {g('hyst+adaptive', pdr, 3600):.1f} & {g('hyst+adaptive', pdr, 900):.1f}\\\\")
o.append("\\bottomrule\\end{tabular}\\end{table}")

bc = pd.read_csv(R + "exp20_burst_capacity_summary.csv")
def cap_cell(v):
    if pd.isna(v): return "$<$250"
    if v >= 6999: return "$>$7{,}000"
    return f"{v:,.0f}".replace(",", "{,}")
o.append("\\begin{table}[!t]\\centering\\caption{Students per gateway sustained at 95\\% event delivery when crossings are synchronised (Gaussian spread $\\sigma_w$ around four daily class-change times; 3 channels, distance-based SF, 6\\,dB capture). Columns: no jitter, uniform jitter up to 60 or 240\\,s, and 240\\,s jitter with one blind repetition.}\\label{tab:burst}\\footnotesize\\setlength{\\tabcolsep}{3pt}")
o.append("\\begin{tabular}{rrrrr}\\toprule $\\sigma_w$ (s) & No jitter & 60\\,s & 240\\,s & 240\\,s + repeat\\\\\\midrule")
for sw, g in bc.groupby("sigma_w_s"):
    g = g.set_index(["jitter_s", "repeats"]).students_at_95pct
    o.append(f"{sw:.0f} & {cap_cell(g[(0,1)])} & {cap_cell(g[(60,1)])} & {cap_cell(g[(240,1)])} & {cap_cell(g[(240,2)])}\\\\")
o.append("\\bottomrule\\end{tabular}\\end{table}")
tl = pd.read_csv(R + "exp21_timing_leakage.csv")
o.append("\\begin{table}[!t]\\centering\\caption{Timing leakage to a passive eavesdropper who sees packet times but not payloads: error of the best fixed-offset estimate of each crossing time, over 100 simulated days (947 matched crossings).}\\label{tab:leak}\\footnotesize\\setlength{\\tabcolsep}{3pt}")
o.append("\\begin{tabular}{lrrr}\\toprule Uplink & Median err.\\ (s) & 90th pct.\\ (s) & Within 60\\,s\\\\\\midrule")
for _, r in tl.iterrows():
    nm = r.scheme.replace("event-driven, no jitter", "Event-driven, no jitter").replace("event-driven, jitter U(0,", "Event-driven, jitter U(0,").replace(" s)", "\\,s)").replace("heartbeat only, period ", "Heartbeat only, period ").replace(" s", "\\,s")
    o.append(f"{nm} & {r.median_err_s:.0f} & {r.p90_err_s:.0f} & {r.within60_pct:.0f}\\%\\\\")
o.append("\\bottomrule\\end{tabular}\\end{table}")
bd = pd.read_csv(R + "exp22_backdating_accuracy.csv")
o.append("\\begin{table}[!t]\\centering\\caption{Roll-call accuracy (\\% of random instants; ``Tol.'' ignores instants within 20\\,m of the fence) with the server timeline built from arrival times (real time) or from back-dated times (age field), 15\\,min heartbeat, 100 simulated days.}\\label{tab:backdate}\\footnotesize\\setlength{\\tabcolsep}{3pt}")
o.append("\\begin{tabular}{rrrrrr}\\toprule Jitter (s) & PDR & \\multicolumn{2}{c}{Real time} & \\multicolumn{2}{c}{Back-dated}\\\\\\cmidrule(lr){3-4}\\cmidrule(lr){5-6} & & Strict & Tol. & Strict & Tol.\\\\\\midrule")
for (J, pdr), g in bd.groupby(["jitter_s", "pdr"]):
    a = g[g["mode"] == "real-time"].iloc[0]; b = g[g["mode"] == "back-dated"].iloc[0]
    o.append(f"{J:.0f} & {pdr:.2f} & {a.acc_strict_pct:.2f} & {a.acc_tol_pct:.2f} & {b.acc_strict_pct:.2f} & {b.acc_tol_pct:.2f}\\\\")
o.append("\\bottomrule\\end{tabular}\\end{table}")

rs = pd.read_csv(R + "exp24_real_burst_stats.csv").set_index("pool")
rc = pd.read_csv(R + "exp24_real_burst_capacity.csv")
def rcap(pool, J, rep):
    v = rc[(rc.pool == pool) & (rc.jitter_s == J) & (rc.repeats == rep)].students_at_95pct.iloc[0]
    return "$>$10{,}000" if v >= 9999 else f"{v:,.0f}".replace(",", "{,}")
o.append("\\begin{table}[!t]\\centering\\caption{Real crossing times (StudentLife, 40 students with an inferred home building, weekdays): events per student-day, share of students with an event in the busiest minute, and students per gateway at 95\\% event delivery from Monte Carlo (3 channels, 6\\,dB capture; 240\\,s jitter, and jitter plus one repetition). Crossing times are resampled from real student-days.}\\label{tab:realburst}\\footnotesize\\setlength{\\tabcolsep}{2.5pt}")
o.append("\\begin{tabular}{lrrrrr}\\toprule Pool (days) & Ev./day & Busiest min. & No jitter & 240\\,s & +rep.\\\\\\midrule")
for pn in ("all weekdays", "Mon/Wed/Fri", "Tue/Thu"):
    r = rs.loc[pn]
    o.append(f"{pn} ({int(r.student_days):,}) & {r.events_per_day:.1f} & {100*r.peak_minute_events_per_student:.1f}\\% & {rcap(pn,0,1)} & {rcap(pn,240,1)} & {rcap(pn,240,2)}\\\\")
o.append("\\bottomrule\\end{tabular}\\end{table}")
bv = pd.read_csv(R + "exp25_burst_model_validation.csv")
o.append("\\begin{table}[!t]\\centering\\caption{Closed-form delivery model versus Monte Carlo: absolute difference in event delivery (percentage points) over populations of 1{,}000--8{,}000 students. Single = jitter 0 or 240\\,s without repetition; repeat = 240\\,s with one blind repetition.}\\label{tab:burstmodel}\\footnotesize\\setlength{\\tabcolsep}{3pt}")
o.append("\\begin{tabular}{lrrrr}\\toprule & \\multicolumn{2}{c}{Single} & \\multicolumn{2}{c}{Repeat}\\\\\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}Load profile & Mean & Max & Mean & Max\\\\\\midrule")
for pn, g in bv.groupby("profile", sort=False):
    a = g[g.repeats == 1].abs_err_pts; b = g[g.repeats == 2].abs_err_pts
    o.append(f"{pn} & {a.mean():.2f} & {a.max():.2f} & {b.mean():.2f} & {b.max():.2f}\\\\")
a = bv[bv.repeats == 1].abs_err_pts; b = bv[bv.repeats == 2].abs_err_pts
o.append(f"\\midrule All & {a.mean():.2f} & {a.max():.2f} & {b.mean():.2f} & {b.max():.2f}\\\\")
o.append("\\bottomrule\\end{tabular}\\end{table}")
wc = pd.read_csv(R + "exp25_worst_case.csv")
o.append("\\begin{table}[!t]\\centering\\caption{Worst case: every student crosses at the same second at each of four daily bells (no timetable assumption). Students per gateway at 95\\% event delivery from the closed-form model, and Monte-Carlo delivery at that population.}\\label{tab:worst}\\footnotesize\\setlength{\\tabcolsep}{3pt}")
o.append("\\begin{tabular}{rrrr}\\toprule Jitter (s) & Repeats & Capacity (model) & MC delivery there\\\\\\midrule")
for _, r in wc.iterrows():
    o.append(f"{r.jitter_s:.0f} & {int(r.repeats)} & {int(r.capacity_model):,} & {100*r.mc_delivery_at_1x:.1f}\\%\\\\".replace(",", "{,}"))
o.append("\\bottomrule\\end{tabular}\\end{table}")
open("../paper/tables.tex", "w").write("\n".join(o) + "\n")
print("ok")
