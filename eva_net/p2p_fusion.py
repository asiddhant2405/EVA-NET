"""
EVA-NET Step 3 — Multi-Tier P2P Data Fusion
=============================================
Simulates asynchronous node communication where close-range
evacuee agents swap missing Vector Diffs via BLE/Wi-Fi Direct,
while broadcasting critical hazard updates over LoRaWAN.

Communication Tiers:
    Tier 1 — BLE / Wi-Fi Direct (10–300m): Full bidirectional diff swap
    Tier 2 — LoRaWAN (1–5km): Critical-only broadcast (confidence ≥ 0.8)
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Optional

import networkx as nx
import numpy as np

from . import config
from .hazard_delta import VectorDiff


@dataclass
class EvacueeAgent:
    """
    A mobile evacuee node in the P2P mesh network.

    Each agent carries:
    - Its current position on the graph
    - A local copy of known Vector Diffs
    - Its current evacuation path
    - Communication statistics
    """
    agent_id: str
    current_node: str           # Current graph node ID
    target_node: str            # Destination shelter node ID
    lat: float = 0.0           # Current GPS latitude
    lon: float = 0.0           # Current GPS longitude
    speed_mps: float = config.AGENT_SPEED_MPS

    # Local knowledge store: edge_id → VectorDiff
    known_diffs: dict[str, VectorDiff] = field(default_factory=dict)

    # Current evacuation path (list of node IDs)
    current_path: list[str] = field(default_factory=list)
    path_index: int = 0  # Current position in path

    # Movement state
    moving_progress: float = 0.0  # Progress along current edge [0, 1]
    reached_shelter: bool = False

    # Statistics
    diffs_sent: int = 0
    diffs_received: int = 0
    reroute_count: int = 0
    p2p_encounters: int = 0

    def add_diff(self, diff: VectorDiff) -> bool:
        """
        Add a Vector Diff to local knowledge if newer/better.

        Returns True if the diff was accepted (new information).
        """
        existing = self.known_diffs.get(diff.edge_id)

        if existing is None:
            # New hazard info — accept
            self.known_diffs[diff.edge_id] = diff
            self.diffs_received += 1
            return True

        # Conflict resolution: newest timestamp wins, ties broken by confidence
        if (diff.timestamp > existing.timestamp) or (
            diff.timestamp == existing.timestamp
            and diff.confidence_score > existing.confidence_score
        ):
            self.known_diffs[diff.edge_id] = diff
            self.diffs_received += 1
            return True

        return False

    def get_missing_diffs(self, other_keys: set[str]) -> list[VectorDiff]:
        """Return diffs that this agent has but the other doesn't."""
        missing_keys = set(self.known_diffs.keys()) - other_keys
        return [self.known_diffs[k] for k in missing_keys]

    def advance_on_path(self, G: nx.DiGraph, tick_duration: float) -> None:
        """
        Move the agent along its current path by one tick.

        Calculates position based on speed and edge length.
        """
        if self.reached_shelter or not self.current_path:
            return

        if self.path_index >= len(self.current_path) - 1:
            # Reached destination
            self.reached_shelter = True
            self.current_node = self.current_path[-1]
            self._update_position(G)
            return

        # Current edge
        src = self.current_path[self.path_index]
        dst = self.current_path[self.path_index + 1]

        edge_data = G.edges.get((src, dst))
        if edge_data is None:
            return

        edge_length = edge_data["length_m"]
        distance_this_tick = self.speed_mps * tick_duration
        self.moving_progress += distance_this_tick / edge_length

        # Check if we've reached the next node
        while self.moving_progress >= 1.0 and self.path_index < len(self.current_path) - 1:
            self.moving_progress -= 1.0
            self.path_index += 1
            self.current_node = self.current_path[self.path_index]

            if self.path_index >= len(self.current_path) - 1:
                self.reached_shelter = True
                self.moving_progress = 0.0
                break

            # Get next edge length for progress calculation
            if self.path_index < len(self.current_path) - 1:
                next_src = self.current_path[self.path_index]
                next_dst = self.current_path[self.path_index + 1]
                next_edge = G.edges.get((next_src, next_dst))
                if next_edge:
                    edge_length = next_edge["length_m"]

        self._update_position(G)

    def _update_position(self, G: nx.DiGraph) -> None:
        """Update lat/lon based on current node and progress."""
        node_data = G.nodes[self.current_node]
        self.lat = node_data["lat"]
        self.lon = node_data["lon"]

        # Interpolate position if between nodes
        if (
            not self.reached_shelter
            and self.current_path
            and self.path_index < len(self.current_path) - 1
            and self.moving_progress > 0
        ):
            next_node = self.current_path[self.path_index + 1]
            next_data = G.nodes[next_node]
            t = min(self.moving_progress, 1.0)
            self.lat = node_data["lat"] + t * (next_data["lat"] - node_data["lat"])
            self.lon = node_data["lon"] + t * (next_data["lon"] - node_data["lon"])


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two GPS points."""
    R = 6_371_000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def find_nearby_agents(
    agents: list[EvacueeAgent],
    range_m: float,
) -> list[tuple[EvacueeAgent, EvacueeAgent, float]]:
    """
    Find all agent pairs within communication range.

    Returns list of (agent_a, agent_b, distance_m) tuples.
    Uses brute-force O(n²) — fine for <100 agents.
    """
    pairs = []
    for i in range(len(agents)):
        for j in range(i + 1, len(agents)):
            a, b = agents[i], agents[j]
            if a.reached_shelter or b.reached_shelter:
                continue
            dist = _haversine_m(a.lat, a.lon, b.lat, b.lon)
            if dist <= range_m:
                pairs.append((a, b, dist))
    return pairs


def ble_wifi_exchange(
    agents: list[EvacueeAgent],
    sim_time: float,
) -> int:
    """
    Tier 1: BLE / Wi-Fi Direct close-range exchange.

    All agents within WIFI_DIRECT_RANGE_M swap their full
    set of missing Vector Diffs bidirectionally.

    Parameters
    ----------
    agents : list[EvacueeAgent]
        All active agents.
    sim_time : float
        Current simulation time.

    Returns
    -------
    int
        Total number of diffs exchanged in this tick.
    """
    total_exchanged = 0
    pairs = find_nearby_agents(agents, config.WIFI_DIRECT_RANGE_M)

    for agent_a, agent_b, dist in pairs:
        agent_a.p2p_encounters += 1
        agent_b.p2p_encounters += 1

        # A → B: diffs A has that B doesn't
        a_to_b = agent_a.get_missing_diffs(set(agent_b.known_diffs.keys()))
        for diff in a_to_b:
            relayed = diff.with_hop()  # Increment hop, decay confidence
            if agent_b.add_diff(relayed):
                agent_a.diffs_sent += 1
                total_exchanged += 1

        # B → A: diffs B has that A doesn't
        b_to_a = agent_b.get_missing_diffs(set(agent_a.known_diffs.keys()))
        for diff in b_to_a:
            relayed = diff.with_hop()
            if agent_a.add_diff(relayed):
                agent_b.diffs_sent += 1
                total_exchanged += 1

    return total_exchanged


def lorawan_broadcast(
    agents: list[EvacueeAgent],
    sim_time: float,
) -> int:
    """
    Tier 2: LoRaWAN long-range broadcast.

    Each agent broadcasts its HIGH-CONFIDENCE diffs (≥ 0.8)
    to all agents within LORAWAN_RANGE_M.

    This simulates the long-range, low-bandwidth LoRa protocol
    that would only carry the most critical updates.

    Parameters
    ----------
    agents : list[EvacueeAgent]
        All active agents.
    sim_time : float
        Current simulation time.

    Returns
    -------
    int
        Total diffs broadcast.
    """
    total_broadcast = 0

    for broadcaster in agents:
        if broadcaster.reached_shelter:
            continue

        # Only broadcast high-confidence diffs
        critical_diffs = [
            d for d in broadcaster.known_diffs.values()
            if d.confidence_score >= config.LORAWAN_MIN_CONFIDENCE
        ]

        if not critical_diffs:
            continue

        # Find all agents in LoRaWAN range
        for receiver in agents:
            if receiver.agent_id == broadcaster.agent_id or receiver.reached_shelter:
                continue

            dist = _haversine_m(
                broadcaster.lat, broadcaster.lon,
                receiver.lat, receiver.lon,
            )

            if dist <= config.LORAWAN_RANGE_M:
                for diff in critical_diffs:
                    relayed = diff.with_hop()
                    if receiver.add_diff(relayed):
                        total_broadcast += 1

    return total_broadcast


def run_p2p_tick(
    agents: list[EvacueeAgent],
    sim_time: float,
) -> dict[str, int]:
    """
    Execute one tick of P2P communication across both tiers.

    Returns
    -------
    dict[str, int]
        {"ble_wifi": count, "lorawan": count}
    """
    ble_count = ble_wifi_exchange(agents, sim_time)
    lora_count = lorawan_broadcast(agents, sim_time)

    return {
        "ble_wifi": ble_count,
        "lorawan": lora_count,
    }


def create_agents(
    G: nx.DiGraph,
    n: int = config.NUM_AGENTS,
    shelter_nodes: Optional[list[str]] = None,
    seed: Optional[int] = 42,
) -> list[EvacueeAgent]:
    """
    Create evacuee agents at random non-shelter positions.

    Parameters
    ----------
    G : nx.DiGraph
        The city grid graph.
    n : int
        Number of agents to create.
    shelter_nodes : list[str] or None
        Designated shelter node IDs. If None, auto-detected.
    seed : int or None
        Random seed.

    Returns
    -------
    list[EvacueeAgent]
        Created agents with positions and targets assigned.
    """
    if seed is not None:
        random.seed(seed)

    if shelter_nodes is None:
        from .spatial_graph import get_shelter_nodes
        shelter_nodes = get_shelter_nodes(G)

    # Non-shelter nodes as starting positions
    all_nodes = list(G.nodes)
    start_candidates = [n for n in all_nodes if n not in shelter_nodes]

    if len(start_candidates) < n:
        start_candidates = all_nodes  # Fallback

    start_nodes = random.sample(start_candidates, min(n, len(start_candidates)))

    agents = []
    for i, start_node in enumerate(start_nodes):
        node_data = G.nodes[start_node]
        target = random.choice(shelter_nodes)

        agent = EvacueeAgent(
            agent_id=f"AGENT_{i:03d}",
            current_node=start_node,
            target_node=target,
            lat=node_data["lat"],
            lon=node_data["lon"],
        )
        agents.append(agent)

    return agents
