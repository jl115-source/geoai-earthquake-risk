# Literature review and research positioning

**Status:** modelling frozen  
**Review date:** 2026-10-05  
**Scope:** targeted scoping review, not a PRISMA/systematic review

This review was conducted after Milestones 1A–1D established the data,
provenance and leakage-safe experiment design. Its purpose is not to justify a
model already chosen. It is a research gate: identify what has already been
done, what claims would be incremental, and what evidence is still needed
before modelling resumes.

The companion [literature matrix](literature_matrix.csv) records the core
papers considered in this pass.

## Executive conclusion

The project has a strong data and experimental foundation, but several initially
attractive claims are already well represented in the literature.

The project should **not** claim novelty from:

1. fitting standard empirical fragility curves to the 2023 Türkiye engineering
   survey;
2. applying XGBoost/Random Forest/CatBoost to Nepal or Türkiye building damage;
3. holding out a region or earthquake as the sole methodological contribution;
4. adding geology, Vs30, fault distance or other site variables to a tree model;
5. using a GNN merely because buildings can be represented as a graph;
6. using the 30,122 `This_study` records as independent observed damage truth.

The strongest defensible research direction emerging from this review is:

> **Do independently defined, pre-event spatial and neighbourhood-context
> features add calibrated predictive information beyond hazard intensity and
> conventional building attributes, and does that incremental information
> persist under leakage-safe geographic or event distribution shift?**

That question is narrower than “GeoAI for earthquake damage,” but much stronger.
It explicitly tests the *incremental value* of spatial context rather than
assuming it is useful.

There is one major gate: the project currently does not have a verified,
independent, large spatial target suitable for that headline experiment.
The 30,122 `This_study` labels are outputs of Liu et al. (2026), not an
independent field-survey truth set. The repository's `Visual_interpretation`
layer is described by the deposit as the manually annotated validation source,
but our audit has not yet recovered a trustworthy explicit damage-grade field
from those files. Spatial modelling therefore remains frozen.

## 1. Classical empirical fragility remains the benchmark, not the novelty

Empirical earthquake vulnerability predates modern ML by decades. Rossetto and
Elnashai (2003) derived vulnerability functions from 99 post-earthquake damage
distributions spanning 19 earthquakes and roughly 340,000 reinforced-concrete
structures. That work is directly relevant to our cross-source harmonization
problem: heterogeneous observational data require an explicit damage-scale
crosswalk rather than naïve integer pooling.

The GEM empirical vulnerability guidelines (Rossetto et al., 2014) make the
same methodological point that our data audit has forced on us: the
characteristics and limitations of the observations should determine the
statistical model and intensity measure, not the reverse. Their later compendium
(Rossetto, Ioannou and Grant, 2015) demonstrates how broad the existing
empirical fragility literature already is.

Lallemant, Kiremidjian and Burton (2015) is especially important for the
baseline design. It compares standard parametric fragility fitting with
generalized linear/cumulative-link models and non-parametric approaches such as
GAMs and kernel smoothing, discusses uncertainty in the intensity measure, and
frames model choice in terms of predictive error. Therefore, a lognormal
fragility curve, ordinal regression or GAM should be treated as essential
benchmark methodology, not a new contribution.

Ioannou, Douglas and Rossetto (2015) show why our hazard provenance matters.
Spatial ground-motion variability and epistemic uncertainty can materially
change empirical fragility functions; sparse shaking observations can flatten
estimated curves and aggregated damage observations can increase uncertainty.
This strengthens the 1D rule that a registered ShakeMap URL or administrative
average is not automatically a building-level hazard covariate.

### Direct consequence for this project

A conventional Türkiye fragility analysis remains useful, but only as a
**benchmark/replication arm**. It should establish a transparent reference
against which later H+X and H+X+Z experiments are judged.

## 2. The exact Türkiye engineering survey has already received a sophisticated bias-aware analysis

This is the most important direct-overlap paper in the review.

