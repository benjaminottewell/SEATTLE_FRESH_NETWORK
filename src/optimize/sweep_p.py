"""sweep_p.py -- Phase 3 sensitivity: re-solve the MCLP across the num_nodes_p range.

Produces the coverage-vs-store-count curve: the demand-side (benefit) input that
Phase 5 weighs against per-store costs to find the viable network size.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import PROJECT_ROOT, load_assumptions, get_range
from src.optimize.prep import build_siting_inputs
from src.optimize.mclp import solve_mclp


def sweep_p():
    """Solve the MCLP for each p in the assumptions range; return the curve."""
    points, weights, reachable = build_siting_inputs()
    p_lo, p_hi = get_range(load_assumptions(), "facility_location", "num_nodes_p")
    total = sum(weights.values())

    rows = []
    prev_covered = None
    for p in range(p_lo, p_hi + 1):
        # 0.5% optimality tolerance: near-exact answers in seconds, not minutes.
        chosen, covered = solve_mclp(weights, reachable, p, gap=0.005, time_limit=120)
        # Marginal is undefined for the first p (nothing to compare against).
        marginal = None if prev_covered is None else round(covered - prev_covered)
        rows.append({
            "p": p,
            "covered_catchment": round(covered),
            "coverage_pct": round(covered / total * 100, 1),
            "marginal_catchment": marginal,   # what store #p itself adds
        })
        prev_covered = covered
        extra = f" (+{marginal:,} from this store)" if marginal is not None else ""
        print(f"  p={p:>2}: {covered / total:6.1%} covered{extra}")
    return pd.DataFrame(rows)


if __name__ == "__main__":
    print("Sweeping store count p (one MILP solve per value)...")
    curve = sweep_p()

    out_csv = PROJECT_ROOT / "outputs" / "tables" / "coverage_sweep.csv"
    curve.to_csv(out_csv, index=False)
    print(f"\nSaved curve -> outputs/tables/{out_csv.name}")

    from src.viz.plots import plot_coverage_curve
    fig_path = plot_coverage_curve(curve)
    print(f"Saved chart -> {fig_path}")
