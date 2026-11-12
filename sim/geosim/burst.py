"""Synchronised-crossing bursts on a LoRa uplink: timetable-driven event times, optional random uplink jitter and
blind repetition, and a collision model (same channel + SF + overlap, capture effect) with distance-based SF.

All timetable parameters are ASSUMED (hostel with class changes) and are swept in the experiments."""
import numpy as np
from . import lora, security
from .capacity import SENS_DBM

# (hour of day, direction) of the daily bursts: leave for class, back for lunch, leave, back in the evening
BURSTS = [(8.5, "out"), (13.0, "in"), (14.0, "out"), (17.5, "in")]


def make_links(n, D, rng, margin_db=10.0, n_exp=security.PATHLOSS_EXP, sigma=security.SHADOW_SIGMA_DB, ptx=security.PTX_DBM):
    d = np.maximum(D * np.sqrt(rng.random(n)), 5.0)
    rx = ptx - security.PL_D0_DB - 10 * n_exp * np.log10(d) + rng.normal(0, sigma, n)
    sf = np.full(n, 12)
    for s in (12, 11, 10, 9, 8, 7):
        sf = np.where(rx - SENS_DBM[s] >= margin_db, s, sf)
    return rx, sf, (rx - SENS_DBM[12]) >= 0


def timetable_crossings(rng, n, sigma_w_s, participate=0.9, extra_trips=1.0, T=86400.0):
    """Returns (node_idx, crossing_time) arrays. Burst crossings ~ N(centre, sigma_w); extra_trips random
    out-and-back trips per student per day (Poisson), uniform in the day."""
    nodes, times = [], []
    for hour, _ in BURSTS:
        m = rng.random(n) < participate
        idx = np.nonzero(m)[0]
        nodes.append(idx); times.append(np.clip(rng.normal(hour * 3600, sigma_w_s, len(idx)), 0, T - 1))
    k = rng.poisson(extra_trips, n)
    idx = np.repeat(np.arange(n), k)
    t_out = rng.uniform(0, T - 3600, len(idx)); t_in = t_out + rng.exponential(1800, len(idx)) + 300
    nodes += [idx, idx]; times += [t_out, np.minimum(t_in, T - 1)]
    return np.concatenate(nodes), np.concatenate(times)


def deliver(t0, node, rx, sf, ok_link, channels, payload, capture_db, rng):
    ch = rng.integers(0, channels, len(t0))
    toa_tab = np.array([lora.time_on_air(payload, sf=s) for s in range(7, 13)])
    toa = toa_tab[sf[node] - 7]
    order = np.argsort(t0, kind="stable")
    inv = np.empty(len(order), int); inv[order] = np.arange(len(order))
    t, c, a, p, s = t0[order], ch[order], toa[order], rx[node][order], sf[node][order]
    ok = np.ones(len(t), bool)
    for i in range(len(t)):
        j = i + 1
        while j < len(t) and t[j] < t[i] + a[i]:
            if c[j] == c[i] and s[j] == s[i]:
                if not (p[i] - p[j] >= capture_db): ok[i] = False
                if not (p[j] - p[i] >= capture_db): ok[j] = False
            j += 1
    ok &= ok_link[node][order]
    return ok[inv]


def empirical_crossings(pool, fuzz_s=10.0):
    """pool: list of arrays of event times (s since midnight), one per real student-day. Returns a crossing generator
    that gives each of n simulated students the events of a randomly drawn real student-day (+/- fuzz_s)."""
    def gen(rng, n, T=86400.0):
        pick = rng.integers(0, len(pool), n)
        nodes = np.concatenate([np.full(len(pool[p]), i) for i, p in enumerate(pick)]).astype(int)
        times = np.concatenate([pool[p] for p in pick]) + rng.uniform(-fuzz_s, fuzz_s, len(nodes))
        return nodes, np.clip(times, 0, T - 1)
    return gen


def burst_delivery(n, sigma_w_s, jitter_s, repeats=1, delays=None, channels=3, D=300.0, payload=10,
                   heartbeat_s=3600.0, capture_db=6.0, seed=0, T=86400.0, crossing_fn=None):
    """Fraction of event packets delivered (any copy), and per-packet delivery over all packets."""
    rng = np.random.default_rng(seed)
    rx, sf, ok_link = make_links(n, D, rng)
    cn, ct = crossing_fn(rng, n, T) if crossing_fn else timetable_crossings(rng, n, sigma_w_s, T=T)
    det_delay = rng.choice(delays, len(ct)) if delays is not None else np.full(len(ct), 29.0)
    ev_nodes, ev_t, ev_id = [], [], []
    for r in range(repeats):
        jit = rng.uniform(0, jitter_s, len(ct)) if jitter_s > 0 else (rng.uniform(0, 30.0, len(ct)) if r > 0 else 0.0)
        ev_nodes.append(cn); ev_t.append(ct + det_delay + jit); ev_id.append(np.arange(len(ct)))
    hb_n = np.repeat(np.arange(n), int(T // heartbeat_s))
    hb_t = rng.uniform(0, heartbeat_s, n)[hb_n] + np.tile(np.arange(int(T // heartbeat_s)) * heartbeat_s, n)
    node = np.concatenate(ev_nodes + [hb_n]); t0 = np.concatenate(ev_t + [hb_t])
    ok = deliver(t0, node, rx, sf, ok_link, channels, payload, capture_db, rng)
    n_ev = len(ct)
    ev_ok = np.zeros(n_ev, bool)
    off = 0
    for r in range(repeats):
        ev_ok |= ok[off:off + n_ev]; off += n_ev
    return dict(event_delivery=float(ev_ok.mean()), packet_pdr=float(ok.mean()), events=n_ev,
                peak_pkts_per_min=float(np.max(np.bincount((t0[:sum(len(a) for a in ev_t)] // 60).astype(int)))))
