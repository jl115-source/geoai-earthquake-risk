import copy
import json
from pathlib import Path

import numpy as np
import pytest

from src.risk.b0 import damage_probabilities, expected_losses, run, validate


@pytest.fixture
def config():
    return json.loads((Path(__file__).parents[1] / 'configs/risk_b0.json').read_text())


def test_ordered_probabilities():
    p = damage_probabilities([0, 0.1, 1, 1e100], [0.1, 0.3, 0.8], 0.4)
    np.testing.assert_allclose(p.sum(axis=1), 1)
    assert (p >= 0).all()
    np.testing.assert_array_equal(p[0], [1, 0, 0, 0])
    assert np.all(np.diff(p @ np.arange(4)) > 0)


def test_analytic_hand_calculation(config):
    c = copy.deepcopy(config)
    c['assets'] = [dict(id='a', taxonomy='binary', geography='g', value=100)]
    c['taxonomies'] = {'binary': dict(pga_medians_g=[0.2], beta=0.5, mdr_means=[0, 0.8], mdr_concentration=10)}
    c['events'] = [dict(id='e', annual_rate=0.1, pga_g=[0.2])]
    t = expected_losses(c)
    assert t.expected_event_loss.iloc[0] == pytest.approx(40)
    assert t.aal.iloc[0] == pytest.approx(4)


def test_monte_carlo_and_ep(config):
    s, t = run(config)
    assert abs(s['simulated_aal']-s['analytic_aal']) < 5*s['aal_monte_carlo_standard_error']
    a = t['annual_losses']
    assert (a.maximum_event_loss <= a.aggregate_loss).all()
    assert (t['ep_curves'].oep <= t['ep_curves'].aep).all()
    assert (t['return_period_losses'].oep_loss <= t['return_period_losses'].aep_loss).all()
    assert a.aggregate_loss.sum() == pytest.approx(t['event_losses'].loss.sum())
    assert t['event_losses'].loss.max() <= sum(x['value'] for x in config['assets'])
    assert t['aal_by_taxonomy'].aal.sum() == pytest.approx(s['analytic_aal'])


@pytest.mark.parametrize('mode', ['independent', 'common_uniform'])
def test_deterministic_and_dependence_mean(config, mode):
    config['damage_dependence'] = mode
    a, ta = run(config)
    b, tb = run(config)
    assert a == b
    assert ta['annual_losses'].equals(tb['annual_losses'])
    assert abs(a['simulated_aal']-a['analytic_aal']) < 5*a['aal_monte_carlo_standard_error']


@pytest.mark.parametrize('zero', ['rate', 'pga', 'value'])
def test_zero_cases(config, zero):
    for e in config['events']:
        if zero == 'rate':
            e['annual_rate'] = 0
        if zero == 'pga':
            e['pga_g'] = [0]*len(config['assets'])
    if zero == 'value':
        for a in config['assets']:
            a['value'] = 0
    s, t = run(config)
    assert s['analytic_aal'] == s['simulated_aal'] == 0
    assert t['annual_losses'].maximum_event_loss.sum() == 0


@pytest.mark.parametrize('field,value', [('annual_rate', -1), ('annual_rate', float('nan')), ('pga_g', [0.1])])
def test_invalid_events(config, field, value):
    config['events'][0][field] = value
    with pytest.raises(ValueError):
        validate(config)


def test_invalid_fragility_and_mdr(config):
    with pytest.raises(ValueError):
        damage_probabilities([1], [0.3, 0.1], 0.4)
    config['taxonomies']['synthetic_weak']['mdr_means'][-1] = 1.1
    with pytest.raises(ValueError):
        validate(config)


def test_sensitivity_preserves_event_set(config):
    _, independent = run(config)
    config['damage_dependence'] = 'common_uniform'
    _, dependent = run(config)
    columns = ['year', 'event_id']
    assert independent['event_losses'][columns].equals(dependent['event_losses'][columns])
