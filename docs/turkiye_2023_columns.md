# Türkiye 2023 source-column dictionary

All 55 source columns are preserved. Executable definitions: `src/data/turkiye_schema.py`.
Each source column also has a `raw__<source>` string column; the blank BC header is named `Unnamed: 54`.
Canonical text is trimmed, blank/whitespace values become null, and raw text is retained unchanged.

| Source column | Canonical column | dtype | Canonical units | Transform / definition |
| --- | --- | --- | --- | --- |
| `assessor_name` | `assessor_name` | string | text | identity: Survey assessor; source contains encoding artifacts, preserved without correction. |
| `City/Town` | `city` | string | text | identity: Survey city/town spelling, not an administrative boundary assignment. |
| `latitude` | `latitude` | Float64 | degrees north | identity: Survey building latitude. |
| `longitude` | `longitude` | Float64 | degrees east | identity: Survey building longitude. |
| `sample_lat` | `sample_latitude` | Float64 | degrees north | identity: Sampled shaking grid latitude; distinct from building location. |
| `sample_lon` | `sample_longitude` | Float64 | degrees east | identity: Sampled shaking grid longitude. |
| `sample_distance_m` | `sample_distance_m` | Float64 | m | identity: Distance from building to sampled grid point. |
| `vs30` | `vs30` | Float64 | m/s | identity: Time-averaged shear-wave velocity over the upper 30 m. |
| `MMI_mean` | `MMI` | Float64 | intensity units | identity: Source mean MMI, linear scale. |
| `MMI_phi` | `MMI_phi` | Float64 | source uncertainty scale (unverified) | identity: MMI phi uncertainty field. Preserve as supplied; workbook does not define exact convention. Do not exponentiate. |
| `MMI_std` | `MMI_std` | Float64 | source uncertainty scale (unverified) | identity: MMI std uncertainty field. Preserve as supplied; workbook does not define exact convention. Do not exponentiate. |
| `MMI_tau` | `MMI_tau` | Float64 | source uncertainty scale (unverified) | identity: MMI tau uncertainty field. Preserve as supplied; workbook does not define exact convention. Do not exponentiate. |
| `PGA_mean` | `PGA` | Float64 | g | exp: Natural-log mean of PGA; exp(source) is a geometric mean/median intensity, not an arithmetic mean. |
| `PGA_phi` | `PGA_phi` | Float64 | source uncertainty scale (unverified) | identity: PGA phi uncertainty field. Preserve as supplied; workbook does not define exact convention. Do not exponentiate. |
| `PGA_std` | `PGA_std` | Float64 | source uncertainty scale (unverified) | identity: PGA std uncertainty field. Preserve as supplied; workbook does not define exact convention. Do not exponentiate. |
| `PGA_tau` | `PGA_tau` | Float64 | source uncertainty scale (unverified) | identity: PGA tau uncertainty field. Preserve as supplied; workbook does not define exact convention. Do not exponentiate. |
| `PGV_mean` | `PGV` | Float64 | cm/s | exp: Natural-log mean of PGV; exp(source) is a geometric mean/median intensity, not an arithmetic mean. |
| `PGV_phi` | `PGV_phi` | Float64 | source uncertainty scale (unverified) | identity: PGV phi uncertainty field. Preserve as supplied; workbook does not define exact convention. Do not exponentiate. |
| `PGV_std` | `PGV_std` | Float64 | source uncertainty scale (unverified) | identity: PGV std uncertainty field. Preserve as supplied; workbook does not define exact convention. Do not exponentiate. |
| `PGV_tau` | `PGV_tau` | Float64 | source uncertainty scale (unverified) | identity: PGV tau uncertainty field. Preserve as supplied; workbook does not define exact convention. Do not exponentiate. |
| `SA(0.3)_mean` | `SA_0p3` | Float64 | g | exp: Natural-log mean of SA(0.3); exp(source) is a geometric mean/median intensity, not an arithmetic mean. |
| `SA(0.3)_phi` | `SA_0p3_phi` | Float64 | source uncertainty scale (unverified) | identity: SA(0.3) phi uncertainty field. Preserve as supplied; workbook does not define exact convention. Do not exponentiate. |
| `SA(0.3)_std` | `SA_0p3_std` | Float64 | source uncertainty scale (unverified) | identity: SA(0.3) std uncertainty field. Preserve as supplied; workbook does not define exact convention. Do not exponentiate. |
| `SA(0.3)_tau` | `SA_0p3_tau` | Float64 | source uncertainty scale (unverified) | identity: SA(0.3) tau uncertainty field. Preserve as supplied; workbook does not define exact convention. Do not exponentiate. |
| `SA(1.0)_mean` | `SA_1p0` | Float64 | g | exp: Natural-log mean of SA(1.0); exp(source) is a geometric mean/median intensity, not an arithmetic mean. |
| `SA(1.0)_phi` | `SA_1p0_phi` | Float64 | source uncertainty scale (unverified) | identity: SA(1.0) phi uncertainty field. Preserve as supplied; workbook does not define exact convention. Do not exponentiate. |
| `SA(1.0)_std` | `SA_1p0_std` | Float64 | source uncertainty scale (unverified) | identity: SA(1.0) std uncertainty field. Preserve as supplied; workbook does not define exact convention. Do not exponentiate. |
| `SA(1.0)_tau` | `SA_1p0_tau` | Float64 | source uncertainty scale (unverified) | identity: SA(1.0) tau uncertainty field. Preserve as supplied; workbook does not define exact convention. Do not exponentiate. |
| `SA(3.0)_mean` | `SA_3p0` | Float64 | g | exp: Natural-log mean of SA(3.0); exp(source) is a geometric mean/median intensity, not an arithmetic mean. |
| `SA(3.0)_phi` | `SA_3p0_phi` | Float64 | source uncertainty scale (unverified) | identity: SA(3.0) phi uncertainty field. Preserve as supplied; workbook does not define exact convention. Do not exponentiate. |
| `SA(3.0)_std` | `SA_3p0_std` | Float64 | source uncertainty scale (unverified) | identity: SA(3.0) std uncertainty field. Preserve as supplied; workbook does not define exact convention. Do not exponentiate. |
| `SA(3.0)_tau` | `SA_3p0_tau` | Float64 | source uncertainty scale (unverified) | identity: SA(3.0) tau uncertainty field. Preserve as supplied; workbook does not define exact convention. Do not exponentiate. |
| `photos_building_id` | `photo_ids` | string | text | identity: Comma-separated photo identifiers; neither unique nor a reliable building key. |
| `existing_placard` | `existing_placard` | string | source code | identity: Existing placard field; entirely blank in registered workbook, coding unspecified. |
| `date` | `survey_date` | datetime64[ns] | date | identity: Survey visit date, not earthquake date. |
| `storeys_above_ground_incl_ground_floor` | `floors` | Float64 | storeys | identity: Above-ground storeys including ground floor. Nullable float permits retaining and flagging fractional invalid input. |
| `storeys_below_ground` | `basement_floors` | Float64 | storeys | identity: Below-ground storeys; zero is valid. |
| `area` | `area` | Float64 | unspecified | identity: Reported area; workbook supplies no unit or footprint/floor-area definition. |
| `construction_age` | `construction_age` | string | source category | identity: Construction vintage band; do not replace with a midpoint/year. |
| `structure_type` | `structure_type` | string | source category | identity: Structural system/height class. Preserve unusual free text, no recoding into Other. |
| `occupancy` | `occupancy` | string | source category | identity: Building use. |
| `is_it_occupied` | `is_occupied` | string | source category | identity: Reported occupied status at survey. |
| `vertical_irregularity` | `vertical_irregularity` | string | source category | identity: Reported vertical irregularity. |
| `horizontal_irregularity` | `horizontal_irregularity` | string | source category | identity: Reported horizontal irregularity. |
| `pounding` | `pounding` | string | source category | identity: Reported pounding. |
| `cladding_type` | `cladding_type` | string | source category | identity: Cladding description. |
| `roof_type` | `roof_type` | string | source category | identity: Roof system. |
| `casualties_reported` | `casualties_reported` | string | source category | identity: Reported casualties flag, not a casualty count. |
| `damage_condition` | `damage_label` | string | source category | identity: Observed damage label. Literal None means undamaged; only empty/whitespace cells are missing. |
| `building_or_storey_leaning` | `building_or_storey_leaning` | string | source text | identity: Leaning/other observations, including free-text foundation cracks. |
| `falling_hazard_unbraced_parapet_or_unsecure_cladding` | `falling_hazard` | string | source category | identity: Reported parapet/cladding falling hazard. |
| `infill_wall_damage` | `infill_wall_damage` | string | source category | identity: Infill wall damage observation. |
| `structural_members_beams_columns` | `member_damage` | string | source category | identity: Beam/column damage observation. |
| `estimated_building_damage` | `estimated_building_damage` | string | percent band | identity: Reported damage percentage band; retained separately from ordinal damage. |
| `Unnamed: 54` | `unlabelled_damage_band` | string | unspecified percent band | identity: Unlabelled Excel column BC, populated in six records. Meaning unverified; never use to fill or override damage. |
