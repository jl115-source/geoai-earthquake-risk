# Roadmap — GeoAI × Catastrophe Risk

This roadmap supersedes the earlier essentially linear
"baseline → spatial augmentation → transfer → loss" plan.

The project now has **two parallel tracks** that reconnect in a controlled
portfolio-risk experiment.

## Completed foundation

- **1A** Türkiye survey ingestion + EDA.
- **1C** Nepal / RC619 / ACI133 / Türkiye spatial-data audit.
- **1D** provenance-preserving harmonization and deterministic held-out-domain
  experiment design.
- **1L** literature review and modelling freeze.
- **1T** spatial-target provenance gate: Liu `Visual_interpretation` rejected as
  the main vulnerability target; `This_study` retained as pseudo/method output.

No predictive model has been fitted.

# Track A — GeoAI vulnerability

## A0 — Freeze the independent target

**Current gate.**

Choose one:

### A0-P preferred

Obtain authorized access to the Türkiye CSB ground survey used by Ainscoe et al.
(2025), then audit:

- damage-grade definitions;
- snapshot/completeness;
- coordinates and building-footprint matching;
- duplicated inspections/regrading;
- field chronology;
- licensing/privacy restrictions.

### A0-F guaranteed fallback

Use the existing independent Türkiye engineering observations and reserve ACI133
for external testing after overlap adjudication.

For the fallback path, freeze a small-N protocol that uses pretrained/frozen
spatial representations and prevents representation fitting on held-out cities.

**Exit criterion:** one independent target and its admissible held-out domains
are versioned in configuration.

## A1 — Conventional vulnerability benchmark

On the frozen target:

[
H ightarrow p(D)
]

then

[
H+X ightarrow p(D)
]

Use transparent benchmarks first:

- empirical/probit/lognormal fragility where defensible;
- cumulative-link/ordinal regression;
- GAM;
- restrained tree/boosting baseline.

Primary evaluation remains probabilistic and domain-held-out.

## A2 — Engineered spatial context

Construct only verified pre-event (Z_{engineered}):

- footprint area/shape/orientation;
- local building density;
- nearest-neighbour distances;
- local height/size distributions;
- block/street morphology where defensible;
- DEM/slope;
- lithology/site class;
- fault/seismic-source distances where they are truly vulnerability/context
  variables rather than chosen hazard proxies;
- land cover / urban form.

Compare on identical rows/folds:

[
H+X
quad	ext{vs}quad
H+X+Z_{engineered}
]

This stage establishes how much value comes from understandable spatial
features before learned representations are introduced.

## A3 — Modern GeoAI representation

Define:

[
Z_{GeoAI}=f_{GeoAI}(	ext{pre-event context})
]

Candidate families, to be selected after target/imagery audit:

1. **EO foundation-model embeddings** from pre-event imagery — preferred first
   learned-representation path because it can be frozen and is appropriate for
   small/medium labelled samples;
2. learned satellite/ViT embeddings if sufficient target data support adaptation;
3. building/neighbourhood graph encoders or GNNs when graph construction adds a
   clear physical/spatial hypothesis;
4. multimodal fusion of EO and building-graph representations.

Do not use post-event imagery in the primary vulnerability predictors.

Primary comparison:

[
H
ightarrow
H+X
ightarrow
H+X+Z_{engineered}
ightarrow
H+X+Z_{GeoAI}
]

using exactly the same eligible observations and held-out domains.

## A4 — Geographic/event transfer

Evaluate:

- held-out city/region;
- held-out earthquake where the data actually support it;
- spatial-buffer sensitivity;
- random-split result only as a leakage diagnostic.

Report both skill and calibration degradation under shift.

**Track A deliverable:** calibrated
(p(D_imid H_i,X_i,Z_i)) for each asset under a defined event intensity.

# Track B — Catastrophe risk

Track B should develop in parallel conceptually and in infrastructure, but no
predictive fitting resumes while the global modelling gate is active.

## B0 — Cat-model mechanics from first principles

Build a small transparent reference implementation before relying on OpenQuake.

For a known event/event set:

1. event/rupture and rate;
2. ground-motion intensity at each asset;
3. exposure/taxonomy/value;
4. vulnerability/fragility;
5. sample or integrate damage state;
6. sample (MDRmid D,	ext{taxonomy});
7. (L_i=V_i MDR_i);
8. aggregate asset losses to event loss.

Implement explicit stochastic sampling and expectation calculations.

