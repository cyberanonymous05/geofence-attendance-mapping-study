"""Summarise hardware measurements into parameter values and a path-loss fit. Usage: python3 ingest_hw.py energy.csv lora.csv
energy.csv: measure,run,duration_s,mean_current_a   (measure in sleep|gps_hot|gps_cold|lora_tx_sf7|lora_tx_sf10)
lora.csv:   distance_m,sf,sent,received,rssi_dbm
"""
import sys
import numpy as np
import pandas as pd


def summarise_energy(df):
    out = {}
    for m, g in df.groupby("measure"):
        out[m] = dict(n=len(g), mean_current_a=g.mean_current_a.mean(), sd_current_a=g.mean_current_a.std(ddof=1),
                      mean_duration_s=g.duration_s.mean())
    return out


def fit_pathloss(df, ptx_dbm=14.0, pl_d0_db=31.5):
    """Least-squares fit of RSSI = Ptx - PL0 - 10 n log10(d) ; returns n and residual sigma (shadowing)."""
    d = df.distance_m.to_numpy(float)
    y = df.rssi_dbm.to_numpy(float)
    X = -10 * np.log10(d)
    n = float(np.sum(X * (y - ptx_dbm + pl_d0_db)) / np.sum(X * X))
    resid = y - (ptx_dbm - pl_d0_db + n * X)
    return n, float(resid.std(ddof=1))


if __name__ == "__main__":
    e = pd.read_csv(sys.argv[1]); l = pd.read_csv(sys.argv[2])
    for k, v in summarise_energy(e).items():
        print(k, v)
    lo = l.assign(pdr=l.received / l.sent)
    print(lo.groupby(["sf", "distance_m"]).pdr.mean().unstack(0).to_string())
    n, sig = fit_pathloss(l)
    print(f"path-loss exponent n={n:.2f}, shadowing sigma={sig:.1f} dB")
