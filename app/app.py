"""Interactive siting + economics explorer for the Seattle fresh-network model.

    streamlit run app/app.py

A thin UI over the v1.0 model: pick the store count, walkshed, and economic
levers; the MCLP re-optimizes placement (cached per p/radius) and the P&L
updates live. Exploratory companion to the defended analysis in the README.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.config import load_assumptions, get_value
from src.optimize.mclp import solve_mclp

APP_DIR = Path(__file__).resolve().parent

st.set_page_config(page_title="Seattle Fresh-Network Explorer", layout="wide")


@st.cache_data
def load_inputs():
    pts = pd.read_csv(APP_DIR / "siting_points.csv")
    outlines = json.loads((APP_DIR / "study_area.geojson").read_text(encoding="utf-8"))
    a = load_assumptions()
    fixed = {
        "cogs": get_value(a, "economics", "product_cost_ratio"),
        "spoil": get_value(a, "economics", "spoilage_rate"),
        "rent_day": get_value(a, "economics", "node_rent_per_month") * 12 / 365,
        "hub_day": get_value(a, "economics", "hub_opex_per_day"),
        "capex": get_value(a, "economics", "automation_capex_per_store"),
        "amort_y": get_value(a, "economics", "capex_amortization_years"),
        "delivery_share": 77.0,   # Phase-4 baseline (window-bound, ~demand-invariant)
    }
    return pts, outlines, fixed


@st.cache_data(show_spinner=False)
def optimize(p, radius_m):
    """Solve the MCLP for this p/radius. Cached, so economics sliders are instant."""
    pts, _, _ = load_inputs()
    xy = list(zip(pts["x_utm"], pts["y_utm"]))
    tree = cKDTree(xy)
    reachable = {pid: nbrs for pid, nbrs in
                 zip(pts["pid"], tree.query_ball_point(xy, r=radius_m))}
    weights = dict(zip(pts["pid"], pts["weight"]))
    chosen, covered = solve_mclp(weights, reachable, p, gap=0.01, time_limit=60)

    # Assign each covered corner to its nearest chosen store -> per-store catchment.
    stores = pts[pts["pid"].isin(chosen)].reset_index(drop=True)
    store_tree = cKDTree(list(zip(stores["x_utm"], stores["y_utm"])))
    covered_ids = [i for i in weights if any(j in set(chosen) for j in reachable[i])]
    cov = pts[pts["pid"].isin(covered_ids)]
    _, nearest = store_tree.query(list(zip(cov["x_utm"], cov["y_utm"])))
    catchment = pd.Series(0.0, index=range(len(stores)))
    for s_idx, pid in zip(nearest, cov["pid"]):
        catchment[s_idx] += weights[pid]
    stores["catchment"] = catchment
    return stores, covered, float(sum(weights.values()))


# ---------------- sidebar ----------------
st.sidebar.title("Levers")
p = st.sidebar.slider("Stores (p)", 5, 20, 10)
radius = st.sidebar.slider("Walkshed radius (m)", 200, 600, 400, step=50)
st.sidebar.caption("Changing the two above re-optimizes placement (a few seconds).")
capture = st.sidebar.slider("Capture rate (%)", 1.0, 5.0, 2.5, step=0.1) / 100
ticket = st.sidebar.slider("Avg ticket ($)", 5.0, 10.0, 7.8, step=0.1)
hours = st.sidebar.slider("On-site staff hours/day", 2, 32, 6)
wage = st.sidebar.slider("Wage ($/hr)", 19.0, 26.0, 21.3, step=0.1)

pts, outlines, fx = load_inputs()
with st.spinner(f"Optimizing {p} store placements..."):
    stores, covered, total = optimize(p, radius)

# ---------------- economics (mirrors src/econ/economics.store_pnl) ----------------
stores = stores.copy()
stores["txns_day"] = stores["catchment"] * capture
stores["revenue"] = stores["txns_day"] * ticket
margin = 1 - fx["cogs"] * (1 + fx["spoil"])
amort_day = fx["capex"] / (fx["amort_y"] * 365)
stores["contribution"] = (stores["revenue"] * margin
                          - fx["delivery_share"] - hours * wage)
stores["fully_loaded"] = (stores["contribution"] - fx["rent_day"]
                          - fx["hub_day"] / p - amort_day)

# ---------------- header + metrics ----------------
st.title("Seattle Fresh-Network Explorer")
st.caption("Exploratory companion to the v1.0 feasibility model — see the README for "
           "the defended analysis, sources, and the pre-registered feasibility bar.")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Catchment covered", f"{covered / total:.0%}",
          help="Share of the weighted daytime population (workers + 0.5×residents) "
               "within a walkshed of at least one store.")
c2.metric("Network revenue", f"${stores['revenue'].sum():,.0f}/day",
          help="Covered catchment × capture rate × average ticket, summed over stores.")
c3.metric("Stores with contribution > 0", f"{int((stores['contribution'] > 0).sum())} of {p}",
          help="Contribution = revenue − product cost (incl. spoilage) − delivery share "
               "− on-site labor. The study's pre-registered feasibility bar.")
c4.metric("Fully-loaded positive", f"{int((stores['fully_loaded'] > 0).sum())} of {p}",
          help="Contribution minus the fixed stack: rent, the store's share of commissary "
               "(hub) operating cost, and automation capex amortized over 7 years. "
               "The 'all costs in' operator view.")
c5.metric("Median store, fully loaded", f"${stores['fully_loaded'].median():,.0f}/day",
          help="The middle store's daily profit with all costs in — the number the "
               "study's verdict thresholds are quoted on.")

with st.expander("What do 'contribution' and 'fully loaded' mean?"):
    st.markdown(
        "Each store's daily P&L is computed two ways:\n\n"
        "1. **Contribution** *(the pre-registered feasibility bar)* — does the store "
        "cover the costs that scale with running it?\n"
        "`revenue − product cost×(1+spoilage) − delivery share − staff hours×wage`\n\n"
        "2. **Fully loaded** *(the operator view)* — subtract the fixed stack too:\n"
        "`contribution − rent − hub-opex share (split across stores) − capex/7yr`\n\n"
        "A store can clear the contribution bar yet lose money fully loaded — that gap "
        "is exactly where the joint-pessimism stress case kills the network (see the "
        "README verdict and `reports/findings.md`).")

# ---------------- map ----------------
stores["viable"] = stores["fully_loaded"] > 0
stores["color"] = stores["viable"].map(lambda v: [22, 140, 60] if v else [193, 18, 31])
demand = pts.copy()
demand["r"] = np.clip(np.sqrt(demand["weight"]) * 2.2, 6, 55)

layers = [
    pdk.Layer("GeoJsonLayer", outlines, stroked=True, filled=False,
              get_line_color=[60, 60, 60], line_width_min_pixels=1.5),
    pdk.Layer("ScatterplotLayer", demand, get_position="[lon, lat]",
              get_radius="r", get_fill_color=[74, 111, 165, 90]),
    pdk.Layer("ScatterplotLayer", stores, get_position="[lon, lat]",
              get_radius=radius, get_fill_color=[228, 87, 46, 35],
              stroked=True, get_line_color=[228, 87, 46, 160], line_width_min_pixels=1),
    pdk.Layer("ScatterplotLayer", stores, get_position="[lon, lat]",
              get_radius=28, get_fill_color="color", pickable=True),
]
tooltip = {"html": "<b>Store</b><br>catchment {catchment}<br>"
                   "fully loaded $/day: {fully_loaded}"}
st.pydeck_chart(pdk.Deck(
    layers=layers, tooltip=tooltip,
    initial_view_state=pdk.ViewState(latitude=47.608, longitude=-122.332, zoom=12.2),
    map_style="light"))
st.caption("Blue dots = demand at street corners (size = catchment). Circles = chosen "
           "store walksheds. Store dots: green = fully-loaded positive, red = losing money.")

# ---------------- per-store table ----------------
show = stores[["txns_day", "revenue", "contribution", "fully_loaded"]].copy()
show = show.sort_values("contribution", ascending=False).round(0).reset_index(drop=True)
show.index = [f"store {i + 1}" for i in show.index]
st.dataframe(show, width="stretch")
st.caption("Delivery share fixed at the Phase-4 baseline ($77/store-day; the fleet is "
           "freshness-window-bound, so it is ~insensitive to demand volume). Rent, hub "
           "opex, and capex amortization from assumptions.yaml.")
