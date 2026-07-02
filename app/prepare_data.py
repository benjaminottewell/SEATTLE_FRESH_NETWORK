"""prepare_data.py -- freeze the demand surface for the interactive app.

The Streamlit app must start instantly with no API keys, so the slow inputs
(census pulls, OSM graph, apportionment) are precomputed here into two small
committed files. Re-run this after any change to the demand pipeline.

    python app/prepare_data.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.optimize.prep import build_siting_inputs
from src.geo.neighborhoods import fetch_study_neighborhoods

APP_DIR = Path(__file__).resolve().parent

if __name__ == "__main__":
    points, weights, reachable = build_siting_inputs()

    # Corners with weights, in both meters (for radius math) and lat/lon (for the map).
    out = points.copy()
    out["x_utm"] = out.geometry.x
    out["y_utm"] = out.geometry.y
    ll = out.to_crs(4326)
    out["lat"] = ll.geometry.y
    out["lon"] = ll.geometry.x
    pd.DataFrame(out[["pid", "weight", "x_utm", "y_utm", "lat", "lon"]]).to_csv(
        APP_DIR / "siting_points.csv", index=False)

    # Simplified neighborhood outlines for map context.
    hoods = fetch_study_neighborhoods().to_crs(32610)
    hoods["geometry"] = hoods.geometry.simplify(25)
    hoods.to_crs(4326).to_file(APP_DIR / "study_area.geojson", driver="GeoJSON")

    print(f"Wrote {len(out)} points -> app/siting_points.csv")
    print("Wrote outlines -> app/study_area.geojson")
