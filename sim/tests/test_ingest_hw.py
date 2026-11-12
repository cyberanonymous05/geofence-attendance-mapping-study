import numpy as np, pandas as pd
from ingest_hw import fit_pathloss, summarise_energy


def test_pathloss_fit_recovers_parameters():
    # synthetic TEST FIXTURE generated from a known model; not measurement data
    rng = np.random.default_rng(0)
    d = np.repeat([100, 200, 400, 800, 1600], 400).astype(float)
    rssi = 14 - 31.5 - 10 * 3.1 * np.log10(d) + rng.normal(0, 5, len(d))
    n, s = fit_pathloss(pd.DataFrame(dict(distance_m=d, rssi_dbm=rssi)))
    assert abs(n - 3.1) < 0.05 and abs(s - 5) < 0.4


def test_energy_summary():
    df = pd.DataFrame(dict(measure=["sleep"] * 3, run=[1, 2, 3], duration_s=[600] * 3, mean_current_a=[1e-5, 2e-5, 3e-5]))
    assert abs(summarise_energy(df)["sleep"]["mean_current_a"] - 2e-5) < 1e-12
