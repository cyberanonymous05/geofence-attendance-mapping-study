"""GeoLife loading helpers (real GPS tracks, Microsoft Research Asia). Data is untrusted input: parsed with pandas only."""
import glob, os
import numpy as np
import pandas as pd
from . import realdata

ROOT = "data/geolife/Geolife Trajectories 1.3/Data"


def list_tracks():
    return sorted(glob.glob(os.path.join(ROOT, "*", "Trajectory", "*.plt")))


def load_track(path):
    lat, lon, t = realdata.load_geolife_plt(path)
    return lat, lon, t


def to_1hz_segments(lat, lon, t, max_gap=10.0, min_len=1800):
    """Split at gaps > max_gap seconds, interpolate to 1 Hz, keep segments >= min_len seconds.
    Returns list of (x, y) in metres around the segment start point."""
    out = []
    order = np.argsort(t)
    lat, lon, t = lat[order], lon[order], t[order]
    keep = np.concatenate([[True], np.diff(t) > 0])
    lat, lon, t = lat[keep], lon[keep], t[keep]
    cuts = np.where(np.diff(t) > max_gap)[0] + 1
    for a, b in zip(np.r_[0, cuts], np.r_[cuts, len(t)]):
        if b - a < 2 or t[b - 1] - t[a] < min_len:
            continue
        x, y = realdata.to_local_xy(lat[a:b], lon[a:b], centre=(lat[a], lon[a]))
        xs, ys = realdata.resample_1hz(t[a:b], x, y)
        if len(xs) >= min_len:
            out.append((xs, ys))
    return out
