"""Verify numbers quoted in paper/main.tex against results/*.csv. Exits non-zero on any mismatch."""
import json, sys
import pandas as pd
R = "results/"; tex = open("../paper/main.tex").read()
d = pd.read_csv(R + "exp1_detection_main.csv").set_index("config")
rt = pd.read_csv(R + "exp7_realtrace_geolife.csv").set_index("config")
bl = pd.read_csv(R + "exp10_baselines.csv")
ft = pd.read_csv(R + "exp11_fixtime.csv")
cc = pd.read_csv(R + "exp12_capacity_capture.csv")
cap = pd.read_csv(R + "exp3_capacity_summary.csv").set_index("sf")
cal = json.load(open(R + "gps_calibration_geolife.json"))
pv = pd.read_csv(R + "exp4_privacy.csv")
checks = [
 (f"{d.loc['plain+fixed5s','spurious_per_day']:.1f}", "plain spurious/day"),
 (f"{d.loc['hyst+adaptive','spurious_per_day']:.2f}", "proposed spurious/day"),
 (f"{d.loc['plain+fixed5s','fixes_per_day']/d.loc['hyst+adaptive','fixes_per_day']:.1f}", "fix reduction x"),
 (f"{d.loc['hyst+adaptive','battery_days']:.1f}", "battery adaptive"),
 (f"{d.loc['plain+fixed5s','battery_days']:.1f}", "battery fixed5"),
 (f"{rt.loc['plain+fixed5s','spurious_per_hour']:.3f}", "real plain spurious/h"),
 (f"{rt.loc['hyst+adaptive','spurious_per_hour']:.3f}", "real proposed spurious/h"),
 (f"{rt.loc['hyst+adaptive','missed_frac']*100:.1f}", "real missed %"),
 (f"{rt.loc['plain+fixed5s','fixes_per_hour']/rt.loc['hyst+adaptive','fixes_per_hour']:.1f}", "real fix reduction"),
 (f"{rt.loc['hyst+adaptive','battery_days']:.1f}", "real battery adaptive"),
 (f"{cal['sigma_per_axis_median']:.1f}", "calibrated sigma"),
 (f"{bl[(bl.config=='movavg5+fixed5s')&(bl.data=='simulated')].spurious.iloc[0]:.1f}", "movavg sim"),
 (f"{bl[(bl.config=='kalman+fixed5s')&(bl.data=='simulated')].spurious.iloc[0]:.1f}", "kalman sim"),
 (f"{ft[(ft.fix_time_s==15)&(ft.config=='hyst+adaptive')].battery_days.iloc[0]:.1f}", "adaptive @15 s fix"),
 (f"{cc[(cc.disc_radius_m==300)&(cc.channels==1)&(cc.model=='capture 6 dB')].students_per_gateway.iloc[0]:,}".replace(",", "{,}"), "capture 1ch"),
 (f"{cc[(cc.disc_radius_m==300)&(cc.channels==8)&(cc.model=='capture 6 dB')].students_per_gateway.iloc[0]:,}".replace(",", "{,}"), "capture 8ch"),
 (f"{int(cap.loc[7,'students_per_gateway_pdr95']):,}".replace(",", "{,}"), "ALOHA SF7 capacity"),
 (f"{pv.bytes_day.iloc[1]:.0f}", "bytes/day proposed"),
]
ab = pd.read_csv(R + "exp16_ablation.csv"); a5 = ab[ab.interval_s == 5].set_index("config")
pg = pd.read_csv(R + "exp17_polygon.csv")
aa = pd.read_csv(R + "exp18_attendance_accuracy.csv")
def acc(cfg, pdr, hb, col): return aa[(aa.config == cfg) & (aa.pdr == pdr) & (aa.heartbeat_s == hb)][col].iloc[0]
checks += [
 (f"{a5.loc['hysteresis band only','spurious_per_day']:.1f}", "ablation band only"),
 (f"{a5.loc['dwell only (20 s)','spurious_per_day']:.1f}", "ablation dwell only"),
 (f"{a5.loc['band + dwell','spurious_per_day']:.2f}", "ablation band+dwell"),
 (f"{a5.loc['none (plain radius)','spurious_per_day']-a5.loc['plausibility filter','spurious_per_day']:.1f}", "filter effect"),
 (f"{pg.missed_pct.min():.1f}", "polygon missed min"), (f"{pg.missed_pct.max():.1f}", "polygon missed max"),
 (f"{pg.fix_reduction.min():.1f}", "polygon fix min"), (f"{pg.fix_reduction.max():.1f}", "polygon fix max"),
 (f"{acc('hyst+adaptive',1.0,3600,'acc_strict_pct'):.1f}", "attend strict proposed"),
 (f"{acc('hyst+adaptive',1.0,3600,'acc_tol_pct'):.1f}", "attend tol proposed"),
 (f"{acc('plain+fixed5s',1.0,3600,'acc_strict_pct'):.1f}", "attend strict plain"),
 (f"{acc('hyst+adaptive',0.9,0,'acc_tol_pct'):.1f}", "attend pdr.9 no hb"),
 (f"{acc('hyst+adaptive',0.9,3600,'acc_tol_pct'):.1f}", "attend pdr.9 1h"),
 (f"{acc('hyst+adaptive',0.9,900,'acc_tol_pct'):.1f}", "attend pdr.9 15m"),
 (f"{acc('hyst+adaptive',0.95,900,'acc_tol_pct'):.1f}", "attend pdr.95 15m"),
]
bs = pd.read_csv(R + "exp20_burst_capacity_summary.csv").set_index(["sigma_w_s", "jitter_s", "repeats"]).students_at_95pct
tl = pd.read_csv(R + "exp21_timing_leakage.csv").set_index("scheme")
bd = pd.read_csv(R + "exp22_backdating_accuracy.csv")
te = pd.read_csv(R + "exp22_backdating_timestamp_error.csv").iloc[0]
tu = pd.read_csv(R + "exp23_tuned_default.csv")
def bda(J, pdr, mode, col): return bd[(bd.jitter_s == J) & (bd.pdr == pdr) & (bd["mode"] == mode)][col].iloc[0]
def tun(data, cfg, col): return tu[(tu.data.str.startswith(data)) & (tu.config.str.startswith(cfg))][col].iloc[0]
fm = lambda v: f"{v:,.0f}".replace(",", "{,}")
checks += [
 (f"{round(bs[(30,0,1)],-1):.0f}", "burst cap 30s ~480"), (fm(round(bs[(30,240,1)],-2)), "burst cap 30s J240 ~1100"),
 
 (fm(round(bs[(300,0,1)],-3)), "burst cap 300s ~3000"), (f"{round(bs[(60,0,1)],-2):.0f}", "burst cap 60s ~900"), (fm(bs[(300,240,1)]), "burst cap 300s J240"),
 (f"{bs[(300,0,1)]/bs[(30,0,1)]:.0f}", "burst ratio 6x"),
 (f"{bs[(30,240,1)]/bs[(30,0,1)]:.1f}", "jitter gain 2.3x"),
 (f"{tl.loc['event-driven, no jitter','median_err_s']:.0f}", "leak median no jitter"),
 (f"{tl.loc['event-driven, jitter U(0,240 s)','median_err_s']:.0f}", "leak median J240"),
 (f"{tl.loc['event-driven, jitter U(0,240 s)','within60_pct']:.0f}", "leak within60 J240"),
 (f"{tl.loc['heartbeat only, period 900 s','median_err_s']:.0f}", "leak heartbeat 900"),
 (f"{bda(0,1.0,'real-time','acc_tol_pct'):.2f}", "rt tol J0"), (f"{bda(240,1.0,'real-time','acc_tol_pct'):.2f}", "rt tol J240"),
 (f"{bda(0,1.0,'real-time','acc_strict_pct'):.2f}", "rt strict J0"), (f"{bda(240,1.0,'real-time','acc_strict_pct'):.2f}", "rt strict J240"),
 (f"{bda(240,1.0,'back-dated','acc_tol_pct'):.2f}", "bd tol"), (f"{bda(240,1.0,'back-dated','acc_strict_pct'):.2f}", "bd strict"),
 (f"{te.mae_s:.1f}", "backdate MAE"), (f"{te.median_err_s:.1f}", "backdate median"), (f"{te.p90_abs_s:.1f}", "backdate p90"),
 (f"{tun('simulated','default','spurious'):.2f}", "tuned sim default spur"), (f"{tun('simulated','tuned (h=25','spurious'):.2f}", "tuned sim spur"),
 (f"{tun('simulated','default','delay'):.1f}", "tuned sim default delay"), (f"{tun('simulated','tuned (h=25','delay'):.1f}", "tuned sim delay"),
 (f"{tun('GeoLife','default','delay'):.1f}", "tuned real default delay"), (f"{tun('GeoLife','tuned (h=25','delay'):.1f}", "tuned real delay"),
 (f"{tun('GeoLife','tuned (h=25','missed'):.1f}", "tuned real missed"), (f"{tun('GeoLife','default','missed'):.1f}", "default real missed"),
]
pa = pd.read_csv(R + "exp19_detector_pareto.csv"); pa = pa[(pa.miss < 0.05) & (pa.sigma == 5.3)]
checks += [(f"{pa[(pa.family=='excess')&(pa.false_per_h<=0.01)].delay_mean.min():.1f}", "pareto excess 0.01"),
           (f"{pa[(pa.family=='hyst')&(pa.false_per_h<=0.01)].delay_mean.min():.1f}", "pareto hyst 0.01")]
