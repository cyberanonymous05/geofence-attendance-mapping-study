"""GPS sampling policies. next_interval(d_meas, detector) -> seconds until next fix."""
import numpy as np
from . import params as P


class Fixed:
    def __init__(self, dt):
        self.dt = float(dt)
        self.name = f"fixed{int(dt)}s"

    def next_interval(self, d, detector=None):
        return self.dt


class Adaptive:
    """Boundary-proximity adaptive sampling.

    interval = clip((|d-R| - guard) / v_max, t_min, t_max).
    If the true speed never exceeds v_max and GPS error stays below `guard`, the next fix
    always occurs before the fence can be crossed (bounded detection delay).
    """
    def __init__(self, R=P.FENCE_RADIUS_M, v_max=P.V_MAX_MPS, guard=25.0, t_min=5.0, t_max=300.0):
        self.R, self.v_max, self.guard, self.t_min, self.t_max = R, v_max, guard, t_min, t_max
        self.name = "adaptive"

    def next_interval(self, d, detector=None):
        if detector is not None and detector.pending:
            return self.t_min
        margin = abs(d - self.R)
        return float(np.clip((margin - self.guard) / self.v_max, self.t_min, self.t_max))
