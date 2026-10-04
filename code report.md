# EVA-NET — Code Report

**EVA-NET (Emergency Vector-Aware Network)** is an offline disaster evacuation navigation system combining a **Python discrete-event simulation engine** and an **interactive Leaflet web application** (Lahaina, Maui case study).

---

## 1. Tech Stack

- **Python Core:** Python 3.10+, NetworkX, GeoPandas, Shapely, Folium, NumPy
- **Frontend App:** Vanilla HTML5 / CSS3 / JavaScript (ES6+), Leaflet.js (v1.9.4), OSRM API, Web Audio API
- **Deployment:** Vercel, Netlify

---

## 2. Codebase Overview

| Component | File | Description |
| :--- | :--- | :--- |
| **Config & Data** | [`eva_net/config.py`](file:///c:/Users/asidd/Desktop/Coding/antigravity/EVA-NET/eva_net/config.py) | Simulation constants, GPS anchors, penalty weights, and emergency shelter database. |
| **Step 1: Spatial Graph** | [`eva_net/spatial_graph.py`](file:///c:/Users/asidd/Desktop/Coding/antigravity/EVA-NET/eva_net/spatial_graph.py) | Builds directed road graph $G=(V,E)$ with GeoPandas vector geometries and street names. |
| **Step 2: Sensing** | [`eva_net/hazard_delta.py`](file:///c:/Users/asidd/Desktop/Coding/antigravity/EVA-NET/eva_net/hazard_delta.py) | Compact `<5 KB` `VectorDiff` telemetry schema and dynamic wildfire/flood expansion logic. |
| **Step 3: P2P Mesh** | [`eva_net/p2p_fusion.py`](file:///c:/Users/asidd/Desktop/Coding/antigravity/EVA-NET/eva_net/p2p_fusion.py) | Agent kinematics and multi-tier P2P data exchange (BLE/Wi-Fi $\le 300\text{m}$, LoRaWAN $\le 3\text{km}$). |
| **Step 4: Reweighting** | [`eva_net/graph_reweight.py`](file:///c:/Users/asidd/Desktop/Coding/antigravity/EVA-NET/eva_net/graph_reweight.py) | Consensus edge reweighting ($W = W_{\text{base}} + H \cdot C + T_{\text{stale}}$) with time-decay. |
| **Step 5: Pathfinding** | [`eva_net/pathfinder.py`](file:///c:/Users/asidd/Desktop/Coding/antigravity/EVA-NET/eva_net/pathfinder.py) | Sub-millisecond $A^*$ search with Euclidean heuristic and Folium HTML map generator. |
| **Orchestrator** | [`eva_net/simulation.py`](file:///c:/Users/asidd/Desktop/Coding/antigravity/EVA-NET/eva_net/simulation.py) | Discrete-event simulation loop producing tick snapshots in `output/`. |
| **Web UI** | [`website/index.html`](file:///c:/Users/asidd/Desktop/Coding/antigravity/EVA-NET/website/index.html) | Navigation drawer, 1–10 safety triage slider, turn-by-turn list, and SOS distress modal. |
| **Web Logic** | [`website/script.js`](file:///c:/Users/asidd/Desktop/Coding/antigravity/EVA-NET/website/script.js) | Client Dijkstra routing, OSRM road geometry, GPS geolocation, P2P swarm, and siren synthesizer. |
| **Web Styles** | [`website/styles.css`](file:///c:/Users/asidd/Desktop/Coding/antigravity/EVA-NET/website/styles.css) | Custom glassmorphism design system, responsive drawer, and map overlays. |

---

## 3. Core Algorithms

1. **Dynamic Edge Cost:** $W_{\text{edge}} = W_{\text{base}} + H(\text{hazard}) \cdot C + 0.5 \cdot (\Delta t)^{1.2}$ *(auto-reverts after 300s)*.
2. **On-Device Pathfinding:** $A^*$ / Dijkstra runs in $< 1\text{ ms}$ (budget: $< 50\text{ ms}$).
3. **Proximity Sync:** Haversine distance scans for peer discovery and hop-decayed confidence propagation.
4. **Offline Siren:** Web Audio API $440\text{ Hz}$ carrier modulated by a $2\text{ Hz}$ LFO.

---

## 4. Quick Run Commands

```bash
# Run Python Simulation (generates output/eva_net_final.html)
pip install -r requirements.txt && python -m eva_net.simulation

# Run Web Navigation App
python -m http.server 8000  # Open http://localhost:8000/website/index.html
```
