"""economics.py -- Phase 5: per-store unit economics against the pre-registered bar.

PRIMARY BAR (pre-registered in assumptions.yaml before any results were run):
contribution margin per node > 0, where contribution = revenue - product cost
(incl. spoilage) - delivery share - direct labor. Rent, hub allocation, and
amortized capex are reported in a secondary "fully loaded" view plus payback,
per the registered secondary lens.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import PROJECT_ROOT, load_assumptions, get_value
from src.optimize.prep import build_siting_inputs
from src.optimize.mclp import solve_mclp
from src.optimize.routing import store_demand_per_run


def baseline_stores(a=None):
    """Run the siting chain once; return stores with their assigned catchment.

    Catchment (not transactions) is the stable quantity -- capture_rate turns it
    into transactions later, so sensitivity sweeps don't need to re-site.
    """
    if a is None:
        a = load_assumptions()
    p = get_value(a, "facility_location", "num_nodes_p")
    points, weights, reachable = build_siting_inputs()
    chosen, _ = solve_mclp(weights, reachable, p, gap=0.005, time_limit=120)
    stores = store_demand_per_run(points, weights, reachable, chosen, a)
    capture = get_value(a, "demand", "capture_rate")
    stores["catchment"] = stores["txns_day"] / capture   # undo capture -> raw catchment
    return stores[["pid", "catchment", "geometry"]]


def delivery_cost_per_store(a):
    """Per-store daily delivery share from the Phase-4 routing run (equal split v1)."""
    csv = PROJECT_ROOT / "outputs" / "tables" / "routing_summary.csv"
    if not csv.exists():
        raise FileNotFoundError("Run src/optimize/routing.py first (routing_summary.csv missing).")
    return float(pd.read_csv(csv)["daily_cost_per_store"].iloc[0])


def store_pnl(stores, a, delivery_share, capture=None, staff_hours=None):
    """Daily P&L per store. Optional overrides let sensitivity sweeps vary levers cheaply."""
    capture = capture if capture is not None else get_value(a, "demand", "capture_rate")
    staff_hours = staff_hours if staff_hours is not None else get_value(a, "economics", "staff_hours_per_day")

    ticket = get_value(a, "demand", "avg_ticket")
    freq = get_value(a, "demand", "visit_frequency")
    cogs_ratio = get_value(a, "economics", "product_cost_ratio")
    spoil = get_value(a, "economics", "spoilage_rate")
    wage = get_value(a, "economics", "labor_wage_per_hour")
    rent_day = get_value(a, "economics", "node_rent_per_month") * 12 / 365
    hub_share = get_value(a, "economics", "hub_opex_per_day") / len(stores)
    capex = get_value(a, "economics", "automation_capex_per_store")
    amort_day = capex / (get_value(a, "economics", "capex_amortization_years") * 365)

    df = stores.copy()
    df["txns_day"] = df["catchment"] * capture * freq
    df["revenue"] = df["txns_day"] * ticket
    df["product_cost"] = df["revenue"] * cogs_ratio * (1 + spoil)  # buy more than you sell
    df["labor"] = staff_hours * wage
    df["delivery"] = delivery_share
    df["contribution"] = df["revenue"] - df["product_cost"] - df["delivery"] - df["labor"]
    df["fully_loaded"] = df["contribution"] - rent_day - hub_share - amort_day
    df["clears_bar"] = df["contribution"] > 0
    # Payback: years of pre-capex cash flow to repay the store's capex.
    # Undefined (NA) for stores that never earn their costs back.
    cash_day = df["fully_loaded"] + amort_day
    df["payback_years"] = (capex / cash_day / 365).where(cash_day > 0)
    return df


if __name__ == "__main__":
    a = load_assumptions()
    stores = baseline_stores(a)
    delivery = delivery_cost_per_store(a)
    pnl = store_pnl(stores, a, delivery)

    unit_margin = 1 - get_value(a, "economics", "product_cost_ratio") * \
        (1 + get_value(a, "economics", "spoilage_rate"))
    ticket = get_value(a, "demand", "avg_ticket")
    fixed_contrib = pnl["labor"].iloc[0] + delivery
    breakeven_txns = fixed_contrib / (ticket * unit_margin)

    show = pnl[["txns_day", "revenue", "product_cost", "labor", "delivery",
                "contribution", "fully_loaded", "payback_years"]].round(
        {"txns_day": 0, "revenue": 0, "product_cost": 0, "labor": 0, "delivery": 0,
         "contribution": 0, "fully_loaded": 0, "payback_years": 1})
    show = show.sort_values("contribution", ascending=False).reset_index(drop=True)
    show.index = [f"store {i + 1}" for i in show.index]
    print("\nPer-store daily P&L (baseline assumptions):\n")
    print(show.to_string())

    n_bar = int(pnl["clears_bar"].sum())
    n_full = int((pnl["fully_loaded"] > 0).sum())
    print(f"\nPRE-REGISTERED BAR (contribution > 0): {n_bar} of {len(pnl)} stores clear it")
    print(f"Fully loaded (rent + hub share + capex): {n_full} of {len(pnl)} stores positive")
    print(f"Break-even (contribution bar): {breakeven_txns:,.0f} transactions/day per store")
    med_payback = pnl.loc[pnl['fully_loaded'] > 0, 'payback_years'].median()
    print(f"Median payback among viable stores: {med_payback:.1f} years")

    out = PROJECT_ROOT / "outputs" / "tables" / "store_pnl_baseline.csv"
    pnl.drop(columns="geometry").round(1).to_csv(out, index=False)
    print(f"\nSaved -> outputs/tables/{out.name}")
