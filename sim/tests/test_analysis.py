import math, numpy as np
from scipy.stats import norm
from geosim import analysis as A


def test_independent_limit():
    c, m = 0.7, 3
    assert abs(A.run_start_prob(c, m, 0.0) - norm.cdf(c) * norm.sf(c) ** m) < 1e-12
    assert abs(A.run_start_prob(c, 3, 1e-6) - norm.cdf(c) * norm.sf(c) ** 3) < 1e-4


def test_matches_bivariate_normal():
    from scipy.stats import multivariate_normal as mvn
    phi, a = 0.6, 0.3
    p_cross = 2 * (norm.cdf(a) - mvn.cdf([a, a], mean=[0, 0], cov=[[1, phi], [phi, 1]]))
    assert abs(2 * A.run_start_prob(a, 1, phi) - p_cross) < 1e-4


def test_monotone_in_h():
    r = [A.hyst_toggles_per_hour(0.0, h, 8.0, 30.0, 5.0) for h in (5, 10, 15, 25)]
    assert r == sorted(r, reverse=True) and r[-1] < r[0]
