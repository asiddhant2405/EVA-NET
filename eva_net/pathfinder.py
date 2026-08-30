"""
EVA-NET Step 5 — Path Calculation & UI Rendering
==================================================
Implements A* / Dijkstra pathfinding on the dynamically
reweighted graph, targeting < 50ms recalculation.

Includes Folium integration for real-time route visualization
with rich interactive popups featuring shelter owner contacts,
emergency radio frequencies, capacity bars, and hazard intelligence.
"""

from __future__ import annotations

import math
import os
import time
from typing import Optional

import folium
import networkx as nx
import numpy as np

from . import config
from .hazard_delta import HazardType


# ═══════════════════════════════════════════════════════════════════
# PATH CALCULATION
# ═══════════════════════════════════════════════════════════════════


def _euclidean_heuristic(G: nx.DiGraph, target: str):
    """
    Create an A* heuristic function using Euclidean distance in meters.
    """
    target_data = G.nodes[target]
    t_lat, t_lon = target_data["lat"], target_data["lon"]

    def heuristic(n, _target):
        n_data = G.nodes[n]
        dlat = (n_data["lat"] - t_lat) / config.DEG_LAT_PER_M
        dlon = (n_data["lon"] - t_lon) / config.DEG_LON_PER_M
        return math.sqrt(dlat**2 + dlon**2)

    return heuristic


def find_shortest_path(
    G: nx.DiGraph,
    source: str,
    target: str,
    algorithm: str = "astar",
) -> tuple[list[str], float, float]:
    """
    Find shortest path on the current weighted graph.

    Uses A* with Euclidean heuristic (preferred) or Dijkstra fallback.
    Measures execution time to verify < 50ms target.

    Parameters
    ----------
    G : nx.DiGraph
        The city grid with current_weight on edges.
    source : str
        Source node ID.
    target : str
        Target node ID.
    algorithm : str
        "astar" or "dijkstra".

    Returns
    -------
    tuple[list[str], float, float]
        (path_nodes, total_cost, computation_time_ms)
    """
    start_ns = time.perf_counter_ns()

    try:
        if algorithm == "astar":
            heuristic = _euclidean_heuristic(G, target)
            path = nx.astar_path(
                G, source, target,
                heuristic=heuristic,
                weight="current_weight",
            )
            cost = nx.astar_path_length(
                G, source, target,
                heuristic=heuristic,
                weight="current_weight",
            )
        else:
            path = nx.dijkstra_path(G, source, target, weight="current_weight")
            cost = nx.dijkstra_path_length(G, source, target, weight="current_weight")

    except nx.NetworkXNoPath:
        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
        return [], float("inf"), elapsed_ms

    elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
    return path, cost, elapsed_ms


