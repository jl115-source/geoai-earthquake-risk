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

1. **Türkiye 2023** — 527-building engineering survey + ShakeMap; first end-to-end vulnerability benchmark.
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

- the Türkiye companion ShakeMap (the 527-building workbook is versioned for provenance);
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

## Milestones

- **M1 — Türkiye conventional vulnerability baseline:** clean/understand the 527-building survey, map damage and shaking, reproduce fragility curves, and define leakage-safe splits.
- **M2 — Geospatial augmentation:** add site/geology/topography/fault-distance and surrounding morphology; compare H → H+X → H+X+Z_spatial.
- **M3 — Transfer/generalization:** harmonize Nepal and RC616; train on some regions/events and test on unseen events/countries.
- **Later — Cat-loss:** map probabilistic damage to MDR/loss distributions and calculate event loss, AAL and EP curves.
