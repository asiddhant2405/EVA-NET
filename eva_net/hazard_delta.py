"""
EVA-NET Step 2 — Hazard Delta Generation (Local Sensing)
=========================================================
Generates lightweight "Vector Diff" packets when an evacuee
encounters an obstacle (flash flood, wildfire, fallen tree, etc.).

Each Vector Diff is < 5 KB and contains:
    {Edge_ID, Hazard_Type, Timestamp, Confidence_Score}

Also provides hazard spawning and expansion for simulation.
"""

from __future__ import annotations

import random
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Optional

import networkx as nx
import numpy as np

from . import config


class HazardType(str, Enum):
    """Enumeration of disaster hazard types supported by EVA-NET."""
    FLASH_FLOOD = "FLASH_FLOOD"
    WILDFIRE = "WILDFIRE"
    FALLEN_TREE = "FALLEN_TREE"
    ROAD_COLLAPSE = "ROAD_COLLAPSE"
    DEBRIS = "DEBRIS"
    POWER_LINE = "POWER_LINE"


@dataclass
class VectorDiff:
    """
    Compact hazard update packet (< 5 KB).

    This is the fundamental data unit exchanged between evacuee
    devices over BLE/Wi-Fi Direct/LoRaWAN.
    """
    edge_id: str
    hazard_type: str  # HazardType value
    timestamp: float  # Unix timestamp (simulation time)
    confidence_score: float  # 0.0 to 1.0
    reporter_id: str  # Agent who first reported this hazard
    hop_count: int = 0  # Number of P2P hops from original reporter

    def to_dict(self) -> dict:
        """Serialize to dict for compact transmission."""
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> VectorDiff:
        """Deserialize from dict."""
        return cls(**d)

    def size_bytes(self) -> int:
        """Estimate payload size — must be < 5 KB."""
        import json
        return len(json.dumps(self.to_dict()).encode("utf-8"))

    def with_hop(self) -> VectorDiff:
        """
        Create a copy with incremented hop count and decayed confidence.
        Used when relaying to another agent.
        """
        return VectorDiff(
            edge_id=self.edge_id,
            hazard_type=self.hazard_type,
            timestamp=self.timestamp,
            confidence_score=max(0.1, self.confidence_score - config.HOP_DECAY),
            reporter_id=self.reporter_id,
            hop_count=self.hop_count + 1,
        )

    def __repr__(self) -> str:
        return (
            f"VectorDiff(edge={self.edge_id}, type={self.hazard_type}, "
            f"conf={self.confidence_score:.2f}, hops={self.hop_count})"
        )


def generate_vector_diff(
    edge_id: str,
    hazard_type: HazardType,
    reporter_id: str,
    sim_time: float,
    confidence: float = config.PRIMARY_CONFIDENCE,
) -> VectorDiff:
    """
    Generate a single Vector Diff when a hazard is detected.

    Parameters
    ----------
    edge_id : str
        The ID of the affected edge.
    hazard_type : HazardType
        Type of hazard encountered.
    reporter_id : str
        ID of the agent reporting the hazard.
    sim_time : float
        Current simulation time.
    confidence : float
        Confidence score (default: PRIMARY_CONFIDENCE from config).

    Returns
    -------
    VectorDiff
        Compact hazard update packet.
    """
    return VectorDiff(
        edge_id=edge_id,
        hazard_type=hazard_type.value,
        timestamp=sim_time,
        confidence_score=confidence,
        reporter_id=reporter_id,
        hop_count=0,
    )


