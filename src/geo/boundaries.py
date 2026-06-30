"""boundaries.py -- pull geographic SHAPES (polygons) for census tracts.

The population data we pulled earlier is just numbers tied to tract ID codes; it
has no location. This module fetches the matching tract *shapes* from the Census
TIGER/Line files, so each tract can be placed on a map and (next step) matched to
a neighborhood. Cached to data/raw/ like every other external pull.
"""

import sys
from pathlib import Path

import geopandas as gpd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import PROJECT_ROOT

TIGER_YEAR = "2024"
STATE_FIPS = "53"
COUNTY_FIPS = "033"   # King County
CACHE_DIR = PROJECT_ROOT / "data" / "raw"


def fetch_tract_boundaries(year=TIGER_YEAR, use_cache=True):
    """Return a GeoDataFrame of census-tract polygons for King County.

    Columns: geoid, name, geometry. Downloads the statewide TIGER zip once,
    caches it to data/raw/, then filters down to King County.
    """
    zip_path = CACHE_DIR / f"tl_{year}_{STATE_FIPS}_tract.zip"

    if use_cache and zip_path.exists():
        print(f"Using cached tract boundaries <- {zip_path.name}")
    else:
        url = (f"https://www2.census.gov/geo/tiger/TIGER{year}/TRACT/"
               f"tl_{year}_{STATE_FIPS}_tract.zip")
        print(f"Downloading tract boundaries -> {zip_path.name} ...")
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        zip_path.write_bytes(r.content)

    # geopandas reads the shapefile straight out of the zip.
    gdf = gpd.read_file(zip_path)

    # Keep only King County, rename to our standard column names, drop the rest.
    king = gdf[gdf["COUNTYFP"] == COUNTY_FIPS].copy()
    king = king.rename(columns={"GEOID": "geoid", "NAMELSAD": "name"})
    return king[["geoid", "name", "geometry"]].reset_index(drop=True)


if __name__ == "__main__":
    tracts = fetch_tract_boundaries()
    print(f"\nKing County tract shapes : {len(tracts)}")
    print(f"Coordinate system (CRS)  : {tracts.crs}")
    print("Sample rows:")
    print(tracts.head(3)[["geoid", "name"]].to_string(index=False))

    # Confirm these shapes line up with our population numbers (same geoids).
    from src.demand.census import fetch_tract_population
    pop = fetch_tract_population()
    overlap = tracts["geoid"].isin(pop["geoid"]).sum()
    print(f"\nGeoid match check: {overlap} of {len(tracts)} tract shapes have "
          f"population data (should be ~all).")

    # Quick map so we can actually SEE the geography appear.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ax = tracts.plot(figsize=(8, 8), edgecolor="white", linewidth=0.3, color="#2b8cbe")
    ax.set_title(f"King County census tracts ({len(tracts)})")
    ax.axis("off")
    out = PROJECT_ROOT / "outputs" / "figures" / "king_tracts.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved map -> {out}")
