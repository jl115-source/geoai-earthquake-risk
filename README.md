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
