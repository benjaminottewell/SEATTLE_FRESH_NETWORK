''' estimate.py -- Phase 1 demand estimation. This is the first step in the pipeline and turns "people nearby" into "dollars per day" '''
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  
from src.config import load_assumptions, get_value, PROJECT_ROOT
from src.viz.plots import plot_demand_by_neighborhood

def estimate_daily_demand(catchment_population, assumptions):
    """Dollars/day a store earns: population x capture x frequency x ticket."""
    capture_rate = get_value(assumptions, "demand", "capture_rate")
    visit_frequency = get_value(assumptions, "demand", "visit_frequency")
    avg_ticket = get_value(assumptions, "demand", "avg_ticket")

    daily_demand = catchment_population * capture_rate * visit_frequency * avg_ticket
    return daily_demand


def effective_catchment(workers, residents, assumptions):
    """Weighted 'people present' for a neighborhood -- a worker counts more than a resident.

    catchment = worker_weight * workers + resident_weight * residents
    """
    worker_weight = get_value(assumptions, "demand", "worker_weight")
    resident_weight = get_value(assumptions, "demand", "resident_weight")
    return workers * worker_weight + residents * resident_weight


def estimate_area_demand(neighborhoods, assumptions):
    """Estimate daily demand for every neighborhood in the table.

    `neighborhoods` is a DataFrame with the real 'worker_jobs' and 'residents'
    columns. For each row we blend those into a weighted catchment, reuse
    estimate_daily_demand(), then rank neighborhoods by demand.
    """
    result = neighborhoods.copy()
    result["catchment"] = [effective_catchment(w, r, assumptions)
                           for w, r in zip(result["worker_jobs"], result["residents"])]
    result["daily_demand"] = [estimate_daily_demand(c, assumptions) for c in result["catchment"]]
    return result.sort_values("daily_demand", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    a = load_assumptions()

    # Load the neighborhood table (real apportioned census numbers).
    csv_path = PROJECT_ROOT / "data" / "neighborhoods.csv"
    neighborhoods = pd.read_csv(csv_path)

    ranked = estimate_area_demand(neighborhoods, a)

    print("Estimated daily demand by neighborhood (real census data):\n")
    show = ranked[["neighborhood", "worker_jobs", "residents", "catchment", "daily_demand"]].copy()
    show[["catchment", "daily_demand"]] = show[["catchment", "daily_demand"]].round(0)
    print(show.to_string(index=False))

    total = ranked["daily_demand"].sum()
    print(f"\nWhole study area: ${total:,.0f} per day across {len(ranked)} neighborhoods")

    fig_path = plot_demand_by_neighborhood(ranked)
    print(f"Saved chart -> {fig_path}")