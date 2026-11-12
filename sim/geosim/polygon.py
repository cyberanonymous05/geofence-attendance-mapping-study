"""Polygon fences. Signed distance to a simple polygon, mapped to an 'equivalent circular distance'
d_eq = R0 + s (s > 0 outside, s < 0 inside), so every detector and sampler written for a circular
fence works unchanged. Signed distance is 1-Lipschitz, so the no-unobserved-crossing argument of the
adaptive sampler carries over verbatim."""
import numpy as np


class PolygonFence:
    def __init__(self, vertices, R0=300.0):
        self.v = np.asarray(vertices, float)
        self.a = self.v
        self.b = np.roll(self.v, -1, axis=0)
        self.ab = self.b - self.a
        self.ab2 = (self.ab ** 2).sum(1)
        self.R0 = R0

    def inside(self, px, py):
        """Even-odd ray casting."""
        x1, y1 = self.a[:, 0], self.a[:, 1]
        x2, y2 = self.b[:, 0], self.b[:, 1]
        cond = (y1 > py) != (y2 > py)
        with np.errstate(divide="ignore", invalid="ignore"):
            xint = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
        return bool(np.sum(cond & (px < xint)) % 2 == 1)

    def boundary_distance(self, px, py):
        ap = np.stack([px - self.a[:, 0], py - self.a[:, 1]], axis=1)
        t = np.clip((ap * self.ab).sum(1) / self.ab2, 0.0, 1.0)
        proj = self.a + self.ab * t[:, None]
        return float(np.sqrt(((np.array([px, py]) - proj) ** 2).sum(1)).min())

    def signed(self, px, py):
        d = self.boundary_distance(px, py)
        return -d if self.inside(px, py) else d

    def equiv(self, px, py):
        return self.R0 + self.signed(px, py)

    def equiv_series(self, x, y):
        return np.array([self.equiv(a, b) for a, b in zip(x, y)])


def rectangle(w, h):
    return [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]


def l_shape(a=700.0, b=350.0):
    """Non-convex L-shaped campus: a x a square with a b x b notch removed, centred near the origin."""
    pts = [(0, 0), (a, 0), (a, b), (b, b), (b, a), (0, a)]
    cx, cy = a * 0.33, a * 0.33
    return [(x - cx, y - cy) for x, y in pts]
