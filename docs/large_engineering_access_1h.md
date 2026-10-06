# Milestone 1H — what is actually obtainable now

This milestone deliberately separates **acquired/public** data from
**permission-gated** candidates.

## Obtainable now

### Noto 2024

Already acquired and fully audited in Milestone 1G.

### Zagreb 2020 — Copernicus EMSN074

**Public, anonymous access; no registration required.**

Authoritative JRC dataset:
https://doi.org/10.2905/JRC.G4YG7J8

Copernicus activation:
https://mapping.emergency.copernicus.eu/activations/EMSN074/DAMAGEASSESSMENT/

The public package includes:
- P02.1 reference buildings derived from **pre-event 2019 VHR imagery**;
- P08.1 detailed roof/chimney damage assessment from post-event drone/VHR imagery;
- reconstruction monitoring;
- vector data in geodatabase/GeoJSON formats and raster products where applicable.

This is **not** the same as Zagreb's 25k+ engineering-inspection database.
Treat Copernicus damage as a remote-sensing damage product.

Acquire/inventory:

```bash
python -m src.data.acquire_zagreb_copernicus
python -m src.data.audit_zagreb_copernicus
```

Raw data remain ignored under `data/raw/zagreb_2020_copernicus/`.
The [actual GDB layer audit](zagreb_2020_copernicus/audit.md) finds 29,398 reference
building polygons but only 556 damage polygons and 99 near-identical mutually
unique footprint pairs (IoU ≥0.99). There are no explicit undamaged controls.
**Auxiliary only: not the large-N supervised building dataset.** Layer counts,
native codebook definitions, geometry checks and linkage diagnostics are versioned.

## Not obtainable anonymously

### Türkiye national MEUCC 2023 — 2.15M buildings

Paper reports 2,153,835 inspected buildings with structural system, damage state,
use, year built, stories, floor area and location. The paper's data availability
statement says building-level survey data are available **upon request from the
Ministry of Environment, Urbanization and Climate Change**.

Status: request required. Not acquired.

### Central Italy 2016–17 Da.D.O.

Official Da.D.O. platform offers original and processed/georeferenced data and
ShakeMaps to **qualified scientific users**, but institutional accreditation and
individual registration are required.

Status: registration required. Not acquired.

### Kırıkhan 2023 — 16,611 buildings

Paper states row-level ministry data are available from the corresponding author
**with permission of the relevant institution**.

Status: author/ministry permission required. Not acquired.

## Immediate project inventory

Actually usable without further permission:
1. Noto 2024 — public, acquired, audited.
2. Türkiye survey / ACI133 / RC619 — already held/audited as previously documented.
3. Zagreb EMSN074 — public Copernicus product; acquisition automated here.

Do not call the three gated datasets "available" until their row-level files have
been delivered and audited.
