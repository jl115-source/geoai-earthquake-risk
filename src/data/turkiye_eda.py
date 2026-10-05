"""Reproducible descriptive EDA; no model fitting or online basemap dependency."""

import argparse
import hashlib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .turkiye import DEFAULT_OUTPUT, ROOT, counts, valid_coordinates, validate_schema, write_json
from .turkiye_schema import DAMAGE_NAMES, SHAKING

COLORS = ["#278278", "#8cab46", "#e7b24b", "#d46a3e", "#8b2840", "#9299a2"]
LABELS = [f"{k}: {v}" for k, v in DAMAGE_NAMES.items()] + ["Missing / unmapped"]


def damage_rates(table):
    records = []
    for structure, group in table.groupby(table.structure_type.fillna("<missing>"), sort=True):
        known = int(group.damage_grade.notna().sum())
        damaged = int((group.damage_grade >= 1).sum())
        severe = int((group.damage_grade >= 3).sum())
        records.append({"structure_type": structure, "total_records": len(group), "known_damage": known,
                        "missing_damage": len(group) - known, "damaged_grade_ge_1": damaged,
                        "severe_grade_ge_3": severe, "damage_rate": damaged / known if known else None,
                        "severe_damage_rate": severe / known if known else None})
    return pd.DataFrame(records)


def geographic_coverage(table):
    records = []
    for city, group in table.groupby(table.city.fillna("<missing>"), sort=True):
        spatial = group.loc[valid_coordinates(group)]
        records.append({"city": city, "records": len(group), "valid_coordinate_records": len(spatial),
                        "unique_coordinates": len(spatial.drop_duplicates(["latitude", "longitude"])),
                        "known_damage": int(group.damage_grade.notna().sum()),
                        **{f"{col}_{stat}": getattr(spatial[col], stat)() if len(spatial) else None
                           for col in ("latitude", "longitude") for stat in ("min", "max")}})
    return pd.DataFrame(records)


