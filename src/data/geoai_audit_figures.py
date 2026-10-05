"""Visual inspection artifacts for pre-event input audit; no model fitting."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from .acquire_expansion import ROOT
from .geoai_feasibility import RAW, OUT


def main():
    destination = ROOT / "results/geoai_1f"
    destination.mkdir(parents=True, exist_ok=True)
    frame = pd.read_parquet(OUT / "feature_manifest.parquet")
    figures, axes = plt.subplots(2, 5, figsize=(17, 9.5))
    for ax, (city, group) in zip(axes.flat, frame.groupby("city", sort=True)):
        # Fixed first source ID with pixels, not an outcome-selected illustration.
        row = group.sort_values("building_id").iloc[0]
        path = RAW / "locations" / row.location_key / "reflectance.npz"
        if path.exists():
            pixels = np.load(path)["reflectance"][[2, 1, 0]].transpose(1, 2, 0)
            ax.imshow(np.clip(pixels / .3, 0, 1))
            ax.scatter([47.5], [47.5], marker='+', s=80, color='yellow')
        ax.set_title(f"{city}\n{row.building_id}", fontsize=10)
        ax.axis('off')
    figures.suptitle('Audited 2022 pre-event RGB context: 960 m square, fixed display scale\nOne deterministic example per recorded city; centre marker is the source coordinate', fontsize=13)
    figures.tight_layout(h_pad=2, rect=(0, 0, 1, .93))
    figures.savefig(destination / 'pre_event_context.png', dpi=150)
    plt.close(figures)
    fig, ax = plt.subplots(figsize=(8, 9))
    eligible = frame.eligible
    ax.scatter(frame.loc[eligible, 'longitude'], frame.loc[eligible, 'latitude'], s=10, label='Eligible', alpha=.6)
    ax.scatter(frame.loc[~eligible, 'longitude'], frame.loc[~eligible, 'latitude'], s=25, marker='x', label='Explicitly excluded', color='crimson')
    for city, group in frame.groupby('city'):
        ax.annotate(city, (group.longitude.median(), group.latitude.median()), xytext=(5, 5), textcoords='offset points', fontsize=8)
    ax.set(xlabel='Longitude', ylabel='Latitude', title='Source-coordinate coverage and frozen cohort exclusions')
    ax.legend(); fig.tight_layout(); fig.savefig(destination / 'cohort_coverage.png', dpi=150); plt.close(fig)
    print(f'Wrote input inspection figures to {destination}')


if __name__ == '__main__':
    main()
