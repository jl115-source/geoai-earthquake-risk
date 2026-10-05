# Milestone 1F execution results

Executed 2026-10-05 from consolidated main after PR #4 and retargeted PR #5 were merged. No model fitting or encoder inference. See [frozen protocol](geoai_experiment_1f.md) and [exact commands](../README.md).

## Input feasibility

- All **559 source records / 499 exact source coordinates** were audited; 474 distinct centres after snapping to the 10 m grid. Display rounding is never used as source-coordinate identity.
- **559/559** have complete ten-band, clear-support pre-event EO chips and complete 2021 WorldCover coverage. **558/559** have complete selected DSM-tile support. The remaining record is already quarantined as a city-coordinate outlier; its DSM support is 91.1784%. This means incomplete extraction support, not proof that no adjacent tile exists.
- The frozen STAC catalog contains 170 items. Eight selected scenes span **2022-07-29 to 2022-09-17**. 519 records use one scene, 36 use two, and four use three; this is a ranked-prefix clear composite, not an all-summer median.
- Actual pixel and mask windows were read. Ten deterministic city RGB examples and the geographic exclusion plot were rendered and visually inspected. This confirms plausible neighbourhood imagery, not cadastral building identity or perfect cloud classification.
- All 559 records fall inside the pinned mainshock hazard grid. Maximum nearest-node separation: **287.57 m**. Newly sampled PGA spans **0.110–1.207 g**. XML creation is 2025-03-20, explicitly retrospective.

## Frozen primary cohort

**498 records / 445 exact-coordinate sites**, with inverse site-multiplicity weights, enter every arm. All 559 rows remain in the eligibility file. No cross-city pair among eligible rows triggers the 2 km buffer. The 61 excluded rows have overlapping reasons: 33 city-coordinate outliers, 22 missing structural family, 18 missing native damage, one incomplete DSM chip. There are no conflicting known labels at exact coordinates in this source table.

The location screen flags 32 Islahiye rows about 32.4–32.7 km from the city median and one Antakya row about 77.3 km away. Coordinates are retained unchanged. This is a declared quarantine, not a verified correction. Some numerically distinct source coordinates agree when displayed to ten decimal places; cache identities preserve those distinctions.

Eligible native-grade counts: **0: 97; 1: 128; 2: 161; 3: 110; 4: 2**. With only two complete-collapse observations, class-specific inference is severely limited. Nurdagi has three rows but only one coordinate/site; its score must be shown with that support and must not be presented as robust city-level validation.

| Test city | Validation city | Train rows | Validation rows | Test rows | Test sites |
|---|---|---:|---:|---:|---:|
| Antakya | Hassa | 421 | 35 | 42 | 42 |
| Hassa | Iskendurun | 395 | 68 | 35 | 35 |
| Iskendurun | Islahiye | 374 | 56 | 68 | 68 |
| Islahiye | Kahramanmaras | 334 | 108 | 56 | 56 |
| Kahramanmaras | Kirikhan | 345 | 45 | 108 | 98 |
| Kirikhan | Narli | 416 | 37 | 45 | 45 |
| Narli | Pazarcik | 400 | 61 | 37 | 24 |
| Nurdagi | Pazarcik | 434 | 61 | 3 | 1 |
| Pazarcik | Turkoglu | 394 | 43 | 61 | 35 |
| Turkoglu | Antakya | 413 | 42 | 43 | 41 |

## Representation and gate

The design locks 16 engineered features and one frozen **SatMAE multispectral ViT-Large, 1024-D** representation. Structural family is a post-event-ascertained design proxy; floors, vintage, occupancy, damage products, undated footprints and other unlisted fields are prohibited. A no-survey-X sensitivity is prespecified. ACI133 stays external and unused.

The fallback is workable as a **small retrospective, held-out-city pilot**. It does not supply a verified pre-event engineering inventory, population-representative vulnerability or independent-event evidence. The encoder is selected and precisely specified but has not been executed. Checkpoint verification, deterministic extraction smoke tests and reviewed 2A initiation remain prerequisites to fitting. CSB permission is unconfirmed and not a blocking dependency.

## Validation and B0

- An offline replay reproduced **all ten processed artifacts byte-for-byte**. Cache specification and chip checksums are validated; no external reads are needed for the replay.
- **76 tests pass**. Unit/data tests cover cloud/shadow exclusion, source scaling and physical units, exact coordinate identity, stale/tampered caches, raster-edge nodata, spectral moments, explicit exclusions, site weights, buffer purging, allowlists and synthetic catastrophe mechanics.
- B0 uses 100,000 synthetic years and 25,962 occurrences. Analytic AAL **8,283.57**, simulated AAL **8,380.73**, Monte Carlo standard error **110.33**, in synthetic replacement-value units. The difference is within one standard error. OEP/AEP tables, event/annual losses and grouping summaries were inspected. No real Türkiye financial-loss claim or learned vulnerability calibration is made.

## Provenance fingerprints

```json
{
  "config_sha256": "7d45cf638e188c16ccfbb065e21bd61787c24c3a3e7c14ea4220999eb5b5359f",
  "survey_sha256": "1f937341caad8a4560fb875244987405425d708079e8b4057959ea2032252142",
  "observations": 559,
  "eligible_records": 498,
  "eligible_sites": 445,
  "overlapping_exclusion_counts": {
    "coordinate_city_outlier_pending_adjudication": 33,
    "missing_or_unmapped_structure_family": 22,
    "missing_native_damage": 18,
    "incomplete_DSM": 1
  },
  "all_arms_same_manifest": true,
  "model_fitting": false,
  "test_city_counts": {
    "Antakya": 42,
    "Hassa": 35,
    "Iskendurun": 68,
    "Islahiye": 56,
    "Kahramanmaras": 108,
    "Kirikhan": 45,
    "Narli": 37,
    "Nurdagi": 3,
    "Pazarcik": 61,
    "Turkoglu": 43
  },
  "pixel_audit_sha256": "91d19f47e8de852a5f7fed17110598b501cc9ed4d0357ba8f45763ebc1c5eff0",
  "hazard_provenance_sha256": "067ae81d27df240b66358cb7276ff497fe676d2d1ffac449c1cba4297fcde651"
}
```
