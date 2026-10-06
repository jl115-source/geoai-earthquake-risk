import json
import zipfile

import geopandas as gpd
import pytest
from shapely.geometry import box, Polygon

from src.data import audit_zagreb_copernicus as audit


def test_many_parts_are_not_many_labelled_buildings():
    reference=gpd.GeoDataFrame({'geometry':[box(0,0,10,10),box(20,0,30,10)]},crs=32633)
    damage=gpd.GeoDataFrame({'damage_gra':['1','2','4'],
        'geometry':[box(0,0,5,10),box(5,0,10,10),box(20,0,30,10)]},crs=32633)
    report=audit.link_report(reference,damage)
    assert report['all_geometry_intersections']['references_with_multiple_damage_records']==1
    assert report['iou_thresholds']['0.99']['mutually_unique_pairs']==1
    assert report['topologically_equal_valid_geometry_pairs']==1
    assert report['iou_0p99_native_damage_counts']=={'4':1}


def test_invalid_geometry_is_reported_not_repaired():
    invalid=Polygon([(0,0),(10,10),(0,10),(10,0),(0,0)])
    reference=gpd.GeoDataFrame({'geometry':[invalid]},crs=32633)
    damage=gpd.GeoDataFrame({'damage_gra':['1'],'geometry':[box(0,0,10,10)]},crs=32633)
    report=audit.link_report(reference,damage)
    assert report['intersection_pairs_touching_invalid_geometry']==1
    assert report['valid_positive_area_intersections']['pairs']==0
    assert report['iou_thresholds']['0.99']['damage_records_unmatched']==1
    assert audit.profile(reference)['geometry']['invalid_nonempty']==1
    assert not reference.is_valid.iloc[0]


def test_crs_must_match_and_be_projected():
    frame=gpd.GeoDataFrame({'geometry':[box(0,0,1,1)]},crs=4326)
    with pytest.raises(ValueError,match='projected'):
        audit.link_report(frame,frame)


def test_extract_rejects_traversal_before_writing(tmp_path):
    p=tmp_path/'bad.zip'
    with zipfile.ZipFile(p,'w') as z:
        z.writestr('ok','text');z.writestr('../escape','bad')
    with pytest.raises(ValueError,match='Unsafe'):
        audit.extract(p,tmp_path/'extract')
    assert not (tmp_path/'escape').exists()
    assert not (tmp_path/'extract/ok').exists()


def test_unpinned_archive_rejected(tmp_path):
    p=tmp_path/'bad.zip';p.write_bytes(b'bad')
    with pytest.raises(ValueError,match='pin'):
        audit.run(p,tmp_path/'out')


def test_actual_gdb_regression_if_available(tmp_path):
    archive=audit.RAW/'EMSN074_geospatial.zip'
    if not archive.exists(): pytest.skip('Acquire EMSN074 for actual GDB regression')
    r=audit.run(archive,tmp_path)
    assert r['layer_count']==30 and r['spatial_layers']==14
    assert r['layers'][audit.REFERENCE]['features']==29398
    assert r['layers'][audit.DAMAGE]['features']==556
    assert r['damage_valid_geometries_and_recognized_codes']==556
    assert [x['count'] for x in r['damage_categories']]==[244,136,155,21]
    assert r['linkage']['iou_thresholds']['0.99']['mutually_unique_pairs']==99
    assert r['unlabelled_reference_buildings_are_not_undamaged']
    committed=json.loads((audit.RESULTS/'layer_audit.json').read_text())
    # Runtime details may differ across operating systems; measurements must not.
    r.pop('runtime');committed.pop('runtime')
    assert r==committed
