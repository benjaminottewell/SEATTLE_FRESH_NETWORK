"""stress.py -- Phase 5 stress case: what survives if we're wrong about everything at once?

The sensitivity sweeps vary ONE parameter at a time, which quietly assumes failures
arrive alone. They don't -- bad worlds correlate (soft demand, high rent, rising wages
tend to co-occur). This scenario sets every starred economic lever to a jointly
adverse-but-plausible value and reports what remains of the network.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import PROJECT_ROOT, load_assumptions
from src.econ.economics import baseline_stores, delivery_cost_per_store, store_pnl

# Adverse-but-plausible, applied JOINTLY. Each stays inside its swept range.
STRESS = {
    ("demand", "capture_rate"): 0.015,            # baseline 0.025
    ("economics", "node_rent_per_month"): 12000,  # baseline 8000 (+50%)
    ("economics", "spoilage_rate"): 0.15,         # baseline 0.08 (range max)
    ("economics", "labor_wage_per_hour"): 26.0,   # baseline 21.30 (range max)
}


def stressed_assumptions():
    a = load_assumptions()
    for (section, name), value in STRESS.items():
        a[section][name]["value"] = value
    return a


if __name__ == "__main__":
    base = load_assumptions()
    a = stressed_assumptions()

    stores = baseline_stores(a)                 # siting is capture-invariant
    delivery = delivery_cost_per_store(a)       # window-bound, unchanged by demand
    pnl = store_pnl(stores, a, delivery).sort_values("contribution", ascending=False)
    base_pnl = store_pnl(stores, base, delivery)

    print("\nSTRESS CASE -- all four levers jointly adverse:")
    for (s, n), v in STRESS.items():
        print(f"  {s}.{n}: {base[s][n]['value']} -> {v}")

    cols = ["txns_day", "revenue", "contribution", "fully_loaded"]
    show = pnl[cols].round(0).reset_index(drop=True)
    show.index = [f"store {i + 1}" for i in show.index]
    print("\nPer-store daily P&L under stress:\n")
    print(show.to_string())

    n_bar = int(pnl["clears_bar"].sum())
    n_full = int((pnl["fully_loaded"] > 0).sum())
    net = pnl["fully_loaded"].sum()
    print(f"\nPre-registered bar (contribution > 0) : {n_bar} of {len(pnl)}  "
          f"(baseline: {int(base_pnl['clears_bar'].sum())})")
    print(f"Fully loaded positive                  : {n_full} of {len(pnl)}  "
          f"(baseline: {int((base_pnl['fully_loaded'] > 0).sum())})")
    print(f"NETWORK fully-loaded total             : ${net:,.0f}/day  "
          f"(baseline: ${base_pnl['fully_loaded'].sum():,.0f}/day)")

    out = PROJECT_ROOT / "outputs" / "tables" / "stress_case.csv"
    pnl.drop(columns="geometry").round(1).to_csv(out, index=False)
    print(f"\nSaved -> outputs/tables/{out.name}")
