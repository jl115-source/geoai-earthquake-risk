# Data layer

`turkiye.py` ingests the registered survey; `turkiye_eda.py` produces descriptive outputs.
`acquire_expansion.py` and `audit_expansion.py` implement the completed local-data audit.
`harmonize.py` creates separate canonical source tables with native labels and provenance.
`design_experiments.py` freezes partition membership and eligibility without fitting models.

See `docs/harmonization_experiment_design.md` and `configs/experiments_1d.json`.
Do not infer permission to pool data from a shared schema. Keep row-level outputs ignored.
