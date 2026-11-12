"""Monte-Carlo LoRa uplink with capture effect, multiple channels and distance-based SF assignment.

Nodes are uniform in a disc of radius D around a central gateway. Each node uses the lowest SF whose
received power exceeds the SX127x typical sensitivity by `margin_db`. Packets collide only if they share
channel and SF and overlap in time (imperfect SF orthogonality ignored). The strongest packet survives
if it exceeds every overlapping packet by `capture_db`. Static per-node shadowing; no fast fading.
"""
import numpy as np
from . import lora, security

SENS_DBM = {7: -123.0, 8: -126.0, 9: -129.0, 10: -132.0, 11: -134.5, 12: -137.0}   # SX1276 typical, BW125


def simulate_pdr(n, rate_hz, payload=10, channels=3, D=300.0, T=86400.0, capture_db=6.0, margin_db=10.0,
                 seed=0, n_exp=security.PATHLOSS_EXP, sigma=security.SHADOW_SIGMA_DB, ptx=security.PTX_DBM):
    rng = np.random.default_rng(seed)
    d = np.maximum(D * np.sqrt(rng.random(n)), 5.0)
    rx = ptx - security.PL_D0_DB - 10 * n_exp * np.log10(d) + rng.normal(0, sigma, n)
    sf = np.full(n, 12)
    for s in (12, 11, 10, 9, 8, 7):
        sf = np.where(rx - SENS_DBM[s] >= margin_db, s, sf)
    ok_link = (rx - SENS_DBM[12]) >= 0
    k = rng.poisson(rate_hz * T, n)
    node = np.repeat(np.arange(n), k)
    if len(node) == 0:
        return 1.0
    t0 = rng.uniform(0, T, len(node))
    ch = rng.integers(0, channels, len(node))
    toa = np.array([lora.time_on_air(payload, sf=s) for s in range(7, 13)])[sf[node] - 7]
    p = rx[node]
    order = np.argsort(t0)
    node, t0, ch, toa, p, sfp = node[order], t0[order], ch[order], toa[order], p[order], sf[node][order]
    ok = np.ones(len(t0), bool)
    for i in range(len(t0)):
        j = i + 1
        while j < len(t0) and t0[j] < t0[i] + toa[i]:
            if ch[j] == ch[i] and sfp[j] == sfp[i]:
                if not (p[i] - p[j] >= capture_db): ok[i] = False
                if not (p[j] - p[i] >= capture_db): ok[j] = False
            j += 1
    ok &= ok_link[node]
    return float(ok.mean())


def capacity(rate_hz, target=0.95, **kw):
    lo, hi = 10, 20
    while simulate_pdr(hi, rate_hz, **kw) >= target and hi < 200000:
        lo, hi = hi, hi * 2
    for _ in range(12):
        mid = (lo + hi) // 2
        if simulate_pdr(mid, rate_hz, **kw) >= target:
            lo = mid
        else:
            hi = mid
    return lo
