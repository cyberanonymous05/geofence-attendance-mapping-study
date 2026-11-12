"""Analytical model of boundary flapping for a stationary student near the fence.

GPS error e_k is a stationary Gaussian AR(1) sequence sampled every dt seconds with std sigma and
correlation phi = exp(-dt/Tc). A student at offset delta inside the fence (true distance R - delta) gives
measured d_k - R = -delta + e_k.

Plain radius test: toggles when sign(e_k - delta) changes between fixes.
    P(toggle per fix) = 2 * P(e_0 <= a, e_1 > a),  a = delta / sigma.
Hysteresis (threshold h, k fixes, dwell T): a false exit is confirmed by a run of m consecutive fixes with
e > delta + h, m = max(k, ceil(T/dt) + 1). Run starts per fix = P(e_0 <= c, e_1..e_m > c), c = (delta+h)/sigma.
False entry (after a false exit) is the mirror event with c' = (h - delta)/sigma. The detector alternates between
two states, so toggles/hour = 2 / (1/lam_x + 1/lam_e), with lam = fixes/hour * run-start probability.
Orthant probabilities are computed exactly (to quadrature accuracy) with the AR(1) Markov structure.
Assumptions: stationary student, no outliers, no plausibility filter, constant dt.
"""
import math
import numpy as np
from scipy.stats import norm


def run_start_prob(c, m, phi, n=1500, span=9.0):
    """P(e_0 <= c, e_1 > c, ..., e_m > c) for a standard-normal AR(1) sequence with correlation phi."""
    if phi <= 0:
        return norm.cdf(c) * (norm.sf(c)) ** m
    s = math.sqrt(1 - phi ** 2)
    dlo = (c + span) / n
    dhi = span / n
    lo = c - (np.arange(n) + 0.5) * dlo            # cell centres, grid for e_0 <= c
    hi = c + (np.arange(n) + 0.5) * dhi            # cell centres, grid for e_j > c
    f0 = norm.pdf(lo) * dlo                        # weights of e_0
    # transition kernels
    K0 = norm.pdf((hi[None, :] - phi * lo[:, None]) / s) / s       # lo -> hi
    f = (f0[:, None] * K0).sum(axis=0) * dhi                       # density mass on e_1 grid (weights)
    f = f  # f[j] = P(e_0<=c, e_1 in dy_j)
    if m == 1:
        return float(f.sum())
    K = norm.pdf((hi[None, :] - phi * hi[:, None]) / s) / s        # hi -> hi
    for _ in range(m - 1):
        f = (f[:, None] * K).sum(axis=0) * dhi
    return float(f.sum())


def plain_toggles_per_hour(delta, sigma, Tc, dt):
    phi = math.exp(-dt / Tc)
    return 3600.0 / dt * 2.0 * run_start_prob(delta / sigma, 1, phi)


def hyst_toggles_per_hour(delta, h, sigma, Tc, dt, k=2, dwell=20.0):
    phi = math.exp(-dt / Tc)
    m = max(k, math.ceil(dwell / dt) + 1)
    fx = 3600.0 / dt
    lam_x = fx * run_start_prob((delta + h) / sigma, m, phi)
    lam_e = fx * run_start_prob((h - delta) / sigma, m, phi)
    if lam_x <= 0 or lam_e <= 0:
        return 0.0
    return 2.0 / (1.0 / lam_x + 1.0 / lam_e)


def design_h(eps_per_hour, sigma, Tc, dt, k=2, dwell=20.0, delta=0.0, h_max=80.0):
    """Smallest hysteresis half-width h (m, 0.5 m steps) whose worst-case false-toggle rate <= eps."""
    h = 0.5
    while h < h_max:
        if hyst_toggles_per_hour(delta, h, sigma, Tc, dt, k, dwell) <= eps_per_hour:
            return h
        h += 0.5
    return float("inf")


def predicted_delay(h, v, dwell, dt, tol=10.0):
    """Approximate detection delay for a walker: extra distance beyond truth tolerance + dwell + half a fix interval."""
    return max(h - tol, 0.0) / v + dwell + dt / 2.0
