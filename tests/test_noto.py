"""Noto acquisition safety, full-record accounting, and optional pinned-data check."""
import hashlib
import json

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import MultiPolygon, Polygon, box

from src.data import acquire_large_geoai as acquire
from src.data import audit_noto as audit


@pytest.fixture
def frame():
    polygon = MultiPolygon([box(136.9,37.1,136.901,37.101)])
    bad = MultiPolygon([Polygon([(137,37),(137.01,37.01),(137,37.01),(137.01,37),(137,37)])])
    return gpd.GeoDataFrame({
        'fid': [1,2,3,4,5,6], 's_fid': ['manual','manual','a','a','b','c'],
        'source': [None,'',None,None,None,None],
        'damage_val': [0,1,9,99,1,0], 'damage_2': [0,0,9,99,1,0],
        'municipality': ['石川県、輪島市、南町']*5+[None], 'conf': ['single']*5+[None],
        'GSI_fire': [0,0,1,0,0,np.nan], 'GSI_tsunami': [0,0,1,0,0,0],
        'GSI_slope_failure': [0,0,0,0,0,0], 'USGS_MMI': [8,8,9,np.nan,13,np.inf],
        'geometry': [polygon,polygon.reverse(),bad,MultiPolygon(),None,MultiPolygon([box(138,37,138.001,37.001)])],
    },crs=4326)


def test_full_accounting_no_repairs(frame):
    before=frame.copy(deep=True)
    result=audit.summarize(frame)
    pd.testing.assert_frame_equal(frame,before)
    assert result['row_count']==6
    assert result['geometry']['null']==1
    assert result['geometry']['empty']==1
    assert result['geometry']['invalid_nonempty']==1
    assert result['geometry']['normalized_wkb_duplicates']['extra_rows_after_first']==1
    assert result['geometry']['topologically_equal_valid_polygon_pairs']==1
    assert result['identifiers']['s_fid_excluding_manual']['extra_rows_after_first']==1
    assert result['damage_val']=={'0':2,'1':2,'9':1,'99':1}
    assert result['damage'] is None
    assert result['damage_2_vs_damage_val_disagreements']==1
    assert result['USGS_MMI']['missing']==1
    assert result['USGS_MMI']['nonfinite_non_null']==1
    assert result['USGS_MMI']['outside_1_to_12']==1
    assert result['secondary_perils']['any_flag']==1
    assert result['secondary_perils']['multiple_flags']==1
    assert result['secondary_perils']['all_three_explicit_zero']==4
    assert result['secondary_perils']['unknown_without_positive_flag']==1
    assert result['secondary_perils']['binary_target_no_flags']==3


def test_unknown_values_preserved(frame):
    frame.loc[0,'damage_val']=7
    frame.loc[0,'GSI_fire']=2
    result=audit.summarize(frame)
    assert result['unknown_damage_codes']['damage_val']=={'7':1}
    assert result['secondary_perils']['unexpected_flag_values']['GSI_fire']=={'2.0':1}
    assert result['secondary_perils']['all_three_explicit_zero']==3


def test_schema_does_not_alias_damage(frame):
    with pytest.raises(ValueError,match='damage_2'):
        audit.validate_schema(frame.rename(columns={'damage_2':'damage'}))
    with pytest.raises(ValueError,match='4326'):
        audit.validate_schema(frame.to_crs(6675))
    frame['USGS_MMI']=frame.USGS_MMI.astype(str)
    with pytest.raises(ValueError,match='USGS_MMI'):
        audit.validate_schema(frame)


def test_aggregate_municipality_preserves_native(frame,tmp_path):
    assert audit.municipality_level(pd.Series(['石川県、輪島市、南町','bad',None])).tolist()==['輪島市',None,None]
    audit.aggregates(frame,tmp_path/'one');audit.aggregates(frame,tmp_path/'two')
    for path in (tmp_path/'one').glob('*.csv'):
        assert path.read_bytes()==(tmp_path/'two'/path.name).read_bytes()
    counts=pd.read_csv(tmp_path/'one/municipality_native_counts.csv')
    assert counts['count'].sum()==6


class Response:
    def __init__(self,content): self.content=content
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def raise_for_status(self): pass
    def iter_content(self,*args): yield self.content


def test_download_checksum_before_promotion(tmp_path,monkeypatch):
    monkeypatch.setattr(acquire,'ROOT',tmp_path)
    monkeypatch.setattr(acquire.requests,'get',lambda *a,**kw:Response(b'bad'))
    path=tmp_path/'raw/test.gpkg'
    with pytest.raises(ValueError,match='MD5'):
        acquire.download('https://example.test/test',path,hashlib.md5(b'good').hexdigest())
    assert not path.exists()
    assert not path.with_suffix('.gpkg.part').exists()
    monkeypatch.setattr(acquire.requests,'get',lambda *a,**kw:Response(b'good'))
    result=acquire.download('https://example.test/test',path,hashlib.md5(b'good').hexdigest())
    assert result['bytes']==4 and path.read_bytes()==b'good'


def test_cached_download_validated_without_network(tmp_path,monkeypatch):
    monkeypatch.setattr(acquire,'ROOT',tmp_path)
    path=tmp_path/'test.gpkg';path.write_bytes(b'good')
    def unexpected(*args,**kwargs): raise AssertionError('network on cached input')
    monkeypatch.setattr(acquire.requests,'get',unexpected)
    acquire.download('https://example.test/test',path,hashlib.md5(b'good').hexdigest())
    with pytest.raises(ValueError,match='MD5'):
        acquire.download('https://example.test/test',path,'wrong')
    assert path.read_bytes()==b'good'


def test_reject_unpinned_audit_input(tmp_path):
    path=tmp_path/'bad.gpkg';path.write_bytes(b'not a geopackage')
    with pytest.raises(ValueError,match='checksum'):
        audit.load_noto(path)


def test_pinned_full_dataset_if_available():
    path=acquire.RAW/acquire.NOTO_REL
    if not path.exists(): pytest.skip('Run acquire_large_geoai noto for full-data validation')
    frame=audit.load_noto(path)
    result=audit.summarize(frame)
    assert len(frame)==140208
    assert result['damage_val']=={'0':112275,'1':3461,'9':9437,'99':15035}
    assert result['secondary_perils']['binary_target_no_flags']==112228
    assert result['USGS_MMI']['missing']==0
    assert result['geometry']['invalid_nonempty']==0
    recorded=json.loads((acquire.ROOT/'docs/noto_2024_execution.json').read_text())
    for key,value in result.items(): assert recorded[key]==value,key
