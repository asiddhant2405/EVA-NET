"""
EVA-NET — Emergency Vector-Aware Network for Evacuation Tracking
=================================================================
Decentralized spatial graph optimization simulation framework.

This package implements the 5-step EVA-NET methodology:
    1. Lightweight Spatial Graph Representation
    2. Local Sensing & Delta Update Generation
    3. Opportunistic P2P Data Fusion
    4. Decentralized Graph Reweighting
    5. On-Device Path Calculation & Rerouting

Usage:
    python -m eva_net.simulation
"""

__version__ = "0.1.0"
__author__ = "EVA-NET Team"

from .config import *
from .spatial_graph import create_city_grid, graph_to_geodataframes, get_shelter_nodes
from .hazard_delta import HazardType, VectorDiff, spawn_random_hazards
from .p2p_fusion import EvacueeAgent, create_agents, run_p2p_tick
from .graph_reweight import compute_edge_weight, apply_diffs_indexed
from .pathfinder import find_shortest_path, render_map
from .simulation import EVANetSimulation
