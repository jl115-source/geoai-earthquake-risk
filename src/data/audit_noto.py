"""Offline full-record Noto audit: native labels, aggregate evidence, no fitting."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
import sqlite3
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
import pyogrio
import shapely

from src.data.acquire_large_geoai import ROOT, RAW, NOTO_REL, NOTO_MD5, digest

FIELDS = {'fid', 's_fid', 'source', 'damage_val', 'municipality', 'conf',
          'damage_2', 'GSI_fire', 'GSI_tsunami', 'GSI_slope_failure', 'USGS_MMI', 'geometry'}
FLAGS = ['GSI_fire', 'GSI_slope_failure', 'GSI_tsunami']
NATIVE_LABELS = {0: 'Survived', 1: 'Destroyed', 9: 'Obscured', 99: 'Missing/inconsistent'}
COLORS = {0: '#3784ba', 1: '#c82732', 9: '#ddb335', 99: '#888888'}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True,
                               allow_nan=False) + '\n', encoding='utf-8')


def counts(series):
    return {str(k) if pd.notna(k) else '<NULL>': int(v)
            for k, v in sorted(series.value_counts(dropna=False).items(), key=lambda x: str(x[0]))}


def duplicate_summary(series):
    values = series.dropna().value_counts()
    repeated = values[values > 1]
    return {'distinct_non_null': int(len(values)), 'duplicate_groups': int(len(repeated)),
            'rows_in_duplicate_groups': int(repeated.sum()),
            'extra_rows_after_first': int((repeated - 1).sum())}


def municipality_level(series):
    # Explicit aggregate-only derivation from native Prefecture-City-Town strings.
    def parse(value):
        if not isinstance(value, str):
            return None
        parts = value.split('、')
        return parts[1] if len(parts) >= 2 and parts[1] else None
    return series.map(parse)


def peril_masks(frame):
    # Null/unknown flags must never enter the apparent shaking-only count.
    flags = frame[FLAGS]
    return flags.eq(1).any(axis=1), flags.eq(0).all(axis=1)


def validate_schema(frame):
    missing = FIELDS - set(frame.columns)
    if missing:
        raise ValueError(f'Missing native Noto fields: {sorted(missing)}')
    if frame.crs is None or frame.crs.to_epsg() != 4326:
        raise ValueError('Expected EPSG:4326')
    for col in ['fid', 'damage_2', 'damage_val', 'USGS_MMI', *FLAGS]:
        if not pd.api.types.is_numeric_dtype(frame[col]):
            raise ValueError(f'Expected numeric native field: {col}')


def load_noto(path):
    if digest(path, 'md5') != NOTO_MD5:
        raise ValueError('Noto checksum mismatch; refusing unpinned input')
    frame = pyogrio.read_dataframe(path, layer='v2.5', fid_as_index=True).reset_index()
    validate_schema(frame)
    return frame.sort_values('fid', kind='stable').reset_index(drop=True)


def inspect_container(path):
    with sqlite3.connect(f'{path.resolve().as_uri()}?mode=ro', uri=True) as conn:
        columns = [{'name': r[1], 'declared_type': r[2], 'not_null': bool(r[3]),
                    'primary_key': bool(r[5])} for r in conn.execute('pragma table_info("v2.5")')]
        styles = []
        for (qml,) in conn.execute('select styleQML from layer_styles'):
            renderer = ET.fromstring(qml).find('renderer-v2')
            styles.append({'attribute': renderer.get('attr'), 'categories': [
                {'value': c.get('value'), 'label': c.get('label')}
                for c in renderer.findall('./categories/category')]})
        return {'layers': pyogrio.list_layers(path).tolist(), 'sqlite_columns': columns,
                'embedded_styles': styles,
                'sqlite_integrity_check': conn.execute('pragma integrity_check').fetchone()[0]}


def summarize(frame):
    validate_schema(frame)
    geom = frame.geometry
    present = ~geom.isna() & ~geom.is_empty
    valid = present & geom.is_valid
    wkb = pd.Series(shapely.to_wkb(shapely.normalize(geom[present].array)))
    gg = geom[valid].array
    left, right = shapely.STRtree(gg).query(gg, predicate='intersects')
    select = left < right
    left, right = left[select], right[select]
    equal = shapely.equals(gg[left], gg[right])
    mmi = frame.USGS_MMI
    finite = np.isfinite(mmi)
    stats = {str(k): float(v) if pd.notna(v) else None for k, v in
             mmi[finite].describe(percentiles=[.01,.05,.25,.5,.75,.95,.99]).items()}
    any_flag, no_flag = peril_masks(frame)
    binary = frame.damage_val.isin([0, 1])
    bounds = geom[present].bounds
    invalid_coords = (~np.isfinite(bounds).all(axis=1) | bounds.minx.lt(-180)
                      | bounds.maxx.gt(180) | bounds.miny.lt(-90) | bounds.maxy.gt(90))
    xy, owners = shapely.get_coordinates(geom.array, return_index=True)
    bad_vertex = (~np.isfinite(xy).all(axis=1) | (np.abs(xy[:,0]) > 180)
                  | (np.abs(xy[:,1]) > 90))
    return {
        'row_count': len(frame), 'crs': frame.crs.to_string(),
        'bounds_wgs84_minx_miny_maxx_maxy': [float(x) for x in frame.total_bounds],
        'geometry': {'types': counts(geom.geom_type), 'null': int(geom.isna().sum()),
            'empty': int(geom.is_empty.sum()), 'invalid_nonempty': int((present & ~geom.is_valid).sum()),
            'invalid_reasons': counts(pd.Series(shapely.is_valid_reason(geom[present & ~geom.is_valid].array))),
            'out_of_range_or_nonfinite_bounds': int(invalid_coords.sum()),
            'records_with_invalid_coordinate_vertices': int(len(np.unique(owners[bad_vertex]))),
            'normalized_wkb_duplicates': duplicate_summary(wkb),
            'topologically_equal_valid_polygon_pairs': int(equal.sum()),
            'rows_in_topologically_equal_pairs': int(len(np.unique(np.r_[left[equal],right[equal]]))),
            'distinct_overlapping_valid_polygon_pairs': int(shapely.overlaps(gg[left],gg[right]).sum()),
            'duplicate_test': 'Normalized exact-coordinate WKB plus topological equals on valid nonempty polygons; no tolerance or repair'},
        'columns': [{'name': col, 'dtype': str(frame[col].dtype),
            'null_count': int(frame[col].isna().sum()), 'null_fraction': float(frame[col].isna().mean()),
            'blank_string_count': int(frame[col].map(lambda x: isinstance(x,str) and not x.strip()).sum())}
            for col in frame.columns],
        'identifiers': {'fid': duplicate_summary(frame.fid), 's_fid': duplicate_summary(frame.s_fid),
            's_fid_manual_rows': int(frame.s_fid.eq('manual').sum()),
            's_fid_excluding_manual': duplicate_summary(frame.loc[frame.s_fid.ne('manual'),'s_fid'])},
        'damage_field_discrepancy': 'Published damage field absent; actual damage_2 preserved. Equivalence to documented original damage field not independently established.',
        'damage': None, 'damage_2': counts(frame.damage_2), 'damage_val': counts(frame.damage_val),
        'damage_2_vs_damage_val_disagreements': int(frame.damage_2.ne(frame.damage_val).sum()),
        'unknown_damage_codes': {c: counts(frame.loc[~frame[c].isin(NATIVE_LABELS) & frame[c].notna(),c])
                                 for c in ['damage_2','damage_val']},
        'confidence': counts(frame.conf),
        'municipality_native_unique_non_null': int(frame.municipality.nunique()),
        'municipality_city_town': counts(municipality_level(frame.municipality)),
        'USGS_MMI': {'statistics': stats, 'missing': int(mmi.isna().sum()),
            'nonfinite_non_null': int((~finite & mmi.notna()).sum()),
            'outside_1_to_12': int((finite & ~mmi.between(1,12)).sum()), 'counts': counts(mmi)},
        'secondary_perils': {'flags': {c: counts(frame[c]) for c in FLAGS},
            'unexpected_flag_values': {c: counts(frame.loc[frame[c].notna() & ~frame[c].isin([0,1]),c]) for c in FLAGS},
            'any_flag': int(any_flag.sum()), 'all_three_explicit_zero': int(no_flag.sum()),
            'unknown_without_positive_flag': int((~any_flag & ~no_flag).sum()),
            'multiple_flags': int(frame[FLAGS].eq(1).sum(axis=1).gt(1).sum()),
            'binary_target_no_flags': int((binary & no_flag).sum()),
            'binary_target_no_flags_damage_val': counts(frame.loc[binary & no_flag,'damage_val']),
            'interpretation': 'No mapped secondary-peril intersection, not proof of shaking-only causation; liquefaction/unmapped hazards remain possible.'},
        'binary_target_records': int(binary.sum()),
        'constraints': {'models_fitted': False, 'target_harmonized': False,
            'post_event_imagery_used_as_predictor': False, 'rows_removed_or_imputed': 0},
    }


def aggregates(frame, directory):
    directory.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{'field': c, 'native_value': k, 'count': v}
        for c in ['damage_2','damage_val','conf',*FLAGS,'USGS_MMI']
        for k,v in counts(frame[c]).items()]).to_csv(directory/'native_counts.csv',index=False)
    pd.DataFrame([{'municipality_native': k,'count': v}
        for k,v in counts(frame.municipality).items()]).to_csv(directory/'municipality_native_counts.csv',index=False)
    pd.crosstab(frame.damage_2,frame.damage_val,dropna=False).to_csv(directory/'damage_cross_tab.csv')
    pd.crosstab(frame.USGS_MMI,frame.damage_val,dropna=False).to_csv(directory/'damage_by_mmi.csv')
    frame.groupby(FLAGS,dropna=False).size().rename('count').to_csv(directory/'peril_combinations.csv')
    work = frame.assign(municipality_city_town=municipality_level(frame.municipality))
    work.groupby(['municipality_city_town','damage_val'],dropna=False).size().rename('count').to_csv(directory/'municipality_damage.csv')
    work.groupby('municipality_city_town',dropna=False).USGS_MMI.agg(['count','min','max','mean','median']).to_csv(directory/'municipality_mmi.csv')
    _, no_flag = peril_masks(frame)
    work[no_flag].groupby(['municipality_city_town','damage_val'],dropna=False).size().rename('count').to_csv(directory/'municipality_damage_no_secondary_flags.csv')


def figures(frame, directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    directory.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.size': 10, 'savefig.dpi': 180})
    usable = ~frame.geometry.isna() & ~frame.geometry.is_empty & frame.geometry.is_valid
    pts = frame.loc[usable].to_crs(6675).geometry.centroid
    east, north = pts.x/1000, pts.y/1000
    def save(fig, name):
        fig.tight_layout()
        fig.savefig(directory/name,metadata={'Software':'geoai-earthquake-risk noto audit'})
        plt.close(fig)
    def geoax(ax, title):
        ax.set(title=title,xlabel='Easting (km; EPSG:6675)',ylabel='Northing (km)')
        ax.set_aspect('equal')
    for field,name in [('damage_val','damage_map.png'),('damage_2','damage_2_map.png')]:
        fig,ax=plt.subplots(figsize=(9,9))
        for code in [99,9,0,1]:
            mask=frame.loc[usable,field].eq(code)
            label = f'{code}: {NATIVE_LABELS[code]}' if field=='damage_val' else f'Native code {code}'
            ax.scatter(east[mask],north[mask],s=1,linewidths=0,c=COLORS[code],rasterized=True,
                       label=f'{label} (n={int(mask.sum()):,})')
        geoax(ax,f'Noto 2024 — native {field}\nAll valid building centroids; overplotting possible')
        ax.legend(markerscale=5,loc='best')
        save(fig,name)
    fig,ax=plt.subplots(figsize=(9,9))
    v=frame.loc[usable,'USGS_MMI'];ok=np.isfinite(v)
    art=ax.scatter(east[ok],north[ok],c=v[ok],s=1,cmap='viridis',linewidths=0,rasterized=True)
    if (~ok).any():
        ax.scatter(east[~ok],north[~ok],c='grey',s=1,label='Missing MMI');ax.legend()
    fig.colorbar(art,ax=ax,label='Native USGS MMI')
    geoax(ax,'Noto 2024 — USGS MMI');save(fig,'mmi_map.png')
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    for ax,col in zip(axes,['damage_2','damage_val']):
        codes=sorted(frame[col].dropna().unique());values=[int(frame[col].eq(x).sum()) for x in codes]
        bars=ax.bar([str(x) for x in codes],values,color=[COLORS.get(x,'black') for x in codes])
        ax.bar_label(bars,fmt='{:,.0f}')
        ax.set(title=col,xlabel='Native code (9/99 are not damage grades)',ylabel='All records')
        ax.set_ylim(0,max(values)*1.13)
    save(fig,'damage_counts.png')
    tab=pd.crosstab(frame.USGS_MMI,frame.damage_val).reindex(columns=[0,1,9,99],fill_value=0)
    fig,axes=plt.subplots(2,1,figsize=(11,8),sharex=True)
    bottom=np.zeros(len(tab))
    for code in tab:
        axes[0].bar(range(len(tab)),tab[code],bottom=bottom,color=COLORS[code],label=f'{code}: {NATIVE_LABELS[code]}')
        bottom+=tab[code]
    axes[0].set(ylabel='All records',title='Native damage_val versus MMI');axes[0].legend()
    denom=tab[0]+tab[1];rate=tab[1].div(denom.where(denom.gt(0)))
    axes[1].plot(range(len(tab)),rate,'o-')
    axes[1].set(ylabel='Destroyed / (survived + destroyed)',xlabel='Native USGS MMI',ylim=(0,1))
    axes[1].set_xticks(range(len(tab)),[f'{x:g}' for x in tab.index],rotation=45)
    save(fig,'damage_vs_mmi.png')
    fig,axes=plt.subplots(1,3,figsize=(15,7))
    for ax,col in zip(axes,FLAGS):
        ax.scatter(east,north,c='#dddddd',s=.4,linewidths=0,rasterized=True)
        mask=frame.loc[usable,col].eq(1)
        ax.scatter(east[mask],north[mask],c='#c82732',s=3,linewidths=0,rasterized=True)
        geoax(ax,f'{col}\n{int(frame[col].eq(1).sum()):,} flagged records')
    save(fig,'secondary_peril_map.png')
    any_flag,no_flag=peril_masks(frame)
    names=FLAGS+['Any flag','Multiple flags','All flags zero']
    values=[int(frame[c].eq(1).sum()) for c in FLAGS]+[int(any_flag.sum()),
        int(frame[FLAGS].eq(1).sum(axis=1).gt(1).sum()),int(no_flag.sum())]
    fig,ax=plt.subplots(figsize=(10,5));bars=ax.barh(names,values)
    ax.bar_label(bars,fmt='{:,.0f}',padding=3)
    ax.set(xlim=(0,max(values)*1.18),xlabel='Records (individual perils may overlap)',title='Secondary-peril intersections — full dataset')
    save(fig,'secondary_peril_counts.png')
    return {'method':'All valid nonempty centroids in EPSG:6675, no sampling; no external basemap',
            'plotted_records':int(usable.sum()),'unplottable_records':int((~usable).sum())}


def run(path, evidence, results):
    frame=load_noto(path)
    report=summarize(frame)
    report['container']=inspect_container(path)
    report['input']={'filename':path.name,'bytes':path.stat().st_size,'md5':digest(path,'md5'),'sha256':digest(path)}
    report['runtime']={p:importlib.metadata.version(p) for p in ['geopandas','pyogrio','shapely','pandas','numpy','matplotlib']}
    report['runtime']['GEOS']=shapely.geos_version_string
    aggregates(frame,evidence/'noto_2024')
    report['visualization']=figures(frame,results)
    report['output_sha256']={f'noto_2024/{p.name}':digest(p) for p in sorted((evidence/'noto_2024').glob('*.csv'))}
    report['figure_sha256']={p.name:digest(p) for p in sorted(results.glob('*.png'))}
    write_json(evidence/'noto_2024_execution.json',report)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=RAW/NOTO_REL)
    parser.add_argument('--evidence-dir',type=Path,default=ROOT/'docs')
    parser.add_argument('--results-dir',type=Path,default=ROOT/'results/noto_2024')
    args=parser.parse_args();report=run(args.input,args.evidence_dir,args.results_dir)
    print(json.dumps({k:report[k] for k in ['row_count','damage_2','damage_val','secondary_perils']},indent=2))


if __name__=='__main__':
    main()
