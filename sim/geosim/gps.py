"""GPS error model: AR(1) correlated Gaussian error with position-dependent sigma + rare outliers.

Parameters are ASSUMED (see params.py) and must be cited or swept in the paper.
"""
import numpy as np
from scipy.signal import lfilter
from . import params as P


def gps_error(rng, x, y, R=P.FENCE_RADIUS_M, degraded_band_m=30.0):
    T = len(x)
    phi = np.exp(-1.0 / P.GPS_CORR_TAU_S)
    gain = np.sqrt(1 - phi ** 2)
    r = np.hypot(x, y)
    sigma = np.where(np.abs(r - R) < degraded_band_m, P.GPS_SIGMA_DEGRADED_M, P.GPS_SIGMA_OPEN_M)
    out = []
    for _ in range(2):
        unit = lfilter([gain], [1, -phi], rng.standard_normal(T))
        e = sigma * unit
        mask = rng.random(T) < P.GPS_OUTLIER_P
        e = e + mask * rng.normal(0, P.GPS_OUTLIER_SIGMA_M, T)
        out.append(e)
    return out[0], out[1]
