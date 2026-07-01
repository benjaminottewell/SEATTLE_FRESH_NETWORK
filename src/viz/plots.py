"""plots.py -- reusable, readable charts & maps. Saves figures to outputs/figures/.

Every figure goes through set_plot_style() so the whole project shares one clean,
legible look (big fonts, white background, high resolution).
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")              # render straight to a file (no popup window)
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import PROJECT_ROOT

FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"
BAR_COLOR = "#4227b8"


def set_plot_style():
    """Readable, consistent defaults applied to every figure in the project."""
    plt.rcParams.update({
        "figure.dpi": 130,
        "savefig.dpi": 200,            # crisp exported images
        "savefig.bbox": "tight",
        "figure.facecolor": "white",
        "font.size": 13,
        "axes.titlesize": 19,
        "axes.titleweight": "bold",
        "axes.labelsize": 14,
    })


def plot_study_area(hoods, output_path=None, basemap=True):
    """Clean map of the study-area neighborhoods: numbered badges + a legend.

    `hoods` is the GeoDataFrame from fetch_study_neighborhoods(). Each neighborhood
    gets a small numbered marker on the map; a legend (dropped over the empty water)
    maps numbers to names. A light street basemap underneath gives context.
    """
    import matplotlib.patches as mpatches

    set_plot_style()
    if output_path is None:
        output_path = FIGURES_DIR / "study_neighborhoods.png"

    # Web Mercator (EPSG:3857) so a street basemap lines up underneath.
    g = hoods.to_crs(3857).copy()
    # Number the neighborhoods north -> south so the badges read top-to-bottom.
    g["_y"] = g.geometry.representative_point().y
    g = g.sort_values("_y", ascending=False).reset_index(drop=True)
    g["num"] = g.index + 1
    colors = [plt.get_cmap("tab10")(i) for i in range(len(g))]

    fig, ax = plt.subplots(figsize=(12, 12))
    g.plot(ax=ax, color=colors, alpha=0.55, edgecolor="white", linewidth=2.5)

    for _, row in g.iterrows():
        pt = row.geometry.representative_point()
        ax.annotate(str(row["num"]), (pt.x, pt.y), ha="center", va="center",
                    fontsize=15, fontweight="bold", zorder=5,
                    bbox=dict(boxstyle="circle,pad=0.3", fc="white", ec="black", lw=1.5))

    if basemap:
        try:
            import contextily as cx
            cx.add_basemap(ax, source=cx.providers.CartoDB.Positron)
        except Exception as e:
            print(f"(basemap skipped: {e})")

    handles = [mpatches.Patch(facecolor=colors[i], alpha=0.7, edgecolor="white",
                              label=f"{row['num']}.  {row['neighborhood']}")
               for i, row in g.iterrows()]
    # Place the legend OUTSIDE the map (below it) so it never covers a neighborhood.
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.02),
              ncol=2, fontsize=12, frameon=True, framealpha=0.95, borderpad=0.9,
              labelspacing=0.6, columnspacing=1.5, title="Neighborhood", title_fontsize=14)

    ax.set_title("Study area — 7 northern-core neighborhoods", pad=14)
    ax.axis("off")
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def plot_demand_by_neighborhood(ranked, output_path=None):
    """Readable horizontal bar chart of estimated daily demand per neighborhood."""
    set_plot_style()
    if output_path is None:
        output_path = FIGURES_DIR / "demand_by_neighborhood.png"

    data = ranked.sort_values("daily_demand")   # ascending -> largest ends up on top

    fig, ax = plt.subplots(figsize=(11, 7))
    bars = ax.barh(data["neighborhood"], data["daily_demand"], color=BAR_COLOR)
    ax.bar_label(bars, labels=[f"${v:,.0f}" for v in data["daily_demand"]],
                 padding=6, fontsize=12)
    ax.set_xlabel("Estimated demand  ($ / day)")
    ax.set_title("Daily demand by neighborhood")
    ax.margins(x=0.13)                  # leave room for the value labels
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def plot_tract_assignment(tracts, hoods, output_path=None, basemap=True):
    """Verification map: census tracts colored by their assigned neighborhood.

    Black neighborhood outlines are drawn on top -- if the assignment is right,
    each colored cluster of tracts sits neatly inside its outline.
    """
    import matplotlib.patches as mpatches

    set_plot_style()
    if output_path is None:
        output_path = FIGURES_DIR / "tracts_assigned.png"

    t = tracts.to_crs(3857)
    h = hoods.to_crs(3857)

    names = sorted(t["neighborhood"].unique())
    cmap = plt.get_cmap("tab10")
    color_for = {n: cmap(i) for i, n in enumerate(names)}

    fig, ax = plt.subplots(figsize=(12, 12))
    t.plot(ax=ax, color=t["neighborhood"].map(color_for), alpha=0.6,
           edgecolor="white", linewidth=0.6)
    h.boundary.plot(ax=ax, color="black", linewidth=2)   # outlines on top to check the tracts nest inside

    if basemap:
        try:
            import contextily as cx
            cx.add_basemap(ax, source=cx.providers.CartoDB.Positron)
        except Exception as e:
            print(f"(basemap skipped: {e})")

    handles = [mpatches.Patch(facecolor=color_for[n], alpha=0.7, edgecolor="white", label=n)
               for n in names]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.02),
              ncol=2, fontsize=12, frameon=True, framealpha=0.95, borderpad=0.9,
              title="Tract assigned to", title_fontsize=14)

    ax.set_title("Centroid-method diagnostic — gaps show why we apportion by area", pad=14)
    ax.axis("off")
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def plot_store_sites(points, chosen_ids, hoods, radius_m, output_path=None, basemap=True):
    """Map of MCLP-chosen store sites with their walkshed coverage circles.

    `points` are the demand/candidate corners (meters CRS) with pid + weight;
    dot size scales with demand weight so the coverage logic is visible.
    """
    import geopandas as gpd
    import numpy as np
    import matplotlib.lines as mlines
    import matplotlib.patches as mpatches

    set_plot_style()
    if output_path is None:
        output_path = FIGURES_DIR / "store_sites.png"

    pts = points.to_crs(3857)
    hd = hoods.to_crs(3857)
    chosen = points[points["pid"].isin(chosen_ids)]
    walksheds = gpd.GeoSeries(chosen.geometry.buffer(radius_m), crs=points.crs).to_crs(3857)
    chosen = chosen.to_crs(3857)

    fig, ax = plt.subplots(figsize=(12, 12))
    ax.scatter(pts.geometry.x, pts.geometry.y, s=np.clip(pts["weight"] / 25, 2, 70),
               color="#4a6fa5", alpha=0.45, linewidths=0, zorder=2)
    hd.boundary.plot(ax=ax, color="black", linewidth=1.2, zorder=3)
    walksheds.plot(ax=ax, facecolor="#e4572e", alpha=0.18, edgecolor="#e4572e",
                   linewidth=1.5, zorder=4)
    ax.scatter(chosen.geometry.x, chosen.geometry.y, s=260, marker="*",
               color="#c1121f", edgecolor="white", linewidth=1, zorder=5)

    if basemap:
        try:
            import contextily as cx
            cx.add_basemap(ax, source=cx.providers.CartoDB.Positron)
        except Exception as e:
            print(f"(basemap skipped: {e})")

    handles = [
        mlines.Line2D([], [], color="#4a6fa5", marker="o", linestyle="", alpha=0.6,
                      markersize=8, label="Demand at corners (size = catchment)"),
        mlines.Line2D([], [], color="#c1121f", marker="*", linestyle="",
                      markersize=16, label="Chosen store site"),
        mpatches.Patch(facecolor="#e4572e", alpha=0.25, edgecolor="#e4572e",
                       label=f"{radius_m} m walkshed"),
    ]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.02),
              fontsize=12, frameon=True, framealpha=0.95, borderpad=0.9)
    ax.set_title(f"Optimized store placement ({len(chosen_ids)} sites, MCLP)", pad=14)
    ax.axis("off")
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def plot_hub_routes(G, routes, hub_latlon, output_path=None):
    """Map of fastest delivery routes from the SoDo hub to each neighborhood.

    `routes` is a dict {neighborhood: node list} from hub_drive_times(). The
    street grid is drawn light gray as its own context (no basemap needed);
    each route gets a color, the hub a black star.
    """
    import osmnx as ox
    import matplotlib.lines as mlines

    set_plot_style()
    if output_path is None:
        output_path = FIGURES_DIR / "hub_routes.png"

    fig, ax = ox.plot_graph(G, show=False, close=False, figsize=(12, 12),
                            bgcolor="white", node_size=0,
                            edge_color="#d9d9d9", edge_linewidth=0.4)

    cmap = plt.get_cmap("tab10")
    handles = []
    for i, (name, route) in enumerate(routes.items()):
        edges = ox.routing.route_to_gdf(G, route)
        edges.plot(ax=ax, color=cmap(i), linewidth=3, alpha=0.85, zorder=3)
        handles.append(mlines.Line2D([], [], color=cmap(i), linewidth=3, label=name))

    hub_lat, hub_lon = hub_latlon
    ax.scatter([hub_lon], [hub_lat], s=350, marker="*", color="black", zorder=5)
    handles.append(mlines.Line2D([], [], color="black", marker="*", linestyle="",
                                 markersize=16, label="SoDo production hub"))

    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.02),
              ncol=2, fontsize=12, frameon=True, framealpha=0.95, borderpad=0.9,
              title="Fastest route to", title_fontsize=14)
    ax.set_title("Fresh-delivery routes from the SoDo hub", pad=14)
    fig.savefig(output_path)
    plt.close(fig)
    return output_path
