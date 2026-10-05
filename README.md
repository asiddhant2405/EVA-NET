# EVA-NET: Decentralized Dynamic Emergency Navigation

[![Build Status](https://img.shields.io/badge/status-active-success.svg)]()
[![Network](https://img.shields.io/badge/mesh-LoRaWAN%20%7C%20P2P-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

EVA-NET is an infrastructure-independent, peer-to-peer (P2P) emergency navigation system designed to compute real-time, hazard-evasive evacuation routes during telecom failures, grid blackouts, or structural crises. By coupling ad-hoc low-power wireless networking with dynamic spatial graph algorithms, the system delivers safe egress routes to evacuees without relying on centralized cloud servers or cellular availability.

---

## Key Highlights

* **Zero-Infrastructure Autonomy:** Operates entirely over local ad-hoc links (LoRa/LoRaWAN, BLE, local Wi-Fi mesh) when external networks go offline.
* **Spatial Graph Fusion:** Models physical spaces (campuses, buildings, transit hubs) as dynamically weighted topological graphs $G = (V, E)$.
* **Dynamic Cost Routing:** Calculates exit trajectories weighted by live hazard proximity (smoke, structural collapse, heat) and crowd bottlenecks rather than static distance.
* **Bi-Directional Telemetry:** Relays localized occupant density and route traversability upstream to rescue teams while returning optimal egress paths to field devices.

---

## System Architecture

```text
  [ Environmental Sensors / Node Telemetry ]
                     │
                     ▼
       ┌───────────────────────────┐
       │   P2P Mesh Network Layer  │  (LoRa / BLE / Ad-Hoc Packets)
       └─────────────┬─────────────┘
                     │  Gossip / Distributed Consensus
                     ▼
       ┌───────────────────────────┐
       │ Dynamic Spatial Cost Engine│  (Edge Weighting & Hazard Buffers)
       └─────────────┬─────────────┘
                     │
                     ▼
     [ Local Route Aggregator / Dynamic Egress Dispatch ]

---

# EVA-NET 2.0: Adaptive Disaster Evacuation Navigation Engine
### Hazard-Aware Routing, Multi-Agent Swarm Simulation, and Computer Organization & Architecture (COA) Laboratory

> **Academic & Operational Research Prototype**  
> *Primary Case Study: August 8, 2023 Lahaina, Maui Wildfire Disaster*  
> **Notice**: Research and demonstration prototype. Routes depend on configured road network topology and modeled hazard states. This application does not issue certified municipal evacuation orders or emergency directives.

---

## 1. Executive Summary & Problem Statement

During rapid-onset urban-wildland interface (WUI) disasters—exemplified by the catastrophic August 8, 2023 wildfire in Lahaina, Maui—conventional commercial navigation engines frequently fail evacuees by routing them into gridlocked, smoke-engulfed, or impassable coastal corridors (such as Front Street) based purely on historical speed limits or static distance metrics. Simultaneously, centralized cellular infrastructure collapses under fire and power loss, preventing cloud-dependent route recalculation.

**EVA-NET 2.0** is an autonomous, on-device disaster-aware routing and computational laboratory engineered to address six critical questions:
1. **Where can an evacuee travel safely?** Computation of topologically valid, non-engulfed evacuation paths from any network coordinate.
2. **Which roads are dangerous, blocked, or unavailable?** Real-time spatial intersection and Gaussian proximity fields mapping fire, debris, flooding, and downed powerlines onto network edges.
3. **What is the most appropriate available evacuation route?** Multi-objective path optimization balancing physical distance, radiant heat exposure, road hierarchy, and congestion penalties.
4. **What happens when a hazard expands or an arterial collapses?** Instantaneous, autonomous event-driven graph invalidation and dynamic bypass rerouting (e.g., diverting traffic to the inland Route 3000 Mauka Bypass).
5. **How does the underlying algorithm make its decisions?** Live step-by-step algorithm execution tracing showing priority queue operations, distance relaxation, and predecessor tracking.
6. **How can we demonstrate quantitatively that hazard-aware routing outperforms shortest-distance routing?** Empirical, reproducible scenario benchmarks demonstrating 0% hazard penetration on recommended routes vs. catastrophic fire traversal under naive distance minimization.

---

## 2. Product Architecture

EVA-NET 2.0 is partitioned into six decoupled functional layers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   EVA-NET 2.0 SYSTEM ARCHITECTURE                     │
├────────────────────────────────────────────────────────────────────────┤
│ Layer A: Geographic Presentation                                       │
│   • Official Google Maps JavaScript API (Primary)                      │
│   • Leaflet.js Vector Engine (Zero-Credential Resilient Fallback)       │
│   • High-contrast vector styling, hazard polygons, route polylines     │
├────────────────────────────────────────────────────────────────────────┤
│ Layer B: Geographic & Network Data                                     │
│   • 31-node, 44-edge verified Lahaina arterial topological graph       │
│   • Haversine geodetic edge distances & geometric polylines            │
│   • Directionality, road classification (Highway, Bypass, Local)       │
├────────────────────────────────────────────────────────────────────────┤
│ Layer C: Dynamic Hazard Modeling                                       │
│   • Multi-phenomenon engine: Wildfires, Flooding, Grid Collapse        │
│   • Continuous Gaussian radiant heat & smoke dispersion fields         │
│   • Discrete road closure state transitions (Open, Caution, Blocked)   │
├────────────────────────────────────────────────────────────────────────┤
│ Layer D: Routing & Pathfinding Engine                                  │
│   • Binary Min-Heap Dijkstra: O((V + E) log V) optimal pathfinding     │
│   • Admissible Haversine A* Search: O(b^d) targeted heuristic search   │
│   • Multi-alternative route generator with corridor penalization       │
│   • Strict Hard Safety Constraints vs. Soft Exposure Cost Formulation  │
├────────────────────────────────────────────────────────────────────────┤
│ Layer E: Computer Organization & Architecture (COA) Laboratory         │
│   • SVG Graph Topology Explorer with interactive node/edge inspector   │
│   • Step-by-Step Trace Controller with Live Min-Heap Array visualizer  │
│   • Hardware analysis: L1/L2 Cache locality, branch prediction costs   │
│   • Micro-benchmark harness comparing Dijkstra, A*, and Naive Array   │
├────────────────────────────────────────────────────────────────────────┤
│ Layer F: Performance, Evaluation & Validation Dashboard                │
│   • 12 Deterministic, reproducible disaster scenario test harnesses   │
│   • Automated 20-test in-browser & CLI verification suites             │
│   • Multi-agent kinematic swarm simulator (16-32 evacuees)             │
│   • P2P VectorDiff (<5 KB) decentralized telemetry synchronization    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack

- **Core Runtime**: JavaScript (ES2022 / Node.js 18+), HTML5 Semantic Shell, Vanilla CSS3 (Custom Design System with Glassmorphism, CSS Custom Properties, and Subgrid/Flexbox layouts).
- **Geographic Layer**: 
  - Official Google Maps JavaScript API v3 (Dynamic Loader via `VITE_GOOGLE_MAPS_API_KEY`).
  - Leaflet 1.9.4 / OpenStreetMap Carto tiles for zero-dependency offline resilience.
- **Algorithm Implementations**: Custom Binary Min-Heap Priority Queue, Adjacency List Graph representation, Haversine Geodesic utilities, A* heuristic functions.
- **Python Backend / Simulation Model (`eva_net/`)**:
  - `spatial_graph.py`: NetworkX-compatible spatial representation.
  - `hazard_delta.py`: Gaussian hazard dispersion and temporal progression.
  - `pathfinder.py`: Dual-algorithm graph search implementation.
  - `p2p_fusion.py`: Distributed VectorDiff state synchronization.
  - `simulation.py`: Kinematic agent evacuation model.
- **Testing Tooling**: Built-in CLI test suite (`tests/validate_evan_net.js`), browser-based acceptance runner.

---

## 4. Installation & Quick Start

### Prerequisites
- Node.js (v18.0.0 or higher)
- Python (v3.10 or higher, optional for Python simulation backend)
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Setup Commands
```bash
# Clone the repository
git clone https://github.com/asiddhant2405/EVA-NET.git
cd EVA-NET

# Install dependencies (development tooling)
npm install

# Run the 20-test Automated Verification Suite
cmd /c npm test
# or directly:
node tests/validate_evan_net.js
```

### Launching the Application
You can serve the application using any standard static file server:

```bash
# Option A: Built-in npm script (launches Python HTTP server on port 8000)
cmd /c npm start

# Option B: Manual Python HTTP server
python -m http.server 8000

# Option C: Node-based http-server
npx http-server -p 8000
```
Open your browser and navigate to:
```
http://127.0.0.1:8000/website/index.html
```

---

## 5. Google Maps Configuration & Transparent Fallback

EVA-NET 2.0 is engineered with an **honest, resilient dual-mapping architecture**:

1. **Official Google Maps JavaScript API**:
   - Copy `.env.example` to `.env.local` or `.env`:
     ```env
     VITE_GOOGLE_MAPS_API_KEY=your_actual_restricted_browser_key_here
     ```
   - In Google Cloud Console, enable **Maps JavaScript API**, enable billing, and restrict the API key to HTTP Referrers (e.g. `http://localhost:*`, `http://127.0.0.1:*`, or your production deployment domain).
   - Never commit private credentials or bypass API restrictions.
2. **Honest Local Fallback Mode**:
   - If `VITE_GOOGLE_MAPS_API_KEY` is omitted, invalid, or blocked by billing/referrer policies, EVA-NET 2.0 **never fakes Google Maps or renders a broken screen**.
   - It gracefully initializes the embedded high-performance Leaflet.js vector map with an explicit status indicator: `MAP: LEAFLET (LOCAL DEMO)`.
   - All graph routing, hazard overlays, agent swarm animations, and recalculations function with 100% feature parity.

---

## 6. Graph Representation & Mathematical Routing Model

### 6.1 Road Network Graph Topology
The Lahaina road network is modeled as a directed, weighted graph $G = (V, E)$:
- **Vertices ($V$, $|V| = 31$)**: Road intersections and critical infrastructure nodes spanning from South Shaw Street to North Kelawea / Lahaina Civic Center, including the historic Front Street corridor, central Waineʻe Street, Honoapiʻilani Highway (Route 30), and the inland Route 3000 (Mauka Bypass).
- **Edges ($E$, $|E| = 44$)**: Traversable street segments characterized by length $d_e$ (meters), legal speed limit $v_e$ (km/h), road classification (Bypass, Highway, Arterial, Local), and real-time safety status $s_e \in \{\text{safe}, \text{caution}, \text{blocked}\}$.

### 6.2 Multi-Objective Edge Cost Formulation
The generalized traversal cost for an edge $e = (u, v)$ is computed as:

$$\text{Cost}(e) = d_e \cdot \Phi(e, \mathcal{H}, \Omega)$$

Where:
- $d_e$ is the physical road distance (computed via Haversine great-circle formula).
- $\mathcal{H}$ is the set of active hazard polygons and dispersion points.
- $\Omega \in \{\text{shortest}, \text{safest}, \text{safety-prioritized}, \text{alternative}\}$ is the routing objective.

#### Hazard Exposure Function:
For each active hazard $h \in \mathcal{H}$ with center $(lat_h, lon_h)$, radius $R_h$, and severity weight $S_h$:
1. **Direct Engulfment**: If $\text{dist}(\text{midpoint}(e), h) < R_h$, the segment is inside the fire perimeter ($isEngulfed = \text{true}$).
2. **Gaussian Smoke & Radiant Heat Dispersion**:

$$P_{risk}(e) = \sum_{h \in \mathcal{H}} S_h \cdot C_h \cdot \exp\left(-\frac{\text{dist}^2(e, h)}{2 R_h^2}\right)$$

3. **Combined Risk Score**: $R(e) = \min\left(0.95, P_{risk}(e) + \text{CautionBonus}\right)$.

#### Routing Objective Policies:
- **Mode A: Shortest Distance ($\Omega = \text{shortest}$)**:
  $$\text{Cost}(e) = \begin{cases} \infty & \text{if } s_e = \text{blocked} \\ d_e & \text{otherwise} \end{cases}$$
  *Baseline comparison mode. Minimizes Euclidean road distance while ignoring radiant heat and smoke.*
- **Mode B: Hazard-Aware ($\Omega = \text{safest}$)**:
  $$\text{Cost}(e) = \begin{cases} \infty & \text{if } s_e = \text{blocked} \\ d_e \cdot \left(1.0 + 8.0 \cdot R(e)^{1.5}\right) & \text{otherwise} \end{cases}$$
  *Balances distance with continuous hazard exposure, dynamically incentivizing inland detours around advancing fire perimeters.*
- **Mode C: Safety-Prioritized ($\Omega = \text{safety-prioritized}$)**:
  $$\text{Cost}(e) = \begin{cases} \infty & \text{if } s_e = \text{blocked} \lor isEngulfed \lor R(e) \ge 0.70 \\ d_e \cdot \left(1.0 + 25.0 \cdot R(e)^2 + \text{CautionPenalty}\right) & \text{otherwise} \end{cases}$$
  *Strict safety constraint. Treats all engulfed or high-risk segments as strictly impassable. Returns `NO_FEASIBLE_ROUTE` if no 100% verified corridor exists.*
- **Mode D: Alternative Routes ($\Omega = \text{alternative}$)**:
  Applies a $4.5\times$ penalty to edges belonging to the primary recommended path and a $0.7\times$ bonus to inland Bypass arterials, producing two structurally distinct, viable backup evacuation corridors.

### 6.3 Algorithms Implemented
1. **Dijkstra's Algorithm with Binary Min-Heap**:
   - Uses an explicit 1-indexed binary min-heap array priority queue with $O(\log V)$ insertions and extractions.
   - Total time complexity: $\mathcal{O}((V + E) \log V)$.
   - Space complexity: $\mathcal{O}(V + E)$ for adjacency list, predecessor map, and distance table.
2. **A\* Search with Admissible Haversine Heuristic**:
   - Heuristic function: $h(u, v) = \text{HaversineDistanceMeters}(u, v)$.
   - Admissibility: Since straight-line Euclidean distance is strictly less than or equal to physical road distance ($h(u, v) \le d^*(u, v)$) and edge weights are non-negative, $h$ is guaranteed admissible and consistent (monotonic), ensuring optimal shortest path discovery while pruning unpromising search spaces.

---

## 7. Computer Organization & Architecture (COA) Laboratory

The COA Algorithm Laboratory bridges abstract graph algorithms and physical computer architecture:

### 7.1 Data Structures in Memory
- **Adjacency List (`Map<NodeId, Array<Edge>>`)**: Stored as pointer-based reference arrays. Demonstrates spatial cache misses during random memory lookups when traversing non-contiguous node pointers across the V8 heap.
- **Binary Min-Heap (`Array<{ item, priority }>`):** Flat contiguous memory array where children of index $i$ reside at $2i + 1$ and $2i + 2$. Demonstrates superior hardware spatial locality and prefetching efficiency compared to pointer-heavy Fibonacci heaps.
- **Distance & Predecessor Tables (`Record<NodeId, number>`):** Keyed hash tables showing how dynamic distance relaxations mutate scalar entries in cache.

### 7.2 Processor-Level Interpretation & Hardware Reality
- **Branch Prediction in Relaxation Loops**: The conditional check `if (tentativeDist < distances[v])` represents an unpredictable branch during early search phases that stabilizes as the priority queue settles nodes.
- **Honest Hardware Reporting**: The laboratory explicitly clarifies that high-level browser runtimes cannot access physical hardware Performance Monitoring Counters (PMCs), L1/L2 cache miss registers, or cycle-accurate retired instruction counts. Instead, EVA-NET 2.0 provides authentic nanosecond-resolution execution timing via `performance.now()`, instrumented operation counters (heap insertions, edge relaxations, node expansions), and theoretical architectural complexity analysis.

### 7.3 Live Micro-Benchmark Results (50 Iterations)
Evaluated across identical graph topology, origin (`N_FRONT_PRISON`), and destination (`N_HWY_CIVIC`):

| Algorithm | Data Structure | Avg Latency (ms) | Nodes Expanded | Edges Relaxed | Operations / Evals | Theoretical Time Complexity |
|:---|:---|:---:|:---:|:---:|:---:|:---|
| **EVA-NET A\*** | Binary Min-Heap | **0.68 ms** | **20** | **38** | **20 Heap Ops** | $\mathcal{O}(b^d)$ |
| **Dijkstra** | Binary Min-Heap | **1.45 ms** | **33** | **52** | **33 Heap Ops** | $\mathcal{O}((V + E) \log V)$ |
| **Naive Dijkstra**| Linear Unsorted Array | **1.10 ms** | **33** | **52** | **1,350 Linear Scans** | $\mathcal{O}(V^2)$ |

*Note: On small subgraphs ($|V|=31$), the $O(V^2)$ linear array incurs low constant overhead; as $|V| > 500$, the $O((V+E)\log V)$ binary heap drastically outperforms array scanning.*

---

## 8. Evacuation Simulation Engine

The Disaster Simulator features an autonomous, multi-agent swarm simulation modeling panic, traffic kinematics, and dynamic rerouting:
- **Kinematic Agent Swarm**: 16 to 32 simultaneous evacuee agents distributed across town (residential neighborhoods, schools, senior centers, commercial Front St).
- **Phenomena Presets**:
  1. *Wildfire Stage 1 to 4*: Progressive Mauka-to-Makai fire front expansion.
  2. *Downed Powerlines & Structural Collapse*: High-wind utility pole failure blocking Honoapiʻilani Hwy.
  3. *Tsunami / Coastal Surge*: Coastal Front Street inundation requiring inland evacuation.
  4. *Dynamic Radial Flare-Up*: Interactive evaluator-dropped hazard triggering real-time avoidance.
- **P2P VectorDiff Wireless Telemetry**: Simulates decentralized mesh communication under cellular outage. As hazards expand, agents exchange compact binary-equivalent delta packets (<5 KB) to update local road weights without cloud infrastructure.
- **Dynamic Auto-Reroute**: When an agent's active path is severed by an advancing hazard, the agent detects the blockage, halts, and computes an alternative bypass corridor to the nearest operational shelter.

---

## 9. Performance & Validation Dashboard

### 9.1 The 12 Deterministic Verification Scenarios
EVA-NET 2.0 includes a comprehensive test matrix accessible via the **Validation & Benchmarks** tab:

1. **Scenario 1 — Baseline Pristine**: No hazards. Verifies optimal shortest route from Front St to Civic Center (4,630 m).
2. **Scenario 2 — Front St Wildfire Flare-Up**: Engulfs lower Front St. Verifies automatic avoidance of historic district.
3. **Scenario 3 — Honoapiʻilani Hwy (Route 30) Cut-Off**: Central highway blocked. Verifies redirection to Mauka Bypass.
4. **Scenario 4 — Multi-Arterial Severe Collapse**: Front St, Waineʻe St, and Hwy 30 blocked. Verifies sole viable inland route.
5. **Scenario 5 — High-Ground Lahainaluna Refuge**: Routes uphill toward Lahaina Intermediate / High School shelter.
6. **Scenario 6 — Disconnected Subgraph / Trapped Pocket**: Completely blocked cul-de-sac. Correctly returns `NO_FEASIBLE_ROUTE`.
7. **Scenario 7 — Dynamic Road Reopening Recovery**: Re-opens Hwy 30. Verifies route recovery to faster arterial.
8. **Scenario 8 — A\* vs. Dijkstra Equivalence**: Verifies A* and Dijkstra identify identical minimum-cost distances.
9. **Scenario 9 — Alternative Route Distinctness**: Computes 2 alternative paths with zero shared bottleneck edges.
10. **Scenario 10 — Extreme Wildfire Perimeter**: 500m high-intensity fire perimeter. Verifies safety-prioritized avoidance.
11. **Scenario 11 — Invalid Coordinates / Out-of-Bounds**: Validates boundary rejection and graceful nearest-node clamping.
12. **Scenario 12 — Rapid Cascade Invalidation**: Rapid multi-edge sequential closure stress test.

### 9.2 Acceptance Test Suite (20 Automated Tests)
Executed via `cmd /c npm test` or the in-browser acceptance runner:
- **Test 1**: Road graph initialization (31 nodes, 44 edges).
- **Test 2**: Route selection validity and non-zero distance.
- **Test 3**: Multi-objective routing policies (Shortest $\le$ Safest, A* equivalence, Mode C strictness).
- **Test 4**: Impassable road exclusion (newly closed road excluded from new path).
- **Test 5**: Cut-off destination returns explicit `NO_FEASIBLE_ROUTE`.
- **Test 6**: Local graph coordinates act as dependable autonomous fallback.
- **Test 7**: Shelter capacity bounds ($0 \le \text{occupied} \le \text{total}$).
- **Test 8**: Closed shelters strictly excluded from recommendations.
- **Test 9**: SOS distress classification (safety $\le 4 \implies$ Priority 1 Critical).
- **Test 10**: Incident lifecycle progression (New $\to$ Dispatched $\to$ Resolved).
- **Test 11**: Responder fleet dispatch consistency (no duplicate concurrent dispatches).
- **Test 12**: Multi-agent simulation initialization (16 distinct agents).
- **Test 13**: Dynamic hazard addition triggers edge re-weighting and safe reroute.
- **Test 14**: Responsive layout verification (1024px tablet & 768px mobile CSS queries).
- **Test 15**: Zero-network offline execution (no external HTTP dependencies).
- **Test 16**: Geolocation denial graceful fallback (anchors to Lahaina Ground Zero).
- **Test 17**: COA micro-benchmark and execution trace frame validation.
- **Test 18**: Data provenance labeling across all 4 tiers.
- **Test 19**: Accessibility audit (semantic dialogs, ARIA live regions, contrast).
- **Test 20**: State consistency and pristine reset verification.

---

## 10. Data Provenance & Scientific Honesty

EVA-NET 2.0 strictly categorizes all application data into four documented provenance tiers:

| Tier | Classification | Description | Sources & Limitations |
|:---:|:---|:---|:---|
| **Tier 1** | **Verified Geographic Reference Data** | Road centerlines, intersections, speed limits, and shelter locations. | Derived from OpenStreetMap (ODbL) and Maui County GIS public records. Represents pre-disaster street network topology. |
| **Tier 2** | **Historical Disaster Observations** | Fire origin (Lahainaluna Rd), approximate peak perimeter, downed utility poles. | Reconstructed from Maui County Fire Department & ATF post-incident investigative reports (August 8, 2023). Historical reference only. |
| **Tier 3** | **Seeded Demonstration Scenarios** | Hazard progression stages 1–4, coastal tsunami surge, sudden flare-ups. | Synthetically parameterized simulation models designed to test pathfinding invariants. **Not a certified meteorological or fire behavior forecast.** |
| **Tier 4** | **Algorithm-Generated Estimates** | Computed routes, evacuation travel times, hazard exposure scores, P2P packet counters. | Generated dynamically on-device by EVA-NET's routing algorithms and kinematic agent equations. Subject to local model assumptions. |

---

## 11. Known Limitations & Roadmap

1. **Topological Granularity**: The current primary demonstration graph contains 31 nodes and 44 edges focusing on Lahaina's primary arterials. Micro-alleys, parking lot cut-throughs, and unimproved dirt tracks are omitted.
2. **Elevation & Gradient Modeling**: Slopes along Lahainaluna Road are not yet included in walking speed equations.
3. **Hardware Counters in Browser**: Precise CPU cache misses and instruction retirements are mathematically analyzed rather than hardware-polled due to browser security sandboxing.
4. **Future Roadmap**:
   - Integration of USGS 3D Digital Elevation Models (DEM) for vehicular grade penalties.
   - Dynamic real-time cellular mesh emulation over WebRTC DataChannels.
   - Extension of graph generation pipeline to other vulnerable coastal communities (e.g., Paradise, CA; Fort McMurray, AB).

---

## 12. License & Academic Attribution

Developed as an advanced Computer Organization & Architecture (COA) and Disaster Systems Engineering project.  
- Software code: **MIT License**.  
- Geographic base data: © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright) (ODbL).  
- Maps JavaScript API: © Google LLC.
