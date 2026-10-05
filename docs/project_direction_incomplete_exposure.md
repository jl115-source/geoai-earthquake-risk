# Project Direction — GeoAI for Catastrophe Risk with Incomplete Exposure Information

**Locked:** 2026-10-05

## Central problem

The project is no longer primarily asking whether GeoAI improves earthquake
damage prediction when a complete engineering inventory is already available.

The central question is:

> **Can transferable pre-event geospatial representations support earthquake
> vulnerability and catastrophe-risk modelling when detailed exposure
> information is missing, heterogeneous or unavailable in a new geography?**

This is the defining research and portfolio direction.

The practical motivation is catastrophe modelling outside data-rich markets:
hazard information and remotely sensed spatial context may be widely available,
while detailed building attributes such as structural system, age, occupancy,
height, construction quality or foundation type are often incomplete.

## Common backbone and variable exposure information

The project should distinguish three information blocks.

### H — common hazard backbone

Use a physically defensible, harmonized shaking representation available across
study regions whenever possible, for example a common subset of USGS ShakeMap
intensity measures. Candidate variables include log PGA, log PGV, log SA(0.3)
and log SA(1.0), but the final common hazard block must be frozen based on actual
cross-region availability rather than outcome performance.

Avoid inventing a single opaque shaking score solely to make datasets look
homogeneous.

### Z — common pre-event GeoAI backbone

Use the same frozen or otherwise transfer-safe spatial encoder across regions:

[
Z_{geo}=f_{geo}(	ext{pre-event spatial context})
]

Potential inputs include consistently available EO imagery and defensible
pre-event contextual rasters. The representation pipeline must use the same
sensor/bands, preprocessing, chip geometry and checkpoint wherever the
comparison claims a common latent space.

### X — heterogeneous exposure information

Building/exposure attributes may vary by region and observation:

[
X_{available}subseteq X_{rich}
]

Examples include structural family, floors, age, occupancy, footprint,
construction material or other engineering descriptors.

Missing attributes are part of the research problem, not automatically a reason
to discard the observation or fabricate an imputed engineering inventory.

## Core experimental ladder

Within data-rich regions, establish an information upper bound and controlled
degradation:

[
H
]

[
H+X_{coarse}
]

[
H+Z_{geo}
]

[
H+X_{coarse}+Z_{geo}
]

[
H+X_{rich}+Z_{geo}
]

The critical comparison is not merely whether GeoAI adds skill when all
engineering data already exist. It is whether GeoAI recovers useful
vulnerability information after rich exposure variables are removed or are
naturally unavailable.

## Missing-modality training

The preferred modelling philosophy is analogous to context-aware foundation
models such as T0, without claiming methodological equivalence.

A vulnerability model should be capable of conditioning on the subset of
exposure context that is actually available:

[
p(Dmid H,Z_{geo},{X_j:m_j=1})
]

where (m_j) identifies whether exposure variable (X_j) is observed.

Potential mechanisms include:

- explicit missingness/mask tokens;
- modality dropout during training;
- separate exposure tokens/encoders with absent-modality masks;
- simple masked linear/tree baselines before more complex architectures.

During training on rich observations, deliberately withholding exposure
variables is a useful controlled experiment. The model should learn to use rich
engineering information when present and fall back toward (H+Z_{geo}) when it
is absent.

Do not treat generic statistical imputation as the central contribution.

## Geographic generalization

The main evaluation setting is deployment into unseen geography with degraded or
different exposure information.

Example:

- source region: (H+X_{rich}+Z);
- target region: (H+X_{coarse}+Z) or (H+Z).

The test asks whether the common hazard + spatial backbone transfers when the
engineering inventory does not.

Random row splits are not the headline evaluation.

## Recovery metrics

Let (S) be a probabilistic predictive skill score with direction normalized so
higher is better.

Define the information lost by removing rich exposure:

[
G_X=S(H+X_{rich})-S(H)
]