Anderson Loake and Jaiswal (2026), *Accounting for Biases in the Analysis of
Building Damage Data for the 2023 M7.8 Türkiye/Syria Earthquake Sequence*,
uses the same Jaiswal engineering-survey source family that underlies our
Milestone 1A workbook. The paper explicitly models sampling bias, missingness,
measurement error and inventory uncertainty in a hierarchical Bayesian
framework.

It also uses PSA/SA at 0.3 s as the primary intensity measure after comparing
candidate IMs. Because of the small engineering-survey sample, the published
fragility example focuses on any-damage occurrence rather than attempting to
claim stable full five-state fragilities. The paper further notes the survey's
non-random spatial design and the fact that it was collected months after the
earthquake sequence.

This makes several possible project directions redundant:

- “derive Türkiye fragility curves” is not novel;
- “show SA(0.3) predicts damage” is not novel;
- “account for survey bias” is not novel for this source;
- “Bayesian uncertainty for the Türkiye survey” is not novel by itself.

Our contribution must therefore be downstream or orthogonal: reproducible
multi-domain evaluation, calibrated prediction, pre-event feature increments,
spatial context, and transfer/generalization.

It is also useful as a methodological comparator. If our simple empirical
baseline disagrees strongly with the bias-aware paper, that disagreement should
be investigated rather than presented as a superior model.

Reference:
- Anderson Loake, M. & Jaiswal, K. S. (2026).
  DOI: https://doi.org/10.1002/esp4.70117

## 3. Tabular ML on earthquake building damage is already mature enough that algorithm choice is not a contribution

### Nepal

The 2015 Gorkha earthquake data have already supported several ML studies.

Ghimire et al. (2022) evaluated machine-learning models for regional damage
prediction using Nepal building-damage observations combined with ShakeMap
intensity. Their results show that basic building attributes can already yield
useful regional damage prediction.

Chen and Zhang (2022) used XGBoost with SMOTE on Nepal data and SHAP
interpretation. Foundation type, roof type and building age emerged as important
features.

K C et al. (2023) used 549,251 Nepal buildings with shaking intensity and
detailed building attributes to predict damage grade and rehabilitation
intervention using decision trees, Random Forest, XGBoost and logistic
regression. XGBoost performed best among their tested models.

Therefore, a large-N Nepal XGBoost benchmark is useful for reproducibility and
feature sanity checks but is **not** a headline contribution.

### Türkiye

Recent Türkiye studies further close the “apply modern ensemble ML to field
damage” gap.

Hariri-Ardebili and Sattar (2026) apply interpretable AutoML to more than 240
reinforced-concrete buildings from the same ACI133 data family in our repository.
Their reported models use building and shaking features with Random Forest and
CatBoost, plus SHAP interpretation. ACI133 should consequently remain primarily
an external/reproduction dataset rather than the source of our novelty claim.

Bıçakcı et al. (2026) evaluate eight tree-based ensemble learners on 16,611
building observations from Kırıkhan, Hatay, including building/site variables
and explainability. Thus “LightGBM + geology/fault distance on real 2023 Türkiye
damage” is already occupied territory.

A separate 2026 Journal of Earthquake Engineering study develops fragility and
ML damage-classification models for 322 buildings using strong-motion-derived
PGA, PGV, CAV, Arias intensity, spectral acceleration and related IMs. Again,
testing many IMs against observed Türkiye damage is not itself novel.

### Direct consequence

The model family should be treated as an experimental instrument. We need
simple, interpretable and strong baselines, but the scientific contribution
must live in the *question, data provenance, experimental design and measured
incremental information*, not in selecting CatBoost over XGBoost.

## 4. Cross-region and cross-event testing already exists

Ghimire and Guéguen (2024) explicitly study host-to-target transfer across
Nepal, Haiti, Serbia and Italy using building age, number of stories,
macroseismic intensity and a traffic-light damage representation. Their
central question is already very close to “train in one region, test in
another,” and they report that successful transfer depends strongly on
contextual similarity between host and target regions.

