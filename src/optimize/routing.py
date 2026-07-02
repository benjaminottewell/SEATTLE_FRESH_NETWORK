"""routing.py -- Phase 4: multi-daily fresh delivery from the SoDo hub (VRPTW).

Chains the earlier phases: MCLP chooses the p store sites; each covered corner is
assigned to its nearest store (per-store demand); the Phase-2 road graph supplies a
real drive-time matrix; OR-Tools then plans one delivery run -- vans, stop order,
durations -- under two constraints: van capacity and the fresh-delivery window.
Every run in the day is identical in v1, so daily cost = runs x run cost + fleet.
"""

import sys
from pathlib import Path

import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import PROJECT_ROOT, load_assumptions, get_value
from src.geo.network import fetch_road_graph
from src.optimize.prep import build_siting_inputs
from src.optimize.mclp import solve_mclp

MAX_VEHICLES = 8   # solver ceiling, not a fleet decision; result reports vans used


def store_demand_per_run(points, weights, reachable, chosen, a):
    """Transactions/day per store -> delivery units per run.

    Each covered corner is served by its NEAREST chosen store (MCLP only
    guarantees coverage; nearest-store assignment is the natural service rule).
    """
    capture = get_value(a, "demand", "capture_rate")
    runs_per_day = get_value(a, "routing", "deliveries_per_day")
    txn_per_unit = get_value(a, "routing", "transactions_per_unit")

    stores = points[points["pid"].isin(chosen)].reset_index(drop=True)
    tree = cKDTree(list(zip(stores.geometry.x, stores.geometry.y)))

    radius = get_value(a, "facility_location", "coverage_radius_m")
    covered = points[points["pid"].map(lambda i: any(j in set(chosen) for j in reachable[i]))]
    _, nearest = tree.query(list(zip(covered.geometry.x, covered.geometry.y)))

    catchment = pd.Series(0.0, index=range(len(stores)))
    for store_idx, pid in zip(nearest, covered["pid"]):
        catchment[store_idx] += weights[pid]

    stores["txns_day"] = catchment * capture
    stores["units_per_run"] = np.ceil(stores["txns_day"] / runs_per_day / txn_per_unit)
    return stores


def drive_time_matrix(stores, a):
    """Hub + stores drive-time matrix (seconds), congested, over the real graph."""
    G = fetch_road_graph()
    factor = get_value(a, "network", "congestion_factor")
    hub_lat, hub_lon = get_value(a, "study_area", "production_hub_coords")

    locs = stores.to_crs(4326)
    xs = [hub_lon] + list(locs.geometry.x)
    ys = [hub_lat] + list(locs.geometry.y)
    nodes = ox.distance.nearest_nodes(G, X=xs, Y=ys)

    n = len(nodes)
    M = np.zeros((n, n), dtype=int)
    for i, src in enumerate(nodes):
        times = nx.single_source_dijkstra_path_length(G, src, weight="travel_time")
        for j, dst in enumerate(nodes):
            if i != j:
                M[i, j] = int(times.get(dst, 10_000) * factor)
    return M   # index 0 = hub, 1..n = stores


