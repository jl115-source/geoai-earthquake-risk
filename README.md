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
  download_turkiye.py
  check_data.py
src/
notebooks/
results/
```

## Initial regions

1. **Türkiye 2023** — engineering-survey damage labels + ShakeMap; first end-to-end vulnerability benchmark.
2. **Nepal 2015** — large post-earthquake housing survey; second-region training/generalization dataset.
3. **Italy Da.D.O.** — multi-event observed-damage database; planned third-region research-grade extension.

The repository does **not** redistribute third-party datasets unless their licenses clearly permit it. See [data/README.md](data/README.md).


## Acquire data

Install dependencies:

```bash
pip install -r requirements.txt
```

Download the core empirical datasets and historical ShakeMaps:

```bash
make data-core
```

This acquires locally:
- GEM GEID detailed Nepal 2015 building-impact data;
- the Nepal USGS ShakeMap grid;
- public Nepal NSO study metadata;
- the RC616 six-earthquake damage archive;
- ShakeMap grids for the six RC616 earthquakes.

The small/open Türkiye engineering survey, Türkiye ShakeMap, GEM vulnerability
functions, GEM exposure summaries, GEID impact summaries and site models are
already versioned under `data/reference/`.

Optional GeoAI augmentation:

```bash
make data-geoai
```

This downloads the 2026 Zenodo Türkiye building-footprint, damage and
geo-environmental context archive locally. It is intentionally not committed to
Git because it is large and the record does not display an explicit license.

Check local acquisition:

```bash
make data-check
```
