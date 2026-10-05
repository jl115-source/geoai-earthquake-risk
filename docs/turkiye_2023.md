# Türkiye 2023 ingestion contract

## Source and attribution

Engineering survey attributed to Kishor Jaiswal and the survey contributors,
distributed with Max Anderson Loake and Kishor Jaiswal's companion analysis,
[TUR2023_02_06](https://github.com/maxandersonloake/TUR2023_02_06).
Workbook license: CC BY 4.0, as recorded in
[third-party licenses](../data/reference/THIRD_PARTY_LICENSES.md).
This implementation adds mappings and physical-scale intensity fields; it does
not alter the original workbook.

The registered file is
`data/reference/turkiye_2023/Jaiswal_2023TurkiyeEQ_us6000jllz_field_str_damage_data.xlsx`,
sheet `all_field_data`, SHA-256
`3603907ec479d7fce0ffc581bf349936baa1c63fee796dc4c93f6ba7e1d9f7ff`.
Excel rows 2–560 contain 559 records and all 55 columns are documented in the
[source dictionary](turkiye_2023_columns.md). Rows 561–611 have formatting but
no cell values; ingestion explicitly lists them in the manifest as empty
worksheet rows. A partially populated record is always retained.

The companion [FullModel.R at be08867](https://github.com/maxandersonloake/TUR2023_02_06/blob/be088671596f04ad5a058f7819ec3bb762156f17/FullModel.R)
defines the five damage states, filters missing damage/type, and exponentiates
PGA/PGV/SA log means. Its SA plot labels use g. The physical-scale convention
used here is PGA/SA in g and PGV in cm/s (ShakeMap convention); no factor of 100
is applied to the workbook's exponentiated values. The workbook itself does
not carry a units row. This unit interpretation is documented explicitly rather
than treating the negative log accelerations as impossible physical values.
Uncertainty `phi`, `std`, and `tau` fields are preserved without assuming their
precise distribution/variance convention. The area unit is unverified.

## Record identity and count reconciliation

559 source rows → 559 canonical rows. 541 have damage, 537 have structure, and
527 have both. The other 32 records are not discarded. There are 499 distinct
coordinate pairs, 45 repeated-coordinate groups containing 105 rows, and 11
exact duplicate excess rows. One repeated-coordinate group has differing damage
labels. Coordinates and photo lists are not proven unique building identifiers.

`building_id = turkiye_2023_r{Excel row:04d}` is unique and stable for the same
workbook, independent of filesystem path. It represents a building survey record.
It is not stable under source row insertion/reordering and does not assert that
559 different physical buildings were visited. `source_row` and the workbook
hash provide provenance. No deduplication or conflict resolution occurs here.

## Canonical schema and preservation

`src/data/turkiye_schema.py` defines nullable pandas dtypes and the full mapping.
Coordinates, floors and shaking are `Float64`; damage is nullable `Int8`;
IDs/cities/types are strings. Floors remain float to retain and report fractional
invalid values instead of rounding them. Dates are `datetime64[ns]`.
`has_damage_and_structure` is a boolean flag, not a model eligibility decision.

All 55 columns are represented by a canonical variable and a `raw__<header>`
string field in the Parquet. Raw fields retain source text (including whitespace),
numeric scalar representations and ISO dates. The workbook remains authoritative
for cell types and formatting. Blank cell values remain null. Canonical text is
trimmed; blank/whitespace-only cells become null. Tokens such as `None`, `NA`
and `Unknown` are not automatic missing markers.

Additional fields include basement storeys, construction vintage, area, occupancy,
irregularities, pounding, cladding/roof, leaning, casualties flag, member/infill
damage, percentage damage estimates, assessor/date/photos, Vs30, sampled grid
locations/distance, MMI, SA(3.0), and all intensity uncertainty terms. The unlabelled
Excel BC column is `unlabelled_damage_band`; its six percentage bands have no
confirmed interpretation and are not used to repair other fields.

No category is merged into `Other`, no construction-age midpoint is invented,
and no damage field fills another. Original spelling/encoding artifacts remain
available. Finite negative source log intensities are valid. Canonical intensity
is `exp(log_mean)`, a geometric mean/median, not a lognormal arithmetic mean.

## Explicit damage mapping

| Original label after exterior whitespace trimming | Grade |
| --- | ---: |
| `None` | 0 |
| `Minor (few cracks)` | 1 |
| `Moderate (extensive cracks in walls)` | 2 |
| `moderate damage but repaired` | 2 |
| `Severe (structural damage to system)` | 3 |
| `Partial collapse (portion collapsed)` | 3 |
| `Complete collapse` | 4 |

Empty labels map to null. Every nonempty label outside this exact mapping maps
to null **with an unmapped-label error**, never by catch-all to collapse. This
is a project ordinal scale matching the companion analysis, not a claim of
equivalence to an independently harmonized EMS-98 or other damage standard.

## Validation and failure behavior

- Schema/sheet/header drift, formulas and Excel error cells fail before writing
  a new table. Extra columns cannot be silently dropped; update the dictionary.
- Numeric/date parse failures retain the raw cell, produce a null canonical
  value and a record-level error. Unknown damage labels behave similarly.
- Coordinates must be finite and within latitude ±90 / longitude ±180. The
  `(0, 0)` pair is flagged as invalid for this survey. Sample-grid coordinates
  are checked too. Missing coordinates are reported separately, not imputed.
- Floors must be integer ≥1; basement floors integer ≥0. Vs30, reported area,
  and exponentiated shaking must be finite and positive. MMI must be 1–12.
  Sample distance and uncertainty terms must be finite and nonnegative. These
  are basic domain checks, not exhaustive engineering verification; there is
  no arbitrary PGA or building-height upper cutoff.
- Missingness, duplicate coordinates and exact duplicate source records are
  reported with counts/IDs. These do not trigger a failing exit on their own.
- Invalid coordinates/values, failed parsing or unknown damage produce a
  nonzero CLI exit **after** the preserved Parquet and report are written for
  inspection. No imputation, row removal or numeric replacement is performed.

Every run writes the full table and machine-readable audit, including source
SHA-256, Parquet SHA-256, library versions and the damage mapping. No run timestamp,
absolute source path or random ordering enters the outputs. Repeat runs in the
pinned environment produce identical Parquet and JSON bytes; cross-version byte
identity is not promised. Unit tests cover every source damage label, schema
corruption, invalid values, retention, rate denominators and a complete offline
round trip against the registered workbook. CI also executes the full EDA.

## EDA interpretation

The eight figures use all retained survey records unless a plotted coordinate
or intensity is missing/invalid. Exclusions are counted in `summary.json` and
plot titles; the canonical data are unchanged. Missing damage is its own
histogram, map and shaking-boxplot category. Repeated coordinates overlap on an
offline longitude/latitude map with city labels; no random spatial jitter is used.

Damage rate means `count(grade >= 1) / count(known grade)` within structure
type. A second rate uses grade ≥3. Tables and labels expose the known/missing
denominators; zero known labels produce null, not zero. All source structure
categories, including missing type, are included. Geography tables report city
counts, known damage, valid coordinate counts, unique coordinates and extents.

The sample is geographically and structurally uneven, dominated by RC frame
buildings, and contains very few complete collapses. Survey visits took place
21–25 June 2023, months after the earthquake sequence; one damage label explicitly
mentions repair. Treat observations and shaking as descriptive associations.
Neither these sample rates nor the reported coverage estimate population-wide
damage probability. No ML models, fragility fits or train/test splits are made.
