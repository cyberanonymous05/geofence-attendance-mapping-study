"""Node pipeline: sampler -> (plausibility filter) -> detector -> events.

Returns the list of (time, state) transition events and the fix count.
"""
import numpy as np
from . import params as P


def run_node(x, y, ex, ey, detector, sampler, plaus_vmax=15.0, use_filter=True, T=None, dist_fn=None, cand_out=None):
    """dist_fn(x, y) -> equivalent distance (R0 + signed distance to the fence boundary); default is the
    circular fence, i.e. the Euclidean distance to the origin. Used for polygon fences."""
    T = T or len(x)
    dist = dist_fn or (lambda a, b: float(np.hypot(a, b)))
    r0 = dist(x[0], y[0])
    detector.reset(inside=r0 <= P.FENCE_RADIUS_M)
    prev_state = detector.state
    events = []
    fixes = 0
    t = 0.0
    last_ok = None  # (t, mx, my)
    while t < T:
        i = int(t)
        mx, my = x[i] + ex[i], y[i] + ey[i]
        accept = True
        if use_filter and last_ok is not None:
            dt = max(t - last_ok[0], 1.0)
            if np.hypot(mx - last_ok[1], my - last_ok[2]) / dt > plaus_vmax:
                accept = False
        fixes += 1
        d = dist(mx, my)
        if accept:
            last_ok = (t, mx, my)
            st = detector.update(t, d)
            if st != prev_state:
                events.append((t, st))
                if cand_out is not None:
                    cand_out.append(getattr(detector, "confirm_t0", None))
                prev_state = st
        t += max(sampler.next_interval(d, detector), 1.0)
    return events, fixes


def truth_transitions(x, y, R=P.FENCE_RADIUS_M, tol=10.0, r=None):
    """Schmitt trigger on true distance: ground-truth state changes (time, new_state).
    r: optional precomputed equivalent-distance series (polygon fences)."""
    r = np.hypot(x, y) if r is None else r
    state = r[0] <= R
    out = []
    for t in range(1, len(r)):
        if state and r[t] > R + tol:
            state = False; out.append((t, False))
        elif (not state) and r[t] <= R - tol:
            state = True; out.append((t, True))
    return out


def _state_at(events, init_state, t):
    st = init_state
    for te, es in events:
        if te <= t:
            st = es
        else:
            break
    return st


def match_events(truth, events, init_state=True, pre_window=60.0):
    """Returns (delays, n_missed, n_spurious).

    delay_i = time from truth transition i until the detector state equals the true new state
    (0 if it already does, i.e. detected early). Missed = detector never reaches that state before
    the next truth transition. Spurious = detector events not consumed by a truth transition.
    """
    used = set()
    delays, missed = [], 0
    for i, (tt, ts) in enumerate(truth):
        t_end = truth[i + 1][0] if i + 1 < len(truth) else float("inf")
        # event consumption for spurious count
        for j, (te, es) in enumerate(events):
            if j not in used and es == ts and tt - pre_window <= te < t_end:
                used.add(j)
                break
        if _state_at(events, init_state, tt) == ts:
            delays.append(0.0)
            continue
        later = [te for te, es in events if te > tt and es == ts and te < t_end]
        if later:
            delays.append(later[0] - tt)
        else:
            missed += 1
    return delays, missed, len(events) - len(used)
