# Milestone 1F — frozen GeoAI fallback and input feasibility

The primary target is the **independent 559-record Türkiye engineering survey**, with explicit eligibility exclusions. ACI133 remains external and unused for feature/parameter selection. `This_study` and `Visual_interpretation` remain rejected as primary vulnerability targets. CSB is a plausible, unconfirmed scale-up route; [the bounded access check](csb_access_1f.md) does not delay this experiment. No contact was sent, encoder executed, or damage model fitted in 1F.

The binding design is [configs/geoai_experiment_1f.json](../configs/geoai_experiment_1f.json). Local per-record evidence, fold membership, features and exclusions are reproducible; aggregate results are recorded in [the execution report](geoai_1f_results.md).

## Target and estimand

Keep native grades **0 none; 1 minor; 2 moderate/repaired; 3 severe/partial collapse; 4 complete collapse**. There are 541 known labels and 18 missing among 559 retained records. These are cumulative sequence/recovery-period observations from June 2023, not mainshock-only damage. Repaired status in grade 2 and only three grade-4 observations limit severity interpretation. Do not merge damage scales across datasets.

The estimand is the incremental held-out-city predictive information of pre-event spatial representations **within this surveyed cohort**, conditional on reconstructed mainshock hazard and retrospectively ascertained structural-design proxies. It is neither causal nor population-representative vulnerability, and does not establish earthquake transfer or operational pre-event forecasting. Survey selection near stations and nonrandom engineering inspection remain limitations.

All arms use identical eligible records, fixed city folds and inverse exact-coordinate multiplicity weights. Missing labels or structure, contradictory labels at identical coordinates, incomplete input support, invalid hazard and city-coordinate outliers receive explicit reasons. Source rows are retained. Same-label duplicate coordinates are not silently deduplicated; each site has total weight one. Conflicting coordinates may represent different nearby buildings: quarantine is conservative, not proof of source error.

A coordinate more than **10 km from its recorded city's median coordinate** is quarantined pending manual source adjudication, without moving or correcting it. This mechanical rule is a location-quality screen, not a verified municipal-boundary test. It can exclude valid peripheral buildings; report their IDs and reasons. Available pixels at an erroneous coordinate do not establish the building's true location.

## Chronology and allowed inputs

| Block | Frozen inputs | Time basis and limitations |
|---|---|---|
| H | natural log of newly sampled PGA in g | Pinned M7.8 `us6000jllz` ShakeMap reconstruction produced 2025-03-20; retrospective hazard exception, not a pre-event product |
| X | structural family only | June 2023 ascertainment of presumed pre-existing design; height suffixes stripped; no independently verified pre-event inventory |
| EO | Sentinel-2 L2A, 2022-06-01 through 2022-09-30 | Every contributing sensing timestamp precedes 2023-02-06 01:17:35 UTC; later archive reprocessing is allowed and disclosed |
| Land cover | ESA WorldCover 2021 v200 | 2021 observation basis, CC BY 4.0; preserve ESA attribution |
| Elevation | AWS Copernicus GLO-30 2021 release | Mainly TanDEM-X 2011–2015 acquisition plus gap fills; **DSM** including structures/vegetation, not bare-earth terrain |
| Encoder | original multispectral SatMAE ViT-Large | Weights published 2022-11-17; global pretraining may include these geographies |

The narrow X permission is an explicit scientific interpretation. Damage may still affect structural classification or missingness. The prespecified **H versus H+GeoAI** sensitivity omits survey X on the same cohort. A stronger strictly verified pre-event X claim is not supported. See [chronology evidence](survey_chronology_1f.md).

H is independently resampled from the companion repository's checksum-pinned XML; it does not overwrite the original canonical workbook IMs. Use nearest actual printed grid node, lower coordinate for exact ties, no extrapolation. Convert XML PGA/PSA `%g` to g; retain PGV in cm/s. The workbook's product revision remains unproved. Physical PGA is fixed before fitting; do not repeat outcome-informed IM selection from the source paper. Other sampled IMs are audit outputs, outside the primary allowlist.

