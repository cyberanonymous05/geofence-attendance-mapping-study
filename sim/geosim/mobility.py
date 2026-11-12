"""Synthetic campus mobility at 1 Hz. Ground truth positions in metres, fence centred at origin.

A student idles inside, makes trips out of the fence, and with probability p_loiter
lingers near the boundary (the hard case for naive radius checks).
"""
import numpy as np
from . import params as P


def _walk(a, b, v):
    d = float(np.hypot(*(b - a)))
    n = max(int(np.ceil(d / v)), 1)
    s = np.linspace(0.0, 1.0, n + 1)[1:, None]
    return a + (b - a) * s


def _dwell(p, secs, wander_sigma, rng):
    n = max(int(secs), 1)
    steps = rng.normal(0.0, wander_sigma, size=(n, 2))
    return p + np.cumsum(steps, axis=0)


def _rand_inside(rng, R):
    r = 0.6 * R * np.sqrt(rng.random())
    th = rng.uniform(0, 2 * np.pi)
    return np.array([r * np.cos(th), r * np.sin(th)])


def generate_day(rng, T=86400, R=P.FENCE_RADIUS_M, p_loiter=0.4):
    pos = _rand_inside(rng, R)
    segs = [_dwell(pos, rng.exponential(3 * 3600) + 600, 0.02, rng)]
    cur = segs[-1][-1]
    total = len(segs[0])
    while total < T:
        v = float(np.clip(rng.normal(P.WALK_SPEED_MPS, 0.2), 0.8, 2.2))
        th = rng.uniform(0, 2 * np.pi)
        u = np.array([np.cos(th), np.sin(th)])
        far = u * rng.uniform(R + 20, R + 1500)
        parts = []
        for leg_target in ("out", "back"):
            if rng.random() < p_loiter:
                edge = u * (R + rng.uniform(-6, 6))
                parts.append(_walk(cur, edge, v)); cur = parts[-1][-1]
                parts.append(_dwell(cur, rng.uniform(60, 600), 0.3, rng)); cur = parts[-1][-1]
            if leg_target == "out":
                parts.append(_walk(cur, far, v)); cur = parts[-1][-1]
                parts.append(_dwell(cur, rng.exponential(1800) + 300, 0.05, rng)); cur = parts[-1][-1]
            else:
                home = _rand_inside(rng, R)
                parts.append(_walk(cur, home, v)); cur = parts[-1][-1]
                parts.append(_dwell(cur, rng.exponential(4 * 3600) + 900, 0.02, rng)); cur = parts[-1][-1]
        for p in parts:
            segs.append(p); total += len(p)
    xy = np.concatenate(segs)[:T]
    return xy[:, 0], xy[:, 1]
