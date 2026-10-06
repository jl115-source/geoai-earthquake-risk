"""Measure EMSN074 layers and footprint linkage, without creating training labels."""
import argparse
import json
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
import pandas as pd
import pyogrio
import shapely

from src.data.acquire_zagreb_copernicus import RAW, RESULTS, digest

ARCHIVE_SHA256 = '96fdaa2e40fc0e9a74f6a1b075df563b700d40e890ea84bc864877a0b6c36c93'
GDB_NAME = 'EMSN074_STD_UTM33_v01.gdb'
REFERENCE = 'P02_building_poly'
DAMAGE = 'P08_damage_assessment_poly'
RECONSTRUCTION = 'P09_reconstruction_monitoring_poly'


def counts(series):
    return {str(k) if pd.notna(k) else '<NULL>': int(v)
            for k,v in sorted(series.value_counts(dropna=False).items(),key=lambda x:str(x[0]))}


def extract(archive, destination):
    """Reject traversal/symlinks and corrupted members before extraction."""
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            target = (destination/info.filename).resolve()
            if not target.is_relative_to(destination.resolve()) or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Unsafe ZIP member')
        if z.testzip() is not None:
            raise ValueError('ZIP CRC failure')
        z.extractall(destination)


def metadata(gdb):
    domains, layers = {}, {}
    items = pyogrio.read_dataframe(gdb,layer='GDB_Items')
    for text in items.Definition.dropna():
        root = ET.fromstring(text)
        name = root.findtext('DomainName')
        if name:
            domains[name] = {x.findtext('Code'):x.findtext('Name') for x in root.findall('.//CodedValue')}
        if root.findtext('DatasetType') == 'esriDTFeatureClass':
            layers[root.findtext('Name')] = {
                'alias':root.findtext('AliasName'), 'oid_field':root.findtext('OIDFieldName'),
                'relationship_classes':[x.text for x in root.findall('./RelationshipClassNames/*')],
                'fields':{f.findtext('Name'):{'alias':f.findtext('AliasName'),
                           'domain':f.findtext('DomainName')} for f in root.findall('.//GPFieldInfoEx')},
            }
    used = {f['domain'] for layer in layers.values() for f in layer['fields'].values() if f['domain']}
    return {'layers':layers,'domains':{k:domains[k] for k in sorted(used) if k in domains}}


def profile(frame):
    columns = {}
    for col in frame.columns:
        if col == 'geometry': continue
        s=frame[col]
        columns[col]={'dtype':str(s.dtype),'nulls':int(s.isna().sum()),'distinct':int(s.nunique()),
                      'blank_strings':int(s.map(lambda x:isinstance(x,str) and not x.strip()).sum())}
        if s.nunique() <= 100: columns[col]['native_counts']=counts(s)
    result={'features':len(frame),'columns':columns,
            'local_fid_unique':bool(frame.index.is_unique),'crs':None,'geometry':None}
    if 'geometry' in frame and len(frame):
        g=frame.geometry;present=~g.isna() & ~g.is_empty
        result['crs']=frame.crs.to_string() if frame.crs else None
        result['bounds_native']=frame.total_bounds.tolist()
        result['bounds_wgs84']=frame.to_crs(4326).total_bounds.tolist() if frame.crs else None
        result['geometry']={'types':counts(g.geom_type),'nulls':int(g.isna().sum()),
            'empty':int(g.is_empty.sum()),'invalid_nonempty':int((present & ~g.is_valid).sum()),
            'normalized_duplicate_extra_rows':int(pd.Series(shapely.to_wkb(shapely.normalize(g[present].array))).duplicated().sum())}
    return result