## Actual pixel audit and reproducibility

`python -m src.data.geoai_feasibility --network` queries and caches every Earth Search STAC page for the survey extent and locked season, then reads **actual raster windows** at every distinct coordinate. It audits all 559 records, including subsequently excluded records. Catalogue intersection alone is insufficient.

Each coordinate gets a north-up **96×96, 10 m UTM 37N grid**, centre snapped to the nearest 10 m. Source bands are bilinearly resampled; SCL/land-cover categories use nearest neighbour. The band order is B02, B03, B04, B05, B06, B07, B08, B8A, B11, B12. Upsampling 20 m bands does not create 10 m physical detail. Source STAC asset scale and offset are applied exactly once; GeoTIFF defaults or a second BOA offset must not override them.

Candidates must cover the point, contain all bands, meet the sensing window and have scene cloud cover ≤20%. Rank ascending scene cloud, descending sensing timestamp, then ID; attempt at most 12. SCL classes 2/4/5/6 are accepted, all others rejected, with a one-pixel dilation of rejected cells. All ten bands must have finite, unmasked measurements. Combine clear observations by pixelwise median, stopping at the first ranked prefix with complete support. No cloud/nodata filling is permitted. This is a deterministic clear-observation composite, not an independently cloud-free ground-truth guarantee; thin cloud and atmospheric error remain possible.

The cache records attempted/selected scenes, timestamps, coverage, chip hashes and context URLs. Network errors are recorded; an incomplete location stays ineligible. Cached audit reports prevent repeated unbounded acquisition; retrying a failed location requires explicitly removing that location's generated cache and rerunning `--network`. An offline run refuses absent caches. New remote catalog revisions are not silently reconciled: retain and hash the original catalog and chips.

The same 960 m square supplies both engineered and learned context. Features are fixed before labels are used for fitting:

- Mean and population standard deviation of green, red, NIR and SWIR1 surface reflectance (eight direct spectral moments).
- Red reflectance texture: mean absolute horizontal/vertical adjacent-pixel differences, averaged equally.
- WorldCover built class 50 and vegetation classes 10/20/30/40/90/95/100 fractions inside 250 m and 480 m pixel-centre circles.
- DSM mean, 95th-minus-5th-percentile relief and mean slope in degrees from 10 m resampled gradients. Slope is a smoothed surface descriptor, not a 10 m terrain measurement.

Input QA found undefined pixelwise normalized-difference denominators in 192 of 499 chips, often at only one dark pixel. Before any fitting, the final protocol therefore chose direct band moments instead of normalized-difference indices. No ratios are filled or silently omitted. These contextual measurements may describe neighbours rather than the individual building; a 2022 image does not prove every surveyed building already existed. No claim of remotely resolving reinforcement or construction quality is made.

## Frozen representation and comparison

Use **one** frozen SatMAE multispectral ViT-Large, 1024-dimensional mean-pooled final non-CLS tokens, with strict encoder-key verification, no task-specific adaptation and deterministic identity/no-mask inference. The complete checkpoint, source revision, channel groups and exact non-z-score normalization are in [the encoder contract](eo_representation_1f.md). The checkpoint is 3.95 GB including optimizer state. Weights are CC BY 4.0; repository code is **CC BY-NC 4.0**. This research design does not establish commercial clearance.

Weights were not downloaded or executed in this milestone. Checksum verification, deterministic inference smoke tests and resource measurement are explicit 2A preflight tasks; imagery feasibility is not a claim of measured encoder throughput. Prithvi is documented as a deferred alternative, not a second primary representation.

