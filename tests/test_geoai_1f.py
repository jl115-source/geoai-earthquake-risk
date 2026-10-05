import json
import numpy as np
import pandas as pd
import pytest

from src.data.freeze_geoai import CONFIG, eligible_manifest, partitions, structure_family
from src.data.geoai_feasibility import BANDS, clear_mask, composite, ranked_candidates, physical_im, reflectance_from_asset


def test_asset_offset_and_hazard_units_are_not_interchangeable():
    assert reflectance_from_asset(np.array([2000]), {'scale': .0001, 'offset': -.1})[0] == pytest.approx(.1)
    assert physical_im([50], 'PGA', '%g')[0] == .5
    assert physical_im([50], 'PGV', 'cm/s')[0] == 50
    with pytest.raises(ValueError, match='Unexpected'):
        physical_im([50], 'PGA', 'g')


def test_cloud_shadow_and_edges_are_rejected():
    scl = np.full((7, 7), 4)
    scl[3, 3] = 3
    clear = clear_mask(scl)
    assert clear.sum() == 40
    assert not clear[2:5, 2:5].any()
    for code in [0, 1, 3, 7, 8, 9, 10, 11]:
        assert not clear_mask(np.full((2, 2), code)).any()


def test_composite_never_fills_unobserved_pixels():
    a = np.ones((10, 2, 2))
    mask = np.array([[True, True], [False, False]])
    value, support = composite([a], [mask])
    assert value is None
    value, support = composite([a, 3*a], [mask, ~mask])
    assert np.all(support == 1)
    assert np.all(value[:, 0, :] == 1)
    assert np.all(value[:, 1, :] == 3)


def test_catalog_selection_rejects_future_cloud_and_missing_bands():
    def item(date, cloud=0):
        return {'id': date, 'properties': {'datetime': date, 'eo:cloud_cover': cloud},
                'assets': {b: {} for b in BANDS + ['scl']},
                'geometry': {'type':'Polygon', 'coordinates': [[[35,35],[38,35],[38,38],[35,38],[35,35]]]}}
    past = item('2022-08-01T00:00:00Z')
    missing = item('2022-09-01T00:00:00Z')
    del missing['assets']['blue']
    candidates = [past, item('2023-02-07T00:00:00Z'), item('2022-07-01T00:00:00Z', 99), missing]
    assert ranked_candidates(candidates, 36, 36) == [past]
    assert not ranked_candidates(candidates, 40, 40)


def test_structure_design_proxy_discards_height():
    assert structure_family('RC MRF (8+ Storeys)') == structure_family('RC MRF (1-3 Storeys)') == 'RC_MRF'
    assert structure_family(None) is None
    assert structure_family('unknown new source label') is None
    assert structure_family('Unreinforced masonry') == 'UNREINFORCED_MASONRY'


def fixture_tables():
    s = pd.DataFrame({'building_id':['a','b','c','d'], 'city':['A','A','B','B'],
                      'latitude':[37,37,37.001,37.001], 'longitude':[37,37,37,37],
                      'damage_grade':[1,2,0,0], 'structure_type':['RC MRF (1-3 Storeys)']*4})
    a = s[['building_id','city']].assign(location_key=['x','x','y','y'], eo_status='complete_clear_composite', worldcover_coverage=1., dem_coverage=1.)
    h = s[['building_id']].assign(PGA_g=.2, in_grid=True)
    c = {'coordinate_city_median_limit_m':10000,'city_domains':['A','B'], 'validation_overrides':{}, 'cross_partition_buffer_m':2000}
    return s,a,h,c


def test_all_rows_retained_conflicts_quarantined_and_sites_weighted():
    s,a,h,c = fixture_tables()
    f = eligible_manifest(s,a,h,c)
    assert len(f) == 4
    assert not f.eligible.iloc[:2].any()
    assert f.exclusion_reasons.iloc[0] == 'conflicting_labels_at_exact_coordinate'
    assert f.site_weight.iloc[2:].tolist() == [.5,.5]
    with pytest.raises(ValueError, match='retain every'):
        eligible_manifest(s,a.iloc[:3],h,c)