and the information recovered through GeoAI:

[
G_Z=S(H+Z_{geo})-S(H).
]

A useful descriptive quantity is:

[
R_{geo}=rac{G_Z}{G_X}
]

when (G_X>0).

Interpret this as a **GeoAI exposure-information recovery fraction**, not as a
causal percentage of engineering information encoded in imagery. It should be
reported with uncertainty and alongside the raw scores.

Additional experiments should test:

- (H+X_{coarse}) versus (H+X_{coarse}+Z);
- performance as increasing fractions/types of (X) are masked;
- source-region versus unseen-region recovery;
- calibration degradation under geographic and missing-modality shift.

## Catastrophe-risk integration

The same incomplete-information experiment must propagate downstream.

Compare portfolio risk under:

### Rich inventory reference

[
H+X_{rich}+Z
ightarrow p(D)
ightarrow p(MDR)
ightarrow L
]

### Data-poor deployment

[
H+X_{coarse}
ightarrow p(D)
ightarrow p(MDR)
ightarrow L
]

or, at the extreme:

[
Hightarrow p(D)ightarrow p(MDR)ightarrow L
]

### Data-poor + GeoAI

[
H+X_{coarse}+Z
ightarrow p(D)
ightarrow p(MDR)
ightarrow L.
]

Hold hazard, exposure values, event set and consequence assumptions fixed when
comparing vulnerability formulations.

Evaluate whether GeoAI reduces error/distortion in:

- event loss;
- AAL;
- OEP/AEP curves;
- return-period losses;
- geographic/taxonomy risk concentration;
- tail-risk estimates.

This is the defining end-to-end question:

> **Can GeoAI recover enough vulnerability information under incomplete exposure
> data to materially improve catastrophe-risk estimates in unseen regions?**

## Dataset strategy

Do not create a giant pooled heterogeneous dataset simply because multiple
sources exist.

Datasets should be chosen according to whether they support the common H/Z
backbone and useful exposure-availability regimes.

The current Türkiye 1F cohort (498 eligible records / 445 sites) remains
valuable as:

- an engineering-rich pilot;
- a controlled masking/degradation test bed;
- an external or small-domain transfer check;
- a validation target for a representation developed at larger scale.

It is **not** sufficient as the sole training corpus for the headline GeoAI
claim.

The next data milestone must identify one or more sufficiently large,
geolocated earthquake-damage datasets that can support:

1. independent damage labels;
2. common or harmonizable hazard H;
3. common pre-event spatial input Z;
4. explicit exposure variables where available;
5. held-out geographic/event domains;
6. missing-exposure experiments.

Noto, xBD earthquake observations, CSB and other candidates should be audited
against this contract rather than adopted merely for headline sample size.

## Scope discipline

Do not let the project become:

- post-event image damage classification;
- a missing-value imputation benchmark;
- an earthquake-occurrence model;
- a generic domain-adaptation exercise detached from catastrophe risk;
- a multi-dataset pooling exercise;
- foundation-model architecture shopping.

The spatial representation must remain **pre-event** for the vulnerability
model. Post-event imagery may create independent labels only.

## Conceptual inspiration from T0

T0 forecasts with different amounts of temporal/covariate context and supports
missing observations. The useful analogy here is the **context philosophy**:

> exploit additional covariates when available, but remain functional when some
> context is absent.

Our earthquake problem is spatial/vulnerability rather than time-series
forecasting, so T0 is conceptual inspiration, not a directly transferred
architecture.

## Desired final project statement

> **GeoAI × Catastrophe Risk — Developed a transferable probabilistic earthquake
> risk framework that combines common seismic hazard and pre-event geospatial
> representations with heterogeneous exposure information, quantifies how much
> GeoAI recovers when detailed building attributes are missing in unseen
> geographies, and propagates the resulting vulnerability uncertainty into
> portfolio AAL/OEP/AEP and tail-risk estimates.**
