"""
EVA-NET Configuration — Centralized Simulation Parameters
==========================================================
All tuneable constants for the EVA-NET simulation framework.
Features real-world geographic coordinates, named streets, and
emergency shelter databases with owner contacts and radio nets.
"""

# ─── Real-World Base GPS Coordinates (Lahaina, Maui — 2023 Wildfire Case Study) ───
BASE_LAT: float = 20.8783
BASE_LON: float = -156.6825

# Grid Topology Parameters
GRID_ROWS: int = 10              # Number of rows in the city grid
GRID_COLS: int = 10              # Number of columns in the city grid
GRID_SPACING_M: float = 120.0    # Meters between intersections

# Approximate degree-to-meter conversions at 20.88° N latitude
DEG_LAT_PER_M: float = 1.0 / 111_320.0
DEG_LON_PER_M: float = 1.0 / (111_320.0 * 0.9367)  # cos(20.88°) ≈ 0.9367

# ─── Real Street Names in Lahaina ────────────────────────────────
REAL_STREETS = [
    "Front St (Coastal)",
    "Honoapiʻilani Hwy (Route 30)",
    "Lahaina Bypass (Route 3000)",
    "Lahainaluna Rd (Mauka Connector)",
    "Keawe St",
    "Papalaua St",
    "Dickenson St",
    "Prison St",
    "Shaw St",
    "Waineʻe St",
    "Luakini St",
    "Baker St",
    "Kenui St",
    "Niheu St (High Ground Access)",
    "Pauoa St",
    "Kupuohi St",
]

# ─── Real Emergency Shelters with Owner Contacts ─────────────────
REAL_SHELTERS = [
    {
        "id": "SHELTER_CIVIC_CENTER",
        "name": "Lahaina Civic Center & Gymnasium",
        "type": "Primary County Evacuation Hub",
        "lat": 20.9125,
        "lon": -156.6862,
        "address": "1840 Honoapiʻilani Hwy, Lahaina, HI 96761",
        "owner": "Capt. Mark Kealoha (Maui Emergency Management)",
        "phone": "(808) 661-4685",
        "alt_phone": "(808) 270-7285",
        "radio_freq": "VHF 155.055 MHz / HAM 146.520 MHz",
        "capacity_total": 500,
        "capacity_occupied": 195,
        "status": "Active Primary Shelter",
        "supplies": [
            "Potable Water Tanker (3,000 Gal)",
            "MRE Food Rations (1,200 kits)",
            "Medical Triage Station with Nurse",
            "50kW Diesel Backup Generator",
            "Satellite Starlink Mesh Uplink",
            "Pet Friendly Area",
            "ADA Wheelchair Accessible",
        ],
    },
    {
        "id": "SHELTER_HIGH_GROUND",
        "name": "Princess Nāhiʻenaʻena High-Ground Shelter",
        "type": "Mauka High-Ground Safe Haven",
        "lat": 20.8710,
        "lon": -156.6570,
        "address": "816 Niheu St (off Lahainaluna Rd), Lahaina, HI 96761",
        "owner": "Principal Leilani Vance / Red Cross Disaster Liaison",
        "phone": "(808) 662-4020",
        "alt_phone": "(808) 280-9941",
        "radio_freq": "VHF 154.280 MHz / GMRS Ch. 7",
        "capacity_total": 350,
        "capacity_occupied": 82,
        "status": "Active High-Ground Refuge",
        "supplies": [
            "First Aid & Trauma Kit",
            "Water Filtration Pallets",
            "Infant & Pediatric Care",
            "Solar + Battery Storage",
            "Pet Shelter Cages",
            "ADA Accessible",
        ],
    },
    {
        "id": "SHELTER_REC_CENTER",
        "name": "Lahaina Recreation Center & Park Shelter",
        "type": "Secondary Mass Care Facility",
        "lat": 20.8912,
        "lon": -156.6780,
        "address": "245 Shaw St, Lahaina, HI 96761",
        "owner": "Sarah Kahele (Red Cross Maui Coordinator)",
        "phone": "(808) 244-0051",
        "alt_phone": "(808) 870-3312",
        "radio_freq": "VHF 156.800 MHz (Marine Ch. 16 Backup)",
        "capacity_total": 250,
        "capacity_occupied": 140,
        "status": "Active Staging Area",
        "supplies": [
            "Bottled Water Pallets",
            "Emergency Cots & Blankets",
            "Dry Rations",
            "Portable 20kW Generator",
            "Paramedic Unit Onsite",
        ],
    },
    {
        "id": "SHELTER_SENIOR_CENTER",
        "name": "West Maui Senior Center & Community Refuge",
        "type": "Medical Priority / Vulnerable Safe Zone",
        "lat": 20.8762,
        "lon": -156.6710,
        "address": "788 Pauoa St, Lahaina, HI 96761",
        "owner": "Dr. Keanu Matsumoto (Community Health Director)",
        "phone": "(808) 661-9432",
        "alt_phone": "(808) 385-6120",
        "radio_freq": "HAM 147.060 MHz (+0.600)",
        "capacity_total": 180,
        "capacity_occupied": 65,
        "status": "Active Priority Care",
        "supplies": [
            "Oxygen Concentrators",
            "Refrigerated Insulin Storage",
            "Wheelchair Transport",
            "Dialysis Backup",
            "25kW Generator",
        ],
    },
    {
        "id": "SHELTER_WAHIKULI",
        "name": "Wahikuli Wayside High-Ground Extraction Point",
        "type": "Open-Air Vehicle & Bus Evacuation Staging",
        "lat": 20.9015,
        "lon": -156.6890,
        "address": "Honoapiʻilani Hwy (Wahikuli Access), Lahaina, HI 96761",
        "owner": "Officer David Kanoa (DLNR / Maui Police Liaison)",
        "phone": "(808) 244-6400",
        "alt_phone": "(808) 270-6555",
        "radio_freq": "VHF 155.475 MHz (Police Dispatch)",
        "capacity_total": 400,
        "capacity_occupied": 110,
        "status": "Active Transit Hub",
        "supplies": [
            "Emergency Bus Extraction",
            "Water Distribution Point",
            "Satellite Dispatch Comms",
            "Traffic Control Escort",
        ],
    },
]

