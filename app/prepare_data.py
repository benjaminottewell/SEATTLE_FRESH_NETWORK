"""prepare_data.py -- freeze the demand surface for the interactive app.

The Streamlit app must start instantly with no API keys, so the slow inputs
(census pulls, OSM graph, apportionment) are precomputed here into two small
committed files. Re-run this after any change to the demand pipeline.

    python app/prepare_data.py
"""

import sys
from pathlib import Path

import geopandas as gpd
import osmnx as ox
import pandas as pd
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.optimize.prep import build_siting_inputs
from src.geo.assign import WORKING_CRS
from src.geo.neighborhoods import fetch_study_neighborhoods
from src.geo.network import fetch_road_graph

APP_DIR = Path(__file__).resolve().parent


def corner_labels(points):
    """Cross-street label for each corner, from the OSM edges meeting at its node.

    The siting points sit exactly on road-graph nodes, so a nearest-node lookup
    recovers each corner's OSM id; the streets that meet there name the corner.
    """
    G = fetch_road_graph()
    nodes = ox.graph_to_gdfs(G, edges=False)[["geometry"]].to_crs(WORKING_CRS)
    tree = cKDTree(list(zip(nodes.geometry.x, nodes.geometry.y)))
    _, idx = tree.query(list(zip(points.geometry.x, points.geometry.y)))

    labels = []
    for osmid in nodes.index[idx]:
        names = set()
        for *_, data in list(G.in_edges(osmid, data=True)) + list(G.out_edges(osmid, data=True)):
            n = data.get("name")
            names.update(n if isinstance(n, list) else [n] if isinstance(n, str) else [])
        labels.append(" & ".join(sorted(names)[:2]) if names else "unnamed corner")
    return labels


if __name__ == "__main__":
    points, weights, reachable = build_siting_inputs()
    hoods = fetch_study_neighborhoods().to_crs(WORKING_CRS)

    # Corners with weights, in both meters (for radius math) and lat/lon (for the
    # map), labeled with cross-streets + neighborhood for the app tooltip/table.
    out = points.copy()
    out["x_utm"] = out.geometry.x
    out["y_utm"] = out.geometry.y
    ll = out.to_crs(4326)
    out["lat"] = ll.geometry.y
    out["lon"] = ll.geometry.x
    out["label"] = corner_labels(points)
    joined = gpd.sjoin(out, hoods, how="left", predicate="within")
    joined = joined[~joined.index.duplicated()]
    out["neighborhood"] = joined["neighborhood"].fillna("")
    pd.DataFrame(out[["pid", "weight", "x_utm", "y_utm", "lat", "lon",
                      "label", "neighborhood"]]).to_csv(
        APP_DIR / "siting_points.csv", index=False)

    # Simplified neighborhood outlines for map context.
    hoods["geometry"] = hoods.geometry.simplify(25)
    hoods.to_crs(4326).to_file(APP_DIR / "study_area.geojson", driver="GeoJSON")

    print(f"Wrote {len(out)} points -> app/siting_points.csv")
    print("Wrote outlines -> app/study_area.geojson")
