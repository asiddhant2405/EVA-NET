"""
EVA-NET Step 4 — Decentralized Graph Reweighting
==================================================
Implements time-decaying edge matrix consensus that dynamically
recalculates edge travel costs using the formula:

    W_edge = W_base + H(hazard) + T(staleness)

Where:
    W_base    — Baseline travel time/distance
    H(hazard) — Penalty multiplier (∞ for complete blockages)
    T(stale)  — Time-decay penalty for old unconfirmed reports
"""

from __future__ import annotations

import math
from typing import Optional

import networkx as nx
import numpy as np

from . import config
from .hazard_delta import VectorDiff


def hazard_penalty(hazard_type: str) -> float:
    """
    H(hazard): Look up the penalty multiplier for a given hazard type.

    Complete blockages (floods, fires, collapses) return float('inf'),
    effectively removing the edge from routing.

    Parameters
    ----------
    hazard_type : str
        HazardType enum value string.

    Returns
    -------
    float
        Penalty value to add to edge weight.
    """
    return config.HAZARD_PENALTIES.get(hazard_type, 20.0)


def staleness_penalty(
    report_time: float,
    current_time: float,
    alpha: float = config.STALENESS_ALPHA,
    beta: float = config.STALENESS_BETA,
) -> float:
    """
    T(staleness): Time-decay penalty for old unconfirmed reports.

    Older reports without reconfirmation get progressively heavier
    penalty, encouraging agents to explore uncertain areas cautiously
    rather than blindly trusting stale information.

    Formula: T(age) = α * (current_time - report_time)^β

    Parameters
    ----------
    report_time : float
        Timestamp of the hazard report.
    current_time : float
        Current simulation time.
    alpha : float
        Scaling coefficient (default from config).
    beta : float
        Exponent controlling decay aggressiveness (default from config).

    Returns
    -------
    float
        Staleness penalty value.
    """
    age = max(0.0, current_time - report_time)

    # If report is very old, hazard may have cleared — reduce penalty
    if age >= config.STALENESS_REVERT_S:
        return 0.0  # Fully reverted

    return alpha * (age ** beta)


def compute_edge_weight(
    base_weight: float,
    hazard_type: Optional[str],
    report_time: Optional[float],
    current_time: float,
    confidence: float = 1.0,
) -> float:
    """
    Compute the full edge weight using the EVA-NET formula.

    W_edge = W_base + H(hazard) * confidence + T(staleness)

    If the hazard is a complete blockage (inf penalty), the edge
    weight is set to infinity regardless of staleness.

    For stale reports that have exceeded STALENESS_REVERT_S,
    the weight reverts to W_base.

    Parameters
    ----------
    base_weight : float
        Baseline travel cost for this edge.
    hazard_type : str or None
        Type of hazard (None = no hazard).
    report_time : float or None
        When the hazard was reported.
    current_time : float
        Current simulation time.
    confidence : float
        Confidence score of the report [0, 1].

    Returns
    -------
    float
        Computed edge weight.
    """
    if hazard_type is None:
        return base_weight

    h_penalty = hazard_penalty(hazard_type)

    # Complete blockage — check if it should revert due to staleness
    if math.isinf(h_penalty):
        if report_time is not None:
            age = current_time - report_time
            if age >= config.STALENESS_REVERT_S:
                # Stale blockage — revert but add uncertainty penalty
                return base_weight + staleness_penalty(report_time, current_time)
        # Active blockage
        return float("inf")

    # Partial hazard — apply confidence-weighted penalty + staleness
    t_penalty = 0.0
    if report_time is not None:
        t_penalty = staleness_penalty(report_time, current_time)
        # If fully stale, just return base
        age = current_time - report_time
        if age >= config.STALENESS_REVERT_S:
            return base_weight

    return base_weight + (h_penalty * confidence) + t_penalty


