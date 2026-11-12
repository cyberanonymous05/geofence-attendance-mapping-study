# Reproduce every number and table in the paper. Needs data/geolife and data/studentlife (see README.md).
# Runtimes on a laptop: tests 3 s; synthetic experiments ~10 min; GeoLife replays ~15 min; burst study ~5 min.
PY=python3

.PHONY: all test synthetic geolife burst tables check
all: test synthetic geolife burst tables check

test:
	$(PY) -m pytest -q

synthetic:
	$(PY) run_experiments.py
	$(PY) run_theory.py
	$(PY) run_pareto.py
	$(PY) make_pareto_fig.py
	$(PY) run_additions.py 16 18

geolife:
	$(PY) calibrate_gps.py
	$(PY) run_realtrace.py
	$(PY) run_realtrace_robust.py
	$(PY) run_extra.py
	$(PY) run_additions.py 17 23
	$(PY) make_trace_figure.py

burst:
	$(PY) run_burst.py 20 21 22 24 25 25b

tables:
	$(PY) make_tables.py

check:
	$(PY) check_paper_numbers.py