def solve_run(matrix, units, a):
    """Plan one delivery run. Returns list of routes [(stop_indices, seconds, load)]."""
    window_s = int(get_value(a, "network", "fresh_delivery_window_min") * 60)
    service_s = int(get_value(a, "routing", "service_minutes_per_stop") * 60)
    capacity = int(get_value(a, "routing", "vehicle_capacity_units"))

    n = len(matrix)
    manager = pywrapcp.RoutingIndexManager(n, MAX_VEHICLES, 0)   # node 0 = hub depot
    routing = pywrapcp.RoutingModel(manager)

    def time_cb(fi, ti):
        f, t = manager.IndexToNode(fi), manager.IndexToNode(ti)
        return int(matrix[f][t]) + (service_s if f != 0 else 0)   # unload after each stop

    def window_cb(fi, ti):
        # Freshness clock: stops at the LAST handoff -- the return drive to the
        # hub doesn't age the goods, so arcs into the depot count service only.
        f, t = manager.IndexToNode(fi), manager.IndexToNode(ti)
        drive = 0 if t == 0 else int(matrix[f][t])
        return drive + (service_s if f != 0 else 0)

    transit = routing.RegisterTransitCallback(time_cb)
    routing.SetArcCostEvaluatorOfAllVehicles(transit)      # driver paid for everything
    window = routing.RegisterTransitCallback(window_cb)
    # Deliveries must all land inside the fresh window (service time included).
    routing.AddDimension(window, 0, window_s, True, "Time")

    demands = [0] + [int(u) for u in units]                       # hub loads nothing
    demand_cb = routing.RegisterUnaryTransitCallback(
        lambda i: demands[manager.IndexToNode(i)])
    routing.AddDimensionWithVehicleCapacity(
        demand_cb, 0, [capacity] * MAX_VEHICLES, True, "Load")

    # Big fixed cost per vehicle -> solver uses as few vans as possible.
    routing.SetFixedCostOfAllVehicles(100_000)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.FromSeconds(15)
    solution = routing.SolveWithParameters(params)
    if solution is None:
        raise RuntimeError("No feasible run plan -- window or capacity too tight.")

    time_dim = routing.GetDimensionOrDie("Time")
    routes = []
    for v in range(MAX_VEHICLES):
        idx = routing.Start(v)
        stops, load, paid_s = [], 0, 0
        while not routing.IsEnd(idx):
            nxt = solution.Value(routing.NextVar(idx))
            paid_s += time_cb(idx, nxt)            # full time incl. the return leg
            node = manager.IndexToNode(idx)
            if node != 0:
                stops.append(node)
                load += demands[node]
            idx = nxt
        if stops:
            window_used = solution.Value(time_dim.CumulVar(routing.End(v)))
            routes.append((stops, window_used, paid_s, load))
    return routes


if __name__ == "__main__":
    a = load_assumptions()
    p = get_value(a, "facility_location", "num_nodes_p")
    runs_per_day = get_value(a, "routing", "deliveries_per_day")

    print(f"Siting {p} stores (MCLP), then routing one delivery run...")
    points, weights, reachable = build_siting_inputs()
    chosen, _ = solve_mclp(weights, reachable, p, gap=0.005, time_limit=120)

    stores = store_demand_per_run(points, weights, reachable, chosen, a)
    matrix = drive_time_matrix(stores, a)
    routes = solve_run(matrix, stores["units_per_run"], a)

    print(f"\nOne fresh run ({get_value(a, 'network', 'fresh_delivery_window_min')}-min window, "
          f"{get_value(a, 'routing', 'vehicle_capacity_units')}-unit vans):")
    total_s = 0
    for k, (stops, window_used, paid_s, load) in enumerate(routes, 1):
        total_s += paid_s
        print(f"  van {k}: {len(stops)} stops, load {load} units, "
              f"last handoff at {window_used / 60:.0f} min ({paid_s / 60:.0f} min paid)")

    # Daily economics of the cadence.
    vans = len(routes)
    driver_rate = get_value(a, "routing", "driver_cost_per_hour")
    fixed = get_value(a, "routing", "vehicle_fixed_cost_per_day")
    variable_day = runs_per_day * (total_s / 3600) * driver_rate
    fixed_day = vans * fixed
    total_day = variable_day + fixed_day

    print(f"\nDaily delivery cost at {runs_per_day} runs/day:")
    print(f"  fleet            : {vans} vans x ${fixed}/day        = ${fixed_day:,.0f}")
    print(f"  driver time      : {runs_per_day} x {total_s / 3600:.2f} h x ${driver_rate}/h = ${variable_day:,.0f}")
    print(f"  TOTAL            : ${total_day:,.0f}/day  (${total_day / p:,.0f} per store)")

    summary = pd.DataFrame([{
        "p_stores": p, "runs_per_day": runs_per_day, "vans": vans,
        "run_minutes_total": round(total_s / 60, 1),
        "daily_cost_total": round(total_day), "daily_cost_per_store": round(total_day / p),
    }])
    out = PROJECT_ROOT / "outputs" / "tables" / "routing_summary.csv"
    summary.to_csv(out, index=False)
    print(f"\nSaved -> outputs/tables/{out.name}")
