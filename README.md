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
