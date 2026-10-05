# Data

Raw third-party data are kept out of Git by default. This keeps the repository reproducible while respecting source licenses and access terms.

## Region 1 — Türkiye 2023

**Engineering survey**
- Source: Max Anderson Loake & Kishor Jaiswal companion repository, `TUR2023_02_06`
- File: `Jaiswal_2023TurkiyeEQ_us6000jllz_field_str_damage_data.xlsx`
- Size: ~219 KB
- License: **CC BY 4.0**
- Contents used here: building coordinates, city, structure type, observed damage state, and ShakeMap-derived PGA/PGV/SA metrics.

**ShakeMap**
- File: `ShakeMapUpd.xml.gz`
- Used to reproduce/interrogate spatial intensity measures.

The small CC BY 4.0 engineering-survey workbook is also mirrored in this repository at:

`data/reference/turkiye_2023/Jaiswal_2023TurkiyeEQ_us6000jllz_field_str_damage_data.xlsx`

Run the downloader to fetch the larger ShakeMap and create a local raw-data copy:

```bash
python scripts/download_turkiye.py
```

## Region 2 — Nepal 2015

Preferred source: Nepal National Statistics Office, **Household Registration for Housing Reconstruction Survey 2016–2017** (survey ID `NPL-CBS-HRHRS-2016-v01`).

Important: the current NSO access conditions allow statistical/scientific research but prohibit redistribution without written agreement. Therefore the raw Nepal microdata are **not mirrored in this public repository**.

The survey includes building-level damage assessment and structural characteristics across earthquake-affected districts. For the 11 census-model districts, every private residential building was visited irrespective of damage state; other areas used a verification model.

After obtaining the official files, place them under:

```
data/raw/nepal/
```

We will write the harmonizer against the official schema rather than an unofficial competition mirror.

## Region 3 — Italy Da.D.O. (planned)

Da.D.O. is the Italian Civil Protection Department's Database of Observed Damage. It contains multiple earthquake-event databases with observed seismic damage and structural/building characteristics.

Access is restricted to qualified users and scientific use. We will not redistribute it. Once access is approved, raw files belong in:

```
data/raw/italy_dado/
```

## Supporting global datasets

- USGS ShakeMap / ShakeMap Atlas — event ground-motion fields.
- GEM Global Exposure Model — building taxonomy and replacement-cost exposure.
- GEM Global Vulnerability Model — conventional vulnerability benchmark.
- GEM GEID — observed aggregate earthquake consequences for event-level validation.

See `datasets.yml` for the machine-readable registry.
