# Milestone 1G data acquisition — Noto 2024 and xBD Mexico

This milestone adds the two large geolocated earthquake-damage candidates
identified during project scoping. It does **not** fit models or harmonize
damage labels.

## Noto 2024

Authoritative source: Zenodo version 2.5.

- **140,208** georeferenced building footprints.
- CRS: **EPSG:4326**.
- Building attributes include `damage`, technically validated `damage_val`,
  municipality, assessment confidence, GSI fire/slope-failure/tsunami flags,
  and **USGS MMI**.
- File: `Noto_Peninsula_Damage_2_5.gpkg`, about 47.9 MB.
- Pinned MD5: `280e9c53cb45086786c20ed0b2c21ffb`.

Acquire locally:

```bash
python -m src.data.acquire_large_geoai noto
```

The file remains under ignored `data/raw/noto_2024/`; only manifests and
aggregate audits should be versioned later.

## xBD Mexico earthquake

The original xBD labels and Maxar imagery remain distributed through the
official xView2 dataset site and require **registration/login**. This repository
does not bypass that requirement or treat an unofficial mirror as authoritative.

After obtaining the official xBD download, audit only the Mexico earthquake
subset:

```bash
python -m src.data.acquire_large_geoai xbd-mexico --xbd-root /path/to/xBD
```

The adapter recursively finds `mexico-earthquake` JSON annotations, counts
building labels/classes and records any geographic metadata available in the
label files.

### xBD-S12 companion

The ETH Zürich xBD-S12 derivative is public on Zenodo and provides aligned
Sentinel-1/2 imagery plus patch metadata. The cropped archive is ~9.5 GB
(MD5 `891b86000caa6019c20a95fc2f3f4e68`).

It is **not** downloaded automatically in 1G because:

1. it does not contain/replace the authoritative original xBD labels;
2. only the Mexico subset is currently relevant;
3. downloading all ~9.5 GB before the label audit is unnecessary.

Once official Mexico labels are present, we can decide whether to pull the
xBD-S12 Mexico patches or generate our own common pre-event EO stack.

## Research status

Noto can be acquired automatically and already supplies the three minimum
building-level components:

[
	ext{footprint/location} + D + H_{mathrm{MMI}}
]

Mexico is admitted to the core comparison only after the official xBD labels
are locally available and their geolocation/hazard join is verified.

No target harmonization is implied by acquisition.
