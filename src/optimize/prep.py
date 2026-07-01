"""prep.py -- build the inputs the Phase-3 siting model (MCLP) needs.

Demand points AND candidate store sites are the real street intersections from the
Phase-2 road graph (people are on corners; stores go on corners). Each tract piece's
weighted catchment is spread equally across the intersections inside it, so demand
lives at street granularity without any new data pull.
"""

import sys
from pathlib import Path

import geopandas as gpd
import osmnx as ox
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import load_assumptions, get_value
from src.geo.assign import tract_neighborhood_pieces, WORKING_CRS
from src.geo.network import fetch_road_graph


def build_siting_inputs():
    """Return (points, weights, reachable) for the MCLP.

    points    -- GeoDataFrame of candidate/demand intersections (WORKING_CRS, meters)
    weights   -- dict {point_id: catchment persons at that corner}
    reachable -- dict {point_id: list of candidate ids within coverage radius of it}
    """
    a = load_assumptions()
    radius = get_value(a, "facility_location", "coverage_radius_m")
    ww = get_value(a, "demand", "worker_weight")
    rw = get_value(a, "demand", "resident_weight")

    # Street intersections from the Phase-2 graph, in meters CRS.
    G = fetch_road_graph()
    nodes = ox.graph_to_gdfs(G, edges=False)[["geometry"]].to_crs(WORKING_CRS)

    # Weighted catchment per tract piece, split equally over its intersections.
    pieces = tract_neighborhood_pieces().reset_index(names="piece_id")
    pieces["catchment"] = ww * pieces["workers"] + rw * pieces["residents"]

    joined = gpd.sjoin(nodes, pieces[["piece_id", "catchment", "geometry"]],
                       how="inner", predicate="within")
    points = joined[["geometry"]].copy()
    # each corner gets an equal share of its piece's catchment
    points["weight"] = joined["catchment"] / joined.groupby("piece_id")["catchment"].transform("size")
    points = points.reset_index(drop=True).reset_index(names="pid")

    dropped = pieces[~pieces["piece_id"].isin(joined["piece_id"])]
    if len(dropped):
        lost = dropped["catchment"].sum()
        print(f"(note: {len(dropped)} slivers with no intersection inside, "
              f"{lost:,.0f} catchment ({lost / pieces['catchment'].sum():.1%}) unplaced)")

    # Which candidates sit within the walk radius of each demand point?
    xy = list(zip(points.geometry.x, points.geometry.y))
    tree = cKDTree(xy)
    neighbor_lists = tree.query_ball_point(xy, r=radius)

    weights = dict(zip(points["pid"], points["weight"]))
    reachable = {pid: nbrs for pid, nbrs in zip(points["pid"], neighbor_lists)}
    return points, weights, reachable


if __name__ == "__main__":
    points, weights, reachable = build_siting_inputs()
    radius = get_value(load_assumptions(), "facility_location", "coverage_radius_m")
    total = sum(weights.values())
    avg_reach = sum(len(v) for v in reachable.values()) / len(reachable)
    print(f"\nDemand/candidate points : {len(points):,} street intersections")
    print(f"Total placed catchment  : {total:,.0f} (vs ~327,784 study-area catchment)")
    print(f"Avg candidates within {radius}m of a point: {avg_reach:.0f}")