rsb = pd.read_csv(R + "exp24_real_burst_stats.csv").set_index("pool")
rcap = pd.read_csv(R + "exp24_real_burst_capacity.csv")
bv = pd.read_csv(R + "exp25_burst_model_validation.csv")
wc = pd.read_csv(R + "exp25_worst_case.csv").set_index(["jitter_s", "repeats"])
ru = pd.read_csv(R + "exp25_real_vs_uniform.csv").set_index("profile")
rps = pd.read_csv(R + "exp25_real_profile_stats.csv").iloc[0]
w2 = pd.read_csv(R + "exp25_worst_case_rep2_cap.csv").iloc[0]
def rc_(pool, J, rep): return rcap[(rcap.pool == pool) & (rcap.jitter_s == J) & (rcap.repeats == rep)].students_at_95pct.iloc[0]
checks += [
 (f"{100*rsb.loc['all weekdays','peak_minute_events_per_student']:.1f}", "real peak-minute % students"),
 (f"{100*rsb.loc['Mon/Wed/Fri','peak_minute_events_per_student']:.1f}", "real peak-minute MWF"),
 (f"{rps.peak_to_mean_per_minute:.1f}", "peak-to-mean"),
 (fm(round(rc_("all weekdays",0,1),-2)), "real cap J0"), (fm(rc_("all weekdays",240,1)), "real cap J240"),
 (fm(round(ru.loc["uniform in time","capacity_J0"],-2)), "uniform cap"),
 (f"{100*(1-ru.loc['real profile','capacity_J0']/ru.loc['uniform in time','capacity_J0']):.0f}", "real vs uniform %"),
 (f"{bv[bv.repeats==1].abs_err_pts.mean():.2f}", "model err mean"), (f"{bv[bv.repeats==1].abs_err_pts.max():.2f}", "model err max"),
 (f"{bv[bv.repeats==2].abs_err_pts.mean():.1f}", "model err rep mean"), (f"{bv[bv.repeats==2].abs_err_pts.max():.1f}", "model err rep max"),
 (str(int(wc.loc[(60,1),"capacity_model"])), "worst 60"), (str(int(wc.loc[(120,1),"capacity_model"])), "worst 120"),
 (str(int(wc.loc[(240,1),"capacity_model"])), "worst 240"), (fm(wc.loc[(240,2),"capacity_model"]), "worst 240 rep model"),
 (fm(round(w2.mc_capacity_rep2_worst, -2)), "worst rep MC"),
]
bad = 0
for val, what in checks:
    ok = val in tex
    print(("OK  " if ok else "MISS"), what, val)
    bad += not ok
sys.exit(1 if bad else 0)
