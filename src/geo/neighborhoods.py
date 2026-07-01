"""neighborhoods.py -- pull Seattle neighborhood SHAPES and select our 7 study areas.

Source: Seattle City Clerk "Neighborhood Map Atlas" boundaries (via the widely-used
seattleio mirror of the city's open GIS data). The dataset has a broad `nhood`
district column and a fine `name` column; our study neighborhoods live in `name`
(except Capitol Hill, whose dense core is the `name` value "Broadway").
"""

import sys
from pathlib import Path

import geopandas as gpd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import PROJECT_ROOT

NEIGHBORHOODS_URL = ("https://raw.githubusercontent.com/seattleio/"
                     "seattle-boundaries-data/master/data/neighborhoods.geojson")
CACHE_PATH = PROJECT_ROOT / "data" / "raw" / "seattle_neighborhoods.geojson"

# The city's fine `name` values don't match our study names 1:1; reconcile them here.
STUDY_AREA = {
    "Central Business District": "Downtown/CBD",
    "Belltown":                  "Belltown",
    "South Lake Union":          "South Lake Union",
    "Broadway":                  "Capitol Hill",          # dense core of Capitol Hill
    "First Hill":                "First Hill",
    "Pioneer Square":            "Pioneer Square",
    "International District":     "Chinatown-International District",
}


def fetch_study_neighborhoods(use_cache=True):
    """Return a GeoDataFrame of just our 7 study neighborhoods, with our names.

    Columns: neighborhood, geometry. Downloads the citywide GeoJSON once and
    caches it to data/raw/, then filters to Seattle + our 7 names and dissolves
    any multi-part neighborhoods into one polygon each.
    """
    if use_cache and CACHE_PATH.exists():
        print(f"Using cached neighborhoods <- {CACHE_PATH.name}")
    else:
        print("Downloading Seattle neighborhood boundaries ...")
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(NEIGHBORHOODS_URL, timeout=120)
        r.raise_for_status()
        CACHE_PATH.write_bytes(r.content)

    gdf = gpd.read_file(CACHE_PATH)

    # Seattle only, and only the fine `name` values we care about.
    seattle = gdf[gdf["city"].astype(str).str.contains("Seattle", case=False, na=False)]
    study = seattle[seattle["name"].isin(STUDY_AREA)].copy()
    study["neighborhood"] = study["name"].map(STUDY_AREA)

    # Merge any multi-part neighborhoods into a single shape each -> 7 rows.
    study = study.dissolve(by="neighborhood", as_index=False)[["neighborhood", "geometry"]]
    return study


if __name__ == "__main__":
    hoods = fetch_study_neighborhoods()
    print(f"\nStudy neighborhoods found: {len(hoods)} (expected 7)")
    print(f"CRS: {hoods.crs}")
    print(hoods[["neighborhood"]].to_string(index=False))

    # Draw the study area using the shared, readable map style (src/viz).
    from src.viz.plots import plot_study_area
    out = plot_study_area(hoods)
    print(f"\nSaved map -> {out}")