Patten, Anderson Loake and Steinsaltz (2024) go considerably broader. Their
satellite-derived building-damage analysis contains 369,813 geolocated
buildings from 26 earthquakes in 15 countries, uses grouped out-of-sample
validation, and separately holds out the 2023 Türkiye–Syria event. This shows
that multi-earthquake grouped validation itself cannot be our novelty claim.

The 2025 Engineering Structures review by Hu et al. identifies generalizability,
data scarcity, feature selection and regional-scale validation as continuing
problems in earthquake-engineering ML. The gap is therefore not that nobody has
noticed domain shift. The useful opportunity is to make the incremental spatial
comparison unusually controlled and leakage-safe.

### What our 1D protocol adds

Our frozen experiment design is still valuable because it treats geography as a
unit of generalization rather than a random feature and explicitly prevents:

- record-level random splits across a held-out geographic domain;
- duplicate/near-duplicate sites crossing partitions;
- test-city nodes entering learned spatial encoders;
- full-dataset normalization, imputation or category learning;
- comparison of H+X and H+X+Z on different eligible samples.

Those controls should be part of the eventual contribution, but they must be
paired with a substantive scientific result.

## 5. Site and geospatial variables have already been used; “add geology” is not enough

Senkaya et al. (2024) use local site descriptors including Vs30, predominant
frequency, HVSR amplification and engineering bedrock depth to predict damage
status following the 2023 Türkiye earthquakes. This demonstrates that local
site conditions are already an established ML feature direction.

Bıçakcı et al. (2026) also include contextual variables such as lithology and
distance-related information in a much larger 2023 Türkiye field dataset.

Classical fragility work likewise recognizes ground-motion spatial variability
as central rather than nuisance-only. Consequently, simply appending DEM,
lithology, Vs30, fault distance or epicentral distance to a gradient-boosted
tree would be incremental.

### More promising spatial question

The less saturated question in this targeted review is **pre-event
neighbourhood morphology and spatial representation**:

- building density at multiple radii;
- local height and footprint distributions;
- orientation/layout and spacing;
- street/block or adjacency context;
- physically justified neighbourhood graphs;
- spatial embeddings learned without access to held-out geography.

GNN-based seismic damage prediction now exists, including region/building graph
models, but prominent recent examples use physics-based simulated structural
response data rather than independent post-earthquake building-level field
damage. That distinction matters. A GNN on observed field damage is only useful
if the graph adds information beyond strong H+X baselines and the split prevents
geographic leakage.

This review therefore supports a *controlled spatial increment* rather than a
“GNN project.”

## 6. Remote-sensing damage assessment is a neighbouring field, not the same research target

There is a large and rapidly growing literature using optical/SAR imagery for
post-event damage mapping, including transfer learning, multimodal fusion,
building-footprint priors and object-level damage classification.

This literature matters for two reasons.

First, it establishes that post-event imagery can be highly predictive. If we
include post-event remote sensing in Z, we are no longer testing pre-event
vulnerability; we are performing damage assessment.

Second, it creates a serious target-provenance problem in our large Türkiye
spatial package.

### Critical finding: `This_study` is not independent ground truth

The Zenodo record for Liu (2026), *Building damage datasets for the 2023 Türkiye
earthquake*, describes:

- `Visual_interpretation` as manually annotated labels used as a
  high-confidence validation dataset;
- `This_study` as building-damage results produced by the methodology developed
  in the associated study.

The associated paper, Liu et al. (2026), *SAR-based individual-building damage
identification and large-scale earthquake damage prediction*, develops a
SAR/coherence-based building-damage method and then an XGBoost damage-density
prediction model using seismic, topographic, geologic and building factors.

Therefore the project's 30,122 `This_study` records **must not be treated as
30,122 independent observed damage labels**. They are method outputs/pseudo
labels. Using the same or related predictors to learn those labels could amount
to reproducing the teacher methodology and would overstate evidence for
physical vulnerability.

