# Data

Raw third-party data are kept out of Git by default unless they are small,
clearly redistributable reference files. This keeps the project reproducible
without bloating clone size or violating source terms.

See `reference/THIRD_PARTY_LICENSES.md` for licensing details and
`datasets.yml` for the machine-readable dataset registry.

## Core empirical domains

### 1. Türkiye — 2023 Kahramanmaraş sequence

Versioned reference data:

- `reference/turkiye_2023/Jaiswal_2023TurkiyeEQ_us6000jllz_field_str_damage_data.xlsx`
  - 559-record engineering survey (527 with damage and structure type);
  - building coordinates, city, structure type and observed damage state;
  - ShakeMap-derived PGA/PGV/SA fields;
  - source repository: `maxandersonloake/TUR2023_02_06`;
  - survey data license: CC BY 4.0.

The companion `ShakeMapUpd.xml.gz` is about 15 MB and is downloaded locally
rather than committed:

```bash
python scripts/download_turkiye.py
```

The downloader validates the source-published file sizes. A previous zero-byte
placeholder is intentionally not retained in the repository.

Also versioned:

- GEID event/impact summaries and OpenQuake site model under
  `reference/geid/turkiye_2023/`.
- GEM Türkiye exposure summaries and vulnerability functions under
  `reference/gem/turkiye/`.

### 2. Nepal — 2015 Gorkha earthquake

Core large building-impact data:

- GEM GEID `Impact_Buildings_Detailed.csv`;
- approximately 78.4 MB; 762,106 records / 19 variables across 11 districts;
- no latitude/longitude; exported building IDs are rounded (74 distinct strings);
- downloaded locally by:

```bash
python scripts/download_external_data.py nepal-geid
```

Supporting files already versioned:

- national/province/district impact summaries;
- economic-impact summary;
- GEID ShakeMap metadata;
- OpenQuake site model with Vs30 and basin-depth fields;
- GEM Nepal exposure summaries;
- GEM Nepal structural/non-structural/contents vulnerability functions.

USGS ShakeMap grid:

```bash
python scripts/download_external_data.py nepal-shakemap
```

Official NSO HRHRS 2016–2017 is the **priority richer source**, with 1,052,948
records / 105 variables advertised by its dictionary. GEID matches its 11-district
subset exactly at district-count level; do not count these as independent surveys.
Official Building microdata are not yet acquired: the public endpoint returned
no file and metadata describe access from CBS premises. Research use is allowed
under NSO terms, including no redistribution or identifying linkage.

### 3. Multi-event RC616 benchmark

DataCenterHub/DEEDS DOI: `10.7277/ACX0-DG18`.

The publication describes 616 low-rise reinforced-concrete / concrete-masonry
buildings across:

- Erzincan 1992;
- Düzce 1999;
- Bingöl 2003;
- Peru/Pisco 2007;
- Wenchuan 2008;
- Haiti 2010.

The archive is CC BY-SA 3.0. The current table has **619**, rather than the
advertised 616, unique experiment records. Stream its three CSV tables locally
without downloading 15.4 GB of photographs/reports:

```bash
python scripts/download_external_data.py rc616
```

Event metadata and ShakeMap mappings are versioned under:

- `reference/geid/rc616_events/`
- `reference/rc616_events.yml`

Download all six ShakeMap grids with:

```bash
python scripts/download_rc616_shakemaps.py
```

## Optional GeoAI augmentation — Türkiye 2026 context

Zenodo DOI: `10.5281/zenodo.18437501`.

The compressed archive is approximately 585 MB and contains:

- national building footprints;
- multiple post-event damage products;
- manually interpreted damage labels;
- DEM;
- epicentral distance;
- fault distance;
- lithology;
- PGV.

Download locally:

```bash
python scripts/download_external_data.py turkiye-context
```

The Zenodo API explicitly declares **CC BY 4.0** (verified 2026-10-05), correcting
the earlier assumption from an empty license label in the rendered page. Keep
original product attributions and terms. Files remain local-only in this project.
The package has 4,410,028 footprint features, not that many independent damage
labels. See the [Milestone 1C audit](../docs/data_expansion_audit.md) for product
counts, missing label semantics and raster-unit limitations.

## ACI133 Türkiye 2023

`python -m src.data.acquire_expansion aci133 aci-metadata` acquires
`ACI133v3.xlsx` from Zenodo record 13386343 (CC BY 4.0). It contains 242 records
and 106 source columns, including author-supplemented data and multiple intensity
products. Twelve records are within 25 m of the existing survey: these are
proximity candidates, not confirmed duplicate buildings. Keep the datasets separate.

## One-command acquisition

Core data:

```bash
make data-core
```

Optional large GeoAI package:

```bash
make data-geoai
```

Everything:

```bash
make data-all
```

Validate local status:

```bash
make data-check
```

The validation step checks exact sizes where the upstream source provides a
stable value, verifies ZIP archives, and requires all six RC616 ShakeMap grids.

## Supporting reference systems

- **USGS ShakeMap / ShakeMap Atlas** — MMI, PGA, PGV and spectral acceleration.
- **GEM Global Exposure Model** — exposure/taxonomy/replacement-value framework.
- **GEM Global Vulnerability Model** — conventional vulnerability baseline.
- **GEM GEID** — observed aggregate and detailed earthquake impacts.
- **OpenQuake** — later catastrophe-risk engine for loss aggregation and EP/AAL outputs.