def spawn_random_hazards(
    G: nx.DiGraph,
    n: int = config.NUM_INITIAL_HAZARDS,
    sim_time: float = 0.0,
    hazard_types: Optional[list[HazardType]] = None,
    seed: Optional[int] = None,
) -> list[VectorDiff]:
    """
    Spawn hazards on random edges in the graph.

    Simulates initial disaster conditions — fire fronts,
    flash floods, debris blocking roads.

    Parameters
    ----------
    G : nx.DiGraph
        The city grid graph.
    n : int
        Number of hazards to spawn.
    sim_time : float
        Current simulation time.
    hazard_types : list[HazardType] or None
        Types to sample from. If None, uses all types.
    seed : int or None
        Random seed.

    Returns
    -------
    list[VectorDiff]
        Generated hazard Vector Diffs.
    """
    if seed is not None:
        random.seed(seed)

    if hazard_types is None:
        hazard_types = list(HazardType)

    edges = list(G.edges(data=True))
    if n > len(edges):
        n = len(edges)

    # Select random edges for hazards
    selected = random.sample(edges, n)
    diffs = []

    for u, v, data in selected:
        htype = random.choice(hazard_types)
        diff = generate_vector_diff(
            edge_id=data["edge_id"],
            hazard_type=htype,
            reporter_id="SYSTEM",  # System-spawned hazard
            sim_time=sim_time,
            confidence=config.PRIMARY_CONFIDENCE,
        )
        diffs.append(diff)

        # Also create the reverse direction hazard (same road, both lanes)
        reverse_data = G.edges.get((v, u))
        if reverse_data:
            rev_diff = generate_vector_diff(
                edge_id=reverse_data["edge_id"],
                hazard_type=htype,
                reporter_id="SYSTEM",
                sim_time=sim_time,
                confidence=config.PRIMARY_CONFIDENCE,
            )
            diffs.append(rev_diff)

    return diffs


def expand_hazards(
    G: nx.DiGraph,
    existing_diffs: list[VectorDiff],
    sim_time: float,
    expand_count: int = config.HAZARD_EXPAND_RATE,
) -> list[VectorDiff]:
    """
    Simulate hazard expansion — fire fronts and floods spread
    to adjacent edges over time.

    Parameters
    ----------
    G : nx.DiGraph
        The city grid graph.
    existing_diffs : list[VectorDiff]
        Currently known hazard diffs.
    sim_time : float
        Current simulation time.
    expand_count : int
        Number of new edges to infect per expansion.

    Returns
    -------
    list[VectorDiff]
        New hazard Vector Diffs from expansion.
    """
    # Collect currently hazardous edges and their types
    hazardous_edges = {}
    for diff in existing_diffs:
        hazardous_edges[diff.edge_id] = diff.hazard_type

    # Only expand spreading hazard types
    spreading_types = {HazardType.WILDFIRE.value, HazardType.FLASH_FLOOD.value}

    # Find adjacent edges to existing hazards
    candidate_edges = set()
    for u, v, data in G.edges(data=True):
        eid = data["edge_id"]
        if eid in hazardous_edges and hazardous_edges[eid] in spreading_types:
            htype = hazardous_edges[eid]
            # Find neighbors of v that aren't already hazardous
            for _, neighbor, ndata in G.edges(v, data=True):
                if ndata["edge_id"] not in hazardous_edges:
                    candidate_edges.add((ndata["edge_id"], htype))

    if not candidate_edges:
        return []

    # Sample from candidates
    candidates_list = list(candidate_edges)
    selected = random.sample(candidates_list, min(expand_count, len(candidates_list)))

    new_diffs = []
    for edge_id, htype in selected:
        diff = VectorDiff(
            edge_id=edge_id,
            hazard_type=htype,
            timestamp=sim_time,
            confidence_score=0.85,  # Slightly lower confidence for inferred spread
            reporter_id="SYSTEM_EXPAND",
            hop_count=0,
        )
        new_diffs.append(diff)

    return new_diffs


def get_hazard_summary(diffs: list[VectorDiff]) -> dict[str, int]:
    """Count hazards by type."""
    counts: dict[str, int] = {}
    for diff in diffs:
        counts[diff.hazard_type] = counts.get(diff.hazard_type, 0) + 1
    return counts