They may still be useful for:

- auxiliary/pseudo-label experiments explicitly labelled as such;
- comparison against independent validation labels;
- representation pretraining, if leakage/provenance permits;
- studying disagreement among damage products.

But they are not currently an acceptable headline supervised target.

The strongest candidate target in the package is the manually interpreted
validation product. Our Milestone 1C audit found 20,690 visual-interpretation
features but did not recover a reliable explicit damage-grade field from the
shapefile attributes. Recovering the original annotation semantics/codebook is
now a **hard gate** for the spatial experiment.

References:
- Dataset: https://doi.org/10.5281/zenodo.18437501
- Liu et al. (2026): https://doi.org/10.1016/j.jag.2026.105260

## 7. Probabilistic calibration should be central, but calibration alone is not novel

Earthquake fragility is inherently probabilistic: the object of interest is a
conditional damage probability, not just a hard class.

Saleh (2024) explicitly derives fragility curves using calibrated probabilistic
classifiers and compares Platt scaling, isotonic regression, beta calibration
and spline calibration across several classifiers. This means “calibrate the
classifier” is not itself novel.

Kourehpaz et al. (2023) show that multivariate fragility functions can improve
Brier-score performance and loss prediction relative to conventional univariate
fragility in a simulation setting.

The project should nevertheless retain probabilistic calibration as a major
quality criterion because much applied damage-ML literature still emphasizes
accuracy/F1. Ordinal probability metrics are especially appropriate because
misclassifying grade 4 as grade 3 is not equivalent to misclassifying grade 4
as grade 0.

### Recommended evaluation hierarchy

For ordinal targets:

1. ranked probability score (primary);
2. multiclass Brier score;
3. log loss;
4. ordinal mean absolute error;
5. calibration/reliability by damage-state exceedance;
6. macro F1 and class recall/support as secondary diagnostics.

For binary exceedance endpoints:

1. Brier score and reliability;
2. log loss;
3. PR-AUC with prevalence reported;
4. ROC-AUC only as a complementary discrimination metric.

Metrics should be computed per held-out domain and then macro-aggregated across
domains rather than letting Nepal-scale samples dominate a pooled score.

## 8. The loss layer is established methodology; our value would be uncertainty-preserving linkage

The later path

[
p(D) \rightarrow p(MDR) \rightarrow p(L)
]

is standard catastrophe-risk logic rather than a novel concept. GEM/OpenQuake
already provides fragility/vulnerability, consequence and loss-exceedance
machinery.

The scientifically useful question for this project is whether improvements in
building-level probability quality and calibration survive translation into
loss metrics. A model that improves classification accuracy but is poorly
calibrated may yield worse portfolio loss estimates.

This argues for keeping loss modelling last, after the damage-probability
experiment is stable.

## 9. Research gap after this review

### Claims that are too weak or already occupied

Do **not** frame the project as:

- “using machine learning to predict earthquake building damage”;
- “using XGBoost on Nepal damage”;
- “using AutoML/SHAP on ACI133”;
- “deriving fragility curves for the Jaiswal Türkiye survey”;
- “using SA(0.3) as an important predictor in Türkiye”;
- “adding geological/site variables to improve Türkiye prediction”;
- “training in one region and testing another”;
- “using a GNN for regional seismic damage”;
- “using 30k Türkiye labels for GeoAI” without disclosing their pseudo-label
  origin.

### Strongest candidate contribution

Subject to recovering independent spatial labels:

> **A leakage-safe, probabilistically evaluated test of the incremental value of
> pre-event neighbourhood and spatial context beyond physical shaking and
> conventional building attributes under geographic distribution shift.**

The key word is **incremental**.

The central comparison should remain:

[
H
\rightarrow
H+X
\rightarrow
H+X+Z_{spatial}
]

on identical eligible records and identical domain folds.

Where:

- **H** = independently sourced, physically calibrated and event-attributed
  ground-motion intensity;