def apply_diffs_to_graph(
    G: nx.DiGraph,
    diffs: list[VectorDiff],
    current_time: float,
) -> int:
    """
    Apply a batch of Vector Diffs to the graph, updating edge weights.

    Implements decentralized consensus:
    - Newer timestamps override older data
    - Ties broken by confidence score
    - Edge weight recalculated using the full formula

    Parameters
    ----------
    G : nx.DiGraph
        The city grid graph (modified in-place).
    diffs : list[VectorDiff]
        Batch of Vector Diffs to apply.
    current_time : float
        Current simulation time.

    Returns
    -------
    int
        Number of edges actually updated.
    """
    updated = 0

    for diff in diffs:
        # Find edge by edge_id
        for u, v, data in G.edges(data=True):
            if data["edge_id"] == diff.edge_id:
                # Check if this diff is newer than existing
                existing_ts = data.get("hazard_timestamp")
                existing_conf = data.get("hazard_confidence", 0.0)

                should_update = False
                if existing_ts is None:
                    should_update = True
                elif diff.timestamp > existing_ts:
                    should_update = True
                elif (
                    diff.timestamp == existing_ts
                    and diff.confidence_score > existing_conf
                ):
                    should_update = True

                if should_update:
                    data["hazard_type"] = diff.hazard_type
                    data["hazard_timestamp"] = diff.timestamp
                    data["hazard_confidence"] = diff.confidence_score
                    data["hazard_reporter"] = diff.reporter_id

                    # Recompute weight
                    data["current_weight"] = compute_edge_weight(
                        base_weight=data["base_weight"],
                        hazard_type=diff.hazard_type,
                        report_time=diff.timestamp,
                        current_time=current_time,
                        confidence=diff.confidence_score,
                    )
                    updated += 1

                break  # Found the edge, move to next diff

    return updated


def refresh_all_weights(G: nx.DiGraph, current_time: float) -> int:
    """
    Recalculate ALL edge weights based on current time.

    This is called periodically to apply time-decay to stale hazards,
    potentially reopening edges whose hazards haven't been reconfirmed.

    Parameters
    ----------
    G : nx.DiGraph
        The city grid graph (modified in-place).
    current_time : float
        Current simulation time.

    Returns
    -------
    int
        Number of edges whose weights changed.
    """
    changed = 0

    for u, v, data in G.edges(data=True):
        old_weight = data["current_weight"]

        new_weight = compute_edge_weight(
            base_weight=data["base_weight"],
            hazard_type=data.get("hazard_type"),
            report_time=data.get("hazard_timestamp"),
            current_time=current_time,
            confidence=data.get("hazard_confidence", 1.0),
        )

        if new_weight != old_weight:
            data["current_weight"] = new_weight

            # If weight reverted to base, clear hazard info
            if data.get("hazard_type") is not None and new_weight == data["base_weight"]:
                data["hazard_type"] = None
                data["hazard_timestamp"] = None
                data["hazard_confidence"] = 0.0
                data["hazard_reporter"] = None

            changed += 1

    return changed


def build_edge_id_index(G: nx.DiGraph) -> dict[str, tuple[str, str]]:
    """
    Build a fast lookup index: edge_id → (u, v).

    Speeds up repeated edge lookups during simulation.
    """
    return {
        data["edge_id"]: (u, v)
        for u, v, data in G.edges(data=True)
    }


def apply_diffs_indexed(
    G: nx.DiGraph,
    diffs: list[VectorDiff],
    current_time: float,
    edge_index: dict[str, tuple[str, str]],
) -> int:
    """
    Apply diffs using the pre-built edge index for O(1) lookups.

    This is the optimized version of apply_diffs_to_graph.
    """
    updated = 0

    for diff in diffs:
        uv = edge_index.get(diff.edge_id)
        if uv is None:
            continue

        u, v = uv
        data = G.edges[u, v]

        existing_ts = data.get("hazard_timestamp")
        existing_conf = data.get("hazard_confidence", 0.0)

        should_update = False
        if existing_ts is None:
            should_update = True
        elif diff.timestamp > existing_ts:
            should_update = True
        elif (
            diff.timestamp == existing_ts
            and diff.confidence_score > existing_conf
        ):
            should_update = True

        if should_update:
            data["hazard_type"] = diff.hazard_type
            data["hazard_timestamp"] = diff.timestamp
            data["hazard_confidence"] = diff.confidence_score
            data["hazard_reporter"] = diff.reporter_id

            data["current_weight"] = compute_edge_weight(
                base_weight=data["base_weight"],
                hazard_type=diff.hazard_type,
                report_time=diff.timestamp,
                current_time=current_time,
                confidence=diff.confidence_score,
            )
            updated += 1

    return updated


def get_weight_matrix_stats(G: nx.DiGraph) -> dict:
    """Get statistics about the current edge weight matrix."""
    weights = [d["current_weight"] for _, _, d in G.edges(data=True) if not math.isinf(d["current_weight"])]
    blocked = sum(1 for _, _, d in G.edges(data=True) if math.isinf(d["current_weight"]))

    if not weights:
        return {"min": 0, "max": 0, "mean": 0, "blocked": blocked, "total": len(G.edges)}

    return {
        "min": round(min(weights), 2),
        "max": round(max(weights), 2),
        "mean": round(np.mean(weights), 2),
        "blocked": blocked,
        "total": len(G.edges),
    }
