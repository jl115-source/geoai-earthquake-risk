# Milestone 1D: harmonization and experiment design

This milestone starts from consolidated `main` at `90a48d8`, after merging
PR #1, updating #2 and #3, and merging both. It adds no acquisitions and fits no
models. Dataset-native labels remain authoritative. A common storage schema is
**not** permission to pool observations or equate damage grades.

## Deliverables and reproduction

- [Canonical record contract](../configs/building_record_1d.schema.json), with
  nullable types, physical units and provenance fields.
- [Frozen experiment configuration](../configs/experiments_1d.json), including
  ordered domains, validation selection, evaluation rules and explicit blockers.
- [Adapter](../src/data/harmonize.py) and
  [partition generator](../src/data/design_experiments.py). Neither imports or
  fits an estimator. All input records survive harmonization.
- [Measured harmonization summary](harmonization/summary.json),
  [native IM catalog](harmonization/native_IM_catalog.json), and
  [fold counts and class supports](harmonization/experiment_summary.json)
  ([compact CSV](harmonization/fold_counts.csv)).

From the repository root, using the already acquired Milestone 1C inputs:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-audit.txt
python -m src.data.turkiye
python -m src.data.harmonize
python -m src.data.design_experiments
python -m pytest -q
```

The last three steps work offline. They use the 1C RC/ACI Parquet files and
extracted spatial package; if those derived inputs are absent, run the existing
`python -m src.data.audit_expansion` against the previously acquired raw inputs.
Do not run acquisition as part of 1D. Missing inputs fail explicitly.

Canonical tables are separate files in ignored `data/processed/harmonized/`.
Row-level split manifests, engineering proximity groups and the reserved ACI
partition are in ignored `data/processed/experiment_design/`. They contain no
imputed features or predictions. The reports committed here contain aggregate
counts and public field definitions, not Nepal microdata. Input, output and
configuration hashes bind manifests to a specific dataset version. Reordering
source rows changes source-record identity; regenerate the design for a new
version rather than treating row-based IDs as permanent physical building IDs.

CI exercises the registered Türkiye subset with `--datasets turkiye_survey`
and unit tests; the full locally acquired stack is checked locally. CI does not
download or upload Nepal microdata.

## One schema, separate observational domains

| Component | Canonical fields | Interpretation |
|---|---|---|
| Record identity | `schema_version`, `dataset_id`, `record_id`, `identity_status` | Source-record identity, never an assertion of one unique physical building |
| Event | `event_id`, `event_scope`, `country` | Shared Türkiye/Syria sequence across both engineering surveys and spatial products; six distinct RC events; Nepal survey after the Gorkha sequence |
| Building attributes | `floors_native`, `floors`, `floors_time_status`, `structure_native`, `structure_family` | Native representation plus cautious parsing; other engineering fields stay in the linked authoritative source |
| Damage | `damage_native`, `damage_scale`, `damage_ordinal_native`, `high_damage_candidate`, `damage_mapping_status`, `label_provenance` | Native damage and explicit mapping status; unknown spatial semantics are not made ordinal |
| Intensity | `PGA`, `PGV`, `SA_0p3`, `SA_1p0`, `im_status`, `im_source`, `im_transform`, `im_event_id` | Nullable physical-scale values; g for accelerations and cm/s for PGV; no automatic event-block selection |
| Location | `latitude`, `longitude`, `coordinate_status`, `coordinate_method`, `city`, `admin1`, `admin2`, `admin3` | WGS84 points or administrative codes; no ward/municipality centroid imputation |
| Provenance | `source_path`, `source_sha256`, `source_row`, `source_row_unit`, `source_id_native`, `author_supplemented`, `license` | Exact local source and record pointer; all extra native fields remain accessible |

The schema has no catch-all universal `damage_grade`. `im_event_id` stays null
where a unique shock/product identity has not been verified. RC `event_id` is
known even though its intensity values are absent. Türkiye published intensities
remain usable as explicitly documented sequence-damage proxies; this does not
establish a causal single-shock fragility experiment.

The adapters retain **793,648 records**: 559 Türkiye, 242 ACI133, 619 RC,
762,106 Nepal and 30,122 `This_study`. The 4.41M footprint layer is context and
does not become another damage-labelled table. No original engineering variable
is discarded: the original/1C tables remain authoritative, linked by hash and
source record. For ACI, physical columns `c001`–`c106` avoid duplicate-header
ambiguity; the formula/supplementation sidecar remains available.

## Damage compatibility

| Dataset | Native representation retained | Permitted now | Cross-dataset status |
|---|---|---|---|
| Türkiye survey | Exact label plus 0–4 companion-analysis ordinal | Within-source ordinal analysis; missing labels stay null | Severe/partial-collapse/complete-collapse versus lower grades is only a provisional broad grouping |
| RC619 | N/None, L/Light, M/Moderate, S/Severe, C, R | Within-source 0–4 ordinal; R remains unmapped | N/L/M/S/C normalization within RC is defensible; cross-survey equality is not established |
| ACI133 | Five-class N/L/M/S/C; original three-class labels remain in source | Within-source 0–4 representation | Same letters alone do not establish the same assessment rubric; supplemental values require review |
| Nepal GEID | Grade 1–5, plus 12 missing | Native ordinal **1–5** | Never subtract one and claim equivalence to engineering 0–4; no binary harmonization enabled |
| `This_study` | Literal codes 1, 2, 3, 4 | Store as native categorical codes | **Ordinal and harmonized fields remain null** until meanings and label generation are verified |

RC metadata define severe damage as structural failure of at least one element;
collapse includes loss of elevation of a floor slab **or part of it**. The Türkiye
survey instead puts partial collapse with severe damage and reserves grade 4 for
complete collapse. Thus the integer 4 cannot be pooled as a universal collapse
endpoint. The candidate `high_damage_candidate` groups native engineering
ordinals ≥3 only to support rubric review; every such value is explicitly
`provisional_not_for_pooling`. It is not the target of any current experiment.

No codebook has resolved spatial `damage_lev`, and the deposit does not establish
that these labels are independent engineering observations. If they are model
outputs using PGV, terrain or morphology, predicting them using those same
variables is teacher-model replication, not independent damage validation.
Independent visual/UNOSAT/Microsoft products also have different definitions and
must not fill missing targets or enter the predictor matrix. See the
[1C source audit](data_expansion_audit.md) and its public dictionaries for evidence.

## Intensity and coordinate readiness

| Dataset | Usable native physical IMs | Coordinate candidates for future point sampling | Current limitation |
|---|---|---:|---|
| Türkiye survey | PGA, PGV, SA(0.3), SA(1.0): 559 each; exp(log mean) | 559 | 499 distinct pairs; sequence target, source-point accuracy and exact shock/product attribution require care |
| ACI133 | Physical units declared across 57 intensity columns, including repeated earthquake blocks | 242 | Canonical IMs remain null; inconsistent headers and author supplementation prevent selecting a unique event block |
| RC619 | None | 353 / 619 | No local ShakeMap grids; 266 lack coordinates, including all Erzincan and Wenchuan records |
| Nepal GEID | None | 0 / 762,106 | Administrative codes only; district ShakeMap averages are not building-level H |
| `This_study` | None verified; package PGV is encoded uint8 | 30,122 | Interior points derived from valid polygons; codebook, physical raster conversion and sequence/event attribution unresolved |

"Coordinate candidate" is not "sampled" or "sampling-ready". No intensity
sampling is performed in 1D, and no new grids are downloaded. For later sampling,
freeze event/product/version and hash; verify bounds and CRS, handle nodata and
out-of-grid locations explicitly, document interpolation, and convert field
units (for example percent-g to g only when the grid declares percent-g).
Never extrapolate beyond coverage. A registered event URL is not a local grid.

For sequence damage, retain each relevant shock's intensity separately. Do not
duplicate the same final damage observation across shocks as independent labels,
select a maximum after looking at model performance, or attach a single shock
without identifying that approximation. Current ACI maxima are preserved as
source variables, not silently substituted for event-specific IMs.

Range-valid coordinates do not prove survey precision or identity. Spatial
coordinates are deterministic interior points calculated in UTM 37N and
transformed to WGS84, not field GPS observations. Native geometry remains in its
source. Nepal IDs are rounded; synthetic source-row keys repair indexing only,
not physical identity. Official HRHRS remains unacquired and cannot be counted
as an external independent Nepal dataset.

## Which attributes are actually common?

There is **no verified universal H+X feature set across all five labelled sources**.

| Attribute | Availability and comparability |
|---|---|
| Floors | Present in all four engineering/survey datasets; Nepal `H:n` parses to n. Pre/post-event time basis is not established uniformly. No floor field in `This_study`. Keep `floors_time_status`; do not use post-collapse floors as vulnerability predictors. |
| Construction/structure | Türkiye detailed categories, Nepal 11 multilabel superstructure flags, RC/ACI cohort descriptions. Do not replace Nepal mixed-material flags with an invented single RC/masonry class. Cohort membership is not a measured taxonomy field. |
| Age | Türkiye vintage/category and ACI numerical age; absent in GEID and RC Priority I. No midpoint or age inferred for Nepal from the unacquired HRHRS dictionary. |
| Area | RC ground/first-floor area versus ACI floor/critical-floor measures; Türkiye area unit unverified. Spatial polygon area is footprint area, not total floor area. Distinct variables until definitions agree. |
| Occupancy | Türkiye and Nepal, with different native labels; not a universal feature. |
| Wall/column indices | RC/ACI only. Definitions, critical-floor versus ground-floor location and measurement timing must be reconciled before sharing coefficients. |
| Vs30 / shaking | Available in Türkiye and ACI source blocks, absent in GEID/RC tables and unverified physically in spatial rasters. |
| Location/administrative IDs | Split and audit fields. Not predictors in the primary vulnerability benchmarks. |

Pre-event feature allowlists must be dataset-specific. Start native vulnerability
designs with independently verified construction/material variables. Floors,
age, area, wall/column dimensions, soft-storey and captive-column fields remain
conditional on definitions and pre-damage measurement provenance. Do not feed
the entire canonical table to an estimator: source IDs, ordinals, candidate
labels, repair, member/infill damage, casualties, placards, critical-damage
encodings, target-derived indices and survey/assessor metadata are prohibited.
All fitting, category vocabularies, scaling, imputation and learned encodings
must be trained inside training folds later; none is performed here.

## Frozen train/validation/test experiments

The [configuration](../configs/experiments_1d.json) contains the exact ordered
domain lists. For each outer fold, **test = current domain, validation = next
domain cyclically, train = all remaining domains**. These choices depend on
domain identity, never damage outcomes. One fixed override uses Pazarcik for
validation when Narli is the Türkiye test city, avoiding a three-record Nurdagi
validation set. Nurdagi remains an outer test city, with its three test records
and very limited inferential value reported explicitly. Hyperparameters/thresholds use training and
validation only; the test set is opened once for that fold. No random row split,
damage balancing or class-dependent geography selection is permitted.

| Experiment | Outer test units | Training / validation / test | Target and status |
|---|---|---|---|
| Türkiye native baseline | Each of 10 cities | 8 cities / next city / held-out city | Native 0–4. H-only then H+approved X; explicit repeated-site controls and sequence caveat |
| Nepal conventional vulnerability | Each of 11 districts | 9 districts / next district / held-out district | Native 1–5, X-only. No fine spatial or H+X claim; municipality-clustered uncertainty |
| RC619 event transfer, X-only | Each of 6 events | 4 events / next event / held-out event | Native 0–4; R excluded explicitly. Same-source event transfer, not cross-scale pooling |
| RC619 paired H+X subset | Same six proposed event folds | Same event roles, coordinate-required subset | **Blocked**: no local grids; two test events have no candidates. Empty folds are reported, not scored as zero or dropped silently |
| Spatial augmentation / city transfer | Antakya, Jindires, Nurdagi | One city / next city / held-out city | **Blocked** until native label semantics, independence and H/X provenance are established |
| ACI133 external engineering validation | Entire source reserved | No current train/validation allocation | **Blocked** by overlap, rubric/event-header reconciliation and supplemented-cell adjudication |

There are 36 generated design folds: 10 + 11 + 6 + 6 + 3. All original records
appear in every relevant fold manifest with a partition or a reason for
exclusion; these are planning artifacts, not a declaration that every experiment
is ready to fit. ACI has a separate 242-row `reserved_external` manifest.
The aggregate report gives exact train/validation/test counts, native class
supports, exclusions, small-sample warnings and empty-partition flags for every
fold. RC Pisco's 27 records likewise support only a weak validation/test estimate;
keep tuning modest and report that limitation rather than promising stable scores.

If a training fold has no examples of a test class, retain/report that limitation;
do not redefine the task or shuffle held-out records to repair it. Report class
support and undefined metrics as unavailable. The RC hazard subset must compare
X-only and H+X on the **same eligible records**; a separate full X-only result
must not be presented as a paired improvement. Once grids exist, freeze an
additional IM-valid cohort without looking at outcomes and regenerate manifests.

Pooling is disabled. RC events may share training data inside the RC native
scale, and Nepal districts inside the Nepal scale. Türkiye and ACI may only
support a later expressly approved common endpoint after adjudication and
overlap control. Spatial labels stay a separate observational product. This
stack supports event transfer through RC and city/region transfer elsewhere;
it currently contains only one spatial earthquake sequence, so it cannot test
**cross-earthquake transfer of a spatial representation**.

## Leakage controls

| Dataset or operation | Leakage risk | Enforced or prescribed control |
|---|---|---|
| Türkiye repeated sites | Exact duplicates, same physical building, contradictory labels | Exact-coordinate conflicts are excluded from supervised design with reason; all rows remain in canonical data. Repeated coordinates receive total evaluation weight 1, explicitly a site-weighted estimand, not deduplication. |
| Türkiye + ACI | Close sites/buildings in different sources | Deterministic 100 m connected components across both sources. Groups crossing city roles are quarantined. Before later ACI testing, purge every shared component from training or external test per a frozen protocol; 25 m is not an identity guarantee. |
| Nepal | Rounded IDs, households/records sharing locations, geographic autocorrelation, duplicate source projections | Never split or join on rounded BUILDING_ID; whole districts held out, municipalities used for uncertainty. Do not add official HRHRS as new independent records. Within-district physical duplicates remain unresolved. |
| RC | Same earthquake/site or event-specific acquisition practice | Whole events assigned together; coordinate repeats receive site weights. Event/country/source IDs are excluded as predictors. Correlated Türkiye earthquakes remain a limitation; leave-country-out is a later sensitivity analysis, not a completed experiment. |
| ACI | Author estimates, formulas and damage-derived features | Preserve source cell flags; exclude supplemented predictors from the primary external comparison unless independently justified. Never use critical damage, alternate damage encodings or masonry damage to predict structural grade. |
| Spatial labels | Teacher outputs, overlapping products, post-event imagery/footprints, label-informed features | Require independent target provenance and pre-event feature chronology. Other damage maps, ARIA overlays, Join_Count and neighbouring damage labels are not X or Z. |
| Spatial graphs/embeddings | Cross-partition message passing or unsupervised use of test geography | Primary comparison is inductive. Build graphs and fit embeddings separately inside training boundaries; no test-city nodes in training graphs or encoder fitting. A transductive result would be a separate claim. |
| All preprocessing | Full-dataset normalization, imputation, vocabulary, feature selection or tuning | Fit on training only; validation for selection; test untouched. No target encodings from other folds. Freeze the feature contract before fitting. |

The 100 m engineering components are conservative leakage groups, not confirmed
building merges; transitive chains may join more than direct 100 m pairs.
The generated group table is stable under input ordering because names hash
sorted record IDs. Exact-coordinate conflicting survey labels are not resolved
by majority vote. Site-weighted and raw-record metrics should both be reported
later because multiple buildings can legitimately share a rounded coordinate.
There are 49 ACI records in components connected to the survey, exceeding the
34 direct 100 m candidates because connected components include transitive links.
The floor inventory also finds 7 RC and 49 ACI fractional reported counts; these
are retained as reported, not rounded or automatically declared impossible.

For spatial experiments, use a maximum neighbourhood radius of 500 m and a
minimum cross-partition separation of 1 km. The generator verifies a conservative
projected city-bounding-box distance bound; it fails if that cannot certify the
buffer. It also freezes 5 km UTM 37N cells for uncertainty clusters. If a future
within-city experiment is added, it must implement buffered spatial blocks and
publish its purged-record counts separately; a random building split is not a
substitute for the city-transfer experiment.

## Spatial H + X + Z versus H + X

Define H as physically calibrated, event-attributed shaking; X as approved
building-level attributes, including pre-event footprint size/shape if that
provenance is established; and Z as surrounding-building density, layout and
height summaries or learned neighbourhood representations. Separate tests can
add verified DEM/lithology/fault-distance context. Do not put encoded raster
values into H as though they had known units. Do not use post-event footprint
deletion or damage-conditioned availability as pre-event vulnerability features.

The primary paired comparison uses identical records, labels, partitions,
preprocessing policies and tuning budgets. A GNN is not automatically warranted
by the record count: compare fixed neighbourhood summaries before a learned
spatial encoder. If only morphology is available, call that X versus X+Z and
report it separately; it does not answer the planned H+X question.

For native ordinal tasks, pre-register ranked probability score as the primary
probabilistic metric, plus ordinal MAE, macro-F1, quadratic weighted kappa,
class-wise recall/support and calibration. For any later approved binary
endpoint report Brier/log loss, PR-AUC with prevalence and calibration. Do not
score unknown spatial ordering with ordinal loss. Macro-average held-out domains
and also report sample-weighted results and each fold individually.

Use 2,000 cluster bootstrap replicates with seed 20231005 on out-of-fold
predictions: survey site component, Nepal municipality, RC event, spatial 5 km
cell. Bootstrap paired model differences with the same sampled clusters.
With only six events or three cities, intervals and fold spread do not establish
broad global transfer. Do not treat millions of correlated footprints as millions
of independent evaluations. These metrics are specifications, not computed scores.

## Decisions before the first fit

1. Freeze dataset-specific pre-event feature allowlists and decide how the
   observed duplicate/conflict exclusions affect the intended estimand.
2. Choose a native-label pilot. Türkiye's published H proxy is available;
   Nepal offers scale for X-only learning. Neither requires pooling native scales.
3. Resolve the spatial codebook, label-generation inputs and feature chronology
   before claiming observed-damage GeoAI. Until then the spatial experiment is blocked.
4. Resolve ACI overlap and augmented-cell/event-header interpretation before
   counting it as an independent external test. RC intensity experiments need
   verified local grids and a transparent coordinate-eligible cohort later.

No additional collection is initiated here. The spatial deposit's **CC BY 4.0**
status is retained in the schema and audit; upstream attribution remains required.
Official Nepal microdata remain outside Git and unacquired. Italy remains deferred.
