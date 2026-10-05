"""Prespecified probability diagnostics; contains no fitting or calibration model."""
import numpy as np


def probability_diagnostics(labels, probabilities, weights=None):
    y, p = np.asarray(labels), np.asarray(probabilities, dtype=float)
    w = np.ones(len(y)) if weights is None else np.asarray(weights, dtype=float)
    if (y.ndim != 1 or p.shape != (len(y), 5) or w.shape != y.shape or len(y) == 0
            or not np.isin(y, np.arange(5)).all() or not np.isfinite(p).all()
            or (p < 0).any() or (p > 1).any() or not np.allclose(p.sum(axis=1), 1, atol=1e-7, rtol=0)
            or not np.isfinite(w).all() or (w < 0).any() or w.sum() <= 0):
        raise ValueError('Valid native grades, five-class probabilities and nonnegative site weights required')
    observed_cdf = y[:, None] <= np.arange(4)
    rps = np.mean((p.cumsum(axis=1)[:, :4] - observed_cdf) ** 2, axis=1)
    result = {'normalized_RPS': float(np.average(rps, weights=w))}
    for name, threshold in [('any_damage', 1), ('severe_or_worse', 3)]:
        pred, observed = p[:, threshold:].sum(axis=1), (y >= threshold).astype(float)
        result[f'{name}_Brier'] = float(np.average((pred - observed) ** 2, weights=w))
        bins = []
        index = np.minimum((pred * 10).astype(int), 9)
        for b in range(10):
            selected = index == b
            mass = float(w[selected].sum())
            bins.append({'lower': b / 10, 'upper': (b + 1) / 10,
                         'records': int(selected.sum()), 'weight': mass,
                         'predicted': float(np.average(pred[selected], weights=w[selected])) if mass else None,
                         'observed': float(np.average(observed[selected], weights=w[selected])) if mass else None})
        result[f'{name}_reliability'] = bins
    return result