- **X** = verified pre-event building characteristics;
- **Z** = verified pre-event site and neighbourhood context;
- **D** = independently defined observed/manual damage target.

The test is not whether a complex model beats a simple model somewhere. It is
whether Z supplies reproducible information *conditional on H and X*, including
on a held-out geographic domain.

## 10. Revised research questions

### RQ1 — Conventional benchmark

How well do physical hazard intensity and conventional pre-event building
attributes predict dataset-native damage under domain holdout?

[
D \sim H
quad\text{vs}\quad
D \sim H+X
]

This is a benchmark question, not the headline novelty.

### RQ2 — Spatial increment

Conditional on an independently verified target, does pre-event local spatial
context improve probabilistic damage prediction beyond H+X?

[
D \sim H+X
quad\text{vs}\quad
D \sim H+X+Z
]

### RQ3 — Distribution shift

Does any gain from Z persist when the evaluation domain is geographically or
event-wise unseen?

The primary result should be the *held-out-domain delta* in probabilistic skill,
not in-sample feature importance.

### RQ4 — Calibration and risk relevance

Are improvements calibrated, and do they improve downstream damage-exceedance
and loss estimates rather than only discrimination metrics?

## 11. Working hypotheses

These are hypotheses, not assumed truths.

**H1.** H+X will outperform H alone for observed engineering damage because
structural vulnerability varies materially among buildings exposed to similar
shaking.

**H2.** Simple fixed spatial/site descriptors may add some information, but
their incremental value will be smaller than naïve feature-importance plots
suggest once geography is held out.

**H3.** Learned neighbourhood representations will only be credible if they
improve H+X on held-out domains under an inductive protocol; random spatial
splits will overstate their value.

**H4.** Some apparent gains from spatial features will disappear when
post-event/teacher-derived variables and target-proxy leakage are excluded.

**H5.** Improvements in discrimination will not necessarily translate to better
calibration; calibration should be evaluated separately.

## 12. Dataset roles after the literature review

| Dataset | Role after review | Headline target? |
|---|---|---|
| Türkiye survey (559) | Bias-aware baseline/replication, H and engineering X benchmarking | No |
| Nepal GEID (762,106) | Large-scale native X-only geographic generalization benchmark; prior literature comparator | No, but important benchmark |
| RC619 | Native event-transfer X-only benchmark; later paired H+X if hazard data become defensible | No |
| ACI133 (242) | Reserved external reproduction/validation dataset; AutoML prior art exists | No |
| `This_study` (30,122) | Method output/pseudo-label product; auxiliary analysis only unless question explicitly changes | **No** |
| `Visual_interpretation` (~20,690 features) | Candidate independent spatial validation target pending label/codebook recovery | Potentially |
| 4.41M footprints | Pre-event neighbourhood/context source if temporal provenance supports it | Predictor/context only |

This role table supersedes any informal statement that the project has “30k
ground-truth spatial labels.”

## 13. Modelling gates created by the review

Modelling remains frozen until the following are resolved or explicitly scoped
out.

### Gate A — independent spatial target

For `Visual_interpretation`:

- recover the original annotation codebook and class meanings;
- establish which attributes encode actual damage severity;
- verify whether polygons/labels are independent of `This_study`;
- document image dates and manual annotation process;
- determine whether “undamaged” buildings were actually assessed or merely
  absent from a damaged-building selection.

If this fails, do not force a GeoAI supervised experiment from the 30,122
pseudo labels.

### Gate B — feature chronology

For every proposed X/Z field, classify it as:

- verified pre-event;
- event/hazard;
- post-event;
- target-derived;
- unknown chronology.

Primary vulnerability models may only use verified pre-event X/Z plus explicit H.

### Gate C — physical hazard definition

For each modelling arm, freeze:

- earthquake/shock/product version;
- intensity variable and units;
- interpolation/sampling method;
- nodata and coverage treatment;
- sequence handling.

