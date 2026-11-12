import numpy as np
from geosim import realdata


def test_projection_scale():
    x, y = realdata.to_local_xy(np.array([13.0, 13.001]), np.array([80.0, 80.0]), centre=(13.0, 80.0))
    assert abs(y[1] - 111.2) < 0.5 and abs(x[1]) < 1e-6


def test_csv_roundtrip(tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("lat,lon,time\n13.0,80.0,0\n13.0,80.001,10\n")
    lat, lon, t = realdata.load_csv(p)
    x, y = realdata.to_local_xy(lat, lon, centre=(13.0, 80.0))
    xs, ys = realdata.resample_1hz(t, x, y)
    assert len(xs) == 9 or len(xs) == 10
