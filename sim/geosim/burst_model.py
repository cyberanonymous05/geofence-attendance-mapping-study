"""Closed-form (quasi-Poisson) model of LoRa event delivery under time-varying load.

A packet of spreading factor s sent at time t is lost if another packet of the same SF and channel starts within
its vulnerability window (+/- tau_s) and is not captured. With per-student packet rate lambda(t) (events, after
detector delay, jitter and repetition, plus heartbeats), N students, SF share f_s, channels C and capture
probability q_i for a node with received power rx_i:
        P_ok(i, t) = exp(-2 tau_s * (N f_s / C) * lambda(t) * q_i),   q_i = P(rx_j > rx_i - capture_dB | same SF).
Event delivery is the lambda_e-weighted average of P_ok over time and nodes (nodes outside SF12 range never deliver).
Assumes independent nodes and Poisson-like local arrivals; exact lower-level collisions are left to Monte Carlo."""
import numpy as np
from . import lora
from .burst import make_links


def link_stats(D=300.0, n=60000, capture_db=6.0, seed=1):
    rng = np.random.default_rng(seed)
    rx, sf, ok = make_links(n, D, rng)
    stats = {}
    for s in range(7, 13):
        g = np.sort(rx[(sf == s) & ok])
        if len(g) < 20: continue
        # q_i = fraction of group with rx_j > rx_i - capture_db  (killers of node i)
        q = 1.0 - np.searchsorted(g, g - capture_db, side="right") / len(g)
        q = np.clip(q, 0.0, 1.0)
        stats[s] = dict(f=len(g) / n, q=q, toa=lora.time_on_air(10, sf=s))
    return stats, float((~ok).mean())


def profile_from_gauss(centres_h, participation, sigma_s, extras=1.0, T=86400):
    """Per-student event-rate profile (events/s) on a 1 s grid: Gaussian bursts + uniform extra trips (2 events each)."""
    t = np.arange(T, dtype=float)
    lam = np.zeros(T)
    for h in centres_h:
        if sigma_s <= 0:
            lam[int(h * 3600)] += participation
        else:
            lam += participation * np.exp(-0.5 * ((t - h * 3600) / sigma_s) ** 2) / (sigma_s * np.sqrt(2 * np.pi))
    lam += 2 * extras / T
    return lam


def profile_from_events(sod, n_student_days, T=86400, smooth_s=10):
    h = np.bincount(np.clip(sod.astype(int), 0, T - 1), minlength=T).astype(float) / n_student_days
    k = np.ones(2 * smooth_s + 1) / (2 * smooth_s + 1)
    return np.convolve(h, k, mode="same")


def event_delivery(lam_e, n, jitter_s=0.0, repeats=1, delay_mean_s=33.0, heartbeat_s=3600.0, channels=3, stats=None, p_out=None):
    stats, p_out = (stats, p_out) if stats is not None else link_stats()
    T = len(lam_e)
    lam = np.roll(lam_e, int(round(delay_mean_s)))                      # detector latency (point mass)
    if jitter_s > 0:
        w = int(jitter_s)
        csum = np.concatenate([[0.0], np.cumsum(np.concatenate([lam, lam[:w]]))])
        lam = (csum[w:w + T] - csum[0:T]) / w                           # moving average over the previous J seconds
        lam = np.roll(lam, 1) if False else lam
    # rate seen by an event packet: its own copies' load plus the others; repeats multiply the event load
    load = repeats * lam + 1.0 / heartbeat_s
    w_e = lam_e / lam_e.sum()                                           # weight by when events happen (before delay)
    w_e = np.roll(w_e, int(round(delay_mean_s)))
    if jitter_s > 0:
        w = int(jitter_s); cs = np.concatenate([[0.0], np.cumsum(np.concatenate([w_e, w_e[:w]]))]); w_e = (cs[w:w + T] - cs[0:T]) / w
    w_e = w_e / w_e.sum()
    p_single = 0.0
    for s, d in stats.items():
        expo = 2.0 * d["toa"] * (n * d["f"] / channels) * load[:, None] * d["q"][None, ::max(len(d["q"]) // 400, 1)]
        p_single += d["f"] * float((w_e[:, None] * np.exp(-expo)).sum(0).mean())
    p_single /= (1.0 - p_out)
    p_any = 1.0 - (1.0 - p_single) ** repeats
    return p_any * (1.0 - p_out)
