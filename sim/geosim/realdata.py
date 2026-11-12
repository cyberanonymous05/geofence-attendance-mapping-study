"""Load real GPS tracks (CSV with lat,lon,unix_time columns; GeoLife .plt) and convert to local metres.

Real fixes already contain real GPS noise, so they are replayed as *measurements* (no injected error);
ground truth is not known, so evaluation on real data reports event counts/flapping, not delay.
"""
import numpy as np
import pandas as pd

R_EARTH = 6371000.0


def load_csv(path):
    df = pd.read_csv(path)
    cols = {c.lower(): c for c in df.columns}
    lat = df[cols.get("lat", cols.get("latitude"))].to_numpy(float)
    lon = df[cols.get("lon", cols.get("longitude"))].to_numpy(float)
    t = df[cols.get("time", cols.get("unix_time", cols.get("timestamp")))].to_numpy(float)
    return lat, lon, t


def load_geolife_plt(path):
    df = pd.read_csv(path, skiprows=6, header=None)
    lat, lon = df[0].to_numpy(float), df[1].to_numpy(float)
    t = pd.to_datetime(df[5] + " " + df[6]).astype("int64").to_numpy() / 1e9
    return lat, lon, t


def to_local_xy(lat, lon, centre=None):
    """Equirectangular projection around centre (default: track median)."""
    lat0, lon0 = centre if centre else (np.median(lat), np.median(lon))
    x = np.radians(lon - lon0) * R_EARTH * np.cos(np.radians(lat0))
    y = np.radians(lat - lat0) * R_EARTH
    return x, y


def resample_1hz(t, x, y):
    ts = np.arange(int(t[0]), int(t[-1]))
    return np.interp(ts, t, x), np.interp(ts, t, y)
