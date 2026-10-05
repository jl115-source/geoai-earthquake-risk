# Project Charter — GeoAI × Catastrophe Risk

## Purpose

This project is intentionally a **GeoAI × Catastrophe Risk** project.

It must satisfy two portfolio goals simultaneously:

1. demonstrate genuine modern geospatial/GeoAI capability; and
2. develop end-to-end earthquake catastrophe-loss modelling skill.

It must not drift into either a narrow earthquake-engineering fragility paper or
a generic OpenQuake tutorial.

## Core modelling concept

Conventional vulnerability is the baseline:

[
H + X ightarrow p(D)
]

where:

- (H): physically defensible earthquake shaking/hazard;
- (X): conventional pre-event building/exposure attributes;
- (D): observed building damage.

The GeoAI track then tests:

[
H
ightarrow
H+X
ightarrow
H+X+Z_{engineered}
ightarrow
H+X+Z_{GeoAI}
]

using identical eligible observations and held-out domains.

(Z_{GeoAI}) must be learned from **pre-event geospatial context** and may use,
subject to data/provenance review:

- Earth-observation foundation-model embeddings;
- frozen or lightly adapted satellite-image encoders;
- building/neighbourhood graphs;
- GNN representations;
- multimodal spatial encoders;
- other modern geospatial representations.

No architecture is mandatory. The simplest method that is scientifically
defensible and demonstrates modern GeoAI should be preferred.

## GeoAI research question

> **Can learned pre-event geospatial representations capture transferable
> vulnerability information beyond earthquake shaking and conventional building
> attributes?**

The primary evaluation setting is geographic/event distribution shift, not a
random row split.

The project must control:

- spatial leakage;
- temporal leakage;
- post-event information leakage;
- target-derived features;
- preprocessing leakage;
- duplicated/overlapping geography.

Post-event imagery may inform ground-truth labels but is prohibited as a primary
vulnerability-model predictor.

## Catastrophe-risk track

Damage prediction is not the project endpoint.

The second track must implement and understand:

[
	ext{Hazard}
ightarrow
	ext{Exposure}
ightarrow
	ext{Vulnerability}
ightarrow
	ext{Damage}
ightarrow
	ext{Financial Loss}
ightarrow
	ext{Portfolio Risk}
]

with:

[
p(D_i)
ightarrow
p(MDR_i mid D_i,mathrm{taxonomy})
ightarrow
L_i = V_i MDR_i
]

followed by event/portfolio aggregation.

Required concepts/outputs include:

- scenario/event loss;
- stochastic event sets;
- average annual loss (AAL);
- event/aggregate exceedance-probability curves;
- OEP and AEP;
- return-period loss / PML;
- appropriate tail metrics such as VaR where useful;
- geographic/taxonomy contributions to risk;
- aleatory/epistemic/predictive uncertainty.

GEM/OpenQuake should be used where appropriate, but the project must implement
enough of the machinery independently to understand and validate those outputs.

## Final integration question

> **Does learned geospatial vulnerability information improve geographic
> transfer, and do those improvements materially affect estimated financial
> loss and portfolio tail risk?**

The integration must hold hazard and exposure fixed and compare conventional
versus GeoAI-enhanced vulnerability under the same stochastic event set.

A preferred architecture for that comparison is:

1. use OpenQuake/GEM to define or generate stochastic ruptures and ground-motion
   fields;
2. reproduce conventional event-based risk with standard vulnerability;
3. consume the *same* ground-motion fields in a transparent custom loss engine;
4. replace only the vulnerability component with
   (p(Dmid H,X,Z_{GeoAI}));
5. map damage probabilities to MDR/loss distributions;
6. compare event losses, AAL, OEP/AEP and return-period losses.

This isolates the value of the GeoAI vulnerability component rather than
confounding it with a different hazard model.

## Success criteria

Publication is optional.

The project is successful if it credibly demonstrates:

### GeoAI

- spatial data engineering;
- remote-sensing/EO representations;
- engineered neighbourhood/context features;
- learned geospatial representations;
- spatial leakage control;
- geographic distribution shift;
- rigorous held-out-domain evaluation.

### Catastrophe modelling

- hazard and event sets;
- exposure/taxonomy/value;
- fragility/vulnerability;
- damage states;
- MDR/consequence modelling;
- stochastic asset/event loss;
- portfolio aggregation;
- AAL/OEP/AEP/EP curves;
- return-period loss;
- uncertainty decomposition;
- practical GEM/OpenQuake usage and independent validation.

## Scope exclusions

Do not turn this project into:

- earthquake occurrence prediction;
- a post-event satellite damage-classification project;
- months of fragility-curve novelty hunting;
- tabular-classifier hyperparameter optimization;
- a GNN-for-the-sake-of-a-GNN project;
- a generic OpenQuake tutorial.

The intersection between **spatial representation, vulnerability transfer and
financial risk** is the defining feature.

## Desired final description

> **GeoAI × Catastrophe Risk — Developed an end-to-end probabilistic earthquake
> catastrophe-risk framework integrating seismic hazard, exposure, conventional
> and learned geospatial vulnerability representations, leakage-safe geographic
> transfer, stochastic financial loss and portfolio AAL/OEP/AEP analysis using
> GEM/OpenQuake.**
