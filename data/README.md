# Data

Raw third-party data are kept out of Git by default unless they are small,
clearly redistributable reference files. This keeps the project reproducible
without bloating clone size or violating source terms.

See `reference/THIRD_PARTY_LICENSES.md` for licensing details and
`datasets.yml` for the machine-readable dataset registry.

## Core empirical domains

### 1. Türkiye — 2023 Kahramanmaraş sequence

Versioned in this repository:

- `reference/turkiye_2023/Jaiswal_2023TurkiyeEQ_us6000jllz_field_str_damage_data.xlsx`
  - engineering survey;
  - building coordinates, city, structure type and observed damage state;
  - ShakeMap-derived PGA/PGV/SA fields;
  - source repository: `maxandersonloake/TUR2023_02_06`;
  - survey data license: CC BY 4.0.

- `reference/turkiye_2023/ShakeMapUpd.xml.gz`
  - ShakeMap used by the companion fragility analysis.

Also versioned:

- GEID event/impact summaries and OpenQuake site model under
  `reference/geid/turkiye_2023/`.
- GEM Türkiye exposure summaries and vulnerability functions under
  `reference/gem/turkiye/`.

### 2. Nepal — 2015 Gorkha earthquake

Core large building-impact data:

- GEM GEID `Impact_Buildings_Detailed.csv`;
- approximately 78.4 MB;
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

Official NSO HRHRS 2016–2017 microdata are retained as an **optional**
validation/source dataset. Their access terms prohibit redistribution without
written agreement, so this repository stores only public metadata/instructions.

### 3. Multi-event RC616 benchmark

DataCenterHub/DEEDS DOI: `10.7277/ACX0-DG18`.

The database contains 616 low-rise reinforced-concrete / concrete-masonry
buildings across:

- Erzincan 1992;
- Düzce 1999;
- Bingöl 2003;
- Peru/Pisco 2007;
- Wenchuan 2008;
- Haiti 2010.

The archive is CC BY-SA 3.0 and is downloaded locally:

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

The Zenodo record currently does not display an explicit license, so these
files are treated as local-only and are not redistributed here.

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

Check local status:

```bash
make data-check
```

## Supporting reference systems

- **USGS ShakeMap / ShakeMap Atlas** — MMI, PGA, PGV and spectral acceleration.
- **GEM Global Exposure Model** — exposure/taxonomy/replacement-value framework.
- **GEM Global Vulnerability Model** — conventional vulnerability baseline.
- **GEM GEID** — observed aggregate and detailed earthquake impacts.
- **OpenQuake** — later catastrophe-risk engine for loss aggregation and EP/AAL outputs.
