"""
EVA-NET Simulation Engine — Main Orchestrator
===============================================
Ties together all 5 steps of the EVA-NET methodology into
a tick-based simulation loop:

    1. Initialize city grid (Step 1)
    2. Place evacuee agents → assign shelter destinations
    3. Spawn initial hazards (Step 2)
    4. LOOP per tick:
        a. Move agents along paths
        b. P2P diff exchange (Step 3)
        c. Apply diffs → reweight graph (Step 4)
        d. Recalculate shortest paths (Step 5)
        e. Expand hazards (fire/flood fronts)
        f. Snapshot Folium map periodically
    5. Generate final interactive Folium HTML map
"""

from __future__ import annotations

import math
import os
import sys
import time
from typing import Optional

# Reconfigure stdout for utf-8 on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import networkx as nx

from . import config
from .spatial_graph import (
    create_city_grid,
    get_shelter_nodes,
    print_graph_stats,
)
from .hazard_delta import (
    HazardType,
    VectorDiff,
    expand_hazards,
    get_hazard_summary,
    spawn_random_hazards,
)
from .p2p_fusion import (
    EvacueeAgent,
    create_agents,
    run_p2p_tick,
)
from .graph_reweight import (
    apply_diffs_indexed,
    build_edge_id_index,
    refresh_all_weights,
    get_weight_matrix_stats,
)
from .pathfinder import (
    find_shortest_path,
    render_map,
    benchmark_pathfinding,
)


