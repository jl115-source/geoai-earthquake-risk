# GeoAI Earthquake Risk

Research-quality project on **transferable earthquake vulnerability and portfolio loss modelling**.

## Research question

Can learned geospatial representations improve earthquake damage and loss estimation in unseen regions beyond conventional intensity-measure + building-taxonomy fragility models?

## Project structure

```
data/
  README.md
  datasets.yml
  raw/          # ignored; downloaded external data
  processed/    # ignored; derived local datasets
scripts/
src/
  data/
  features/
  models/
  risk/
notebooks/
configs/
results/
```

## Core empirical domains

1. **Türkiye 2023** — 559-record engineering survey + ShakeMap; first end-to-end vulnerability benchmark.
2. **Nepal 2015** — large GEID building-impact dataset, with official HRHRS documentation and optional local microdata for scale/generalization.
3. **RC616 multi-event benchmark** — 616 buildings across six earthquakes in Turkey, Peru, China and Haiti for leave-one-event / leave-one-country-out transfer tests.

**Italy Da.D.O. is deliberately deferred** as an optional later extension. The three core domains already give us a clean combination of engineering detail, scale and independent-event transfer.

The repository does **not** redistribute third-party datasets unless their licenses clearly permit it. See [data/README.md](data/README.md).

## Acquire data

Install dependencies:

```bash
pip install -r requirements.txt
```

Download the core empirical datasets, documentation and ShakeMaps:

```bash
make data-core
```

This acquires locally:

- the Türkiye companion ShakeMap (the 559-record workbook is versioned for provenance);
- GEM GEID detailed Nepal 2015 building-impact data;
- the Nepal USGS ShakeMap grid;
- public Nepal NSO metadata, questionnaire and survey documentation;
- the RC616 six-earthquake damage archive;
- ShakeMap grids for all six RC616 earthquakes.

Small/open GEM exposure/vulnerability references, GEID event summaries and site models are versioned under `data/reference/`.

Optional GeoAI augmentation:

```bash
make data-geoai
```

This downloads the 2026 Zenodo Türkiye building-footprint, damage and
geo-environmental context archive locally. It is intentionally not committed to
Git because it is large and the record does not display an explicit license.

Validate the local data layer:

```bash
make data-check
```

## Milestone 1A: Türkiye 2023 ingestion and EDA

From the repository root, with Python 3.11 or newer:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-turkiye.txt
python -m src.data.turkiye
python -m src.data.turkiye_eda
python -m pytest -q
```

These commands run offline after dependency installation, using the already
registered, versioned raw workbook in `data/reference/turkiye_2023/`. There is
no download, ShakeMap re-sampling, or ML fitting in this milestone. To explicitly
use a separately acquired raw workbook:

```bash
python -m src.data.turkiye --input data/raw/turkiye_2023/Jaiswal_2023TurkiyeEQ_us6000jllz_field_str_damage_data.xlsx
```

An alternate workbook must have the documented sheet and source columns. A
changed source schema fails loudly. No implicit preference for a local download
can change the default input. Both modules accept `--output-dir`; EDA also
accepts `--input path/to/buildings.parquet`.

Outputs (derived data/results remain git-ignored):

- `data/processed/turkiye_2023/buildings.parquet`: all survey records, canonical
  typed fields, additional engineering variables and every original cell as
  `raw__<source header>` text.
- `data/processed/turkiye_2023/quality_report.json`: missingness for every column,
  damage/structure/city counts, duplicate groups and record-level validation issues.
- `data/processed/turkiye_2023/manifest.json`: input/output SHA-256, source rows,
  mappings, transformation policies and library versions.
- `data/processed/turkiye_2023/source_dictionary.json`: all 55 source columns.
- `results/turkiye_2023/report.md`: EDA report with eight PNG figures; accompanying
  CSVs cover classes, structures, missingness, damage rates and geographic coverage.
  `summary.json` includes shaking ranges and every plot's coordinate/intensity
  exclusion counts. Open `report.md` in a Markdown viewer to inspect the figures.

The canonical minimum schema is `building_id, latitude, longitude, city,
structure_type, floors, damage_grade, PGA, PGV, SA_0p3, SA_1p0`.
PGA/SA are in **g**, PGV in **cm/s**, after exponentiating source natural-log
means. They are geometric means/medians, not arithmetic means. Original log
values and uncertainty fields remain available. The literal damage label
`None` maps to **0 (undamaged)**; it is not a missing value.

### What the registered survey actually contains

The workbook has **559 records across 10 cities/towns**, surveyed 21–25 June
2023. The often-used **527** is the subset with both damage and structure type,
not the raw record count. All 559 records are retained, with
`has_damage_and_structure` identifying this subset without filtering.

| Damage grade | Meaning | Records |
| --- | --- | ---: |
| 0 | None | 111 |
| 1 | Minor | 147 |
| 2 | Moderate, including repaired | 169 |
| 3 | Severe or partial collapse | 111 |
| 4 | Complete collapse | 3 |
| null | Missing label | 18 |

There are **499 unique coordinate pairs**, with **105 records in 45 repeated
coordinate groups** and **11 exact duplicate excess records**. No duplicate
is removed. `building_id` identifies a source survey row, not a verified unique
physical building. Resolve identity before later splitting or modelling.

Structure type is missing in 22 records and above-ground floor count in 8.
RC moment-resisting-frame categories account for 430 records. Unusual structure
descriptions remain intact. All records have coordinates and all four required
shaking measures. The implemented checks find no invalid coordinates,
impossible numeric values, or unknown damage labels in this source version.
Important auxiliary fields are sparse: placards are entirely empty, area is
missing for 364 records, and an unlabelled percentage column has six entries.

PGA spans **0.108–1.057 g**, PGV **16.57–155.81 cm/s**, SA(0.3)
**0.247–1.722 g**, and SA(1.0) **0.163–1.569 g**. Coverage is uneven:
Kahramanmaras has 110 records, while Nurdagi has 3. These are engineering-survey
sample proportions, not population damage probabilities. Damage rates use only
known labels in the denominator, with denominators and missing counts shown.

See [the ingestion contract](docs/turkiye_2023.md) and the
[complete source-column dictionary](docs/turkiye_2023_columns.md) for provenance,
damage mapping, units and validation rules. The CI workflow reruns ingestion,
EDA and tests and uploads all generated outputs for PR review.

## Milestones

- **M1 — Türkiye conventional vulnerability baseline:** clean/understand the 559-record survey, map damage and shaking, reproduce fragility curves, and define leakage-safe splits.
- **M2 — Geospatial augmentation:** add site/geology/topography/fault-distance and surrounding morphology; compare H → H+X → H+X+Z_spatial.
- **M3 — Transfer/generalization:** harmonize Nepal and RC616; train on some regions/events and test on unseen events/countries.
- **Later — Cat-loss:** map probabilistic damage to MDR/loss distributions and calculate event loss, AAL and EP curves.
