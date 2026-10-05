# 1F-C evidence: hazard and engineering-attribute chronology

**Final 1F decision:** use the newly sampled, checksum-pinned XML PGA described in `geoai_experiment_1f.md`, not workbook IMs. The implemented variable is `structure_family`; unusual categories map to `OTHER`, missing/unmapped categories are explicitly excluded from the paired primary cohort. The recommendations below record the evidence considered; the JSON config is the binding protocol.

Checked 2026-10-05. **A retrospective vulnerability benchmark is defensible; a verified pre-earthquake inventory or operational pre-event forecasting claim is not established.** Distinguish when the represented property existed, when it was observed, and when its digital product was created.

## Primary-paper evidence

The [companion paper, section 2](https://onlinelibrary.wiley.com/doi/full/10.1002/esp4.70117) says engineers recorded building age, structural type and damage in a post-earthquake June survey near recording stations. Table 1 defines structural systems by construction, and height subdivides some RC systems. It uses M7.8 mainshock ShakeMap intensities while acknowledging omission of cumulative shaking. Section 3.3.1 describes removal and selective inclusion of damaged masonry buildings. Appendix A compares IMs against these same survey outcomes and favours SA(0.3), also considering GEM availability. Therefore SA(0.3)-only is a literature-informed, outcome-informed choice, not untouched prospective feature selection. The paper does not establish original-versus-surviving storey counts or a per-field pre-event verification procedure. Its 527 analysed observations must not replace this repository's 559 retained source records.

## Direct source inspection

Pinned repository commit: `be088671596f04ad5a058f7819ec3bb762156f17`.

- [README](https://github.com/maxandersonloake/TUR2023_02_06/blob/be088671596f04ad5a058f7819ec3bb762156f17/README.md) identifies `Data/ShakeMapUpd.xml.gz` as the M7.8 mainshock map.
- [FullModel.R](https://github.com/maxandersonloake/TUR2023_02_06/blob/be088671596f04ad5a058f7819ec3bb762156f17/FullModel.R) reads the workbook rather than rebuilding its shaking samples, exponentiates its mean IM columns, and reads the companion XML separately. This verifies the log transform, not the exact ShakeMap revision that produced each workbook value.
- [Functions.R](https://github.com/maxandersonloake/TUR2023_02_06/blob/be088671596f04ad5a058f7819ec3bb762156f17/Functions.R) extracts the XML values in their file scale. Do not copy its positional parsing, dropped-first-row or coordinate-rounding behavior into a new sampling pipeline without independent validation.

Read-only inspection of the existing local workbook found dates **2023-06-21 through 2023-06-25 on all 559 rows**, no cell comments and no original/pre-event qualifier in `storeys_above_ground_incl_ground_floor`. The workbook's `construction_age` values are construction-year bands, not elapsed ages: 1935–1976, 1977–1984, 1985–2000, 2001–2018, 2018+, plus missing. A band is not a surveyed construction certificate. The open-ended 2018+ band does not itself document a February-2023 cutoff. The `structure_type` field embeds storey bands for RC categories. These observations describe the source file; none establish the survey's verification practice.

The [pinned companion XML](https://github.com/maxandersonloake/TUR2023_02_06/blob/be088671596f04ad5a058f7819ec3bb762156f17/Data/ShakeMapUpd.xml.gz) header was streamed, without obtaining additional building microdata:

| Header | Value |
|---|---|
| `event_id`, `shakemap_id` | `us6000jllz` |
| magnitude | 7.8 |
| event timestamp | `2023-02-06T01:17:35` |
| `process_timestamp` | `2025-03-20T18:39:27` |
| `shakemap_version`, `code_version` | `1`, `4.1.5` |
| originator, status | `us`, `automatic` |
| seismic stations, intensity observations | 252, 0 |
| grid | 961 × 841; longitude 35.2–39.2, latitude 35.5–39.0 |
| XML acceleration units | `%g` for PGA, PSA03, PSA10, PSA30 |
| XML velocity units | `cm/s` for PGV |

This is a **2025-produced reconstruction of 2023 shaking**, not a pre-event or real-time-2023 product. XML acceleration requires division by 100 for g. This does **not** imply dividing the workbook's exponentiated means by 100: its existing ingestion treats those logged means as log(g). The exact link between workbook samples and this XML revision remains unverified. Do not present XML version 1 as the workbook's proved sampling version. The 1F pipeline now completes that explicitly versioned resampling audit, preserving the old workbook IM columns unchanged.

## Recommended feature policy

### Primary X: narrow retrospective structural-family variable

If the estimand is explicitly retrospective, allow one derived categorical variable `structural_family_retrospective`, obtained by a fixed label-only mapping:

| Native category | Family |
|---|---|
| All `RC MRF (...)` categories | `RC_MRF` |
| All `RC Wall (...)` categories | `RC_WALL` |
| All `RC Dual system (...)` categories | `RC_DUAL` |
| `Reinforced masonry` | `REINFORCED_MASONRY` |
| `Unreinforced masonry` | `UNREINFORCED_MASONRY` |
| `Column with slab corrugated Asgolan` | `OTHER_DOCUMENTED_SYSTEM` |
| `1st storey stone, 2nd storey aerated concrete` | `OTHER_DOCUMENTED_SYSTEM` |
| Missing | `UNKNOWN` |

Mapping the two unusual categories together is a declared small-sample design choice, not the paper's taxonomy or a source correction. Preserve both original strings. Alternatively keep them distinct with regularization; do not select between these choices using outcomes. Remove every height suffix before encoding; otherwise an apparently innocent structural-system predictor reintroduces unaudited storey information.

This permission is a **scientific interpretation**, not newly discovered documentary proof: masonry versus concrete structural systems describe construction that plausibly existed before the event, whereas their ascertainment happened afterward. It supports comparison conditional on post-event-ascertained pre-existing system proxies. It does not prove that damage could not influence assessor classification or missingness. Record `observation_time=post_event`, `represented_time=pre_existing_design_inferred`, `verification=not_independently_verified`, and retain an H-versus-H+GeoAI sensitivity that uses no survey-derived X. No missingness flag, survey date or assessor identity should become a predictor.

### Exclude from primary X

- Numeric floors and embedded height bands: original-versus-surviving height is undocumented.
- Construction vintage: plausible pre-existing property but estimation/source verification is undocumented; reserve for an explicitly declared retrospective sensitivity, not the strict primary allowlist.
- Current occupancy, occupied status, placard, leaning, pounding, structural-member/infill damage, hazards, casualties, photos and damage-derived descriptions: post-event conditions or potential target proxies.
- Survey date, assessor, city identity, observation selection, raw coordinates and record/photo IDs: retain for audit/splits/joins only, not predictive features.

For a **strict operational pre-event** claim, even the retrospective family proxy is ineligible until independently validated. In that interpretation H+X cannot honestly be declared ready from the present survey alone. The practical way to complete this fallback without pretending is to freeze the narrower retrospective estimand explicitly, retain the limitations, and require all EO/spatial context inputs themselves to precede the first mainshock.

### H and the target

Use a fixed mainshock H definition such as the predeclared workbook PGA, or an a priori multi-IM block, uniformly in all four comparisons. Do not choose the winning IM against held-out cities or repeat the published ROC selection. If SA(0.3) is retained for comparability, disclose the inherited outcome-informed selection and show a fixed PGA sensitivity. Mainshock conditioning does not establish mainshock-only damage: labels were ascertained after the sequence and recovery interval. Results concern damage among the observed survey cohort, not calibrated population-wide loss or a causal incremental GeoAI effect.