class EVANetSimulation:
    """
    Main simulation engine for EVA-NET.

    Orchestrates the full 5-step methodology in a tick-based loop,
    producing Folium map snapshots of the evacuation progress.
    """

    def __init__(
        self,
        grid_rows: int = config.GRID_ROWS,
        grid_cols: int = config.GRID_COLS,
        num_agents: int = config.NUM_AGENTS,
        num_hazards: int = config.NUM_INITIAL_HAZARDS,
        total_ticks: int = config.TOTAL_TICKS,
        seed: int = 42,
        verbose: bool = True,
    ):
        self.grid_rows = grid_rows
        self.grid_cols = grid_cols
        self.num_agents = num_agents
        self.num_hazards = num_hazards
        self.total_ticks = total_ticks
        self.seed = seed
        self.verbose = verbose

        # State
        self.graph: Optional[nx.DiGraph] = None
        self.agents: list[EvacueeAgent] = []
        self.all_diffs: list[VectorDiff] = []
        self.edge_index: dict[str, tuple[str, str]] = {}
        self.tick: int = 0
        self.sim_time: float = 0.0

        # Statistics
        self.stats: dict = {
            "total_p2p_exchanges": 0,
            "total_reroutes": 0,
            "total_hazards_spawned": 0,
            "path_calc_times_ms": [],
            "agents_sheltered_by_tick": [],
        }

    def log(self, msg: str, level: str = "INFO") -> None:
        """Print simulation log message."""
        if self.verbose:
            icons = {
                "INFO": "ℹ️ ",
                "HAZARD": "🔥",
                "P2P": "📡",
                "PATH": "🗺️ ",
                "AGENT": "👤",
                "TICK": "⏱️ ",
                "OK": "✅",
                "WARN": "⚠️ ",
            }
            icon = icons.get(level, "  ")
            print(f"  {icon} [T={self.tick:>3} | {self.sim_time:>6.1f}s] {msg}")

    def initialize(self) -> None:
        """
        Step 1: Build the city grid and place agents.
        """
        print()
        print("╔══════════════════════════════════════════════════════╗")
        print("║           EVA-NET SIMULATION INITIALIZING           ║")
        print("║     Emergency Vector-Aware Network Simulation       ║")
        print("╚══════════════════════════════════════════════════════╝")
        print()

        # ── Step 1: Create spatial graph ──────────────────────────
        self.log("Building synthetic city grid...", "INFO")
        self.graph = create_city_grid(
            rows=self.grid_rows,
            cols=self.grid_cols,
            seed=self.seed,
        )
        self.edge_index = build_edge_id_index(self.graph)
        print_graph_stats(self.graph)

        # ── Place agents ──────────────────────────────────────────
        shelter_nodes = get_shelter_nodes(self.graph)
        self.log(f"Shelters: {shelter_nodes}", "INFO")

        self.agents = create_agents(
            self.graph,
            n=self.num_agents,
            shelter_nodes=shelter_nodes,
            seed=self.seed,
        )
        self.log(f"Placed {len(self.agents)} evacuee agents", "AGENT")

        # ── Initial pathfinding for all agents ────────────────────
        self._recalculate_all_paths()

        # ── Step 2: Spawn initial hazards ─────────────────────────
        self.log("Spawning initial hazards...", "HAZARD")
        initial_diffs = spawn_random_hazards(
            self.graph,
            n=self.num_hazards,
            sim_time=0.0,
            seed=self.seed + 1,
        )
        self.all_diffs.extend(initial_diffs)
        self.stats["total_hazards_spawned"] += len(initial_diffs)

        # Apply initial hazards to graph
        updated = apply_diffs_indexed(
            self.graph, initial_diffs, 0.0, self.edge_index,
        )
        self.log(f"Spawned {len(initial_diffs)} hazard diffs, updated {updated} edges", "HAZARD")

        # Give initial hazard knowledge to nearby agents
        for diff in initial_diffs:
            for agent in self.agents:
                # System-spawned hazards — everyone near the hazard knows about it
                # For simulation purposes, the "SYSTEM" reporter shares with agents
                # who are at the affected edge endpoints
                edge_uv = self.edge_index.get(diff.edge_id)
                if edge_uv and agent.current_node in edge_uv:
                    agent.add_diff(diff)

        # Recalculate paths after hazard spawn
        self._recalculate_all_paths()

        summary = get_hazard_summary(initial_diffs)
        for htype, count in summary.items():
            self.log(f"  {htype}: {count} edges affected", "HAZARD")

        print()

    def _recalculate_all_paths(self) -> None:
        """Recalculate shortest paths for all active agents."""
        for agent in self.agents:
            if agent.reached_shelter:
                continue

            old_path = list(agent.current_path)

            path, cost, elapsed_ms = find_shortest_path(
                self.graph, agent.current_node, agent.target_node,
            )
            self.stats["path_calc_times_ms"].append(elapsed_ms)

            if path:
                agent.current_path = path
                agent.path_index = 0
                agent.moving_progress = 0.0

                # Track reroutes
                if old_path and path != old_path:
                    agent.reroute_count += 1
                    self.stats["total_reroutes"] += 1
            else:
                # No path found — try alternative shelters
                shelters = get_shelter_nodes(self.graph)
                for shelter in shelters:
                    if shelter != agent.target_node:
                        alt_path, alt_cost, alt_time = find_shortest_path(
                            self.graph, agent.current_node, shelter,
                        )
                        if alt_path:
                            agent.current_path = alt_path
                            agent.target_node = shelter
                            agent.path_index = 0
                            agent.moving_progress = 0.0
                            agent.reroute_count += 1
                            self.stats["total_reroutes"] += 1
                            self.log(
                                f"{agent.agent_id} rerouted to alternative "
                                f"shelter {shelter}",
                                "PATH",
                            )
                            break

    def _recalculate_agent_path(self, agent: EvacueeAgent) -> None:
        """Recalculate path for a single agent."""
        if agent.reached_shelter:
            return

        old_path = list(agent.current_path)

        path, cost, elapsed_ms = find_shortest_path(
            self.graph, agent.current_node, agent.target_node,
        )
        self.stats["path_calc_times_ms"].append(elapsed_ms)

        if path:
            agent.current_path = path
            agent.path_index = 0
            agent.moving_progress = 0.0

            if old_path and path != old_path:
                agent.reroute_count += 1
                self.stats["total_reroutes"] += 1
        else:
            # Try alternative shelters
            shelters = get_shelter_nodes(self.graph)
            for shelter in shelters:
                if shelter != agent.target_node:
                    alt_path, _, _ = find_shortest_path(
                        self.graph, agent.current_node, shelter,
                    )
                    if alt_path:
                        agent.current_path = alt_path
                        agent.target_node = shelter
                        agent.path_index = 0
                        agent.moving_progress = 0.0
                        agent.reroute_count += 1
                        self.stats["total_reroutes"] += 1
                        break

    def run_tick(self) -> dict:
        """
        Execute one simulation tick.

        Returns dict with tick statistics.
        """
        self.tick += 1
        self.sim_time += config.TICK_DURATION_S

        tick_stats = {
            "tick": self.tick,
            "p2p_exchanges": 0,
            "edges_reweighted": 0,
            "new_hazards": 0,
            "agents_sheltered": 0,
            "reroutes": 0,
        }

        # ── 4a: Move agents along paths ──────────────────────────
        for agent in self.agents:
            agent.advance_on_path(self.graph, config.TICK_DURATION_S)
            if agent.reached_shelter:
                tick_stats["agents_sheltered"] += 1

        # ── 4b: P2P communication (Step 3) ───────────────────────
        p2p_result = run_p2p_tick(self.agents, self.sim_time)
        tick_stats["p2p_exchanges"] = p2p_result["ble_wifi"] + p2p_result["lorawan"]
        self.stats["total_p2p_exchanges"] += tick_stats["p2p_exchanges"]

        # ── 4c: Apply received diffs → reweight graph (Step 4) ───
        # Each agent applies their known diffs to the shared graph
        all_agent_diffs = []
        for agent in self.agents:
            all_agent_diffs.extend(agent.known_diffs.values())

        # Deduplicate by edge_id (keep newest)
        deduped: dict[str, VectorDiff] = {}
        for diff in all_agent_diffs:
            existing = deduped.get(diff.edge_id)
            if existing is None or diff.timestamp > existing.timestamp:
                deduped[diff.edge_id] = diff

        updated = apply_diffs_indexed(
            self.graph, list(deduped.values()),
            self.sim_time, self.edge_index,
        )
        tick_stats["edges_reweighted"] = updated

        # Periodic full weight refresh (time-decay)
        if self.tick % 10 == 0:
            refresh_all_weights(self.graph, self.sim_time)

        # ── 4d: Recalculate paths (Step 5) ────────────────────────
        # Only recalculate if graph changed or agent has new diffs
        if updated > 0 or tick_stats["p2p_exchanges"] > 0:
            reroutes_before = self.stats["total_reroutes"]
            self._recalculate_all_paths()
            tick_stats["reroutes"] = self.stats["total_reroutes"] - reroutes_before

        # ── 4e: Expand hazards periodically ───────────────────────
        if (
            self.tick % config.HAZARD_EXPAND_INTERVAL == 0
            and self.tick < self.total_ticks * 0.8  # Stop expanding late in sim
        ):
            new_diffs = expand_hazards(
                self.graph, self.all_diffs,
                self.sim_time,
            )
            if new_diffs:
                self.all_diffs.extend(new_diffs)
                self.stats["total_hazards_spawned"] += len(new_diffs)
                apply_diffs_indexed(
                    self.graph, new_diffs,
                    self.sim_time, self.edge_index,
                )
                tick_stats["new_hazards"] = len(new_diffs)

                # Share with nearby agents
                for diff in new_diffs:
                    edge_uv = self.edge_index.get(diff.edge_id)
                    if edge_uv:
                        for agent in self.agents:
                            if agent.current_node in edge_uv:
                                agent.add_diff(diff)

                self._recalculate_all_paths()

        # Track sheltered agents
        sheltered = sum(1 for a in self.agents if a.reached_shelter)
        self.stats["agents_sheltered_by_tick"].append(sheltered)

        return tick_stats

    def run(self) -> None:
        """
        Execute the full simulation.
        """
        self.initialize()

        print("╔══════════════════════════════════════════════════════╗")
        print("║            SIMULATION RUNNING                      ║")
        print("╚══════════════════════════════════════════════════════╝")
        print()

        start_time = time.time()

        for t in range(self.total_ticks):
            tick_stats = self.run_tick()

            # Log significant events
            if tick_stats["p2p_exchanges"] > 0:
                self.log(
                    f"P2P: {tick_stats['p2p_exchanges']} diffs exchanged",
                    "P2P",
                )

            if tick_stats["reroutes"] > 0:
                self.log(
                    f"Rerouted {tick_stats['reroutes']} agent(s)",
                    "PATH",
                )

            if tick_stats["new_hazards"] > 0:
                self.log(
                    f"Hazard expansion: +{tick_stats['new_hazards']} new edges",
                    "HAZARD",
                )

            sheltered = sum(1 for a in self.agents if a.reached_shelter)
            if tick_stats["agents_sheltered"] > 0 or self.tick % 20 == 0:
                self.log(
                    f"Sheltered: {sheltered}/{len(self.agents)} agents",
                    "AGENT",
                )

            # ── 4f: Folium snapshot ───────────────────────────────
            if self.tick % config.SNAPSHOT_INTERVAL == 0 or self.tick == 1:
                self._save_snapshot()

            # Early exit if all agents sheltered
            if sheltered == len(self.agents):
                self.log("All agents reached safety!", "OK")
                break

        elapsed = time.time() - start_time

        # ── Final snapshot ────────────────────────────────────────
        self._save_snapshot(final=True)

        # ── Print final statistics ────────────────────────────────
        self._print_summary(elapsed)

    def _save_snapshot(self, final: bool = False) -> None:
        """Save a Folium map snapshot."""
        # Build paths dict
        paths = {}
        for agent in self.agents:
            if agent.current_path and not agent.reached_shelter:
                paths[agent.agent_id] = agent.current_path

        suffix = "final" if final else f"tick_{self.tick:04d}"
        filename = os.path.join(
            config.OUTPUT_DIR,
            f"eva_net_{suffix}.html",
        )

        render_map(
            self.graph,
            agents=self.agents,
            paths=paths,
            tick=self.tick,
            sim_time=self.sim_time,
            filename=filename,
        )

        if final:
            self.log(f"Final map saved: {filename}", "OK")
        else:
            self.log(f"Snapshot saved: {filename}", "INFO")

    def _print_summary(self, elapsed_seconds: float) -> None:
        """Print final simulation statistics."""
        sheltered = sum(1 for a in self.agents if a.reached_shelter)
        path_times = self.stats["path_calc_times_ms"]
        weight_stats = get_weight_matrix_stats(self.graph)

        print()
        print("╔══════════════════════════════════════════════════════╗")
        print("║           EVA-NET SIMULATION COMPLETE               ║")
        print("╠══════════════════════════════════════════════════════╣")
        print(f"║  Simulation time     : {self.sim_time:>24.1f}s  ║")
        print(f"║  Wall-clock time     : {elapsed_seconds:>24.2f}s  ║")
        print(f"║  Total ticks         : {self.tick:>25}   ║")
        print("╠══════════════════════════════════════════════════════╣")
        print(f"║  Agents sheltered    : {sheltered:>18}/{len(self.agents):>3}   ║")
        print(f"║  Total P2P exchanges : {self.stats['total_p2p_exchanges']:>25}   ║")
        print(f"║  Total reroutes      : {self.stats['total_reroutes']:>25}   ║")
        print(f"║  Hazards spawned     : {self.stats['total_hazards_spawned']:>25}   ║")
        print("╠══════════════════════════════════════════════════════╣")

        if path_times:
            import numpy as np
            print(f"║  Path calc mean      : {np.mean(path_times):>22.3f}ms  ║")
            print(f"║  Path calc P95       : {np.percentile(path_times, 95):>22.3f}ms  ║")
            print(f"║  Path calc max       : {max(path_times):>22.3f}ms  ║")
            under_50 = sum(1 for t in path_times if t < 50)
            print(f"║  Under 50ms target   : {under_50:>18}/{len(path_times):>3}   ║")

        print("╠══════════════════════════════════════════════════════╣")
        print(f"║  Edge weight min     : {weight_stats['min']:>25}   ║")
        print(f"║  Edge weight mean    : {weight_stats['mean']:>25}   ║")
        print(f"║  Edge weight max     : {weight_stats['max']:>25}   ║")
        print(f"║  Blocked edges (∞)   : {weight_stats['blocked']:>25}   ║")
        print("╚══════════════════════════════════════════════════════╝")

        # Per-agent summary
        print()
        print("  Agent Details:")
        print("  ─────────────────────────────────────────────────────")
        print(f"  {'Agent':<12} {'Status':<10} {'Reroutes':>8} {'P2P':>5} {'Diffs':>6}")
        print("  ─────────────────────────────────────────────────────")
        for agent in self.agents:
            status = "✅ SAFE" if agent.reached_shelter else "🔴 MOVING"
            print(
                f"  {agent.agent_id:<12} {status:<10} "
                f"{agent.reroute_count:>8} {agent.p2p_encounters:>5} "
                f"{len(agent.known_diffs):>6}"
            )

        print()
        print(f"  📁 Maps saved to: {config.OUTPUT_DIR}/")
        print()


def main():
    """Entry point for running the simulation."""
    sim = EVANetSimulation(
        grid_rows=config.GRID_ROWS,
        grid_cols=config.GRID_COLS,
        num_agents=config.NUM_AGENTS,
        num_hazards=config.NUM_INITIAL_HAZARDS,
        total_ticks=config.TOTAL_TICKS,
        seed=42,
        verbose=True,
    )
    sim.run()

    # Run pathfinding benchmark
    print()
    benchmark_pathfinding(sim.graph)


if __name__ == "__main__":
    main()