## B1 — Scenario loss

For a historical event:

[
p(D)ightarrow p(MDR)ightarrow p(L)
]

Produce:

- expected asset loss;
- event loss distribution;
- geography/taxonomy loss contribution;
- uncertainty decomposition.

Validate the hand-built calculation against GEM/OpenQuake where possible.

## B2 — Stochastic event-based risk

Use GEM/OpenQuake hazard infrastructure for stochastic ruptures and
ground-motion fields.

Understand and reproduce:

- event loss tables;
- annualization;
- AAL;
- aggregate loss curves;
- return-period loss/PML;
- EP curves;
- **OEP**: maximum event loss in each year;
- **AEP**: sum of event losses in each year.

Current OpenQuake event-based risk calculations can export EP, OEP and AEP
aggregate loss curves. Use the engine as both infrastructure and a validation
reference, not a black box.

## B3 — Exposure and consequence realism

Develop:

- replacement values;
- occupancy/use;
- structural/nonstructural/contents loss where useful;
- damage-state-to-MDR consequence functions;
- MDR uncertainty/correlation;
- aggregation tags for geography and taxonomy.

Where empirical values are unavailable, keep synthetic/illustrative assumptions
explicitly separate from observed-data results.

## B4 — Portfolio risk diagnostics

Produce:

- AAL by geography/taxonomy;
- OEP and AEP curves;
- return-period losses;
- tail loss/VaR metrics where appropriate;
- source/event contribution;
- concentration/diversification diagnostics;
- sensitivity to vulnerability and consequence uncertainty.

**Track B deliverable:** a validated conventional portfolio-risk engine and
OpenQuake workflow.

# Track C — Reconnection: GeoAI → portfolio risk

This is the defining project milestone.

## C1 — Hold hazard and exposure fixed

Generate/freeze one stochastic event set and associated ground-motion fields.

Run two otherwise identical risk calculations:

### Conventional

[
H+X
ightarrow p(D)
ightarrow p(MDR)
ightarrow L
]

### GeoAI-enhanced

[
H+X+Z_{GeoAI}
ightarrow p(D)
ightarrow p(MDR)
ightarrow L
]

No change to hazard, exposure, event set, value assumptions or consequence
mapping unless explicitly part of a sensitivity experiment.

## C2 — Custom vulnerability on OpenQuake ground motions

Preferred implementation:

- OpenQuake supplies stochastic ruptures/GMFs;
- our code reads those same GMFs;
- conventional vulnerability is first reproduced outside the engine as a unit
  test of the loss machinery;
- the vulnerability component is then replaced by the calibrated
  GeoAI-conditioned (p(Dmid H,X,Z));
- the same MDR/value/aggregation code produces event losses.

This is cleaner than trying to force a high-dimensional asset-conditioned GeoAI
model into a standard taxonomy-level OpenQuake vulnerability XML.

## C3 — Risk impact analysis

Measure:

[
Delta AAL,quad
Delta OEP(T),quad
Delta AEP(T),quad
Delta PML_T
]

and attribute differences to:

- geography;
- building class;
- hazard intensity;
- spatial representation;
- calibration;
- tail events.

Ask:

> Does the incremental GeoAI information matter only for damage-class metrics,
> or does it materially alter financial and tail-risk estimates?

## C4 — Uncertainty

Separate where possible:

- hazard aleatory variability;
- ground-motion model uncertainty;
- exposure/value uncertainty;
- vulnerability/model uncertainty;
- damage-state/consequence/MDR uncertainty;
- representation/model shift uncertainty.

The final portfolio conclusion should show whether GeoAI-induced changes are
large relative to these other uncertainty sources.

# Final deliverables

1. reproducible data/provenance layer;
2. literature/research gate;
3. GeoAI vulnerability benchmark and learned representation;
4. leakage-safe transfer evaluation;
5. transparent catastrophe-loss engine;
6. GEM/OpenQuake validation;
7. stochastic portfolio AAL/OEP/AEP analysis;
8. integrated conventional-vs-GeoAI risk comparison;
9. concise technical report/notebook/dashboard explaining the full chain.

# Final portfolio narrative

**GeoAI × Catastrophe Risk — Developed an end-to-end probabilistic earthquake
catastrophe-risk framework integrating seismic hazard, exposure, conventional
and learned geospatial vulnerability representations, leakage-safe geographic
transfer, stochastic financial loss and portfolio AAL/OEP/AEP analysis using
GEM/OpenQuake.**
