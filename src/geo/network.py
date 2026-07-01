"""network.py -- Phase 2: the road network and drive-times from the SoDo hub.

Builds a routable drive graph of the study area + SoDo from OpenStreetMap, then
clocks the fastest route from the production hub to each neighborhood. Edge speeds
come from OSM speed-limit tags (imputed by road type where untagged); those are
free-flow, so reported times also include a congestion-adjusted column driven by
assumptions.network.congestion_factor.
"""

import sys
from pathlib import Path

import networkx as nx
import osmnx as ox
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import PROJECT_ROOT, load_assumptions, get_value
from src.geo.neighborhoods import fetch_study_neighborhoods

GRAPH_PATH = PROJECT_ROOT / "data" / "raw" / "road_graph_drive.graphml"


def fetch_road_graph(use_cache=True):
    """Return the routable drive graph covering the study area and the SoDo hub.

    Downloaded once from OpenStreetMap and cached as GraphML; edges carry
    speed_kph and travel_time (free-flow seconds).
    """
    if use_cache and GRAPH_PATH.exists():
        print(f"Loading cached road graph <- {GRAPH_PATH.name}")
        return ox.load_graphml(GRAPH_PATH)

    a = load_assumptions()
    hub_lat, hub_lon = get_value(a, "study_area", "production_hub_coords")
    hoods = fetch_study_neighborhoods()

    # Cover the neighborhoods plus the hub, with margin so routes near the edge
    # of the area aren't artificially cut off.
    from shapely.geometry import Point
    area = hoods.union_all().union(Point(hub_lon, hub_lat).buffer(0.01))
    polygon = area.convex_hull.buffer(0.005)

    print("Downloading drive network from OpenStreetMap (one-time, ~1 min) ...")
    G = ox.graph_from_polygon(polygon, network_type="drive")
    G = ox.routing.add_edge_speeds(G)        # kph from OSM tags, imputed by road type
    G = ox.routing.add_edge_travel_times(G)  # free-flow seconds per edge

    GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
    ox.save_graphml(G, GRAPH_PATH)
    print(f"Saved graph -> data/raw/{GRAPH_PATH.name} "
          f"({len(G.nodes):,} nodes, {len(G.edges):,} edges)")
    return G


def hub_drive_times(G=None):
    """Fastest hub->neighborhood drive for each study neighborhood.

    Returns a DataFrame: neighborhood, network_km, freeflow_min, congested_min,
    within_window. Also returns the routes (node lists) for mapping.
    """
    if G is None:
        G = fetch_road_graph()

    a = load_assumptions()
    hub_lat, hub_lon = get_value(a, "study_area", "production_hub_coords")
    factor = get_value(a, "network", "congestion_factor")
    window = get_value(a, "network", "fresh_delivery_window_min")

    hoods = fetch_study_neighborhoods()
    targets = hoods.geometry.representative_point()

    hub_node = ox.distance.nearest_nodes(G, X=hub_lon, Y=hub_lat)
    dest_nodes = ox.distance.nearest_nodes(G, X=targets.x.tolist(), Y=targets.y.tolist())

    rows, routes = [], {}   # routes keyed by neighborhood so sorting can't misalign them
    for name, dest in zip(hoods["neighborhood"], dest_nodes):
        route = ox.routing.shortest_path(G, hub_node, dest, weight="travel_time")
        routes[name] = route
        edges = ox.routing.route_to_gdf(G, route)
        freeflow_min = edges["travel_time"].sum() / 60
        congested_min = freeflow_min * factor
        rows.append({
            "neighborhood": name,
            "network_km": round(edges["length"].sum() / 1000, 2),
            "freeflow_min": round(freeflow_min, 1),
            "congested_min": round(congested_min, 1),
            "within_window": congested_min <= window,
        })

    table = (pd.DataFrame(rows)
               .sort_values("congested_min")
               .reset_index(drop=True))
    return table, routes, G


if __name__ == "__main__":
    table, routes, G = hub_drive_times()

    a = load_assumptions()
    window = get_value(a, "network", "fresh_delivery_window_min")
    factor = get_value(a, "network", "congestion_factor")

    print(f"\nDrive times from the SoDo hub (congestion factor x{factor}, "
          f"fresh window = {window} min):\n")
    print(table.to_string(index=False))

    out_csv = PROJECT_ROOT / "outputs" / "tables" / "hub_drivetimes.csv"
    table.to_csv(out_csv, index=False)
    print(f"\nSaved table -> outputs/tables/{out_csv.name}")

    n_ok = int(table["within_window"].sum())
    print(f"Within the {window}-min fresh window: {n_ok} of {len(table)} neighborhoods")

    from src.viz.plots import plot_hub_routes
    hub_lat, hub_lon = get_value(a, "study_area", "production_hub_coords")
    fig_path = plot_hub_routes(G, routes, (hub_lat, hub_lon))
    print(f"Saved route map -> {fig_path}")
