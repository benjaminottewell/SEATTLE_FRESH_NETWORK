"""mclp.py -- Phase 3 store siting: the Maximal Covering Location Problem.

Given p stores to place, choose candidate corners so the covered catchment is as
large as possible. `reachable[i]` lists the candidate sites within the walk radius
of demand point i, so coverage is pre-computed -- the model itself is three lines:
an objective and two constraint families.
"""

import sys
from pathlib import Path

from pulp import LpProblem, LpMaximize, LpVariable, lpSum, PULP_CBC_CMD, value

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import load_assumptions, get_value
# build_siting_inputs is imported in the __main__ block only, so lightweight
# consumers (the interactive app) can import solve_mclp without the geo stack.


def solve_mclp(weights, reachable, p, gap=None, time_limit=None):
    """Pick the p sites that cover the most catchment.

    weights   -- {point_id: catchment at that corner}
    reachable -- {point_id: candidate ids within coverage radius}
    gap       -- optional relative optimality tolerance (e.g. 0.005 = stop within
                 0.5%% of provably best; CBC finds good solutions fast but proving
                 exact optimality is what takes minutes)
    Returns (chosen_site_ids, covered_catchment).
    """
    candidates = list(weights.keys())   # every corner is also a candidate site

    prob = LpProblem("store_siting", LpMaximize)
    open_site = LpVariable.dicts("open", candidates, cat="Binary")   # 1 = store here
    covered = LpVariable.dicts("covered", candidates, cat="Binary")  # 1 = point served

    prob += lpSum([weights[i] * covered[i] for i in weights])                      # 1) objective: total covered catchment

    prob += lpSum([open_site[j] for j in candidates]) == p                      # 2) budget: exactly p stores open

    for i in weights:
        prob += covered[i] <= lpSum([open_site[j] for j in reachable[i]])  # 3) honesty: i only counts as covered
                                       #    if some open store can reach it

    prob.solve(PULP_CBC_CMD(msg=0, gapRel=gap, timeLimit=time_limit))

    chosen = [j for j in candidates if value(open_site[j]) > 0.5]
    covered_catchment = sum(weights[i] for i in weights if value(covered[i]) > 0.5)
    return chosen, covered_catchment


if __name__ == "__main__":
    from src.optimize.prep import build_siting_inputs
    points, weights, reachable = build_siting_inputs()
    p = get_value(load_assumptions(), "facility_location", "num_nodes_p")

    chosen, covered_catchment = solve_mclp(weights, reachable, p)

    total = sum(weights.values())
    print(f"\nMCLP result with p = {p} stores:")
    print(f"  covered catchment : {covered_catchment:,.0f} of {total:,.0f} "
          f"({covered_catchment / total:.1%})")
    print(f"  store sites chosen: {len(chosen)}")

    from src.viz.plots import plot_store_sites
    from src.geo.neighborhoods import fetch_study_neighborhoods
    radius = get_value(load_assumptions(), "facility_location", "coverage_radius_m")
    fig_path = plot_store_sites(points, chosen, fetch_study_neighborhoods(), radius)
    print(f"Saved site map -> {fig_path}")