Do not select a shock or maximum IM because it gives the best score.

### Gate D — final estimand

Decide before fitting whether the spatial headline estimates:

1. city-held-out prediction of manually interpreted damage;
2. event-held-out prediction of engineering damage;
3. another explicitly defined target.

One Türkiye/Syria sequence cannot support a claim of cross-earthquake transfer
for a learned spatial representation.

### Gate E — benchmark feature allowlists

Freeze allowed and prohibited predictors per source before opening model results.
Post-event damage descriptors, repair decisions, casualties, placards, alternate
damage encodings and teacher-damage products remain prohibited.

## 14. Recommended modelling plan once the gates clear

The literature review does **not** recommend jumping to a GNN.

### Stage 1 — benchmark

- empirical/lognormal/probit fragility where appropriate;
- proportional-odds/cumulative-link model;
- GAM;
- restrained gradient-boosted tree baseline;
- probability calibration fitted inside training/validation only.

### Stage 2 — ablation

On identical rows/folds:

1. H;
2. H+X;
3. H+X+fixed Z;
4. H+X+learned Z, only if justified.

Report `ΔRPS`, `ΔBrier`, `Δlog-loss` and calibration changes for every held-out
domain.

### Stage 3 — stress tests

- raw-record and site-weighted metrics;
- spatial-buffer sensitivity;
- alternative neighbourhood radii;
- feature chronology sensitivity;
- class-support/rare-collapse sensitivity;
- explicit comparison of random-split versus domain-holdout performance as a
  leakage demonstration, **only as an audit**, not the headline score.

### Stage 4 — risk

Only after probability quality is credible:

[
p(D) \rightarrow p(MDR) \rightarrow p(L)
]

Propagate predictive and consequence uncertainty to event/portfolio loss.

## 15. Candidate paper/project positioning

A defensible working title is:

**Does Spatial Context Improve Earthquake Building Vulnerability Models Under
Geographic Distribution Shift?**

Alternative:

**Beyond Shaking and Taxonomy: Leakage-Safe Evaluation of Spatial Context for
Probabilistic Earthquake Building Damage**

The intended contribution would be methodological/empirical rather than a new
neural architecture:

1. provenance-preserving multi-source earthquake-damage benchmark design;
2. strict separation of native damage scales and observational products;
3. leakage-safe geographic/event evaluation;
4. controlled H → H+X → H+X+Z ablation;
5. probability calibration/ordinal scoring;
6. honest null result if spatial context does not transfer.

A null result would still be useful. If Z performs well under random splits but
adds little on held-out domains, that directly demonstrates why spatial leakage
matters.

## 16. Core references

- Anderson Loake, M. & Jaiswal, K. S. (2026). *Accounting for Biases in the
  Analysis of Building Damage Data for the 2023 M7.8 Türkiye/Syria Earthquake
  Sequence*. Earthquake Spectra. https://doi.org/10.1002/esp4.70117
- Bıçakcı, C. et al. (2026). *Explainable Ensemble Learning for Rapid Seismic
  Damage Assessment: A Comprehensive Benchmark Using Real Data from the 2023
  Kahramanmaraş Earthquakes*. Buildings.
  https://doi.org/10.3390/buildings16132660
- Chen, W. & Zhang, L. (2022). *Building vulnerability assessment in seismic
  areas using ensemble learning: A Nepal case study*. Journal of Cleaner
  Production. https://doi.org/10.1016/j.jclepro.2022.131418
- Ghimire, S. et al. (2022). *Testing machine learning models for seismic damage
  prediction at a regional scale using building-damage dataset compiled after
  the 2015 Gorkha Nepal earthquake*. Earthquake Spectra.
  https://doi.org/10.1177/87552930221106495
- Ghimire, S. & Guéguen, P. (2024). *Host-to-target region testing of machine
  learning models for seismic damage prediction in buildings*. Natural Hazards.
  https://doi.org/10.1007/s11069-023-06394-z
