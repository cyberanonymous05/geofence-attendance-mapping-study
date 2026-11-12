"""Boundary detectors. update(t, d) takes fix time (s) and measured distance to centre (m);
returns current confirmed state (True = inside)."""
from . import params as P


class PlainRadius:
    name = "plain"

    def __init__(self, R=P.FENCE_RADIUS_M):
        self.R = R
        self.state = True

    def reset(self, inside=True):
        self.state = inside

    def update(self, t, d):
        self.state = d <= self.R
        return self.state

    @property
    def pending(self):
        return False


class Hysteresis:
    """Schmitt-trigger thresholds (R-h to enter, R+h to exit) + k consecutive fixes + dwell time."""
    name = "hyst"

    def __init__(self, R=P.FENCE_RADIUS_M, h=15.0, k=2, dwell_s=20.0):
        self.R, self.h, self.k, self.dwell = R, h, k, dwell_s
        self.state = True
        self._cnt = 0
        self._t0 = None
        self.confirm_t0 = None     # time of the first fix of the run that confirmed the last transition

    def reset(self, inside=True):
        self.state = inside
        self._cnt, self._t0 = 0, None
        self.confirm_t0 = None

    def update(self, t, d):
        if self.state:
            cond = d > self.R + self.h        # candidate exit
        else:
            cond = d <= self.R - self.h       # candidate entry
        if cond:
            if self._cnt == 0:
                self._t0 = t
            self._cnt += 1
            if self._cnt >= self.k and (t - self._t0) >= self.dwell:
                self.state = not self.state
                self.confirm_t0 = self._t0
                self._cnt, self._t0 = 0, None
        else:
            self._cnt, self._t0 = 0, None
        return self.state

    @property
    def pending(self):
        return self._cnt > 0


class MovingAverage:
    """Baseline: radius test on the mean of the last n measured distances."""
    name = "movavg"

    def __init__(self, R=P.FENCE_RADIUS_M, n=5):
        self.R, self.n = R, n
        self.buf = []
        self.state = True

    def reset(self, inside=True):
        self.state, self.buf = inside, []

    def update(self, t, d):
        self.buf.append(d)
        self.buf = self.buf[-self.n:]
        self.state = (sum(self.buf) / len(self.buf)) <= self.R
        return self.state

    @property
    def pending(self):
        return False


class KalmanRadius:
    """Baseline: 1-D constant-velocity Kalman filter on measured distance, then a radius test.
    State [d, d_dot]; measurement noise sigma_m; process acceleration sigma_a (m/s^2)."""
    name = "kalman"

    def __init__(self, R=P.FENCE_RADIUS_M, sigma_m=6.0, sigma_a=0.3):
        self.R, self.sm2, self.sa2 = R, sigma_m ** 2, sigma_a ** 2
        self.state = True
        self.x = None
        self.t_last = None

    def reset(self, inside=True):
        self.state, self.x, self.P, self.t_last = inside, None, None, None

    def update(self, t, d):
        import numpy as np
        if self.x is None:
            self.x = np.array([d, 0.0]); self.P = np.diag([self.sm2, 4.0]); self.t_last = t
        else:
            dt = max(t - self.t_last, 1e-3); self.t_last = t
            F = np.array([[1, dt], [0, 1]])
            Q = self.sa2 * np.array([[dt ** 4 / 4, dt ** 3 / 2], [dt ** 3 / 2, dt ** 2]])
            self.x = F @ self.x; self.P = F @ self.P @ F.T + Q
            S = self.P[0, 0] + self.sm2
            K = self.P[:, 0] / S
            self.x = self.x + K * (d - self.x[0])
            self.P = self.P - np.outer(K, self.P[0, :])
        self.state = self.x[0] <= self.R
        return self.state

    @property
    def pending(self):
        return False


class ExcessArea:
    """Evidence-accumulation (leaky CUSUM-style) detector. Accumulates the area of the measured
    distance above (exit) or below (entry) the threshold R+h / R-h, with a reflecting barrier at zero:
        S <- max(0, S + (excess) * dt),   alarm when S >= A.
    Brief dips reduce S instead of resetting it; a student walking away accumulates evidence quadratically.
    dt is capped at dt_cap so one sparse fix cannot confirm alone."""
    name = "excessarea"

    def __init__(self, R=P.FENCE_RADIUS_M, h=10.0, A=300.0, dt_cap=30.0):
        self.R, self.h, self.A, self.dt_cap = R, h, A, dt_cap
        self.state = True
        self.S = 0.0
        self.t_prev = None

    def reset(self, inside=True):
        self.state, self.S, self.t_prev = inside, 0.0, None

    def update(self, t, d):
        dt = 0.0 if self.t_prev is None else min(t - self.t_prev, self.dt_cap)
        self.t_prev = t
        ex = (d - (self.R + self.h)) if self.state else ((self.R - self.h) - d)
        self.S = max(0.0, self.S + ex * dt)
        if self.S >= self.A:
            self.state = not self.state
            self.S = 0.0
        return self.state

    @property
    def pending(self):
        return self.S > 0.0
