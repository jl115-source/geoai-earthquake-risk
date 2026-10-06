# Milestone 1I — Patten corpus access audit

## Correct status

Patten, Anderson Loake & Steinsaltz (2024) used a large geolocated earthquake
building-damage corpus: **369,813 buildings from 26 earthquakes in 15 countries**.

Their public ODDRIN code demonstrates that the modelling table contains explicit
building coordinates: it writes `Longitude` and `Latitude` from each spatial
building-damage object before fitting the classifier.

However, **we have not established public access to the assembled row-level
369,813-building corpus**.

The previously proposed Dryad acquisition route was incorrect. The later paper's
reported building counts must not be interpreted as evidence that those row-level
building points are available for anonymous download. Likewise, the Figshare
workbook inspected during the access search contains **3,460 aggregate report
rows**, not individual building observations.

## What is supported

- The published studies assembled a multi-event, multi-country geolocated corpus.
- The authors' code constructs and uses per-building longitude/latitude.
- UNOSAT and Copernicus are among the upstream damage-data sources.
- Public ODDRIN code contains ingestion/harmonisation logic for those source
  products.

## What is *not* established

- No verified public download of the complete Patten modelling table.
- No verified public row-level archive containing the full 26-event point corpus.
- No downloaded 378,984-row "raw" point dataset.
- No completed local audit of coordinates, event counts, class counts or
  selection-bias strata for the assembled corpus.

## Project implication

Treat Patten et al. as a **methodological and dataset-design precedent**, not as an
acquired project dataset.

A future reproduction would require one of:

1. obtaining the authors' assembled row-level table directly;
2. reconstructing the relevant events from public UNOSAT/Copernicus source
   products, event by event, while preserving native provenance and addressing
   known selection/missingness bias;
3. identifying a genuinely public row-level release and auditing it before use.

Until one of those succeeds, this corpus must not appear in the project's
"available data" inventory.

## Scientific lesson

The access failure is itself useful: even widely cited multi-event earthquake
damage papers may depend on assembled source products that are not released as a
single reusable research table. Our project should continue to distinguish:

- **paper-reported sample size**
- **public source availability**
- **successfully downloaded row-level data**
- **audited modelling-ready data**

These are not interchangeable.
