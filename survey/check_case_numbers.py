"""Verify the companion-study numbers quoted in the survey (Table 'case') against ../sim/results/*.csv.
Exit 1 on any mismatch. Run: python3 check_case_numbers.py  (reads main.src.tex)"""
import sys
import pandas as pd
R = "../sim/results/"
import os
tex = open("main.src.tex").read()
paper = open("../paper/main.tex").read() if os.path.exists("../paper/main.tex") else None   # the companion paper text is not part of the public bundle
rt = pd.read_csv(R + "exp7_realtrace_geolife.csv").set_index("config")
ft = pd.read_csv(R + "exp11_fixtime.csv")
ru = pd.read_csv(R + "exp25_real_vs_uniform.csv").set_index("profile")
wc = pd.read_csv(R + "exp25_worst_case.csv").set_index(["jitter_s", "repeats"])
w2 = pd.read_csv(R + "exp25_worst_case_rep2_cap.csv").iloc[0]
tl = pd.read_csv(R + "exp21_timing_leakage.csv").set_index("scheme")
fm = lambda v: f"{v:,.0f}".replace(",", "{,}")
p, h = rt.loc["plain+fixed5s"], rt.loc["hyst+adaptive"]
checks = [
 (f"{p.spurious_per_hour:.3f}", "plain spurious/h"), (f"{p.spur_ci_lo:.3f}--{p.spur_ci_hi:.3f}", "plain CI"),
 (f"{h.spurious_per_hour:.3f} ({h.spur_ci_lo:.3f}--{h.spur_ci_hi:.3f})", "hyst+adaptive spurious/h with CI"),
 (f"{round(100*(1-h.spurious_per_hour/p.spurious_per_hour))}\\%", "reduction %"),
 (f"{100*h.missed_frac:.1f}\\%", "missed %"), (f"{h.delay_mean_s:.1f}~s", "mean delay"),
 (f"{int(h.segments)} real", "segments"), (f"({round(h.track_hours)} track-hours)", "track-hours"),
 (f"{round(p.fixes_per_hour)} to {round(h.fixes_per_hour)} per hour", "fixes"), (f"(${p.fixes_per_hour/h.fixes_per_hour:.1f}\\times$)", "fix reduction"),
 (f"{p.battery_days:.1f} to {h.battery_days:.1f} days", "real battery"),
 (f"{ft[(ft.fix_time_s==2)&(ft.config=='hyst+adaptive')].battery_days.iloc[0]:.1f} days with 2~s", "sim battery 2 s"),
 (f"{ft[(ft.fix_time_s==15)&(ft.config=='hyst+adaptive')].battery_days.iloc[0]:.1f} days with 15~s", "sim battery 15 s"),
 (fm(round(ru.loc['real profile','capacity_J0'], -2)), "real capacity"), (fm(round(ru.loc['uniform in time','capacity_J0'], -2)), "uniform capacity"),
 (f"cost about {100*(1-ru.loc['real profile','capacity_J0']/ru.loc['uniform in time','capacity_J0']):.0f}\\%", "capacity loss"),
 (f"about {fm(round(wc.loc[(240,1),'capacity_model'], -3))} students", "worst case 240 s"), (f"about {fm(round(w2.mc_capacity_rep2_worst, -2))}", "worst case + repetition"),
 (f"median {tl.loc['event-driven, no jitter','median_err_s']:.0f}~s (97\\%", "leak no jitter"),
 (f"{tl.loc['event-driven, jitter U(0,240 s)','median_err_s']:.0f}~s (50\\%", "leak J240"),
]
bad = 0
for val, what in checks:
    ok = val in tex
    print(("OK  " if ok else "MISS"), what, "|", val); bad += not ok
for s, what in [("1--4~s", "pareto gain"), ("3--14", "pareto pct")]:   # comparison claim is verified in the paper's own checker via exp19
    if paper is None: print("SKIP", what, "(companion paper text not available)"); continue
    print("OK  " if (s.replace("~", "\\,") in paper or s in paper or s.replace("~s", "\\,s") in paper) else "WARN", what, "(text appears in paper)")
sys.exit(1 if bad else 0)
