import json
import numpy as np
import pandas as pd
import pytest
from src.data.freeze_geoai import eligible_manifest, CONFIG
from src.models.damage_metrics import probability_diagnostics
from src.features.satmae_preflight import normalize


def test_severe_endpoint_sums_both_upper_classes_and_respects_weights():
    p = np.array([[.1,.1,.2,.3,.3],[.2,.3,.3,.1,.1]])
    d = probability_diagnostics([4,2],p,[2,1])
    assert d['severe_or_worse_Brier'] == pytest.approx((2*.4**2+.2**2)/3)
    assert d['any_damage_Brier'] == pytest.approx((2*.1**2+.2**2)/3)
    assert sum(b['weight'] for b in d['severe_or_worse_reliability']) == 3


def test_grade4_prediction_against_grade3_has_zero_exceedance_error():
    d = probability_diagnostics([3], [[0,0,0,0,1]])
    assert d['normalized_RPS'] == .25
    assert d['severe_or_worse_Brier'] == 0
    assert d['severe_or_worse_reliability'][-1]['observed'] == 1
    assert d['severe_or_worse_reliability'][0]['observed'] is None


def test_reject_invalid_probability_vectors():
    with pytest.raises(ValueError):
        probability_diagnostics([3], [[0,0,0,.5,.4]])


def test_two_hazard_components_and_fixed_compression_contract():
    c = json.loads(CONFIG.read_text())
    assert c['allowlists']['H'] == ['log_PGA_m78_g','log_PGA_m75_g']
    assert c['hazard_sensitivity']['columns'] == ['log_PGA_m78_g']
    assert c['compression_sensitivity']['components'] == 64
    assert c['model_fitting_allowed'] is False


def test_normalization_is_uint8_quantization_not_zscore():
    c = json.loads(CONFIG.read_text())['encoder']
    means = np.asarray(c['mean'])[:,None,None]/10000
    x = np.broadcast_to(means,(10,96,96)).copy()
    y = normalize(x,c)
    np.testing.assert_allclose(y,127/255,atol=1e-7)
    assert y.dtype == np.float32
    with pytest.raises(ValueError):
        normalize(np.full((10,96,96),np.nan),c)


def test_pinned_grid_sampling_units_event_and_outside_bounds(tmp_path, monkeypatch):
    from src.data import geoai_feasibility as module
    monkeypatch.setattr(module,'RAW',tmp_path)
    monkeypatch.setattr(module,'OUT',tmp_path)
    fields = [('LON','dd'),('LAT','dd'),('PGA','%g'),('PGV','cm/s'),('PSA03','%g'),('PSA06','%g'),('PSA10','%g')]
    xml = '<shakemap_grid event_id="second"><event event_id="second"/><grid_specification nlon="2" nlat="2"/>'
    xml += ''.join(f'<grid_field index="{i}" name="{n}" units="{u}"/>' for i,(n,u) in enumerate(fields,1))
    xml += '<grid_data>36 37 10 5 30 99 40\n37 37 20 6 40 99 50\n36 36 30 7 50 99 60\n37 36 40 8 60 99 70</grid_data></shakemap_grid>'
    path=tmp_path/'grid.xml';path.write_text(xml)
    survey=pd.DataFrame({'building_id':['inside','outside'],'latitude':[37.,40.],'longitude':[36.,36.]})
    module.sample_hazard(survey,False,filename='grid.xml',url='https://example.invalid/pinned',checksum=module.digest(path),event_id='second')
    h=pd.read_parquet(tmp_path/'hazard.parquet')
    assert h.PGA_g.iloc[0] == .1 and h.SA_1p0_g.iloc[0] == .4
    assert h.PGV_cm_s.iloc[0] == 5
    assert np.isnan(h.PGA_g.iloc[1]) and not h.in_grid.iloc[1]
    with pytest.raises(ValueError,match='event'):
        module.sample_hazard(survey,False,filename='grid.xml',checksum=module.digest(path),event_id='wrong')
