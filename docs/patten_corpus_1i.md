# Milestone 1I — Patten / Oxford 26-event building-point corpus

## Why this dataset matters

Patten, Anderson Loake & Steinsaltz (2024) modelled **369,813 geolocated
buildings from 26 earthquakes in 15 countries**. Their public ODDRIN code
constructs explicit `Longitude` and `Latitude` columns for every building
before writing the classification input table.

The 2026 follow-up, *A Bayesian approach for earthquake impact modelling*,
publishes the underlying earthquake-impact dataset on Dryad:

- DOI: **10.5061/dryad.05qfttfcv**
- 26 point-damage events listed in the paper:
  - 2013-09-24 Pakistan
  - 2015-04-25 Nepal
  - 2016-04-16 Ecuador
  - 2016-08-24 Italy
  - 2016-10-26 Italy
  - 2017-09-07 Mexico
  - 2017-09-19 Mexico
  - 2017-11-12 Iran
  - 2018-02-26 Papua New Guinea
  - 2018-07-29 Indonesia
  - 2018-10-06 Haiti
  - 2019-08-08 Türkiye
  - 2019-09-24 Pakistan
  - 2019-09-26 Indonesia
  - 2019-11-08 Iran
  - 2019-11-26 Albania
  - 2020-01-24 Türkiye
  - 2020-10-30 Türkiye
  - 2020-12-29 Croatia
  - 2021-01-14 Indonesia
  - 2021-08-14 Haiti
  - 2022-06-22 Afghanistan
  - 2022-07-02 Iran
  - 2022-07-27 Philippines
  - 2022-11-21 Indonesia
  - 2023-02-06 Türkiye

The 2026 paper reports **378,984 classified buildings** before its later
selection-bias filtering. This is not automatically identical to the 369,813-row
2024 modelling table: Patten (2024) explicitly removed `possible damage`
records, and the later archive may contain revised/source-rich data.

## Acquire

```bash
python -m src.data.acquire_patten_dryad
python -m src.data.audit_patten_dryad
```

To inspect file names and total size first:

```bash
python -m src.data.acquire_patten_dryad --metadata-only
```

Raw Dryad files stay under ignored `data/raw/patten_dryad/`. Versioned evidence
is written to `docs/patten_dryad/`.

## Expected scientific value

If the Dryad point table audits as expected, this gives us the missing
**multi-earthquake / multi-country geolocated benchmark**. We can then attach
strictly pre-event global/EO context to each building point and evaluate
leave-event-out or leave-country-out representation transfer.

## Important caution

The 2026 paper identifies strong **selection/missingness bias** in several
Copernicus/UNOSAT event products. Therefore:

- absence from a damage product must not be converted to an unaffected label;
- `possibly damaged` should not be silently forced into either binary class;
- event/source/date strata need to be audited before pooling;
- the newer paper's source-aware filtering is preferable to blindly reproducing
  the 2024 binary table.

This milestone acquires/audits only. No model fitting or target harmonisation.