def link_report(reference, damage):
    """Diagnostic geometry linkage. No join on layer-local FIDs; no geometry repair."""
    if reference.crs != damage.crs or reference.crs is None or reference.crs.is_geographic:
        raise ValueError('Linkage requires a common projected CRS')
    a,b=reference.geometry.array,damage.geometry.array
    i,j=shapely.STRtree(a).query(b,predicate='intersects')
    valid=shapely.is_valid(a[j]) & shapely.is_valid(b[i])
    raw_i,raw_j=i.copy(),j.copy()
    i,j=i[valid],j[valid]
    area=shapely.area(shapely.intersection(b[i],a[j]))
    positive=area>0;i,j,area=i[positive],j[positive],area[positive]
    iou=area/(shapely.area(b[i])+shapely.area(a[j])-area)
    def cardinality(left,right):
        dc=np.bincount(left,minlength=len(b));rc=np.bincount(right,minlength=len(a))
        return {'pairs':len(left),'damage_records_matched':int((dc>0).sum()),
            'reference_records_matched':int((rc>0).sum()),'damage_records_unmatched':int((dc==0).sum()),
            'damage_records_with_multiple_references':int((dc>1).sum()),
            'references_with_multiple_damage_records':int((rc>1).sum()),
            'mutually_unique_pairs':int(((dc[left]==1)&(rc[right]==1)).sum())}
    thresholds={str(t):cardinality(i[iou>=t],j[iou>=t]) for t in [.5,.9,.95,.99,.999]}
    exact=shapely.equals(b[i],a[j])
    return {'method':'Diagnostic spatial links only; exact equality and fixed IoU thresholds. Invalid geometries excluded from area/equality comparisons without repair. No row-level labels created.',
        'all_geometry_intersections':cardinality(raw_i,raw_j),
        'intersection_pairs_touching_invalid_geometry':int((~valid).sum()),
        'damage_records_touching_invalid_geometry':len(set(raw_i[~valid])),
        'valid_positive_area_intersections':cardinality(i,j),
        'topologically_equal_valid_geometry_pairs':int(exact.sum()),
        'iou_thresholds':thresholds,
        'valid_damage_records_at_least_95pct_covered_by_reference':len(set(i[area/shapely.area(b[i])>=.95])),
        'iou_0p99_native_damage_counts':counts(damage.iloc[np.unique(i[iou>=.99])].damage_gra),
        'shared_non_geometry_fields':sorted(set(reference.columns)&set(damage.columns)-{'geometry'}),
        'id_linkage':'OBJECTID/FID is layer-local; shared aoi_id, or_src_id and other attributes are not unique building identifiers.'}


def run(archive,output):
    if digest(archive)!=ARCHIVE_SHA256:
        raise ValueError('Archive differs from audited EMSN074 pin; review new version explicitly')
    # Fresh extraction avoids stale files or modifications in an earlier unpacked GDB.
    with tempfile.TemporaryDirectory(dir=archive.parent,prefix='audit_') as temporary:
        extract(archive,Path(temporary));gdb=Path(temporary)/GDB_NAME
        layers=pyogrio.list_layers(gdb)
        frames={name:pyogrio.read_dataframe(gdb,layer=name,fid_as_index=True) for name,_ in layers}
        profiles={name:profile(f) for name,f in frames.items()}
        meta=metadata(gdb)
        link=link_report(frames[REFERENCE],frames[DAMAGE])
        damage=frames[DAMAGE]
        domain_name=meta['layers'][DAMAGE]['fields']['damage_gra']['domain']
        categories=meta['domains'][domain_name]
        report={'archive_sha256':ARCHIVE_SHA256,'layers':profiles,'metadata':meta,
            'layer_count':len(layers),'spatial_layers':sum(g is not None for _,g in layers),
            'reference_building_layers':[REFERENCE,'P02_building_point'],
            'damage_assessment_layers':[DAMAGE],'reconstruction_layers':[RECONSTRUCTION],
            'damage_categories':[{'native_value':k,'documented_name':categories.get(k), 'count':v}
                                 for k,v in counts(damage.damage_gra).items()],
            'damage_valid_geometries_and_recognized_codes':int((damage.is_valid & ~damage.is_empty & damage.damage_gra.isin(categories)).sum()),
            'linkage':link,'decision':'auxiliary_only_not_large_N_building_vulnerability_training',
            'unlabelled_reference_buildings_are_not_undamaged':True,
            'models_fitted':False,'target_harmonized':False,'merge_authorized':False,
            'runtime':{'pyogrio':pyogrio.__version__,'GEOS':shapely.geos_version_string}}
    output.mkdir(parents=True,exist_ok=True)
    (output/'layer_audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False,sort_keys=True,allow_nan=False)+'\n')
    pd.DataFrame([{'layer':k,'features':v['features'],'crs':v['crs'],
                   'invalid':v['geometry']['invalid_nonempty'] if v['geometry'] else None}
                  for k,v in profiles.items()]).to_csv(output/'layer_counts.csv',index=False)
    pd.DataFrame(report['damage_categories']).to_csv(output/'damage_counts.csv',index=False)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,default=RAW/'EMSN074_geospatial.zip')
    p.add_argument('--output',type=Path,default=RESULTS)
    args=p.parse_args();r=run(args.archive,args.output)
    print(json.dumps({k:r[k] for k in ['layer_count','spatial_layers','damage_categories','linkage','decision']},indent=2))


if __name__=='__main__':main()