def test_context_buffer_quarantines_both_sides():
    s,a,h,c = fixture_tables()
    s['damage_grade'] = 1
    f = eligible_manifest(s,a,h,c)
    folds = partitions(f,c)
    assert folds.partition.eq('excluded').all()
    assert folds.exclusion_reasons.eq('cross_partition_2km_context_buffer').all()
    s.loc[s.city.eq('B'), 'latitude'] = 38
    f = eligible_manifest(s,a,h,c)
    folds = partitions(f,c)
    assert set(folds.partition) == {'test','validation'}


def test_frozen_allowlist_and_no_training_gate():
    c = json.loads(CONFIG.read_text())
    assert c['model_fitting_allowed'] is False
    assert c['allowlists']['X'] == ['structure_family']
    assert c['allowlists']['H'] == ['log_PGA_g']
    assert 'This_study' in c['prohibited'] and 'floors' in c['prohibited']
    assert c['encoder']['published'] < c['event_cutoff']
    assert c['arms']['HX_GeoAI'] == ['H','X','Z_GeoAI']


def test_unknown_coverage_fails_closed():
    s,a,h,c = fixture_tables()
    a.loc[2, 'dem_coverage'] = np.nan
    f = eligible_manifest(s,a,h,c)
    assert not f.eligible.iloc[2]
    assert 'incomplete_DSM' in f.exclusion_reasons.iloc[2]


def test_cache_rejects_changed_spec_and_tampering(tmp_path, monkeypatch):
    from src.data import geoai_feasibility as module
    monkeypatch.setattr(module, 'spec_hash', lambda: 'current')
    with pytest.raises(ValueError, match='Stale'):
        module.validate_cache({'audit_spec_hash':'old'}, tmp_path)
    chip = tmp_path / 'reflectance.npz'
    chip.write_bytes(b'original')
    report = {'audit_spec_hash':'current', 'status':'complete_clear_composite',
              'chip_sha256': module.digest(chip), 'worldcover_2021':{}, 'copernicus_dem_2021':{}}
    module.validate_cache(report,tmp_path)
    chip.write_bytes(b'changed')
    with pytest.raises(ValueError, match='checksum'):
        module.validate_cache(report,tmp_path)


def test_coordinate_identity_never_uses_display_rounding():
    from src.data.geoai_feasibility import location_key
    a, b = 37.4788819623, 37.4788819622673
    assert f'{a:.10f}' == f'{b:.10f}'
    assert location_key(a,37) != location_key(b,37)


def test_warp_masks_outside_source_but_keeps_valid_zero():
    import rasterio
    from rasterio.io import MemoryFile
    from rasterio.transform import from_bounds
    from src.data.geoai_feasibility import read_window
    with MemoryFile() as mem:
        with mem.open(driver='GTiff',height=2,width=2,count=1,dtype='float32',
                      crs='EPSG:4326',transform=from_bounds(-.01,-.01,.01,.01,2,2)) as ds:
            ds.write(np.zeros((2,2),dtype='float32'),1)
            result=read_window(ds,(-2000,-2000,2000,2000),target_crs=3857,size=10)
            assert np.ma.getmaskarray(result).any()
            assert not np.ma.getmaskarray(result).all()
            assert (result.compressed()==0).all()


def test_engineered_moments_do_not_fill_undefined_ratios(tmp_path, monkeypatch):
    from src.data import freeze_geoai as module
    monkeypatch.setattr(module, 'RAW', tmp_path)
    folder = tmp_path / 'locations' / 'test'
    folder.mkdir(parents=True)
    np.savez(folder/'reflectance.npz', reflectance=np.zeros((10,96,96)))
    np.savez(folder/'worldcover_2021.npz', values=np.full((96,96),50))
    np.savez(folder/'copernicus_dem_2021.npz', values=np.full((96,96),5.))
    f = module.engineered_features({'location_key':'test'})
    assert f['red_mean'] == f['nir_std'] == f['dsm_slope_mean'] == 0
    assert f['built_fraction_250m'] == f['built_fraction_480m'] == 1
    assert f['vegetation_fraction_250m'] == 0
    assert f['dsm_mean'] == 5
    assert set(f) == set(json.loads(CONFIG.read_text())['allowlists']['Z_engineered'])