The four primary arms are **H → H+X → H+X+Z_engineered → H+X+Z_GeoAI**. The final arm replaces engineered Z with SatMAE Z so the source of added information is clear. A union of both Z blocks requires a separately declared sensitivity. Use the same regularized multinomial logistic readout, fixed C grid and validation RPS selection for all arms, as specified in JSON; no readout is fitted now. All task-specific scaling/encoding happens inside training folds. Unseen structural categories map to OTHER; no learned representation, normalization or PCA is fitted on validation/test imagery. No encoder selection by held-out performance.

Outer test cities, in order: **Antakya, Hassa, Iskendurun, Islahiye, Kahramanmaras, Kirikhan, Narli, Nurdagi, Pazarcik, Turkoglu** (source spellings retained). Validation is the next city cyclically, except Narli uses Pazarcik because Nurdagi has only three source observations. Remaining cities train. Purge both sides of any cross-partition pair less than **2 km** apart, exceeding twice the square's 679 m circumradius; no context overlap or label propagation across folds. Empty or very small city folds are reported, never replaced after results are seen.

Primary scoring is normalized five-class ranked probability score; macro-average nonempty test-city scores and list every city's support. Report ordinal MAE, fixed-five-class macro F1, class recall, any-damage Brier and calibration. Use 2,000 paired within-city site-bootstrap draws (seed 20231005) plus fold spread; nearby sites are still correlated, so these are conditional uncertainty summaries, not population confidence guarantees. Rare/absent training classes require explicit reporting and fixed five-column probabilities, not changed labels. No hyperparameter choice may use outer test-city scores or ACI133 labels.

ACI133's 242 observations stay untouched externally. Before a later external evaluation, adjudicate shared buildings, event headers and native label compatibility, and purge all training/validation sites with overlapping 960 m context (2 km screen) with retained external sites. The previous 25/100 m building-overlap checks alone are insufficient for EO context. No pooling or external score is authorized by 1F.

## Default-deny features and remaining gate

Only the named H/X/Z columns may become predictors. IDs, coordinates and cities are join/split/audit metadata. Prohibit floors/height bands, construction vintage, occupancy, occupied status, placards, repairs, damage descriptions, casualties, photos, assessor/date, target-derived products, post-event imagery, current/undated footprints, and all unlisted workbook variables. The large spatial package's footprints, PGV/damage layers and undated source products do not enter this experiment merely because they are available. No current OSM or Microsoft footprint counts are treated as pre-event exposure.

**Labels:** native survey grades with explicit exclusions. **Pre-event inputs:** audited 2022 Sentinel-2, 2021 WorldCover and older DSM. **Representation:** frozen SatMAE-Large contract. **Held-out cities:** the ten-city schedule above. **Prohibited variables:** everything outside the explicit allowlists, particularly post-event and target-derived information.

Model fitting remains disabled in 1F. Design review and encoder preflight precede an explicitly started 2A. CSB access is not one of those blocking conditions. B0 is separately authorized synthetic catastrophe mechanics, documented in [risk_b0.md](risk_b0.md), with no learned vulnerability inputs.

## Source and licence record

- [Earth Search official collection and scale/offset documentation](https://github.com/Element84/earth-search/blob/main/README.md); Copernicus Sentinel data attribution/terms apply, not the API's code licence.
- [Sentinel-2 L2A band and scene-classification documentation](https://docs.sentinel-hub.com/api/latest/data/sentinel-2-l2a/).
- [ESA WorldCover data and CC BY 4.0 attribution](https://esa-worldcover.org/en/data-access).
- [AWS Copernicus DEM release and licence links](https://registry.opendata.aws/copernicus-dem/) and [Copernicus acquisition/product description](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM). Preserve its custom attribution/licence; do not relabel it CC BY.
- Survey and companion hazard repository: [pinned source](https://github.com/maxandersonloake/TUR2023_02_06/tree/be088671596f04ad5a058f7819ec3bb762156f17). Retain source/USGS attribution; the new XML checksum is in `geoai_feasibility.py` and generated provenance.

Raw imagery, chips, restricted microdata, weights and processed row tables remain outside Git. The repository contains reproducible code, configuration, aggregate execution evidence and source links.
