# geosim
Run `python3 -m pytest -q` then `python3 run_experiments.py 100`. Outputs in `results/`. All results are simulated.
Parameter status (DATASHEET / ASSUMED / STANDARD) is in `geosim/params.py`; ASSUMED ones must be cited or swept in the paper.

Real data: download GeoLife 1.3 (Microsoft Research) into `data/geolife/`, then `python3 calibrate_gps.py` and `python3 run_realtrace.py`.
Tables: `python3 make_tables.py` writes `../paper/tables.tex`. Hardware: see `../hardware/PROTOCOL.md` and `ingest_hw.py`.

## Additional experiments (exp16-18)
`python3 run_additions.py [16|17|18]` runs the detector ablation (exp16), polygon fences on real GeoLife
pedestrian tracks (exp17, needs `data/geolife/`) and end-to-end attendance accuracy with a lossy uplink (exp18).
Then `python3 make_tables.py` and `python3 check_paper_numbers.py` regenerate and verify the paper tables.

## Novelty experiments (exp19-23)
- `python3 run_pareto.py` then `python3 make_pareto_fig.py`: hysteresis vs evidence-accumulation (CUSUM-style) Pareto study (exp19).
- `python3 run_burst.py [20|21|22]`: synchronised-crossing capacity with jitter/repetition (exp20), timing leakage (exp21),
  back-dated roll-call accuracy (exp22). Timetable parameters are ASSUMED.
- `python3 run_additions.py 23`: Pareto-suggested detector tuning on the full pipeline (exp23).

## Real crossing times and the burst model (exp24-25)
Data: StudentLife (CC BY 4.0), RData version at https://zenodo.org/records/3529253 (file `dataset_rds.zip`, 230 MB).
Unzip into `data/studentlife/` so that `data/studentlife/dataset_rds/sensing/wifi_location.Rds` exists (needs `pyreadr`).
- `python3 run_burst.py 24`: derive home departures/returns and run the trace-driven capacity study.
- `python3 run_burst.py 25 25b`: closed-form model vs Monte Carlo, worst case (all students cross at the same second), real vs uniform load.
