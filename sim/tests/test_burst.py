import numpy as np, pandas as pd
from geosim import burst_model as M, studentlife as S


def test_delivery_monotone_and_jitter_helps_tight_burst():
    st, pout = M.link_stats(n=20000)
    lam = M.profile_from_gauss([9.0], 0.9, 20)
    d = [M.event_delivery(lam, n, 0, 1, stats=st, p_out=pout) for n in (200, 800, 3200)]
    assert d[0] > d[1] > d[2]
    assert M.event_delivery(lam, 800, 240, 1, stats=st, p_out=pout) > d[1]
    # uniform arrivals never do worse than a burst of the same volume
    uni = np.full(86400, lam.sum() / 86400)
    assert M.event_delivery(uni, 800, 0, 1, stats=st, p_out=pout) > d[1]


def test_studentlife_events_departure_and_return():
    # one student, home = 'a'; away 09:00-10:00, then back
    t0 = 1_364_400_000
    rows = []
    for k in range(40):                       # at home, 20 s scans
        rows.append((t0 + 20 * k, "in[a]"))
    away0 = t0 + 20 * 40
    for k in range(200):                      # away 200*20 s
        rows.append((away0 + 20 * k, "in[b]"))
    back0 = away0 + 20 * 200
    for k in range(40):
        rows.append((back0 + 20 * k, "in[a]"))
    df = pd.DataFrame(rows, columns=["timestamp", "location"])
    df["uid"] = "0"; df["day"] = 1; df["dow"] = 1; df["sod"] = (df.timestamp % 86400)
    ev = S.events(df, {"0": "a"})
    assert list(ev.kind) == ["out", "in"]
