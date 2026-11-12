"""Software defences for the spoofing / lost-device limitations.

1. RSSI-range consistency (gateway-side): a node claiming to be inside the fence whose RSSI
   implies it is far away is flagged. Log-distance path loss + log-normal shadowing (ASSUMED params).
2. Static-device flag: displacement below `min_move_m` over window W => device probably left behind.
"""
import numpy as np

PTX_DBM = 14.0
PL_D0_DB = 31.5      # free-space loss at 1 m, 868 MHz
PATHLOSS_EXP = 2.9   # ASSUMED campus value, swept in paper
SHADOW_SIGMA_DB = 6.0


def rssi(rng, d_m, n=PATHLOSS_EXP, sigma=SHADOW_SIGMA_DB):
    d = np.maximum(d_m, 1.0)
    return PTX_DBM - PL_D0_DB - 10 * n * np.log10(d) + rng.normal(0, sigma, np.shape(d))


def rssi_flag(rng, d_true, d_claimed, k=2.0, n=PATHLOSS_EXP, sigma=SHADOW_SIGMA_DB):
    """True where observed RSSI deviates > k*sigma from expectation at the claimed distance."""
    obs = rssi(rng, d_true, n, sigma)
    exp = PTX_DBM - PL_D0_DB - 10 * n * np.log10(np.maximum(d_claimed, 1.0))
    return np.abs(obs - exp) > k * sigma


def static_flag(x, y, window_s, min_move_m=10.0):
    """True if the device moved less than min_move_m over any window of window_s seconds."""
    step = 600
    idx = np.arange(0, len(x) - window_s, step)
    for i in idx:
        xs, ys = x[i:i + window_s:60], y[i:i + window_s:60]
        if np.hypot(xs.max() - xs.min(), ys.max() - ys.min()) < min_move_m:
            return True
    return False