def benchmark_pathfinding(
    G: Optional[nx.DiGraph] = None,
    n_trials: int = 100,
) -> dict:
    """
    Benchmark pathfinding performance to verify < 50ms target.
    """
    if G is None:
        from .spatial_graph import create_city_grid
        G = create_city_grid()

    nodes = list(G.nodes)
    times = []

    import random
    random.seed(42)

    for _ in range(n_trials):
        src, tgt = random.sample(nodes, 2)
        _, _, elapsed = find_shortest_path(G, src, tgt)
        times.append(elapsed)

    results = {
        "trials": n_trials,
        "mean_ms": round(float(np.mean(times)), 3),
        "max_ms": round(float(max(times)), 3),
        "min_ms": round(float(min(times)), 3),
        "p95_ms": round(float(np.percentile(times, 95)), 3),
        "p99_ms": round(float(np.percentile(times, 99)), 3),
        "under_50ms": sum(1 for t in times if t < 50),
    }

    print("╔══════════════════════════════════════════════════════╗")
    print("║          A* Pathfinding Benchmark Results            ║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"║  Trials         : {results['trials']:>30}  ║")
    print(f"║  Mean latency   : {results['mean_ms']:>27.3f} ms  ║")
    print(f"║  P95 latency    : {results['p95_ms']:>27.3f} ms  ║")
    print(f"║  P99 latency    : {results['p99_ms']:>27.3f} ms  ║")
    print(f"║  Max latency    : {results['max_ms']:>27.3f} ms  ║")
    print(f"║  Under 50ms     : {results['under_50ms']:>26}/{n_trials}  ║")
    print("╚══════════════════════════════════════════════════════╝")

    return results


# ═══════════════════════════════════════════════════════════════════
# FOLIUM UI RENDERING
# ═══════════════════════════════════════════════════════════════════

COLORS = {
    "road_normal": "#4A90E2",
    "road_hazard_partial": "#FF9800",
    "road_blocked": "#E53935",
    "path_safe": "#00E676",
    "path_rerouted": "#FFD600",
    "agent_active": "#00B0FF",
    "agent_sheltered": "#00E676",
    "shelter": "#00C853",
    "fire": "#FF3D00",
    "flood": "#2979FF",
}

HAZARD_ICONS = {
    "WILDFIRE": "fire",
    "FLASH_FLOOD": "tint",
    "FALLEN_TREE": "tree",
    "ROAD_COLLAPSE": "road",
    "DEBRIS": "warning-sign",
    "POWER_LINE": "flash",
}


def _create_shelter_popup_html(sinfo: dict, nid: str) -> str:
    """Create rich, beautifully styled HTML popup for shelters."""
    if not sinfo:
        return f"<b>🏥 Emergency Shelter</b><br>ID: {nid}"

    name = sinfo.get("name", "Emergency Shelter")
    stype = sinfo.get("type", "Evacuation Facility")
    addr = sinfo.get("address", "Lahaina, HI")
    owner = sinfo.get("owner", "Maui Disaster Agency")
    phone = sinfo.get("phone", "(808) 661-4685")
    alt_phone = sinfo.get("alt_phone", "(808) 270-7285")
    radio = sinfo.get("radio_freq", "VHF 155.055 MHz")
    cap_tot = sinfo.get("capacity_total", 500)
    cap_occ = sinfo.get("capacity_occupied", 180)
    avail = cap_tot - cap_occ
    pct = int((cap_occ / cap_tot) * 100) if cap_tot else 0
    supplies = sinfo.get("supplies", [])
    supplies_html = "".join([f"<li>✓ {s}</li>" for s in supplies[:4]])

    return f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; width: 280px; padding: 4px; color: #1e293b;">
        <div style="background: #0f172a; color: #fff; padding: 10px 12px; border-radius: 6px 6px 0 0; margin: -5px -5px 10px -5px;">
            <span style="background: #10b981; color: #fff; font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px; text-transform: uppercase;">
                SAFE SHELTER
            </span>
            <h4 style="margin: 6px 0 2px 0; font-size: 14px; font-weight: 700; color: #f8fafc;">{name}</h4>
            <div style="font-size: 11px; color: #94a3b8;">{stype}</div>
        </div>
        
        <div style="font-size: 12px; margin-bottom: 8px;">
            <div style="margin-bottom: 4px;">📍 <b>Address:</b> {addr}</div>
            <div style="margin-bottom: 4px;">👤 <b>Shelter Lead:</b> {owner}</div>
            <div style="margin-bottom: 4px;">📞 <b>Emergency Phone:</b> <a href="tel:{phone}" style="color: #0284c7; font-weight: bold; text-decoration: none;">{phone}</a> (Alt: {alt_phone})</div>
            <div style="margin-bottom: 4px;">📻 <b>Radio Net:</b> <code style="background: #e2e8f0; padding: 2px 4px; border-radius: 3px; font-size: 11px;">{radio}</code></div>
        </div>

        <div style="background: #f1f5f9; padding: 8px; border-radius: 6px; margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; font-size: 11px; font-weight: 600; margin-bottom: 4px;">
                <span>Bed Capacity</span>
                <span style="color: #059669;">{avail} Available ({pct}% Full)</span>
            </div>
            <div style="background: #cbd5e1; height: 7px; border-radius: 4px; overflow: hidden;">
                <div style="background: #10b981; width: {pct}%; height: 100%;"></div>
            </div>
        </div>

        <div style="font-size: 11px; color: #475569;">
            <b>Supplies & Facilities:</b>
            <ul style="margin: 4px 0 0 16px; padding: 0; line-height: 1.4;">
                {supplies_html}
            </ul>
        </div>
    </div>
    """


def render_map(
    G: nx.DiGraph,
    agents: list = None,
    paths: dict = None,
    tick: int = 0,
    sim_time: float = 0.0,
    filename: Optional[str] = None,
) -> folium.Map:
    """
    Render the full EVA-NET simulation state on an actual map of Lahaina, Maui.
    Includes rich interactive popup cards with contact details, radio frequencies,
    capacity, and dual route visualization.
    """
    if agents is None:
        agents = []
    if paths is None:
        paths = {}

    # Center map on the Lahaina grid
    center_lat = np.mean([d["lat"] for _, d in G.nodes(data=True)])
    center_lon = np.mean([d["lon"] for _, d in G.nodes(data=True)])

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=15,
        tiles="cartodbdark_matter",
        attr="EVA-NET Disaster Evacuation System",
    )

    # ── Layer: Road Network ───────────────────────────────────────
    road_layer = folium.FeatureGroup(name="🛣️ Road Network & Streets", show=True)

    for u, v, data in G.edges(data=True):
        u_data, v_data = G.nodes[u], G.nodes[v]
        coords = [[u_data["lat"], u_data["lon"]], [v_data["lat"], v_data["lon"]]]
        st_name = data.get("street_name", "Street")

        if math.isinf(data["current_weight"]):
            color = COLORS["road_blocked"]
            weight = 4
            opacity = 0.9
            dash = "8 4"
            status_tag = "⛔ BLOCKED BY DISASTER"
        elif data["hazard_type"] is not None:
            color = COLORS["road_hazard_partial"]
            weight = 3
            opacity = 0.8
            dash = "5 3"
            status_tag = f"⚠️ HAZARD: {data['hazard_type']}"
        else:
            color = COLORS["road_normal"]
            weight = 2.5
            opacity = 0.45
            dash = None
            status_tag = "✅ CLEAR"

        line = folium.PolyLine(
            coords,
            color=color,
            weight=weight,
            opacity=opacity,
            dash_array=dash,
            tooltip=f"<b>{st_name}</b><br>{status_tag}<br>Length: {data['length_m']:.0f}m",
        )
        line.add_to(road_layer)

    road_layer.add_to(m)

    # ── Layer: Hazard Zones ───────────────────────────────────────
    hazard_layer = folium.FeatureGroup(name="⚠️ Active Hazards & Fires", show=True)
    hazard_edges_seen = set()

    for u, v, data in G.edges(data=True):
        if data["hazard_type"] is not None and data["edge_id"] not in hazard_edges_seen:
            hazard_edges_seen.add(data["edge_id"])
            u_data, v_data = G.nodes[u], G.nodes[v]
            mid_lat = (u_data["lat"] + v_data["lat"]) / 2
            mid_lon = (u_data["lon"] + v_data["lon"]) / 2

            htype = data["hazard_type"]
            icon_name = HAZARD_ICONS.get(htype, "warning-sign")
            icon_color = "red" if htype in ("WILDFIRE", "FLASH_FLOOD", "ROAD_COLLAPSE") else "orange"
            conf = data.get("hazard_confidence", 0.9) * 100

            hazard_popup = f"""
            <div style="font-family: 'Segoe UI', Arial, sans-serif; width: 220px; padding: 4px;">
                <h4 style="margin: 0 0 6px 0; color: #dc2626; font-size: 13px;">🚨 {htype}</h4>
                <div style="font-size: 11px; line-height: 1.4;">
                    <div><b>Location:</b> {data.get('street_name', 'Street')}</div>
                    <div><b>Mesh Confidence:</b> <span style="color: #059669; font-weight: bold;">{conf:.0f}% Verified</span></div>
                    <div><b>Status:</b> Road Impassable</div>
                    <div><b>EVA-NET Action:</b> Mesh Reroute Active</div>
                </div>
            </div>
            """

            folium.Marker(
                location=[mid_lat, mid_lon],
                icon=folium.Icon(icon=icon_name, prefix="glyphicon", color=icon_color),
                popup=folium.Popup(hazard_popup, max_width=250),
                tooltip=f"🚨 {htype} — Click for intel",
            ).add_to(hazard_layer)

    hazard_layer.add_to(m)

    # ── Layer: Shelters with Rich Popups ──────────────────────────
    shelter_layer = folium.FeatureGroup(name="🏥 Emergency Safe Shelters", show=True)

    for nid, ndata in G.nodes(data=True):
        if ndata.get("is_shelter"):
            sinfo = ndata.get("shelter_info") or {}
            popup_html = _create_shelter_popup_html(sinfo, nid)

            folium.Marker(
                location=[ndata["lat"], ndata["lon"]],
                icon=folium.Icon(icon="home", prefix="glyphicon", color="green", icon_color="white"),
                popup=folium.Popup(popup_html, max_width=320),
                tooltip=f"🏥 {ndata.get('name', 'Safe Shelter')} (Click for Owner & Contact info)",
            ).add_to(shelter_layer)

    shelter_layer.add_to(m)

    # ── Layer: Evacuation Routes ──────────────────────────────────
    path_layer = folium.FeatureGroup(name="🗺️ Dynamic Evacuation Routes", show=True)

    color_cycle = [
        "#00E676", "#00BCD4", "#FFEA00", "#E040FB",
        "#FF9100", "#76FF03", "#00E5FF", "#69F0AE",
    ]

    for idx, (agent_id, path) in enumerate(paths.items()):
        if len(path) < 2:
            continue

        path_coords = []
        for node_id in path:
            ndata = G.nodes[node_id]
            path_coords.append([ndata["lat"], ndata["lon"]])

        color = color_cycle[idx % len(color_cycle)]

        folium.PolyLine(
            path_coords,
            color=color,
            weight=4,
            opacity=0.85,
            tooltip=f"🟢 EVA-NET Safest Route: {agent_id} ({len(path)} waypoints)",
            dash_array="8 4",
        ).add_to(path_layer)

    path_layer.add_to(m)

    # ── Layer: Agents ─────────────────────────────────────────────
    agent_layer = folium.FeatureGroup(name="👤 Evacuee Devices (Mesh Peers)", show=True)

    for agent in agents:
        status_str = "✅ SAFELY SHELTERED" if agent.reached_shelter else "🚶 EVACUATING"
        status_color = "#00E676" if agent.reached_shelter else "#00B0FF"

        agent_popup = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; width: 220px; padding: 4px;">
            <h4 style="margin: 0 0 6px 0; color: #0284c7; font-size: 13px;">👤 {agent.agent_id}</h4>
            <div style="font-size: 11px; line-height: 1.4;">
                <div><b>Status:</b> <span style="color: {status_color}; font-weight: bold;">{status_str}</span></div>
                <div><b>Current Node:</b> {agent.current_node}</div>
                <div><b>Target Shelter:</b> {agent.target_node}</div>
                <div><b>P2P Mesh Encounters:</b> {agent.p2p_encounters} peers</div>
                <div><b>Dynamic Reroutes:</b> {agent.reroute_count} times</div>
                <div><b>Known Hazard Diffs:</b> {len(agent.known_diffs)}</div>
            </div>
        </div>
        """

        folium.CircleMarker(
            location=[agent.lat, agent.lon],
            radius=6.5,
            color=COLORS["agent_active"] if not agent.reached_shelter else COLORS["agent_sheltered"],
            fill=True,
            fill_opacity=0.9,
            popup=folium.Popup(agent_popup, max_width=250),
            tooltip=f"👤 {agent.agent_id} [{status_str}] — Click for device state",
        ).add_to(agent_layer)

    agent_layer.add_to(m)

    # ── Controls & UI Overlay ─────────────────────────────────────
    folium.LayerControl(collapsed=False).add_to(m)

    safe_count = sum(1 for a in agents if a.reached_shelter)
    legend_html = f"""
    <div style="
        position: fixed; bottom: 20px; left: 20px; z-index: 1000;
        background: rgba(15, 23, 42, 0.92); color: #f8fafc; padding: 16px 20px;
        border-radius: 12px; font-family: 'Segoe UI', -apple-system, sans-serif;
        font-size: 13px; backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.15);
        box-shadow: 0 12px 32px rgba(0,0,0,0.4); max-width: 320px;
    ">
        <div style="font-size: 15px; font-weight: 800; margin-bottom: 8px;
                     background: linear-gradient(90deg, #00E676, #00B0FF);
                     -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 0.5px;">
            🛰️ EVA-NET LAHAINA SIMULATION
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span>⏱️ Elapsed: <b>{sim_time:.0f}s</b> (Tick {tick})</span>
            <span style="color: #10b981; font-weight: 700;">✅ {safe_count}/{len(agents)} Safe</span>
        </div>
        <div style="font-size: 12px; color: #94a3b8; margin-bottom: 8px;">
            ⚠️ Active Hazards: <b>{len(hazard_edges_seen)}</b> | 🏥 Shelters: <b>5</b>
        </div>
        <hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.12); margin: 8px 0;">
        <div style="font-size: 11px; color: #cbd5e1; line-height: 1.6;">
            <div><span style="color:#00E676; font-weight:bold;">━━</span> <b>EVA-NET Safest Route</b> (Mesh Aware)</div>
            <div><span style="color:#E53935; font-weight:bold;">━ ━</span> <b>Blocked Road</b> (Wildfire/Flood)</div>
            <div><span style="color:#00C853; font-size:12px;">🏥</span> <b>Click Shelter</b> for Owner Contact & Radio</div>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    if filename is None:
        filename = os.path.join(config.OUTPUT_DIR, config.MAP_FILENAME)

    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else ".", exist_ok=True)
    m.save(filename)

    return m
