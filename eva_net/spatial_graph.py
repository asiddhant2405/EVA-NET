"""
EVA-NET Step 1 — Lightweight Spatial Graph Representation
==========================================================
Builds a realistic real-world spatial graph G = (V, E) of Lahaina, Maui.

Vertices (V) = intersections / landmarks / designated shelters with owner contacts
Edges    (E) = directed road segments with street names and geometries

Uses GeoPandas + Shapely for vector geometry storage and
NetworkX for the adjacency structure with mutable edge weights.
"""

from __future__ import annotations

import random
from typing import Optional

import geopandas as gpd
import networkx as nx
import numpy as np
from shapely.geometry import LineString, Point

from . import config


def _node_id(row: int, col: int) -> str:
    """Generate a deterministic node ID from grid coordinates."""
    return f"N_{row:03d}_{col:03d}"


def _edge_id(u: str, v: str) -> str:
    """Generate a deterministic edge ID from node pair."""
    return f"E_{u}_{v}"


def create_city_grid(
    rows: int = config.GRID_ROWS,
    cols: int = config.GRID_COLS,
    spacing_m: float = config.GRID_SPACING_M,
    base_lat: float = config.BASE_LAT,
    base_lon: float = config.BASE_LON,
    num_shelters: int = config.NUM_SHELTERS,
    seed: Optional[int] = 42,
) -> nx.DiGraph:
    """
    Create a spatial road graph of Lahaina, Maui with real-world landmarks,
    real street names, and designated shelters with contact info.

    Parameters
    ----------
    rows, cols : int
        Grid dimensions for the road network.
    spacing_m : float
        Distance in meters between adjacent intersections.
    base_lat, base_lon : float
        Anchor GPS coordinates (Lahaina, Maui).
    num_shelters : int
        Number of designated safe-zone nodes.
    seed : int or None
        Random seed for reproducibility.

    Returns
    -------
    nx.DiGraph
        Directed graph with rich node/edge attributes including geometries.
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    G = nx.DiGraph()

    # ── Step 1a: Create Vertices (Intersections) ──────────────────
    for r in range(rows):
        for c in range(cols):
            nid = _node_id(r, c)
            lat = base_lat + r * spacing_m * config.DEG_LAT_PER_M
            lon = base_lon + c * spacing_m * config.DEG_LON_PER_M
            
            # Intersection naming based on grid
            h_street = config.REAL_STREETS[r % len(config.REAL_STREETS)]
            v_street = config.REAL_STREETS[(c + 4) % len(config.REAL_STREETS)]
            name = f"{h_street} & {v_street}"

            G.add_node(
                nid,
                row=r,
                col=c,
                lat=lat,
                lon=lon,
                name=name,
                geometry=Point(lon, lat),
                is_shelter=False,
                shelter_info=None,
            )

    # ── Step 1b: Designate Shelters with Real Contact Data ─────────
    # Place real shelters at key tactical positions in the city
    shelter_placements = [
        (_node_id(rows - 1, cols - 1), config.REAL_SHELTERS[0]),  # Civic Center (North/Hwy 30)
        (_node_id(0, cols - 1), config.REAL_SHELTERS[1]),        # High Ground Mauka Shelter
        (_node_id(rows // 2, 0), config.REAL_SHELTERS[2]),       # Rec Center & Park (Central/Shaw)
        (_node_id(0, 0), config.REAL_SHELTERS[3]),               # Senior Center (South)
        (_node_id(rows - 1, 0), config.REAL_SHELTERS[4]),        # Wahikuli Wayside (Northwest)
    ]

    for i in range(min(num_shelters, len(shelter_placements))):
        nid, sinfo = shelter_placements[i]
        if nid in G.nodes:
            G.nodes[nid]["is_shelter"] = True
            G.nodes[nid]["name"] = sinfo["name"]
            G.nodes[nid]["shelter_info"] = sinfo

    # ── Step 1c: Create Directed Edges with Real Street Names ─────
    for r in range(rows):
        for c in range(cols):
            u = _node_id(r, c)
            u_data = G.nodes[u]

            # Horizontal neighbor (East-West street)
            if c + 1 < cols:
                v = _node_id(r, c + 1)
                v_data = G.nodes[v]
                street_name = config.REAL_STREETS[r % len(config.REAL_STREETS)]
                _add_bidirectional_edge(G, u, v, u_data, v_data, spacing_m, street_name)

            # Vertical neighbor (North-South arterial)
            if r + 1 < rows:
                v = _node_id(r + 1, c)
                v_data = G.nodes[v]
                street_name = config.REAL_STREETS[(c + 4) % len(config.REAL_STREETS)]
                _add_bidirectional_edge(G, u, v, u_data, v_data, spacing_m, street_name)

    return G


def _add_bidirectional_edge(
    G: nx.DiGraph,
    u: str,
    v: str,
    u_data: dict,
    v_data: dict,
    length_m: float,
    street_name: str = "Local Road",
) -> None:
    """Add directed edges in both directions between u and v with street metadata."""
    geom_fwd = LineString(
        [(u_data["lon"], u_data["lat"]), (v_data["lon"], v_data["lat"])]
    )
    geom_rev = LineString(
        [(v_data["lon"], v_data["lat"]), (u_data["lon"], u_data["lat"])]
    )

    # Road quality factor
    base_weight = length_m * (1.0 + np.random.uniform(-0.05, 0.05))

    for src, dst, geom in [(u, v, geom_fwd), (v, u, geom_rev)]:
        eid = _edge_id(src, dst)
        G.add_edge(
            src,
            dst,
            edge_id=eid,
            street_name=street_name,
            geometry=geom,
            length_m=length_m,
            base_weight=base_weight,
            current_weight=base_weight,
            hazard_type=None,
            hazard_timestamp=None,
            hazard_confidence=0.0,
            hazard_reporter=None,
        )


def graph_to_geodataframes(G: nx.DiGraph) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Export the graph's nodes and edges as GeoDataFrames.

    Returns
    -------
    tuple[GeoDataFrame, GeoDataFrame]
        (nodes_gdf, edges_gdf) with CRS EPSG:4326
    """
    # ── Nodes GeoDataFrame ────────────────────────────────────────
    node_records = []
    for nid, data in G.nodes(data=True):
        node_records.append({
            "node_id": nid,
            "name": data.get("name", nid),
            "lat": data["lat"],
            "lon": data["lon"],
            "is_shelter": data["is_shelter"],
            "shelter_info": data.get("shelter_info"),
            "geometry": data["geometry"],
        })
    nodes_gdf = gpd.GeoDataFrame(node_records, crs="EPSG:4326")

    # ── Edges GeoDataFrame ────────────────────────────────────────
    edge_records = []
    for u, v, data in G.edges(data=True):
        edge_records.append({
            "edge_id": data["edge_id"],
            "street_name": data.get("street_name", "Road"),
            "u": u,
            "v": v,
            "length_m": data["length_m"],
            "base_weight": data["base_weight"],
            "current_weight": data["current_weight"],
            "hazard_type": data["hazard_type"],
            "geometry": data["geometry"],
        })
    edges_gdf = gpd.GeoDataFrame(edge_records, crs="EPSG:4326")

    return nodes_gdf, edges_gdf


