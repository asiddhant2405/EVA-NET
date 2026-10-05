# EVA-NET 2.0: Evaluator Demonstration Guide
### Rapid Walkthrough & Live Interactive Evaluation Playbook

> **Target Audience**: Academic Examination Committee, Software Architects, and Emergency Systems Evaluators.  
> **Estimated Demonstration Time**: 5 to 8 minutes.

---

## 1. Quick Initial Setup

### Step 1: Verify Environment
Ensure Node.js and a web server are available:
```bash
node -v   # v18+ recommended
python -V # v3.10+
```

### Step 2: Run Verification Test Suite (CLI)
Before launching the UI, demonstrate algorithm correctness to the committee by executing the 20-test suite:
```bash
node tests/validate_evan_net.js
```
**Expected Output**:
```
════════════════════════════════════════════════════════════════
   EVA-NET 2.0 — ACCEPTANCE TEST SUITE (20 VERIFICATION TESTS)   
════════════════════════════════════════════════════════════════
✅ [PASS] TEST 1 — INITIALIZATION: Road graph loads with 31 nodes and 44 edges.
...
✅ [PASS] TEST 20 — RESET AND STATE CONSISTENCY: Reset restores exact pristine baseline without corrupting state.
════════════════════════════════════════════════════════════════
   TEST RESULTS: 20 / 20 TESTS PASSED (0 FAILED)   
════════════════════════════════════════════════════════════════
```

### Step 3: Launch Local Application
```bash
# Launch via Python HTTP server (or npm start)
python -m http.server 8000
```
Open Chrome or any modern browser to:
```
http://127.0.0.1:8000/website/index.html
```

---

## 2. Recommended Demonstration Sequence

### Phase 1: Map-First Interface & Route Calculation (60 seconds)
*Goal: Demonstrate that the application is map-first, uncluttered, and allows a first-time user to calculate an optimal evacuation route within seconds.*

1. **Observe Map-First Workspace**:
   - The map occupies the entire screen. The real white roads from the map tiles are completely unobstructed.
   - Closed roads are rendered as **dashed red** lines, and caution/smoke roads are rendered as **dashed amber** lines.
   - The top header is compact (52px), displaying the brand `EVA-NET v2.0`, geographic context (`Lahaina, Maui • 2023 Case Study`), and data provenance badge (`Simulated Demo Mode`).
2. **Inspect Floating Route Planner (Top-Left)**:
   - Notice the sleek, floating glassmorphism card containing:
     - Origin input: **Front St & Prison St** (Ground Zero).
     - Safe Shelter Destination: **Lahaina Civic Center & Gymnasium**.
     - Routing mode selector: **Hazard-Aware (Recommended)**, **Shortest**, **Zero-Hazard**, and **Bypass**.
3. **Click `Calculate Evacuation Route`**:
   - The engine computes the path in < 1 ms using local Dijkstra on a Binary Min-Heap.
   - The **Route Results Card** displays:
     - Feasibility badge: `✅ Feasible Route Active`.
     - Distance: `4.6 km`.
     - Travel Time: `6 min`.
     - Hazard Score: `98 / 100` (Lower modeled exposure).
     - Avoided Closures: `8 Segments`.
     - Clear plain-language explanation of why this path detours away from the active Front Street firestorm.

---

### Phase 2: The Signature "What-If" Crisis Demonstration (60 seconds)
*Goal: Prove that EVA-NET autonomously detects dynamic hazard expansion and reroutes traffic away from deadly traps without cloud dependence.*

1. **Click `⚡ WHAT-IF DEMO` (Top Navbar Right)**:
   - **Action**: Click the high-contrast button labeled `⚡ WHAT-IF DEMO`.
   - **What Happens**:
     - Step 1: Establishes baseline route up Honoapiʻilani Hwy (Route 30).
     - Step 2: Gale-force gusts trigger a sudden wildfire flare-up. Central Hwy 30 (`E_HWY_03`) is completely severed and turns red dashed.
     - Step 3: **Autonomous Rerouting**: The engine re-evaluates the graph, discovering the inland corridor via **Mauka Bypass (Route 3000)** via Keawe St.
     - The route polyline smoothly updates on the map without page reload.
   - **Evaluator Observation**:
     - Rationale updates: *"Trade-Off: +1.4 km distance for 100% fire avoidance and guaranteed passage."*
     - The map dynamically highlights the new detour corridor.

---

### Phase 3: Multi-Agent Evacuation Simulation Swarm (90 seconds)
*Goal: Demonstrate multi-hazard phenomena, 16-agent evacuation kinematics with blue human figures, and decentralized P2P VectorDiff telemetry.*

