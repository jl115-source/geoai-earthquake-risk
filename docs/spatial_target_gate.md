# Spatial Target Gate — Visual_interpretation

**Decision date:** 2026-10-05  
**Status:** resolved for this source: **not approved as the primary vulnerability target**

## Question

Can the Liu (2026) `Visual_interpretation` product provide an independent,
building-level damage target for the project's main GeoAI vulnerability
experiment?

## Evidence from the acquired files

The Milestone 1C full scan found:

| City | Features | Attributes relevant to damage |
|---|---:|---|
| Antakya | 17,148 | only `Join_Count` (0–7) |
| Jindires | 2,764 | footprint source/id/height/var/region only |
| Nurdagi | 778 | footprint source/id/height/var/region only |

Antakya's `Join_Count` is a generic spatial-join count, not a documented damage
severity scale. Jindires and Nurdagi contain no explicit damage class at all.

Therefore the files do not encode a clean common ordinal damage target.

## Evidence from the dataset and associated studies

The Zenodo deposit describes `Visual_interpretation` as manually annotated
damage labels used as a high-confidence validation dataset, and explicitly
describes `This_study` as results produced by the associated methodology.

The Liu et al. workflow is a **post-event damaged-building identification**
workflow based on Sentinel-1 coherence. Its validation logic is detection
oriented: correct identification, missed identification and false
identification relative to manually/visually interpreted damaged buildings.

Related work from the same research line states that UNITAR manually interpreted
damaged buildings from high-resolution optical imagery, and uses those points to
validate SAR building-damage detections. That supports independence from the SAR
method, but it does not establish a complete building-by-building ordinal
vulnerability census.

## Why Antakya `Join_Count == 0` cannot automatically mean "undamaged"

A zero spatial-join count establishes only that no reference damage point was
joined to that footprint. It does **not** by itself prove:

- that the building was explicitly inspected;
- that an undamaged label was assigned;
- that the reference mapping had complete recall;
- that all footprints in the area belonged to the manual assessment universe.

The file can potentially support a **binary reference-detection experiment** if
the original assessment extent and annotation semantics are reconstructed, but
that is a different estimand from an engineering vulnerability model.

## Conclusion

`Visual_interpretation` is **not approved** for the main

[
p(Dmid H,X,Z)
]

vulnerability experiment.

`This_study` also remains prohibited as independent ground truth because it is
a method output/pseudo-label product.

The current large spatial package remains useful for:

- footprint/neighbourhood context;
- spatial-feature engineering;
- damage-product comparison;
- auxiliary/pseudo-label studies clearly labelled as such;
- later validation studies.

It does not currently supply the primary supervised target.

## Preferred target strategy

### Preferred scale-up target — Türkiye CSB ground survey

Ainscoe et al. (2025) report access to a Ministry of Environment, Urbanization
and Climate Change building-by-building ground survey:

- 911,181 geolocated inspection points in their February 17 snapshot;
- explicit grades: Undamaged, Slightly Damaged, Moderately Damaged, Heavily
  Damaged, To be Demolished Urgently, Collapsed, Unable to Assess;
- after geolocation/footprint quality control, 327k footprint-linked buildings
  in their published analysis;
- 228,859 undamaged and 50,395 damaged footprints, plus 48,044 unable to assess.

This is much closer to the ideal GeoAI vulnerability target because it is a
ground survey rather than a remote-sensing model output.

However it is **not publicly redistributable**. The authors state that access is
through the Turkish Ministry. It is therefore an access opportunity, not a
dataset currently owned by this project.

### Guaranteed fallback — existing engineering observations

If the CSB target cannot be obtained, the project should still complete the
GeoAI track using the independent engineering observations already held:

- primary Türkiye survey: 559 records / 541 known damage;
- ACI133: 242 reserved external observations after overlap/provenance
  adjudication.

For this small-N path, modern GeoAI should use **frozen/pretrained
representations** rather than training a large encoder from scratch. Examples
include pre-event EO foundation-model embeddings or a fixed building-graph
encoder followed by a strongly regularized probabilistic damage model.

This path is smaller, but it remains scientifically clean and still demonstrates
the desired GeoAI skills.

## Model freeze consequence

The project-wide modelling freeze remains in place until a primary target path
is explicitly frozen:

1. **preferred:** authorized CSB ground-survey access; or
2. **fallback:** engineering-observation GeoAI experiment with a predeclared
   small-N representation/evaluation protocol.

No pseudo-label substitution is permitted merely to increase sample size.

## Sources

- Liu (2026) dataset: https://doi.org/10.5281/zenodo.18437501
- Liu et al. (2026): https://doi.org/10.1016/j.jag.2026.105260
- Liu et al. (2024): https://doi.org/10.1109/JSTARS.2024.3377218
- Ainscoe et al. (2025):
  https://doi.org/10.1038/s43247-025-02623-4
