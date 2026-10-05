# Third-party data and licenses

This repository includes or downloads third-party scientific data. The project
code license does **not** override the licenses of those data.

## GEM Global Exposure / Vulnerability Model

Source:
- https://github.com/gem/global_exposure_model
- https://github.com/gem/global_vulnerability_model

License: **CC BY-NC-SA 4.0**.

Files under `data/reference/gem/` are copied unchanged for research/reference
purposes and remain subject to GEM's license and attribution requirements.

## GEM Global Earthquake Impact Database (GEID)

Source:
- https://github.com/gem/geid

License: **CC BY-NC-SA 4.0**.

Files under `data/reference/geid/` and the large Nepal building-impact file
downloaded by `scripts/download_external_data.py` remain subject to GEID's
license.

## Türkiye 2023 engineering survey

Source:
- https://github.com/maxandersonloake/TUR2023_02_06

The engineering survey workbook is distributed there under **CC BY 4.0**.
The companion analysis code is MIT licensed.

## RC616 low-rise reinforced-concrete damage database

Source:
- DataCenterHub / DEEDS, DOI 10.7277/ACX0-DG18

License: **CC BY-SA 3.0**.

The three source CSV tables are streamed locally from the published archive;
the 15.4 GB media archive is not downloaded in full. No row data are committed.

## ACI133 Türkiye 2023 engineering dataset

Source: https://zenodo.org/records/13386343, Hariri-Ardebili (2024).

License: **CC BY 4.0**, confirmed by the Zenodo record API on 2026-10-05.
The workbook includes original ACI Committee 133 observations and author-supplied
completions/variants. Preserve these provenance distinctions and the original
Pujol et al. and Hariri-Ardebili/Sattar references. Downloaded locally only.

## Türkiye 2026 geospatial context package

Source:
- Zenodo DOI 10.5281/zenodo.18437501

License: **CC BY 4.0**, confirmed by
https://zenodo.org/api/records/18437501 on 2026-10-05. This corrects the earlier
inference from an empty license label in rendered page text. Credit Liu (2026)
and preserve individual ARIA, UNOSAT, Microsoft, GBA and other source attributions.
The record-level license does not independently establish the original terms
of every bundled product. The archive remains local-only in this project.

## Nepal NSO HRHRS 2016–2017

Source:
- National Statistics Office Nepal, study NPL-CBS-HRHRS-2016-v01

The public-use microdata are for statistical/scientific research. The official
access conditions prohibit redistribution without written agreement. The
project therefore stores only public metadata/instructions and does not mirror
the NSO microdata. Research use also requires aggregate reporting, prohibits
reidentification/identifying linkage, and requires citation and supplying
resulting publications to NSO. The metadata describes acquisition from CBS
premises. As of the Milestone 1C audit, the official Building microdata were
**not obtained**: the public Get Microdata endpoint returns an empty response.
This is an access limitation, not a claim that local research use is prohibited.