1. **Open Simulator Drawer**:
   - Click the **`Disaster Simulator`** tab in the top navigation bar.
   - Notice that the simulator slides in smoothly as a dedicated right-side drawer, preserving full visibility of the map and planner card.
2. **Inspect Controls & Evacuee Figures**:
   - Notice the evacuees rendered on the map as **Blue Human Figures** (with silhouette and gait).
   - Telemetry shows: 16 Agents In Transit, 0 Reroutes.
   - P2P VectorDiff shows active Ad-Hoc 915 MHz LoRa mesh packet sync.
3. **Execute Swarm Simulation**:
   - Click **`Start Simulation`** (`▶`).
   - Evacuee human figures advance along road segments toward designated safe shelters.
   - Agents turn **Green** upon safe arrival at shelters, and the counter updates to 16 Safely Arrived.
   - Close the drawer via `×` to return to full-map navigation.

---

### Phase 4: Computer Organization & Architecture (COA) Laboratory (90 seconds)
*Goal: Demonstrate graph theory depth, binary min-heap priority queues, execution step tracing, and authentic micro-benchmarks.*

1. **Open Algorithm Lab Modal**:
   - Click the **`Algorithm Lab`** tab (`🔬`) in the top navigation bar.
   - A dedicated full-screen academic modal dialog opens cleanly over the interface.
2. **Inspect Interactive SVG Graph Topology**:
   - Left column displays the vector topology with 31 nodes and 44 edges.
   - Click any node (e.g. `N_FRONT_PRISON` or `N_HWY_CIVIC`) to inspect its coordinates, degree, and adjacency list memory pointers.
3. **Inspect Execution Trace Stepper & Min-Heap Array**:
   - Step forward (`Next ▶`) or click `▶ Play` to watch Dijkstra relax edges step by step.
   - Observe the live **Binary Min-Heap Array Snapshot** showing node IDs and cumulative distances at each heap index.
   - The Distance & Predecessor table updates in real time.
4. **Execute the 50-Iteration Micro-Benchmark**:
   - Click **`⚡ Run Benchmark`**.
   - The browser executes 50 iterations comparing:
     - **Binary Min-Heap Dijkstra**
     - **EVA-NET A* (Haversine Heuristic)**
     - **Linear Array (Unoptimized)**
   - Authentic runtimes are measured in milliseconds via `performance.now()`:
     - Notice that A* expands fewer nodes than Dijkstra.
     - Min-Heap out-performs unoptimized linear arrays.
   - Close the modal with `×` or the ESC key.

---

### Phase 5: Validation Suite & Acceptance Matrix (60 seconds)
*Goal: Demonstrate test reproducibility across 12 deterministic disaster scenarios and 20 automated unit/integration tests.*

1. **Open Validation Modal**:
   - Click the **`Validation Suite`** tab (`📊`) in the top navigation bar.
2. **Run All 12 Reproducible Scenarios**:
   - Click **`▶ Run All 12 Scenarios`**.
   - Scenarios #1 through #12 execute and display green `PASS` badges.
3. **Run In-Browser Acceptance Tests**:
   - Click **`⚡ Run Test Suite`**.
   - All 20 acceptance tests run live in the browser, matching the CLI verification suite.
4. **Inspect Trade-Off Table**:
   - Mode A (Shortest: 2.4 km, High Risk) vs Mode B (Hazard-Aware: 3.8 km, Low Risk) vs Mode C (Zero-Hazard: 4.1 km).
   - Close the modal.

---

## 3. Evaluator Q&A Cheat Sheet

| Question | Answer & Architectural Evidence |
| :--- | :--- |
| **Why not just use standard Google Maps?** | Google Maps assumes cellular connectivity and cloud server access, and optimizes for speed limits. During the Lahaina disaster, towers burned down and Front St was gridlocked. EVA-NET runs 100% on-device on an embedded graph without internet. |
| **Why does the route take the longer bypass?** | Wildfire smoke, toxic embers, and downed powerlines introduce continuous exponential risk penalties onto coastal edges. The Mauka Bypass (Route 3000) adds ~1.4 km of travel but avoids 100% of fire perimeters. |
| **What is the time complexity of the routing engine?** | $O((V + E) \log V)$ using a custom Binary Min-Heap Priority Queue. Linear array scans $O(V^2)$ are strictly eliminated. |
| **How does EVA-NET sync without cellular data?** | When field changes occur (e.g. a road is closed), EVA-NET generates a compact `< 5 KB` VectorDiff delta packet designed for 915 MHz LoRa ad-hoc mesh peer-to-peer transmission. |