def run_eda(source=DEFAULT_OUTPUT / "buildings.parquet", output=ROOT / "results/turkiye_2023"):
    source, output = Path(source), Path(output)
    table = pd.read_parquet(source)
    validate_schema(table)
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.titleweight": "bold", "figure.facecolor": "white"})

    def save(fig, name):
        fig.savefig(output / f"{name}.png", dpi=160, bbox_inches="tight", metadata={"Software": "geoai-earthquake-risk"})
        plt.close(fig)

    grade = table.damage_grade.fillna(-1)
    categories = [0, 1, 2, 3, 4, -1]
    spatial_ok = valid_coordinates(table)
    fig, ax = plt.subplots(figsize=(10, 9), layout="constrained")
    for code, color, label in zip(categories, COLORS, LABELS):
        subset = table.loc[spatial_ok & (grade == code)]
        ax.scatter(subset.longitude, subset.latitude, s=22, c=color, alpha=.7,
                   label=f"{label} (n={len(subset)})", edgecolors="white", linewidths=.25)
    for city, group in table.loc[spatial_ok].groupby("city"):
        ax.annotate(city, (group.longitude.median(), group.latitude.median()), xytext=(5, 9),
                    textcoords="offset points", fontsize=8,
                    bbox={"facecolor": "white", "alpha": .8, "edgecolor": "none", "pad": 1})
    if spatial_ok.any():
        ax.set_aspect(1 / np.cos(np.deg2rad(float(table.loc[spatial_ok, "latitude"].mean()))))
    ax.set(xlabel="Longitude (degrees east)", ylabel="Latitude (degrees north)",
           title=f"Türkiye 2023 surveyed building locations\n{spatial_ok.sum()} records plotted; {(~spatial_ok).sum()} missing/invalid locations excluded")
    ax.grid(alpha=.15)
    ax.legend(loc="upper left", fontsize=8)
    fig.supxlabel("Coordinate map; no basemap. Repeated coordinates overlap; no jitter or deduplication.", fontsize=9)
    save(fig, "spatial_damage")

    class_counts = pd.DataFrame({"damage_class": LABELS, "count": [int((grade == c).sum()) for c in categories]})
    class_counts.to_csv(output / "damage_class_counts.csv", index=False)
    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    bars = ax.barh(LABELS, class_counts["count"], color=COLORS)
    ax.bar_label(bars, padding=3)
    ax.invert_yaxis()
    ax.set(xlabel="Survey records", title=f"Damage class counts (all {len(table)} records)")
    ax.set_xlim(0, max(class_counts["count"].max() * 1.15, 1))
    save(fig, "damage_histogram")

    structure_counts = pd.Series(counts(table.structure_type), name="count").sort_values()
    structure_counts.rename_axis("structure_type").to_csv(output / "structure_type_counts.csv")
    fig, ax = plt.subplots(figsize=(11, 6), layout="constrained")
    bars = ax.barh(structure_counts.index, structure_counts, color="#327887")
    ax.bar_label(bars, padding=3)
    ax.set(xlabel="Survey records", title="Structure types (source categories preserved)", xlim=(0, max(structure_counts.max() * 1.15, 1)))
    save(fig, "structure_types")

    exclusions = {}
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), layout="constrained")
    boxfig, boxaxes = plt.subplots(2, 2, figsize=(12, 8), layout="constrained")
    for (field, unit), ax, boxax in zip(SHAKING.items(), axes.flat, boxaxes.flat):
        usable = (table[field].notna() & np.isfinite(table[field]) & (table[field] > 0)).fillna(False)
        exclusions[field] = {"used": int(usable.sum()), "missing": int(table[field].isna().sum()),
                             "invalid": int((table[field].notna() & ~usable).sum())}
        ax.hist(table.loc[usable, field].astype(float), bins=24, color="#327887", edgecolor="white")
        ax.set(xlabel=f"{field} ({unit})", ylabel="Survey records", title=f"{field}: n={usable.sum()}, excluded={(~usable).sum()}")
        groups = [table.loc[usable & (grade == c), field].astype(float).to_numpy() for c in categories]
        # Empty groups remain labelled; no fake data inserted for the boxplot.
        positions = [i + 1 for i, g in enumerate(groups) if len(g)]
        if positions:
            boxax.boxplot([g for g in groups if len(g)], positions=positions, widths=.6)
        boxax.set_xticks(range(1, 7), [f"{c if c >= 0 else 'NA'}\nn={len(g)}" for c, g in zip(categories, groups)])
        boxax.set(xlabel="Damage grade (NA = missing/unmapped)", ylabel=f"{field} ({unit})", title=field)
    fig.suptitle("Shaking distributions: exp(source log-mean)")
    boxfig.suptitle("Shaking by damage grade: descriptive survey distributions")
    save(fig, "shaking_distributions")
    save(boxfig, "shaking_by_damage")

    canonical = [c for c in table if not c.startswith("raw__")]
    missingness = pd.DataFrame({"field": canonical, "missing_count": [int(table[c].isna().sum()) for c in canonical]})
    missingness["missing_fraction"] = missingness.missing_count / len(table)
    missingness.to_csv(output / "missingness.csv", index=False)
    missing_plot = missingness.loc[missingness.missing_count > 0].sort_values("missing_fraction")
    fig, ax = plt.subplots(figsize=(11, max(4, len(missing_plot) * .3)), layout="constrained")
    if len(missing_plot):
        bars = ax.barh(missing_plot.field, 100 * missing_plot.missing_fraction, color="#a26951")
        ax.bar_label(bars, labels=missing_plot.missing_count.astype(str), padding=3)
    else:
        ax.text(.5, .5, "No missing canonical values", ha="center", transform=ax.transAxes)
    ax.set(xlabel="Missing (%) — bar labels are record counts", xlim=(0, 115),
           title="Canonical-field missingness\nZero-missing fields included in missingness.csv")
    save(fig, "missingness")

    rates = damage_rates(table)
    rates.to_csv(output / "damage_rate_by_structure.csv", index=False)
    fig, ax = plt.subplots(figsize=(12, 6), layout="constrained")
    y = np.arange(len(rates))
    ax.barh(y - .18, rates.damage_rate * 100, height=.35, label="Any damage: grade ≥ 1", color="#327887")
    ax.barh(y + .18, rates.severe_damage_rate * 100, height=.35, label="Severe / collapse: grade ≥ 3", color="#d46a3e")
    ax.set_yticks(y, [f"{r.structure_type} (known={r.known_damage}, missing={r.missing_damage})" for r in rates.itertuples()])
    ax.set(xlim=(0, 105), xlabel="% of records with known damage within each structure type",
           title="Observed damage rates by structure type\nMissing labels excluded from denominator; no known labels → undefined rate")
    ax.legend(loc="upper center", bbox_to_anchor=(.5, -.17), ncol=2, fontsize=8)
    save(fig, "damage_rates")

    coverage = geographic_coverage(table)
    coverage.to_csv(output / "geographic_coverage.csv", index=False)
    fig, ax = plt.subplots(figsize=(10, 5), layout="constrained")
    bars = ax.barh(coverage.city, coverage.records, color="#327887")
    ax.bar_label(bars, labels=[f"{r.records} records / {r.unique_coordinates} coordinate pairs" for r in coverage.itertuples()], padding=3, fontsize=8)
    ax.set(xlabel="Survey records", xlim=(0, max(coverage.records.max() * 1.7, 1)), title="Geographic coverage by recorded city/town")
    save(fig, "geographic_coverage")

    summary = {
        "records": len(table), "known_damage": int(table.damage_grade.notna().sum()),
        "known_structure": int(table.structure_type.notna().sum()),
        "damage_and_structure": int(table.has_damage_and_structure.sum()),
        "damage_class_counts": counts(table.damage_grade), "city_counts": counts(table.city),
        "valid_coordinate_records": int(spatial_ok.sum()), "excluded_coordinate_records": int((~spatial_ok).sum()),
        "unique_valid_coordinates": len(table.loc[spatial_ok].drop_duplicates(["latitude", "longitude"])),
        "shaking_plot_accounting": exclusions,
        "shaking_ranges": {c: {"min": float(table.loc[np.isfinite(table[c]) & (table[c] > 0), c].min()),
                               "max": float(table.loc[np.isfinite(table[c]) & (table[c] > 0), c].max())}
                           if exclusions[c]["used"] else {"min": None, "max": None} for c in SHAKING},
        "input_parquet_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "interpretation": "Survey-record descriptions, not regional damage probabilities. Repeated coordinates retained, convenience/engineering sample, uneven city and structure coverage. No causal or population-rate inference.",
    }
    write_json(output / "summary.json", summary)
    report = ["# Türkiye 2023 exploratory analysis", "",
              f"Retained **{len(table)} survey records** at **{summary['unique_valid_coordinates']} distinct valid coordinate pairs**.",
              f"**{summary['damage_and_structure']} records have both known damage and structure type**. This explains the registered 527-building analysis subset; no records were removed to force that count.",
              "", "## Damage classes", "", "| Grade | Meaning | Records |", "| --- | --- | ---: |"]
    report += [f"| {c if c >= 0 else 'NA'} | {label} | {int((grade == c).sum())} |" for c, label in zip(categories, LABELS)]
    report += ["", "## Geographic coverage", "", "| City/town | Records | Unique coordinates |", "| --- | ---: | ---: |"]
    report += [f"| {r.city} | {r.records} | {r.unique_coordinates} |" for r in coverage.itertuples()]
    report += ["", "## Interpretation", "", summary["interpretation"], "",
               "PGA and SA are in g; PGV is in cm/s. The canonical intensity is exp(source log-mean), a geometric mean/median, not an arithmetic mean. Source uncertainty fields are retained unchanged.",
               "Damage rates use known damage labels as denominators. CSV tables show all counts and missing labels. Plot exclusions for invalid/missing coordinates and shaking are in summary.json.", ""]
    for name in ("spatial_damage", "damage_histogram", "structure_types", "shaking_distributions", "shaking_by_damage", "missingness", "damage_rates", "geographic_coverage"):
        report += [f"![{name.replace('_', ' ')}]({name}.png)", ""]
    (output / "report.md").write_text("\n".join(report), encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_OUTPUT / "buildings.parquet")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results/turkiye_2023")
    args = parser.parse_args()
    summary = run_eda(args.input, args.output_dir)
    print(f"EDA for {summary['records']} retained records: {args.output_dir / 'report.md'}")


if __name__ == "__main__":
    main()
