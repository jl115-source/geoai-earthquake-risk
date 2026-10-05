"""Explicit dictionary for every column in the registered Türkiye workbook."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Column:
    source: str
    canonical: str
    dtype: str
    units: str
    description: str
    transform: str = "identity"


COLUMNS = [
    Column("assessor_name", "assessor_name", "string", "text", "Survey assessor; source contains encoding artifacts, preserved without correction."),
    Column("City/Town", "city", "string", "text", "Survey city/town spelling, not an administrative boundary assignment."),
    Column("latitude", "latitude", "Float64", "degrees north", "Survey building latitude."),
    Column("longitude", "longitude", "Float64", "degrees east", "Survey building longitude."),
    Column("sample_lat", "sample_latitude", "Float64", "degrees north", "Sampled shaking grid latitude; distinct from building location."),
    Column("sample_lon", "sample_longitude", "Float64", "degrees east", "Sampled shaking grid longitude."),
    Column("sample_distance_m", "sample_distance_m", "Float64", "m", "Distance from building to sampled grid point."),
    Column("vs30", "vs30", "Float64", "m/s", "Time-averaged shear-wave velocity over the upper 30 m."),
]
for source, target, unit in [
    ("MMI", "MMI", "intensity units"), ("PGA", "PGA", "g"),
    ("PGV", "PGV", "cm/s"), ("SA(0.3)", "SA_0p3", "g"),
    ("SA(1.0)", "SA_1p0", "g"), ("SA(3.0)", "SA_3p0", "g"),
]:
    COLUMNS.append(Column(
        f"{source}_mean", target, "Float64", unit,
        "Source mean MMI, linear scale." if source == "MMI" else
        f"Natural-log mean of {source}; exp(source) is a geometric mean/median intensity, not an arithmetic mean.",
        "identity" if source == "MMI" else "exp",
    ))
    for suffix in ("phi", "std", "tau"):
        COLUMNS.append(Column(
            f"{source}_{suffix}", f"{target}_{suffix}", "Float64",
            "source uncertainty scale (unverified)",
            f"{source} {suffix} uncertainty field. Preserve as supplied; workbook does not define exact convention. Do not exponentiate.",
        ))

COLUMNS += [
    Column("photos_building_id", "photo_ids", "string", "text", "Comma-separated photo identifiers; neither unique nor a reliable building key."),
    Column("existing_placard", "existing_placard", "string", "source code", "Existing placard field; entirely blank in registered workbook, coding unspecified."),
    Column("date", "survey_date", "datetime64[ns]", "date", "Survey visit date, not earthquake date."),
    Column("storeys_above_ground_incl_ground_floor", "floors", "Float64", "storeys", "Above-ground storeys including ground floor. Nullable float permits retaining and flagging fractional invalid input."),
    Column("storeys_below_ground", "basement_floors", "Float64", "storeys", "Below-ground storeys; zero is valid."),
    Column("area", "area", "Float64", "unspecified", "Reported area; workbook supplies no unit or footprint/floor-area definition."),
    Column("construction_age", "construction_age", "string", "source category", "Construction vintage band; do not replace with a midpoint/year."),
    Column("structure_type", "structure_type", "string", "source category", "Structural system/height class. Preserve unusual free text, no recoding into Other."),
    Column("occupancy", "occupancy", "string", "source category", "Building use."),
    Column("is_it_occupied", "is_occupied", "string", "source category", "Reported occupied status at survey."),
    Column("vertical_irregularity", "vertical_irregularity", "string", "source category", "Reported vertical irregularity."),
    Column("horizontal_irregularity", "horizontal_irregularity", "string", "source category", "Reported horizontal irregularity."),
    Column("pounding", "pounding", "string", "source category", "Reported pounding."),
    Column("cladding_type", "cladding_type", "string", "source category", "Cladding description."),
    Column("roof_type", "roof_type", "string", "source category", "Roof system."),
    Column("casualties_reported", "casualties_reported", "string", "source category", "Reported casualties flag, not a casualty count."),
    Column("damage_condition", "damage_label", "string", "source category", "Observed damage label. Literal None means undamaged; only empty/whitespace cells are missing."),
    Column("building_or_storey_leaning", "building_or_storey_leaning", "string", "source text", "Leaning/other observations, including free-text foundation cracks."),
    Column("falling_hazard_unbraced_parapet_or_unsecure_cladding", "falling_hazard", "string", "source category", "Reported parapet/cladding falling hazard."),
    Column("infill_wall_damage", "infill_wall_damage", "string", "source category", "Infill wall damage observation."),
    Column("structural_members_beams_columns", "member_damage", "string", "source category", "Beam/column damage observation."),
    Column("estimated_building_damage", "estimated_building_damage", "string", "percent band", "Reported damage percentage band; retained separately from ordinal damage."),
    Column("Unnamed: 54", "unlabelled_damage_band", "string", "unspecified percent band", "Unlabelled Excel column BC, populated in six records. Meaning unverified; never use to fill or override damage."),
]

DAMAGE_MAP = {
    "None": 0,
    "Minor (few cracks)": 1,
    "Moderate (extensive cracks in walls)": 2,
    "moderate damage but repaired": 2,
    "Severe (structural damage to system)": 3,
    "Partial collapse (portion collapsed)": 3,
    "Complete collapse": 4,
}
DAMAGE_NAMES = {0: "None", 1: "Minor", 2: "Moderate", 3: "Severe / partial collapse", 4: "Complete collapse"}
SHAKING = {"PGA": "g", "PGV": "cm/s", "SA_0p3": "g", "SA_1p0": "g"}
SCHEMA = {c.canonical: c.dtype for c in COLUMNS} | {
    "building_id": "string", "source_row": "Int64", "damage_grade": "Int8",
    "has_damage_and_structure": "boolean",
}


def dictionary():
    return [asdict(c) for c in COLUMNS]
