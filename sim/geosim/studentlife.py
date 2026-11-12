"""Real crossing times from the StudentLife dataset (Dartmouth, spring 2013, CC BY 4.0, via Zenodo 3529253).

WiFi-inferred building location of 48 students, ~20 s scan interval when moving. A student's 'home' is the
building where they most often are between 02:00 and 05:00 local time. A departure is the first non-home
sample after a home sample (gap <= max_gap_s) that is followed by >= away_min_s of continuous non-home samples; a
return is the mirror event. Times are seconds since local midnight, with the event placed at the midpoint of the
two samples that bracket it (uncertainty <= max_gap_s/2).

Caveat: building-level WiFi location, not a GPS fence; the quantity of interest is the timing structure of
students leaving and entering the place they live, which is what a campus fence crossing is for a hostel."""
import numpy as np, pandas as pd

TZ = "America/New_York"


def load(path):
    import pyreadr
    df = list(pyreadr.read_r(path).values())[0]
    df["uid"] = df.uid.astype(str)
    ts = pd.to_datetime(df.timestamp, unit="s", utc=True).dt.tz_convert(TZ)
    df["day"] = ts.dt.date
    df["sod"] = ts.dt.hour * 3600 + ts.dt.minute * 60 + ts.dt.second
    df["dow"] = ts.dt.dayofweek
    return df.sort_values(["uid", "timestamp"]).reset_index(drop=True)


def _tokens(loc):
    inner = loc[loc.index("[") + 1: loc.rindex("]")]
    return {t.strip() for t in inner.split(";") if t.strip()}


def home_of(df, min_samples=200):
    night = df[(df.sod >= 2 * 3600) & (df.sod < 5 * 3600) & df.location.str.startswith("in[")]
    homes = {}
    for uid, g in night.groupby("uid"):
        if len(g) >= min_samples:
            homes[uid] = g.location.value_counts().index[0][3:-1]
    return homes


def events(df, homes, max_gap_s=120, away_min_s=300):
    """Returns DataFrame(uid, day, dow, sod, kind) with kind in {'out','in'}."""
    rows = []
    for uid, g in df[df.uid.isin(homes)].groupby("uid"):
        h = homes[uid]
        t = g.timestamp.values.astype(np.int64)
        at_home = np.array([h in _tokens(l) for l in g.location.values])
        sod = g.sod.values; day = g.day.values; dow = g.dow.values
        n = len(t)
        i = 0
        # run-length encode home/away
        change = np.nonzero(at_home[1:] != at_home[:-1])[0] + 1
        starts = np.concatenate([[0], change]); ends = np.concatenate([change, [n]])
        for a, b in zip(starts, ends):
            if a == 0: continue
            gap = t[a] - t[a - 1]
            if gap > max_gap_s or day[a] != day[a - 1]: continue
            dur = (t[b] - t[a]) if b < n else 0
            if dur < away_min_s and at_home[a - 1]:      # short excursion from home: not a departure
                continue
            if (not at_home[a - 1]) and (t[a] - t[a - 1] > max_gap_s): continue
            if not at_home[a - 1]:
                prev_dur = t[a] - t[starts[np.searchsorted(starts, a) - 1]]
                if prev_dur < away_min_s: continue
            mid = sod[a - 1] + (sod[a] - sod[a - 1]) / 2.0
            rows.append((uid, day[a], dow[a], mid, "out" if at_home[a - 1] else "in"))
    return pd.DataFrame(rows, columns=["uid", "day", "dow", "sod", "kind"])
