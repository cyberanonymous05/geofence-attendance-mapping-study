"""Cluster bootstrap: resample whole users (clusters) with replacement, so that correlated segments from the same
user are drawn together and intervals are not too narrow."""
import numpy as np


def cluster_indices(users, rng):
    """users: array-like of cluster labels, one per row. Returns row indices of a cluster-bootstrap resample."""
    users = np.asarray(users)
    uniq, inv = np.unique(users, return_inverse=True)
    groups = [np.nonzero(inv == k)[0] for k in range(len(uniq))]
    pick = rng.integers(0, len(uniq), len(uniq))
    return np.concatenate([groups[k] for k in pick])