def get_shelter_nodes(G: nx.DiGraph) -> list[str]:
    """Return list of node IDs that are designated shelters."""
    return [n for n, d in G.nodes(data=True) if d.get("is_shelter", False)]


def get_node_position(G: nx.DiGraph, node_id: str) -> tuple[float, float]:
    """Return (lat, lon) for a given node."""
    d = G.nodes[node_id]
    return d["lat"], d["lon"]


def get_all_node_ids(G: nx.DiGraph) -> list[str]:
    """Return all node IDs as a list."""
    return list(G.nodes)


def get_edge_by_id(G: nx.DiGraph, edge_id: str) -> Optional[tuple[str, str, dict]]:
    """Look up an edge by its edge_id attribute."""
    for u, v, data in G.edges(data=True):
        if data["edge_id"] == edge_id:
            return u, v, data
    return None


def print_graph_stats(G: nx.DiGraph) -> None:
    """Print summary statistics about the graph."""
    shelters = get_shelter_nodes(G)
    hazards = [(u, v) for u, v, d in G.edges(data=True) if d["hazard_type"] is not None]
    blocked = [
        (u, v) for u, v, d in G.edges(data=True)
        if d["current_weight"] == float("inf")
    ]

    print("╔══════════════════════════════════════════════════════╗")
    print("║        EVA-NET Lahaina Spatial Graph Statistics      ║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"║  Nodes (intersections) : {len(G.nodes):>26}  ║")
    print(f"║  Edges (road segments) : {len(G.edges):>26}  ║")
    print(f"║  Designated Shelters   : {len(shelters):>26}  ║")
    print(f"║  Active hazards        : {len(hazards):>26}  ║")
    print(f"║  Blocked edges (∞)     : {len(blocked):>26}  ║")
    print("╚══════════════════════════════════════════════════════╝")
