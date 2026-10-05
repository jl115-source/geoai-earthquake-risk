"""Synthetic first-principles catastrophe losses; no fitted vulnerability."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def damage_probabilities(pga, medians, beta):
    """Ordered log-logistic exceedance probabilities at PGA in g."""
    pga, medians = np.asarray(pga, float), np.asarray(medians, float)
    if (not np.isfinite(pga).all() or (pga < 0).any() or medians.ndim != 1
        or not len(medians) or not np.isfinite(medians).all() or (medians <= 0).any()
        or (np.diff(medians) <= 0).any() or not np.isfinite(beta) or beta <= 0):
        raise ValueError("Invalid PGA or ordered fragility parameters")
    z = (np.log(np.maximum(pga, np.finfo(float).tiny))[..., None] - np.log(medians)) / beta
    exceed = np.where(pga[..., None] == 0, 0, np.exp(-np.logaddexp(0, -z)))
    return np.concatenate([1-exceed[..., :1], exceed[..., :-1]-exceed[..., 1:], exceed[..., -1:]], axis=-1)


def validate(c):
    if c.get('input_status') != 'synthetic_illustrative_not_calibrated':
        raise ValueError('B0 requires explicitly synthetic inputs')
    if not isinstance(c.get('seed'), int) or c['seed'] < 0:
        raise ValueError('Invalid seed')
    if not isinstance(c.get('years'), int) or c['years'] < 2:
        raise ValueError('years must be an integer >= 2')
    if c.get('damage_dependence') not in {'independent', 'common_uniform'}:
        raise ValueError('Invalid dependence assumption')
    for rows in (c['assets'], c['events']):
        if not rows or len({r['id'] for r in rows}) != len(rows):
            raise ValueError('Empty records or duplicate IDs')
    for t in c['taxonomies'].values():
        damage_probabilities([0], t['pga_medians_g'], t['beta'])
        m = np.asarray(t['mdr_means'], float)
        if (m.shape != (len(t['pga_medians_g'])+1,) or not np.isfinite(m).all()
            or (m < 0).any() or (m > 1).any() or (np.diff(m) < 0).any() or m[0] != 0
            or not np.isfinite(t['mdr_concentration']) or t['mdr_concentration'] <= 0):
            raise ValueError('Invalid bounded MDR parameters')
    for a in c['assets']:
        if a['taxonomy'] not in c['taxonomies'] or not np.isfinite(a['value']) or a['value'] < 0:
            raise ValueError('Invalid exposure')
    for e in c['events']:
        im = np.asarray(e['pga_g'], float)
        if (not np.isfinite(e['annual_rate']) or e['annual_rate'] < 0
            or im.shape != (len(c['assets']),) or not np.isfinite(im).all() or (im < 0).any()):
            raise ValueError('Invalid event rate or per-asset PGA')
    periods = np.asarray(c['return_periods_years'], float)
    if periods.ndim != 1 or not len(periods) or not np.isfinite(periods).all() or (periods <= 1).any():
        raise ValueError('Return periods must be finite and > 1 year')


def expected_losses(c):
    validate(c)
    rows = []
    for e in c['events']:
        for a, pga in zip(c['assets'], e['pga_g']):
            t = c['taxonomies'][a['taxonomy']]
            prob = damage_probabilities(pga, t['pga_medians_g'], t['beta'])
            loss = float(a['value'] * (prob @ t['mdr_means']))
            rows.append(dict(event_id=e['id'], asset_id=a['id'], taxonomy=a['taxonomy'],
                geography=a['geography'], annual_rate=e['annual_rate'], expected_event_loss=loss,
                aal=e['annual_rate'] * loss))
    return pd.DataFrame(rows)


def sample_event_losses(c, e, count, rng):
    loss = np.zeros(count)
    shared = rng.random(count) if c['damage_dependence'] == 'common_uniform' else None
    for a, pga in zip(c['assets'], e['pga_g']):
        t = c['taxonomies'][a['taxonomy']]
        cdf = np.cumsum(damage_probabilities(pga, t['pga_medians_g'], t['beta']))
        cdf[-1] = 1.0
        states = np.searchsorted(cdf, rng.random(count) if shared is None else shared, side='right')
        mean = np.asarray(t['mdr_means'])[states]
        mdr = mean.copy()  # endpoint means are point masses
        middle = (mean > 0) & (mean < 1)
        k = t['mdr_concentration']
        mdr[middle] = rng.beta(mean[middle]*k, (1-mean[middle])*k)
        loss += a['value'] * mdr
    return loss


def run(c):
    validate(c)
    years = c['years']
    streams = np.random.SeedSequence(c['seed']).spawn(2 * len(c['events']))
    aggregate, maximum, occurrences = np.zeros(years), np.zeros(years), []
    for index, e in enumerate(c['events']):
        # Occurrence streams are isolated from vulnerability random draws so
        # dependence sensitivities keep exactly the same stochastic event set.
        occurrence_rng = np.random.default_rng(streams[2 * index])
        loss_rng = np.random.default_rng(streams[2 * index + 1])
        indices = np.repeat(np.arange(years), occurrence_rng.poisson(e['annual_rate'], years))
        loss = sample_event_losses(c, e, len(indices), loss_rng)
        np.add.at(aggregate, indices, loss)
        np.maximum.at(maximum, indices, loss)
        occurrences.append(pd.DataFrame(dict(year=indices+1, event_id=e['id'], loss=loss)))
    expected = expected_losses(c)
    periods = np.asarray(c['return_periods_years'], float)
    thresholds = np.unique(np.r_[0, aggregate, maximum])
    tables = {
        'annual_losses': pd.DataFrame(dict(year=np.arange(1, years+1), aggregate_loss=aggregate, maximum_event_loss=maximum)),
        'event_losses': pd.concat(occurrences, ignore_index=True),
        'expected_asset_losses': expected,
        'return_period_losses': pd.DataFrame(dict(return_period_years=periods,
            oep_loss=np.quantile(maximum, 1-1/periods, method='inverted_cdf'),
            aep_loss=np.quantile(aggregate, 1-1/periods, method='inverted_cdf'), expected_tail_years=years/periods)),
        'ep_curves': pd.DataFrame(dict(loss_threshold=thresholds,
            oep=(years-np.searchsorted(np.sort(maximum), thresholds, side='right'))/years,
            aep=(years-np.searchsorted(np.sort(aggregate), thresholds, side='right'))/years)),
        'aal_by_taxonomy': expected.groupby('taxonomy', as_index=False).aal.sum(),
        'aal_by_geography': expected.groupby('geography', as_index=False).aal.sum()}
    summary = dict(input_status=c['input_status'], value_unit=c['value_unit'], years=years, seed=c['seed'],
        damage_dependence=c['damage_dependence'], analytic_aal=float(expected.aal.sum()),
        simulated_aal=float(aggregate.mean()), aal_monte_carlo_standard_error=float(aggregate.std(ddof=1)/np.sqrt(years)),
        occurrences=sum(len(x) for x in occurrences), zero_loss_years=int((aggregate == 0).sum()),
        config_sha256=hashlib.sha256(json.dumps(c, sort_keys=True).encode()).hexdigest())
    return summary, tables


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', type=Path, default=Path('configs/risk_b0.json'))
    p.add_argument('--output', type=Path, default=Path('results/b0'))
    args = p.parse_args()
    c = json.loads(args.config.read_text())
    summary, tables = run(c)
    args.output.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(args.output / f'{name}.csv', index=False)
    for name, data in [('config', c), ('summary', summary)]:
        (args.output / f'{name}.json').write_text(json.dumps(data, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