# ─── Agents ──────────────────────────────────────────────────────
NUM_AGENTS: int = 20             # Number of evacuee agents
NUM_SHELTERS: int = 5            # Designated safe-zone nodes
AGENT_SPEED_MPS: float = 12.0    # Vehicle/running speed ~43 km/h

# ─── Hazards ─────────────────────────────────────────────────────
NUM_INITIAL_HAZARDS: int = 5     # Starting hazard count
HAZARD_EXPAND_RATE: int = 2      # New hazard edges per expansion tick
HAZARD_EXPAND_INTERVAL: int = 15 # Ticks between hazard expansions

# ─── Communication Ranges ────────────────────────────────────────
BLE_RANGE_M: float = 100.0          # Bluetooth Low Energy range
WIFI_DIRECT_RANGE_M: float = 300.0  # Wi-Fi Direct range
LORAWAN_RANGE_M: float = 3000.0     # LoRaWAN broadcast range
LORAWAN_MIN_CONFIDENCE: float = 0.8 # Minimum confidence for LoRaWAN broadcast

# ─── Reweighting Formula ─────────────────────────────────────────
# W_edge = W_base + H(hazard) + T(staleness)
STALENESS_ALPHA: float = 0.5    # Time-decay α coefficient
STALENESS_BETA: float = 1.2     # Time-decay β exponent
STALENESS_REVERT_S: float = 300.0  # Seconds before stale hazard fully reverts

# Hazard penalty multipliers (∞ = complete blockage)
HAZARD_PENALTIES: dict = {
    "FLASH_FLOOD":    float('inf'),
    "WILDFIRE":       float('inf'),
    "FALLEN_TREE":    50.0,
    "ROAD_COLLAPSE":  float('inf'),
    "DEBRIS":         30.0,
    "POWER_LINE":     40.0,
}

# ─── Simulation Timing ───────────────────────────────────────────
TICK_DURATION_S: float = 1.0     # Simulated seconds per tick
TOTAL_TICKS: int = 120           # Total simulation duration (ticks)
SNAPSHOT_INTERVAL: int = 10      # Ticks between Folium map snapshots

# ─── Confidence Scoring ──────────────────────────────────────────
PRIMARY_CONFIDENCE: float = 0.9  # Direct reporter confidence
HOP_DECAY: float = 0.1          # Confidence decay per P2P hop

# ─── Output ──────────────────────────────────────────────────────
OUTPUT_DIR: str = "output"
MAP_FILENAME: str = "eva_net_simulation.html"