- Hariri-Ardebili, M. A. & Sattar, S. (2026). *Interpretable AutoML for
  Post-Earthquake RC Building Damage: Insights from the 2023 Türkiye Sequence*.
  NIST publication record.
- Hu, S. et al. (2025). *Machine learning in earthquake engineering: A review on
  recent progress and future trends in seismic performance evaluation and
  design*. Engineering Structures.
  https://doi.org/10.1016/j.engstruct.2025.120721
- Ioannou, I., Douglas, J. & Rossetto, T. (2015). *Assessing the impact of
  ground-motion variability and uncertainty on empirical fragility curves*.
  Soil Dynamics and Earthquake Engineering.
  https://doi.org/10.1016/j.soildyn.2014.10.024
- K C, S., Bhusal, A., Gautam, D. & Rupakhety, R. (2023). *Earthquake damage
  and rehabilitation intervention prediction using machine learning*.
  Engineering Failure Analysis.
  https://doi.org/10.1016/j.engfailanal.2022.106949
- Kourehpaz, P. et al. (2023). *Toward multivariate fragility functions for
  seismic damage and loss estimation of high-rise buildings*. Earthquake
  Engineering & Structural Dynamics. https://doi.org/10.1002/eqe.3993
- Lallemant, D., Kiremidjian, A. & Burton, H. (2015). *Statistical procedures
  for developing earthquake damage fragility curves*. Earthquake Engineering &
  Structural Dynamics. https://doi.org/10.1002/eqe.2522
- Liu, H. et al. (2026). *SAR-based individual-building damage identification
  and large-scale earthquake damage prediction*. International Journal of
  Applied Earth Observation and Geoinformation.
  https://doi.org/10.1016/j.jag.2026.105260
- Patten, H., Anderson Loake, M. & Steinsaltz, D. (2024). *Data-Driven
  Earthquake Multi-impact Modeling: A Comparison of Models*. International
  Journal of Disaster Risk Science.
  https://doi.org/10.1007/s13753-024-00567-5
- Rossetto, T. & Elnashai, A. (2003). *Derivation of vulnerability functions for
  European-type RC structures based on observational data*. Engineering
  Structures. https://doi.org/10.1016/S0141-0296(03)00060-9
- Rossetto, T. et al. (2014). *Guidelines for the empirical vulnerability
  assessment*. GEM Foundation.
- Rossetto, T., Ioannou, I. & Grant, D. N. (2015). *Existing Empirical Fragility
  and Vulnerability Functions: Compendium and Guide for Selection*. GEM.
  https://doi.org/10.13117/GEM.VULNSMOD.TR2015.01
- Saleh, E. (2024). *The development of fragility curves using calibrated
  probabilistic classifiers*. Structures.
  https://doi.org/10.1016/j.istruc.2024.106618
- Senkaya, M. et al. (2024). *Prediction of local site influence on seismic
  vulnerability using machine learning: A study of the 6 February 2023 Türkiye
  earthquakes*. Engineering Geology.
  https://doi.org/10.1016/j.enggeo.2024.107605
- Abeysuriya, K. G. et al. (2026). *Deep learning for image-based structural
  element damage assessments in post-earthquake buildings: a systematic
  review*. AI in Civil Engineering. https://doi.org/10.1007/s43503-026-00099-5
- *Graph neural network-based region-building seismic damage prediction*
  (2026). Engineering Structures.
  https://doi.org/10.1016/j.engstruct.2025.121881

## Review limitations

This is a targeted scoping review intended to position the project before model
development. It is not a systematic review and does not claim exhaustive
coverage of every fragility, remote-sensing or structural-response paper.
Search emphasis was deliberately placed on empirical building damage,
regional-scale ML, domain shift, spatial context, probabilistic prediction and
papers that overlap our actual datasets.

Before a manuscript, perform a formal citation-forward/backward search around
the core papers, verify bibliographic metadata, and update this review with any
new publications appearing after 2026-10-05.
