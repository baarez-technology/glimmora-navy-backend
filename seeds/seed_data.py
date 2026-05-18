"""
GLIMMORA AEGIS — Database Seed Script
Run with: python seeds/seed_data.py

Seeds 7 users (matching frontend mock data), 5 scenarios, and 3 doctrine documents.
Idempotent: re-running skips existing records by service_number / title.
"""

import os
import sys
import uuid
from datetime import UTC, datetime

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.models.doctrine import DoctrineDocument
from app.models.documentation import DocumentationTopic
from app.models.scenario import Scenario
from app.models.session import Session as DBTrainingSession
from app.models.user import User
from app.services.auth_service import hash_password


def _now() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# User seed definitions — 7 roles matching the frontend mock users exactly
# ---------------------------------------------------------------------------
USERS = [
    {
        "service_number": "IN-2024-001",
        "name": "LT Jayesh Kumar",
        "rank": "LT",
        "unit": "INS Vikrant",
        "role": "trainee",
        "password": "aegis123",
        "classification_clearance": "RESTRICTED",
    },
    {
        "service_number": "IN-2019-042",
        "name": "CDR Arjun Sharma",
        "rank": "CDR",
        "unit": "INS Dronacharya",
        "role": "instructor",
        "password": "aegis123",
        "classification_clearance": "SECRET",
    },
    {
        "service_number": "IN-2015-018",
        "name": "CAPT Priya Menon",
        "rank": "CAPT",
        "unit": "Fleet Training Centre",
        "role": "evaluator",
        "password": "aegis123",
        "classification_clearance": "SECRET",
    },
    {
        "service_number": "IN-2016-031",
        "name": "CDR Rakesh Iyer",
        "rank": "CDR",
        "unit": "Naval Doctrine Cell",
        "role": "doctrine",
        "password": "aegis123",
        "classification_clearance": "TOP SECRET",
    },
    {
        "service_number": "IN-2010-007",
        "name": "RADM Vikram Bhatia",
        "rank": "RADM",
        "unit": "Fleet Training Command",
        "role": "fleet",
        "password": "aegis123",
        "classification_clearance": "TOP SECRET",
    },
    {
        "service_number": "IN-2008-003",
        "name": "CMDE Sanjay Rao",
        "rank": "CMDE",
        "unit": "Systems Authority",
        "role": "admin",
        "password": "aegis123",
        "classification_clearance": "TOP SECRET",
    },
    {
        "service_number": "IN-2017-055",
        "name": "CDR Ananya Rao",
        "rank": "CDR",
        "unit": "Sustainment Cell",
        "role": "maintainer",
        "password": "aegis123",
        "classification_clearance": "SECRET",
    },
]


# ---------------------------------------------------------------------------
# Scenario seed definitions — one per domain
# ---------------------------------------------------------------------------
SCENARIOS = [
    {
        "title": "Bridge Watch — Restricted Waters Navigation",
        "domain": "bridge",
        "difficulty": "intermediate",
        "doctrine_version": "1.0",
        "estimated_duration_minutes": 90,
        "tags": ["navigation", "bridge", "colregs", "restricted-waters"],
        "definition": {
            "objectives": [
                "Navigate through simulated restricted channel safely",
                "Apply COLREGS Rule 9 — Narrow Channels",
                "Coordinate with CIC for traffic picture",
            ],
            "initial_conditions": {
                "weather": "Visibility 3nm, Sea State 3",
                "traffic": "3 merchant vessels in channel",
                "time": "Dusk — civil twilight",
                "own_ship": "INS Vikrant, speed 8 knots, heading 045",
            },
            "events": [
                {"t_plus_mins": 5, "event": "Merchant vessel alters course unexpectedly"},
                {"t_plus_mins": 15, "event": "Engine room reports reduced propulsion"},
                {"t_plus_mins": 25, "event": "VHF channel 16 distress call nearby"},
            ],
            "success_criteria": {
                "no_collision": True,
                "speed_compliance": True,
                "correct_signals_used": True,
                "timely_reporting": True,
            },
            "evaluation_rubric": {
                "situational_awareness": 0.30,
                "rules_application": 0.40,
                "communications": 0.20,
                "decision_speed": 0.10,
            },
        },
    },
    {
        "title": "CIC Operations — Anti-Air Threat Prosecution",
        "domain": "cic",
        "difficulty": "advanced",
        "doctrine_version": "1.0",
        "estimated_duration_minutes": 120,
        "tags": ["cic", "anti-air", "threat-prosecution", "radar"],
        "definition": {
            "objectives": [
                "Classify and track inbound air contacts",
                "Coordinate with OOW for manoeuvring",
                "Execute weapons engagement per ROE",
            ],
            "initial_conditions": {
                "weather": "Clear, Sea State 2",
                "contacts": [
                    {"id": "TGT-01", "type": "unknown-air", "bearing": "270", "range_nm": 40},
                    {"id": "TGT-02", "type": "friendly-helo", "bearing": "090", "range_nm": 15},
                ],
                "own_ship": "INS Vishakhapatnam, AA Defence State 2",
            },
            "events": [
                {"t_plus_mins": 8, "event": "TGT-01 IFF returns hostile"},
                {"t_plus_mins": 12, "event": "TGT-01 descends to sea-skimmer altitude"},
                {"t_plus_mins": 18, "event": "Jamming on primary radar"},
            ],
            "success_criteria": {
                "correct_id_within_5min": True,
                "engagement_authorisation_correct": True,
                "blue_on_blue_avoided": True,
            },
            "evaluation_rubric": {
                "contact_management": 0.35,
                "threat_assessment": 0.35,
                "weapons_coordination": 0.20,
                "communications": 0.10,
            },
        },
    },
    {
        "title": "Engineering — Propulsion Casualty Control",
        "domain": "engineering",
        "difficulty": "advanced",
        "doctrine_version": "1.0",
        "estimated_duration_minutes": 75,
        "tags": ["engineering", "propulsion", "casualty-control", "engine-room"],
        "definition": {
            "objectives": [
                "Respond to sudden propulsion failure at sea",
                "Implement casualty control procedures",
                "Restore propulsion within 30 minutes",
                "Maintain safe electrical load",
            ],
            "initial_conditions": {
                "weather": "Sea State 4, 25 knot wind",
                "state": "Ship underway at 15 knots, open ocean",
                "crew": "Normal sea watch",
            },
            "events": [
                {"t_plus_mins": 0, "event": "STBD GT trips — loss of starboard propulsion"},
                {"t_plus_mins": 2, "event": "Electrical bus load alarm"},
                {"t_plus_mins": 10, "event": "Lube oil pressure low on port GT"},
                {"t_plus_mins": 20, "event": "Flooding alarm in engine room bilge"},
            ],
            "success_criteria": {
                "propulsion_restored_30min": True,
                "no_secondary_casualties": True,
                "correct_reporting": True,
            },
            "evaluation_rubric": {
                "procedure_compliance": 0.40,
                "speed_of_response": 0.25,
                "communication": 0.20,
                "leadership": 0.15,
            },
        },
    },
    {
        "title": "Damage Control — Fire and Flooding Scenario",
        "domain": "damage_control",
        "difficulty": "extreme",
        "doctrine_version": "1.0",
        "estimated_duration_minutes": 60,
        "tags": ["damage-control", "fire", "flooding", "survivability"],
        "definition": {
            "objectives": [
                "Control simultaneous fire and flooding",
                "Maintain ship stability",
                "Conduct correct personnel accounting",
                "Prevent loss of watertight integrity",
            ],
            "initial_conditions": {
                "weather": "Night, Sea State 3",
                "state": "Ship in harbour, reduced watch",
                "threat": "Uncontrolled fire in 2-deck stores + flooding in forward bilge",
            },
            "events": [
                {"t_plus_mins": 0, "event": "Fire alarm activates — 2 Deck Fwd stores"},
                {"t_plus_mins": 3, "event": "Flooding detected — Frame 15 bilge"},
                {"t_plus_mins": 8, "event": "Fire spreads to adjacent compartment"},
                {"t_plus_mins": 15, "event": "Power failure to forward section"},
                {"t_plus_mins": 25, "event": "Stability warning — 8 degree list"},
            ],
            "success_criteria": {
                "fire_contained_20min": True,
                "flooding_stopped_15min": True,
                "no_personnel_casualties": True,
                "list_corrected": True,
            },
            "evaluation_rubric": {
                "prioritisation": 0.30,
                "team_coordination": 0.30,
                "technical_execution": 0.25,
                "reporting": 0.15,
            },
        },
    },
    {
        "title": "Small Boats — VBSS Boarding Operation",
        "domain": "small_boats",
        "difficulty": "advanced",
        "doctrine_version": "1.0",
        "estimated_duration_minutes": 90,
        "tags": ["small-boats", "vbss", "boarding", "maritime-security"],
        "definition": {
            "objectives": [
                "Execute Visit Board Search and Seizure (VBSS) procedure",
                "Maintain radio discipline throughout",
                "Complete documentation and evidence preservation",
            ],
            "initial_conditions": {
                "weather": "Day, Sea State 2, 10 knot wind",
                "target": "Suspected drug smuggling dhow",
                "own_forces": "2 x RIBS, 8-person boarding team, armed",
            },
            "events": [
                {"t_plus_mins": 5, "event": "Target vessel attempts evasion"},
                {"t_plus_mins": 12, "event": "Boarding team aboard — armed crew member identified"},
                {"t_plus_mins": 20, "event": "Contraband found — evidence handling required"},
                {"t_plus_mins": 35, "event": "Weather deteriorates — RHIB recovery required"},
            ],
            "success_criteria": {
                "no_blue_casualties": True,
                "correct_escalation_of_force": True,
                "evidence_preserved": True,
                "comms_maintained": True,
            },
            "evaluation_rubric": {
                "tactical_execution": 0.35,
                "rules_of_engagement": 0.30,
                "evidence_handling": 0.20,
                "communications": 0.15,
            },
        },
    },
    {
        "title": "Unmanned Systems — Autonomous Fleet Control",
        "domain": "unmanned_systems",
        "difficulty": "advanced",
        "doctrine_version": "1.0",
        "estimated_duration_minutes": 80,
        "tags": ["unmanned", "uuv", "usv", "drones", "swarm"],
        "definition": {
            "objectives": [
                "Deploy and track autonomous UUV assets",
                "Maintain waypoint tracking stability",
                "Activate cooperative drone swarm decoy shield",
            ],
            "initial_conditions": {
                "weather": "Clear, Sea State 1",
                "assets": ["UUV-Alpha", "USV-Beta", "Drone-Swarm-1"],
                "own_ship": "INS Chennai",
            },
            "events": [
                {"t_plus_mins": 5, "event": "UUV-Alpha reports buoyancy calibration error"},
                {"t_plus_mins": 15, "event": "Autopilot communications link degraded"},
                {"t_plus_mins": 25, "event": "Inbound missile alert — activate swarm decoy shield"},
            ],
            "success_criteria": {
                "buoyancy_stabilized": True,
                "waypoints_aligned": True,
                "decoy_shield_active": True,
            },
            "evaluation_rubric": {
                "system_calibration": 0.35,
                "navigation_tracking": 0.35,
                "cooperative_control": 0.30,
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Doctrine document seed data
# ---------------------------------------------------------------------------
DOCTRINE_DOCS = [
    {
        "title": "Navigation Safety Manual",
        "domain": "bridge",
        "version": "1.0",
        "content_text": (
            "Navigation Safety Manual — Indian Navy Edition 1.0\n\n"
            "1. COLREGS Application\nAll officers of the watch shall apply the International "
            "Regulations for Preventing Collisions at Sea (COLREGS) without exception. "
            "Rule 8 — Action to Avoid Collision — requires early and substantial action. "
            "Rule 9 — Narrow Channels — vessels shall keep to the starboard side of the "
            "fairway or channel as near as is safe and practicable.\n\n"
            "2. Bridge Team Management\nThe OOW shall maintain an effective lookout by sight "
            "and hearing and by all available means. The navigator shall cross-check all "
            "electronic position fixes with visual bearings where possible.\n\n"
            "3. Speed in Restricted Visibility\nIn or near an area of restricted visibility, "
            "a vessel shall proceed at a safe speed adapted to the prevailing circumstances "
            "and conditions. All engines shall be ready for immediate manoeuvre.\n\n"
            "4. Anchoring Procedures\nPrior to anchoring, OOW shall verify holding ground, "
            "scope requirement, and swing circle clearance. Anchor party to be briefed and "
            "stationed 30 minutes prior."
        ),
    },
    {
        "title": "Combat Information Centre Operations Manual",
        "domain": "cic",
        "version": "1.0",
        "content_text": (
            "CIC Operations Manual — Indian Navy Edition 1.0\n\n"
            "1. Track Management\nAll air and surface contacts shall be assigned a track "
            "number within 60 seconds of detection. Track quality ratings (TQ1–TQ5) shall be "
            "maintained and broadcast to all stations.\n\n"
            "2. IFF Procedures\nInterrogation of all contacts shall occur on initial detection. "
            "Squawk mode 3/A responses shall be verified against flight plans. Hostile "
            "declaration requires BOTH no valid IFF AND hostile intent demonstrated.\n\n"
            "3. Weapons Engagement Authority\nEngagement of air threats requires: "
            "(a) Hostile identification, (b) Weapons Free authority from CO, "
            "(c) Safety bearing verification, (d) Blue force deconfliction.\n\n"
            "4. Electronic Warfare\nOn detection of jamming or spoofing, CIC shall "
            "immediately switch to alternate sensor suite, notify CO, and increase "
            "lookout watch. All sensor degradation shall be logged."
        ),
    },
    {
        "title": "Damage Control Manual",
        "domain": "damage_control",
        "version": "1.0",
        "content_text": (
            "Damage Control Manual — Indian Navy Edition 1.0\n\n"
            "1. DCRO Responsibilities\nThe Damage Control Repair Officer is responsible for "
            "the execution of all DC drills and operational response. DCRO shall maintain a "
            "current stability booklet and damage control plan.\n\n"
            "2. Fire Classification\nFires are classified: Class A (Solid combustibles), "
            "Class B (Flammable liquids), Class C (Electrical), Class D (Metal). "
            "Correct extinguishant selection is critical — water on Class C or D fires "
            "is prohibited.\n\n"
            "3. Flooding Response\nOn discovery of flooding: (a) Sound alarm, "
            "(b) Identify source and attempt isolation, (c) Pump out if safe, "
            "(d) Shore up structure with timber shores, (e) Report to DCO.\n\n"
            "4. Stability Management\nIf list exceeds 5 degrees, DCRO shall convene "
            "stability meeting immediately. Damage stability calculations shall be "
            "performed before transferring ballast. Minimum GM of 0.15m to be maintained.\n\n"
            "5. Abandonment\nAbandonment shall only be ordered by the Commanding Officer. "
            "Sequence: Personal survival equipment, emergency radio, liferafts, "
            "man overboard drill, distress signal."
        ),
    },
]

DOCUMENTATION_TOPICS = [
    # --- BRIDGE WATCH & NAVIGATION ---
    {
        "title": "Basic: COLREGS Rule 9 Narrow Channel Navigation",
        "domain": "bridge",
        "description": "Rules of the road for navigating in narrow channels, including right-of-way, vessel signaling, and overtaking.",
        "content_markdown": """# Aegis Navigation: COLREGS Rule 9 (Basic)
Learn the essential rules of navigating safely through narrow channels, shallow fairways, and restricted ports.

---

## 1. Introduction & Hydrodynamic Context
Under **Rule 9** of the International Regulations for Preventing Collisions at Sea (COLREGS), maneuvering in narrow channels presents unique hazards. Due to restricted water depths and widths, vessels experience severe hydrodynamic forces known as the **Bank Effect** (where a vessel's stern is drawn toward the bank and the bow is pushed away) and **Squat** (where the draft increases in shallow water). Understanding these physics is vital to prevent grounding or collision.

---

## 2. The Core Navigation Rule
Under **Rule 9 (a)**:
> A vessel proceeding along the course of a narrow channel or fairway shall keep as near to the outer limit of the channel or fairway which lies on her starboard side as is safe and practicable.

This means you should always **stay to the right**! 

### Operational Guidelines:
- **Small Vessels & Sailing Vessels**: Under **Rule 9 (b)** and **(c)**, vessels of less than 20 meters in length or sailing vessels shall not impede the passage of a vessel which can safely navigate only within a narrow channel or fairway.
- **Fishing Vessels**: Under **Rule 9 (d)**, a vessel engaged in fishing shall not impede the passage of any other vessel navigating within a narrow channel or fairway.

---

## 3. Sound Signals for Overtaking & Blind Bends
In a narrow channel, overtaking can only take place if the vessel to be overtaken takes action to permit safe passing.

### Overtaking Signals (Rule 34 (c)):
| Sound Signal | Intent / Agreement |
| :--- | :--- |
| **Two prolonged blasts followed by one short blast** | "I intend to overtake you on your starboard side" |
| **Two prolonged blasts followed by two short blasts** | "I intend to overtake you on your port side" |
| **One prolonged, one short, one prolonged, and one short** | "I agree to your overtaking request (Permitted)" |

### Blind Bends (Rule 9 (f)):
A vessel nearing a bend or an area of a narrow channel where other vessels may be obscured by an intervening obstruction shall navigate with particular alertness and caution and shall sound **one prolonged blast** (4 to 6 seconds). Any approaching vessel within hearing distance shall answer with **one prolonged blast**.

---

## 4. Operational Watchstanding Checklist
- [ ] Monitor under-keel clearance (UKC) continuously.
- [ ] Secure double-lookout watch on the bridge wings.
- [ ] Sound one prolonged blast when approaching a blind bend.
- [ ] Align steering pumps to maximum response capacity (Dual steering pump operation).
- [ ] Restrict speed to comply with local speed limits and reduce bank suction effects.
""",
        "example_interactive": "HELM STARBOARD 10"
    },
    {
        "title": "Intermediate: COLREGS Rule 10 Traffic Separation Schemes",
        "domain": "bridge",
        "description": "Guidelines for entering, crossing, and proceeding along traffic lanes to prevent head-on collisions in heavy ports.",
        "content_markdown": """# Aegis Navigation: COLREGS Rule 10 (Intermediate)
This section explains the strict procedures required for entering, crossing, and proceeding along Traffic Separation Schemes (TSS).

---

## 1. Introduction to TSS Operations
Traffic Separation Schemes (TSS) are routing measures managed by the International Maritime Organization (IMO) to regulate flow in busy, congested lanes (e.g., Strait of Malacca, English Channel). TSS separates opposing streams of marine traffic through separation zones or lines. Proceeding in a TSS requires absolute adherence to Rule 10 to ensure collision avoidance.

---

## 2. Proceeding Along and Crossing Lanes
Under **Rule 10 (b)** and **(c)**, vessels must follow these guidelines:
1. **Direction of Flow**: Proceed in the appropriate traffic lane in the general direction of traffic flow for that lane.
2. **Separation Line**: So far as practicable, keep clear of a traffic separation line or separation zone.
3. **Entering and Leaving**: Normally join or leave a traffic lane at the termination of the scheme, but when joining or leaving from either side, do so at as small an angle to the general direction of traffic flow as practicable.
4. **Crossing at Right Angles**:
   > A vessel shall, so far as practicable, avoid crossing traffic lanes but if obliged to do so shall cross on a heading as nearly as practicable at right angles to the general direction of traffic flow.

### Why Right Angles?
Crossing at a 90-degree heading ensures that the crossing vessel spends the **minimum amount of time** inside the active traffic lane and presents the most clear, unambiguous aspect (visual profile) to ongoing vessels.

```
       [   Traffic Lane (Westbound) <--   ]
                     ^
                     |  Cross at 90° Heading
                     |
       [==================================]  Separation Zone
                     |
                     |  Cross at 90° Heading
                     ^
       [   Traffic Lane (Eastbound) -->   ]
```

---

## 3. High-Priority Exclusions (Rule 10 (g) - (j))
- **No Anchoring**: A vessel shall, so far as practicable, avoid anchoring within a traffic separation scheme or near its terminations.
- **Inshore Traffic Zones**: A vessel shall not use inshore traffic zones when she can safely use the appropriate traffic lane within the adjacent TSS. Exception applies to vessels of less than 20 meters, sailing vessels, and vessels engaged in fishing.
- **Sailing/Fishing Exclusions**: A vessel engaged in fishing or sailing shall not impede the passage of any vessel proceeding along a traffic lane.

---

## 4. TSS Navigation Checklist
- [ ] Confirm radar targets using ARPA and vector indicators.
- [ ] Calculate the 90-degree true heading vector for crossing.
- [ ] Avoid entering the separation zone unless in an emergency or to cross.
- [ ] Maintain continuous VHF Channel 16 watch and notify Vessel Traffic Services (VTS).
""",
        "example_interactive": "SET_COURSE_TSS 090"
    },
    {
        "title": "Advanced: COLREGS Rule 19 Restricted Visibility Crisis",
        "domain": "bridge",
        "description": "High-tactical requirements for speed adjustments, sound signals, and radar watchkeeping during dense fog crises.",
        "content_markdown": r"""# Aegis Navigation: COLREGS Rule 19 (Advanced)
Special operational mandates for navigating safely when vessels are not in sight of one another due to fog, mist, falling snow, or heavy rainstorms.

---

## 1. Safety Speed & Engine Readiness
Every vessel must proceed at a **safe speed** adapted to the prevailing circumstances and restricted visibility conditions:
- **Rule 19 (b)**: A power-driven vessel shall have her engines ready for immediate maneuver. This requires keeping the engineering watch on standby and operating under "Maneuvering Speed" settings.

---

## 2. Actions Upon Radar Detection (Rule 19 (d))
If you detect another vessel by radar alone:
1. **Plot and Assess**: Determine if a close-quarters situation is developing or if a risk of collision exists.
2. **Execute Early Action**: Avoid late, minor steering adjustments. If making an alteration of course:
   - **DO NOT alter course to port** for a vessel forward of the beam, other than for a vessel being overtaken.
   - **DO NOT alter course towards** a vessel abeam or abaft the beam.

```
                    [ Avoid Port Turns ]
                           \  |  /
             Hostile Target  \|/
                            ( O )
                            / | \
                           /  |  \
                 [ Avoid Abeam/Abaft Turns ]
```

---

## 3. Sound Signals in Restricted Visibility (Rule 35)
Power-driven vessels must sound periodic fog signals (intervals not exceeding 2 minutes):
- **One Prolonged Blast**: Vessel underway and making way through the water.
- **Two Prolonged Blasts** (separated by 2 seconds): Vessel underway but stopped (making no way).
- **One Prolonged + Two Short Blasts**: Vessel restricted in maneuverability, sailing, or engaged in fishing.

---

## 4. Restricted Visibility Emergency Checklist
- [ ] Switch on navigation lights immediately.
- [ ] Post a dedicated lookout on the forecastle (bow) and bridge wings.
- [ ] Place engines on "standby / maneuvering speed".
- [ ] Sound one prolonged blast every 2 minutes using the ship's whistle.
- [ ] Set radar to multiple range scales and commence ARPA tracking (plot CPA/TCPA).
""",
        "example_interactive": "REDUCE_SPEED_SAFETY"
    },

    # --- CIC & WARFARE OPERATIONS ---
    {
        "title": "Basic: Radar Target Range & Bearing Designation",
        "domain": "cic",
        "description": "Fundamentals of radar operation, bearing calculations, and track initiation protocols for unknown targets.",
        "content_markdown": """# Aegis CIC: Target Range & Bearing (Basic)
Master the fundamental combat operations procedures for identifying, calculating, and designating unknown radar tracks.

---

## 1. Principles of Radar Range and Bearing
Radar (Radio Detection and Ranging) systems emit high-frequency radio waves that reflect off target surfaces. The time delay of the returned signal calculates **Range**, while the directional angle of the antenna array measures **Bearing**.
- **True Bearing**: Measured relative to True North (000° to 359°).
- **Relative Bearing**: Measured relative to the ship's bow (000° Right/Left).

---

## 2. Standard Target Report Formatting
All contacts detected by sensor operators must be announced to the Tactical Action Officer (TAO) using standard warfare terminology:
> **"Contact! Track [Number], Bearing [True], Range [Nautical Miles], Speed [Knots]!"**

### Format Breakdown:
- **Designator**: Track identifier assigned by the console (e.g., TGT-01).
- **Bearing**: Reported in three digits (e.g., "Zero Four Five degrees").
- **Range**: Reported in yards or nautical miles (e.g., "Twenty-Two Nautical Miles").

---

## 3. Target Reporting Code Table
| Parameter | Value | Pronunciation / Notation |
| :--- | :--- | :--- |
| **True North** | 000°T | "Three-Zero-Zero True" |
| **Starboard Bow** | 045°R | "Zero-Four-Five Relative" |
| **Threat Target** | Hostile | "Vampire" (Inbound hostile missile) |

---

## 4. Target Acquisition SOP Checklist
- [ ] Calibrate radar gains to reduce sea and rain clutter.
- [ ] Hook the target target and assign a tracking index.
- [ ] Cross-reference target position with civilian marine AIS logs.
- [ ] Report contact bearing and CPA vector to the Bridge watchstanders.
""",
        "example_interactive": "SELECT_BEARING_045"
    },
    {
        "title": "Intermediate: Air Threat Classification and IFF Procedures",
        "domain": "cic",
        "description": "Standard operating procedures for Combat Information Center officers classifying unknown air tracks using IFF.",
        "content_markdown": """# Aegis CIC: Air Threat Classification (Intermediate)
Learn standard operating guidelines for classifying aircraft contacts using cryptographic Identification Friend or Foe (IFF) protocols.

---

## 1. Cryptographic IFF Systems
Identification Friend or Foe (IFF) is a sensor system that queries incoming aircraft transponders. It operates across multiple secure transmission modes to prevent friendly-fire incidents.

### IFF Mode Overview:
- **Mode 1 & 2**: Military mission and unit identification.
- **Mode 3/A**: Standard civilian air traffic control transponder.
- **Mode C**: Automated pressure altitude reporting.
- **Mode 4 & 5**: High-security, cryptographically encrypted military keys.

---

## 2. Track Classification Workflow
Tracks are systematically classified using the following decision tree:

```mermaid
graph TD
    A[Detect Radar Track] --> B{Cryptographic Mode 4/5?}
    B -- Valid --> C[FRIENDLY]
    B -- Invalid/None --> D{Mode 3 flight plan match?}
    D -- Match --> E[COMMERCIAL]
    D -- No Match --> F{Hostile flight path?}
    F -- Yes --> G[SUSPECT/HOSTILE]
    F -- No --> H[UNKNOWN]
```

---

## 3. Declaration of Hostile Intent
Under the Rules of Engagement (ROE), a contact is declared **Hostile** if it exhibits hostile acts or clear hostile intent, such as:
1. Active radar illumination (targeting lock) of own-ship.
2. Inbound flight profile exceeding Mach 1 at low altitude (skimming).
3. Failure to respond to multiple warning queries on Military Air Distress (MAD - 243.0 MHz) or International Air Distress (IAD - 121.5 MHz).

---

## 4. Classification checklist
- [ ] Query the track on Mode 4 and Mode 5 cryptographic IFF.
- [ ] Check commercial flight schedules for civilian route matches.
- [ ] Coordinate with regional air traffic control via secure datalink (Link 16).
- [ ] Initiate voice warnings over Military and International Distress frequencies.
""",
        "example_interactive": "DECLARE TGT-01 HOSTILE"
    },
    {
        "title": "Advanced: Anti-Air Shield Defense & Command Authorization",
        "domain": "cic",
        "description": "High-priority coordination of SM-2 missiles, tactical fire control, and Command approval under electronic jamming.",
        "content_markdown": """# Aegis CIC: Air Shield Defense (Advanced)
High-intensity defense coordination procedures against saturation anti-ship missile attacks under active electronic warfare.

---

## 1. Threat Evaluation and Weapon Assignment (TEWA)
When defending against incoming supersonic sea-skimming missiles (designated **Vampires**), combat operators utilize the Aegis Combat System to prioritize targets based on Time to Intercept (TTI) and Closest Point of Approach (CPA).

---

## 2. Weapons Launch Doctrine
The Tactical Action Officer (TAO) coordinates fire control using a layered defense approach:
- **Outer Layer**: Standard Missile 2 (SM-2) or Standard Missile 6 (SM-6) for long-range intercepts.
- **Middle Layer**: Evolved SeaSparrow Missiles (ESSM) for medium-range defense.
- **Inner Layer**: Phalanx Close-In Weapon System (CIWS) and decoy chaff launchers (Nulka SRBOC) for terminal intercept.

```
       [ Long-Range ]           [ Medium-Range ]          [ Terminal Defense ]
           SM-2 / SM-6                ESSM                    CIWS / Chaff
       <--- 100+ NM --->       <--- 20-30 NM --->        <--- 1-2 NM --->
```

---

## 3. Step-by-Step Engagement Protocol
1. **Jamming Resolution**: On detecting electronic jamming, activate Frequency Hopping and burn-through radar modes.
2. **Target Tracking Lock**: Achieve continuous fire-control tracking lock using SPY-1 radar directors.
3. **Command Approval**: Obtain final weapon release authorization from the Commanding Officer.
4. **Fire Command**: Execute launcher release sequence: **"Fire SM-2, Track 02!"**

---

## 4. Anti-Air Shield Readiness Checklist
- [ ] Confirm SPY-1 radar is set to maximum threat power.
- [ ] Align launcher guide rails with standby missiles.
- [ ] Arm decoy chaff and active electronic decoy systems.
- [ ] Establish secure coordination with escort combatants via Link 16.
""",
        "example_interactive": "FIRE_SM2_TRACK_02"
    },

    # --- MARINE ENGINEERING ---
    {
        "title": "Basic: Propulsion Auxiliaries & Mechanical Lube Alignment",
        "domain": "engineering",
        "description": "Essential training on alignment of oil loops, fuel pumps, and secondary gearboxes prior to startup sequence.",
        "content_markdown": """# Aegis Engineering: Lube Oil Alignment (Basic)
Master the mechanical valve lineups and system alignments required to safely circulate lube oil through major ship propulsion gearboxes.

---

## 1. Engineering Principles
Naval gas turbines and reduction gears operate under high mechanical loads and thermal stresses. Running these systems without proper Lubricating Oil (Lube Oil) circulation will cause immediate friction damage, bearing melt, and catastrophic propulsion failure. The lube oil loop must be fully aligned and pressurized prior to starting any turbine.

---

## 2. Standard Lube Oil Circuit Lineup
The lube oil circuit consists of a sump, pumps, strainers, purifiers, and coolers. Follow this sequence for system alignment:
1. **Sump Lineup**: Check the lube oil sump level (must be between 70% and 85%).
2. **Valve Positions**:
   - **Suction Valves**: Ensure primary suction valves from the sump to the lube oil service pumps are open.
   - **Bypass Valves**: Ensure the bypass line around the cooler is closed, routing all oil through the lube oil cooler.
3. **Filter Engagement**: Verify the duplex strainers are aligned to the primary filter element.

---

## 3. Operational Parameter Targets
| Parameter | Minimum Value | Nominal Value | Maximum Value |
| :--- | :--- | :--- | :--- |
| **Oil Temp** | 32°C | 43°C | 55°C |
| **Header Press** | 15 PSI | 25 PSI | 35 PSI |
| **Sump level** | 65% | 75% | 85% |

---

## 4. Mechanical Alignment Checklist
- [ ] Verify lube oil heater is engaged (pre-heats oil to minimum 32°C).
- [ ] Align duplex filters and confirm pressure differential is below 2 PSI.
- [ ] Open main reduction gear (MRG) spray header supply valve.
- [ ] Switch on the auxiliary electric lube oil pump and verify header pressure stabilizes.
""",
        "example_interactive": "OPEN_LUBE_BYPASS"
    },
    {
        "title": "Intermediate: LM2500 Gas Turbine Start Sequence",
        "domain": "engineering",
        "description": "Technical documentation covering the starting sequence, interlocks, and emergency trip limits for propulsion gas turbines.",
        "content_markdown": """# Aegis Engineering: LM2500 Start Sequence (Intermediate)
Step-by-step technical procedures to successfully spin, ignite, and stabilize the General Electric LM2500 gas turbine propulsion engine.

---

## 1. Engine Architecture & Pre-Start Interlocks
The LM2500 is a marine aeroderivative gas turbine consisting of a gas generator (compressor, combustor, high-pressure turbine) and a free power turbine. Before starting, the Unified Fuel Control (UFC) verifies the following safety interlocks:
- **Gearbox Pressure**: Lube oil pressure > 15 PSI.
- **Enclosure Temperature**: Enclosure cooling fan active.
- **Bleed Air**: Starter air pressure > 45 PSI.

---

## 2. Step-by-Step Start Timeline
The start sequence is highly automated but must be monitored closely:

```
[ Air Crank ]           [ Ignition Engage ]          [ Self-Sustaining ]
Purge gas generator        Starter igniters open         Engine reaches idle
0 - 1200 RPM               1200 - 3000 RPM              4500+ RPM
```

1. **Purge Crank**: Engage the starter air valve to spin the engine to 1200 RPM, purging any residual fuel vapors from the enclosure.
2. **Ignition & Fuel**: At 1200 RPM, engage the spark igniters and open the fuel fuel shutoff valves.
3. **Acceleration**: Monitor the Exhaust Gas Temperature (EGT) rise. The engine must accelerate past the self-sustaining speed of 4500 RPM.
4. **Starter Disengage**: At 4800 RPM, the starter air valve automatically closes.

---

## 3. Post-Start Verification checklist
- [ ] Confirm EGT stabilizes below 400°C at idle.
- [ ] Check fuel manifold pressure (nominally 120 PSI).
- [ ] Verify vibration levels are within normal limits (< 2.0 mils).
- [ ] Ensure enclosure fire suppression system (CO2/Halon) is armed.
""",
        "example_interactive": "START_TURBINE"
    },
    {
        "title": "Advanced: Thermal Overheat Recovery & Fuel Isolation",
        "domain": "engineering",
        "description": "Critical emergency checklist to suppress severe exhaust gas thermal trip violations and manage system cooling.",
        "content_markdown": """# Aegis Engineering: Thermal Overheat Recovery (Advanced)
Emergency response guidelines for managing high exhaust gas temperature (EGT) spikes and turbine thermal trips on propulsion gas turbines.

---

## 1. Thermodynamics of a "Hot Start"
A **Hot Start** occurs when the fuel-to-air ratio in the combustion chamber is too rich, or when compressor airflow is restricted during start-up. This causes temperatures in the high-pressure turbine to rise rapidly, threatening to melt turbine blades. Immediate action is required to prevent a catastrophic thermal crisis.

---

## 2. Emergency Response Protocol (High EGT > 840°C)
If EGT exceeds safety parameters (840°C):
1. **Immediate Fuel Isolation**: Shut down the fuel supply instantly by closing the quick-acting emergency fuel shutoff valves.
2. **Enclosure Ventilation**: Maintain enclosure cooling blowers to evacuate ambient heat.
3. **Motor the Engine (Post-Shutdown Cooling)**:
   > Engage the auxiliary starter air valve to crank the engine (without fuel) for at least 5 minutes. This draws cool ambient air through the compressor and combustion chamber, cooling the turbine blades down below 200°C.
4. **Rotor Bow Prevention**: Continue slow mechanical rotation (turning gear) to prevent shaft bowing due to uneven cooling.

---

## 3. Critical Temperature Thresholds
| Limit Type | Value | Action Required |
| :--- | :--- | :--- |
| **Normal Operational Max** | 720°C | Monitor exhaust ventilation |
| **High Alarm** | 780°C | Reduce propulsion pitch / throttle |
| **Automatic Safety Trip** | 840°C | Automatic shutdown / Execute Hot Start cooling |

---

## 4. Emergency Recovery Checklist
- [ ] Throw the emergency fuel isolation quick-release lever.
- [ ] Verify secondary fuel manifold valves are fully closed.
- [ ] Align high-pressure starter bleed air and begin dry cranking.
- [ ] Monitor compressor casing for any sound of metallic rubbing (bearing failure).
""",
        "example_interactive": "SHUT_FUEL_VALVE_FAST"
    },

    # --- DAMAGE CONTROL ---
    {
        "title": "Basic: Aegis Fire Classification & Boundaries",
        "domain": "damage_control",
        "description": "Core classification of structural solid, liquid, electrical, and metallic fires, and cooling boundaries.",
        "content_markdown": """# Aegis Damage Control: Fire Classification (Basic)
Learn the core classifications of fires on board naval vessels and master the procedures for establishing boundaries.

---

## 1. The Physics of Fire: The Tetrahedron
Fire requires four elements to exist: Fuel, Oxygen, Heat, and an Uninhibited Chemical Chain Reaction. Removing any of these elements collapses the fire.

---

## 2. Classifications of Fire & Extinguishing Agents
Naval fires are classified by their fuel source, requiring specific extinguishing agents to prevent flare-ups or electrocution:
- **Class A**: Ordinary solid combustibles (wood, paper, bedding).
  - *Primary Agent*: **Water (Firemain)** or AFFF (Aqueous Film Forming Foam).
- **Class B**: Flammable liquids (F-76 fuel oil, JP-5 aviation gas, lube oil).
  - *Primary Agent*: **AFFF** (smothers the oxygen supply) or Halon/Heptane.
- **Class C**: Electrical fires (switchboards, consoles, wiring).
  - *Primary Agent*: **Carbon Dioxide (CO2)** (non-conductive gas). Never use water!
- **Class D**: Combustible metals (magnesium flares, aircraft components).
  - *Primary Agent*: **CO2 / Dry Powders** or high-volume water fog from a safe distance.

---

## 3. Standard Boundary Isolation SOP
To prevent fire from spreading throughout the ship's compartments, Damage Control teams establish strict boundaries:
1. **Vertical Boundaries**: Cool the deck above and the overhead below the affected space using fire hoses.
2. **Horizontal Boundaries**: Cool the forward, aft, port, and starboard bulkheads adjacent to the fire.
3. **Smoke Boundaries**: Secure all ventilation dampers and seal structural hatches to contain lethal carbon monoxide gases.

---

## 4. Boundary Establishment Checklist
- [ ] Check adjacent spaces for heat levels (use thermal imaging sensors).
- [ ] Remove all flammable materials from adjacent bulkheads (paint, paper, oil canisters).
- [ ] Lay fire hoses to adjacent compartments and continuously wet down bulkheads.
- [ ] Secure all electrical power and mechanical ventilation to the fire zone.
""",
        "example_interactive": "SET_FIRE_BOUNDARY"
    },
    {
        "title": "Intermediate: Bulkhead Shoring & Compartment Isolation",
        "domain": "damage_control",
        "description": "Tactical deployment of timber and steel shores to reinforce fractured structures under heavy listing.",
        "content_markdown": """# Aegis Damage Control: Bulkhead Shoring (Intermediate)
Master the structural engineering principles and assembly procedures required to shore up buckling bulkheads and contain flooding.

---

## 1. Introduction to Shoring
Shoring is the process of supporting a damaged structure (bulkheads, decks, hatches) using heavy timbers or steel poles to prevent structural collapse under hydrostatic pressure.

---

## 2. Shoring Materials & Structural Components
A standard shoring assembly consists of:
- **Shores**: The compression members (wooden logs like Douglas Fir, or adjustable steel telescopic cylinders).
- **Shoals**: Flat wooden boards placed under the ends of shores to distribute the load over a larger area.
- **Strongback**: A heavy beam placed vertically or horizontally directly against the weakened bulkhead to distribute pressure.
- **Wedges**: Wooden blocks driven in pairs to tighten the assembly and apply initial compression.

```
       [ Weakened Bulkhead ]
                ||
                || <--- Strongback
                ||=======o================== [ Secure Deck Element ]
                ||      /  Steel Telescopic
                ||     /      Shore
                ||    /
                ||===o
```

---

## 3. Calculations for Load Capacity
Steel shores are highly adjustable and hold greater weight than timber shores:
- **Model 3-5 (3 to 5 feet)**: Collapsed capacity: 20,000 lbs. Fully extended capacity: 12,000 lbs.
- **Model 6-11 (6 to 11 feet)**: Collapsed capacity: 20,000 lbs. Fully extended capacity: 6,000 lbs.

---

## 4. Bulkhead Reinforcement Checklist
- [ ] Establish compartment boundaries and secure hatch seals.
- [ ] Cut wooden shores slightly shorter than measured length to accommodate wedges.
- [ ] Place shoals directly over structural deck frames (never on flat sheet metal).
- [ ] Drive wedges in pairs from opposite directions using shoring mallets.
- [ ] Monitor shoring pressure continuously for joint slipping.
""",
        "example_interactive": "APPLY_BULKHEAD_SHORE"
    },
    {
        "title": "Advanced: CBRN Collective Protection Systems",
        "domain": "damage_control",
        "description": "Deploying high-pressure overpressure filters, closed-loop recycling, and decontamination air locks during gas attacks.",
        "content_markdown": """# Aegis Damage Control: CBRN Protocols (Advanced)
Comprehensive procedures for protecting ship personnel and securing internal spaces during Chemical, Biological, Radiological, and Nuclear (CBRN) attacks.

---

## 1. Collective Protection System (CPS) Architecture
Naval vessels are divided into pressurized zones called **Collective Protection System (CPS)** zones. CPS protects against airborne contaminants by maintaining internal compartments at a higher air pressure than the outside atmosphere (overpressure). This positive pressure prevents contaminated external air from leaking in.

---

## 2. Decontamination Air Lock Operations
When personnel enter or exit the CPS zone, they must pass through a multi-stage **Decontamination Air Lock (DAL)**:
1. **Gross Decon Station**: Wash down protective suits (IPE/MOPP gear) to remove chemical or radiological particles.
2. **Outer Air Lock**: Evacuate and purge air using high-volume carbon filtration blowers.
3. **Inner Air Lock**: Verify zero chemical agent detection before opening the hatch to the clean zone.

---

## 3. CBRN Defense Status Levels (MOPP Levels)
| MOPP Level | Threat Profile | Action Required |
| :--- | :--- | :--- |
| **MOPP 1** | Attack Suspected | Issue gas masks; verify CPS zone integrity |
| **MOPP 2** | Attack Probable | Set protective mask carrier on belt; pre-position decon kits |
| **MOPP 3** | Attack Imminent | Don gas mask and protective suit; close all weatherdeck hatches |
| **MOPP 4** | Active Attack | Don gloves and boots; activate full CPS pressurized filters |

---

## 4. CBRN Defense Checklist
- [ ] Set ship to MOPP Level 4.
- [ ] Confirm CPS zone pressure exceeds 2.0 inches of water column.
- [ ] Switch ship ventilation systems to "Recirculate / Carbon Filter" mode.
- [ ] Deploy chemical agent detector paper (M9/M8 paper) to weatherdecks.
- [ ] Verify firemain pressure is aligned to weatherdeck washdown nozzles.
""",
        "example_interactive": "ACTIVATE_CBRN_LOCK"
    },

    # --- SMALL BOATS OPERATIONS ---
    {
        "title": "Basic: RHIB Launch & Davit Alignment",
        "domain": "small_boats",
        "description": "Basic launching procedures for Rigid Hull Inflatable Boats using hydraulic tension davits.",
        "content_markdown": """# Aegis Small Boats: RHIB Launch (Basic)
Master the mechanical launch operations, davit calibrations, and safety procedures required to deploy Rigid Hull Inflatable Boats.

---

## 1. Equipment Profile: The Hydraulic Tension Davit
Rigid Hull Inflatable Boats (RHIBs) are launched using specialized single-pivot or dual-point hydraulic davit arms. These davits maintain constant line tension to prevent the boat from slamming against the ship's hull in rough seas (constant tension mode).

---

## 2. Launch Sequence & Coordination
Launching a RHIB in active seaways requires precise timing between the deck crew and the boat coxswain:
1. **Crew Boarding**: The boat crew boards the RHIB while it is held in the stowed position at the embarkation deck.
2. **Slew Out**: Pivot the davit arm out over the side of the ship.
3. **Lowering**: Lower the RHIB smoothly into the water.
4. **Release Sequence**:
   - **Sea Painter**: Release the sea painter line (tethers the bow to the ship to maintain heading).
   - **Quick Release Hook**: Pull the quick-release release lever when the RHIB rests on a wave crest to prevent snap loads.

---

## 3. Operational Limits for Boat Launching
- **Maximum Sea State**: Sea State 4 (waves up to 4 feet).
- **Ship Speed**: Maximum 8 knots underway.
- **Wind Speed**: Maximum 25 knots.

---

## 4. Davit Launch Checklist
- [ ] Verify boat crew is wearing approved life vests and protective helmets.
- [ ] Calibrate hydraulic constant tension valves to boat weight.
- [ ] Install RHIB hull drain plug securely.
- [ ] Align communication links between the Bridge and the Davit Station.
- [ ] Test coxswain engine start prior to slewing out.
""",
        "example_interactive": "LAUNCH_RHIB_DAVIT"
    },
    {
        "title": "Intermediate: VBSS Boarding & Tactical Query",
        "domain": "small_boats",
        "description": "Standard operating procedures for querying commercial vessels and launching board teams.",
        "content_markdown": """# Aegis Small Boats: VBSS Operations (Intermediate)
Standard operating guidelines for executing maritime interdiction, querying suspect merchant vessels, and launching tactical boarding forces.

---

## 1. Introduction to VBSS Operations
Visit, Board, Search, and Seizure (VBSS) operations are conducted to enforce maritime embargoes, combat piracy, and counter smuggling. VBSS actions must be grounded in international law (UNCLOS) and require disciplined tactical execution.

---

## 2. Pre-Boarding Bridge Queries
Before a boarding force is deployed, the parent ship's bridge conducts a standardized query of the target vessel via VHF Channel 16:
> **"Suspect Vessel, this is Coalition Warship. State your vessel name, registry, cargo, port of origin, and destination."**

---

## 3. Tactical Boarding Phase Workflow
The boarding sequence is divided into three tactical phases:

```
[ Ingress & Approach ]        [ Boarding & Securing ]        [ Search & Control ]
Approach at blind angles        Hook-and-ladder climb         Secure crew; inspect
and evaluate threat.           and clear upper margins.      manifest and cargo logs.
```

1. **Approach**: RHIBs approach the suspect vessel from its stern quarter (a radar blind spot).
2. **Access**: Deploy tactical hook ladders to the target gunwale.
3. **Sweep**: Boarding team climbs, secures the weatherdecks, and sweeps the bridge and engine room to control the vessel.
4. **Search**: Inspect cargo hold against the vessel manifest.

---

## 4. VBSS Execution Checklist
- [ ] Complete tactical bridge query and record transponder data.
- [ ] Brief boarding team on Rules of Engagement (ROE) and force escalation limits.
- [ ] Equip team with active communications and biometric collection kits.
- [ ] Establish high-caliber cover fire from the parent warship's deck mounts.
""",
        "example_interactive": "SEND_BOARDING_FORCE"
    },
    {
        "title": "Advanced: VBSS Tactical Extraction Under Fire",
        "domain": "small_boats",
        "description": "Complex tactical withdrawal of small boarding crafts under extreme sea conditions and active threat envelopes.",
        "content_markdown": """# Aegis Small Boats: Tactical Extraction (Advanced)
Special high-intensity operational procedures for extracting boarding forces under active threat fire and heavy weather conditions.

---

## 1. Tactical Withdrawal Doctrine
When a boarding team encounters overwhelming hostile force or an active fire envelope, the parent warship coordinates a **Hot Extraction**. This requires highly synchronized boat maneuvering, suppressive fire support, and smoke deployment to mask withdrawal.

---

## 2. Defensive RHIB Maneuvering
To survive close-range small arms and RPG fire during extraction:
- **Defensive S-Turns**: RHIB coxswains execute high-speed S-turns to disrupt hostile targeting solutions.
- **Visual Obscuration**: Launch active smoke screen canisters from the parent ship and extraction craft.
- **Suppressive Cover**: Parent ship deck mounts (25mm bushings, 50-caliber machine guns) suppress hostile firing positions.

---

## 3. Extraction Action Table
| Phase | Action | Responsibility |
| :--- | :--- | :--- |
| **Phase 1** | Sound extraction alert; fall back to gunwale muster | Boarding Team Leader |
| **Phase 2** | Initiate suppressive fire and deploy smoke screens | Gunner / Parent Ship |
| **Phase 3** | Secure fast recovery line and hook RHIB to davit | Coxswain / Deck Crew |

---

## 4. Emergency Extraction Checklist
- [ ] Confirm all boarding team members are accounted for.
- [ ] Coordinate suppressive fire sectors with bridge fire control.
- [ ] Launch smoke pots on the windward side of the target vessel.
- [ ] Set RHIB engine throttles to maximum backup capacity.
- [ ] Prepare medical triage station in the ship's hangar.
""",
        "example_interactive": "INITIATE_TACTICAL_EXTRACTION"
    },

    # --- UNMANNED SYSTEMS ---
    {
        "title": "Basic: UUV Buoyancy & Depth Control",
        "domain": "unmanned_systems",
        "description": "Operational checklists for stabilizing underwater vehicles using trim tanks and buoyancy pumps.",
        "content_markdown": """# Aegis Unmanned Systems: UUV Trim (Basic)
Learn the physical principles and control checklists required to adjust variable ballast and maintain depth control on Unmanned Underwater Vehicles (UUVs).

---

## 1. Physics of UUV Depth Control
Unmanned Underwater Vehicles (UUVs) utilize variable ballast tanks, trim tanks, and external hydroplanes (fins) to navigate through the water column.
- **Positive Buoyancy**: Vehicle rises (water blown from ballast tanks).
- **Negative Buoyancy**: Vehicle sinks (water flooded into ballast tanks).
- **Neutral Buoyancy**: Vehicle maintains depth without motor effort.

---

## 2. Pitch and Trim Calibration
To ensure stable navigation, the UUV's center of gravity must align with its center of buoyancy.
1. **Trim Tanks**: Adjust forward and aft trim volumes to eliminate any bow-up or bow-down pitch bias.
2. **Speed-to-Depth Relationship**: Fin controls are ineffective at low speeds; buoyancy engines must be utilized for vertical movement below 1.5 knots.

---

## 3. Variable Ballast Targets
| Variable | Value | Status Indicator |
| :--- | :--- | :--- |
| **Fwd Trim Vol** | 1.2 Liters | Balanced |
| **Aft Trim Vol** | 1.2 Liters | Balanced |
| **Buoyancy Engine** | 0.0 Liters | Neutrally Buoyant |

---

## 4. Pre-Launch Buoyancy Checklist
- [ ] Inspect external hydroplane control linkages for physical damage.
- [ ] Calibrate internal depth pressure sensors.
- [ ] Verify battery compartment seal integrity (confirm zero water leakage).
- [ ] Perform variable ballast pump cycle test (dry run).
""",
        "example_interactive": "CALIBRATE_UUV_TRIM"
    },
    {
        "title": "Intermediate: USV Waypoint Tracking & Paths",
        "domain": "unmanned_systems",
        "description": "Configuring unmanned surface vehicles to calculate collision-free intercept routes in congested waters.",
        "content_markdown": """# Aegis Unmanned Systems: Waypoint Navigation (Intermediate)
Standard operating guidelines for configuring autonomous path-planning, obstacle avoidance, and waypoint tracking algorithms on Unmanned Surface Vehicles (USVs).

---

## 1. Autonomous Path Planning & Navigation
Unmanned Surface Vehicles (USVs) calculate routes using real-time GPS data, onboard LIDAR, and electronic navigational charts (ENC). The autopilot follows a sequence of pre-defined coordinates called **Waypoints**.

---

## 2. Obstacle & Collision Avoidance (COLREGS Compliance)
USV navigation computers must process COLREGS rules when calculating paths around other vessels:
- **Give-Way Situations**: The USV must calculate a detour to pass safely astern of standing contacts.
- **Vector Field Guidance**: Autopilots use vector equations to smooth turns between waypoints, reducing rudder wear and maintaining engine efficiency.

```
       [ Starting Point ] --------> ( Detour Waypoint ) --------> [ Target Point ]
                                          |
                                    Hostile Radar
                                     Contact Zone
```

---

## 3. Path Parameter Targets
- **Waypoint Radius**: 10 meters (distance at which waypoint is declared "passed").
- **Cross-Track Error (XTE)**: Keep below 2.0 meters (permissible lateral deviation from the planned course).
- **Safe Depth Contour**: Assured depth > UUV/USV draft + 1.5 meters.

---

## 4. Autopilot Configuration Checklist
- [ ] Load latest electronic charts and verify safe depth zones.
- [ ] Input target coordinate waypoints into the navigation computer.
- [ ] Test the emergency satellite link fallback system.
- [ ] Confirm autopilot cross-track error bounds are armed.
""",
        "example_interactive": "ALIGN_USV_WAYPOINTS"
    },
    {
        "title": "Advanced: Drone Swarm Decoy Shield Deployment",
        "domain": "unmanned_systems",
        "description": "Synchronizing surface, underwater, and aerial swarm assets using decentralized cooperative navigation.",
        "content_markdown": """# Aegis Unmanned Systems: Drone Swarm Shield (Advanced)
Cooperative multi-agent control procedures for deploying defensive drone swarms to protect capital warships against saturation missile attacks.

---

## 1. The Physics of Swarm Decoy Shields
When protecting a target ship from incoming anti-ship cruise missiles, multiple aerial and surface drones coordinate to deploy a **Decoy Shield**. Drones carry active radar reflectors and heat simulators (chaff/flares) to create a giant radar cross-section (RCS) signature. This signature distracts the incoming missile's seeker, drawing it away from the ship.

---

## 2. Decentralized Cooperative Control
The drone swarm operates without a single point of failure using decentralized consensus algorithms. Drones maintain relative distance and coordinate maneuvers using local peer-to-peer radio frequency datalinks:
- **Cohesion**: Keep close proximity to swarm members.
- **Alignment**: Match heading and velocity with nearby drones.
- **Separation**: Avoid collisions within the swarm.

---

## 3. Swarm Deployment Sequence
1. **Launch Alert**: Detect inbound hostile supersonic missile trackingown-ship.
2. **Rapid Deployment**: Launch drone swarms from high-speed pneumatics on the weatherdeck.
3. **Decoy Array Alignment**: Drones fly to a tactical offset distance (1-2 NM from own-ship) and align in a decoy plane.
4. **Signature Activation**: Engage high-power active electromagnetic signature generators to mimic the parent ship.

---

## 4. Swarm Shield Deployment Checklist
- [ ] Verify pneumatic drone launcher pressure holds at 3000 PSI.
- [ ] Sync drone peer-to-peer encryption keys.
- [ ] Align decoy offset coordinates relative to the threat's approach vector.
- [ ] Arm active electromagnetic decoy arrays on all swarm units.
""",
        "example_interactive": "LAUNCH_SWARM_DECOY"
    }
]


def seed(db):
    print("Seeding GLIMMORA AEGIS database...")

    # --- Admin user as creator for scenarios/docs ---
    # Find or create admin first (needed as FK for scenarios)
    admin_user = None

    # Create users
    created_users: dict[str, User] = {}
    for u_data in USERS:
        existing = db.query(User).filter(User.service_number == u_data["service_number"]).first()
        if existing:
            print(f"  [SKIP] User exists: {u_data['service_number']} — {u_data['name']}")
            created_users[u_data["service_number"]] = existing
        else:
            user = User(
                id=uuid.uuid4(),
                service_number=u_data["service_number"],
                name=u_data["name"],
                rank=u_data["rank"],
                unit=u_data["unit"],
                role=u_data["role"],
                password_hash=hash_password(u_data["password"]),
                classification_clearance=u_data["classification_clearance"],
                is_active=True,
                created_at=_now(),
                updated_at=_now(),
            )
            db.add(user)
            db.flush()
            created_users[u_data["service_number"]] = user
            print(
                f"  [OK]   Created user: {u_data['service_number']} — {u_data['name']} ({u_data['role']})"
            )

    db.commit()

    # Identify admin and instructor for FK usage
    admin_user = created_users.get("IN-2008-003")
    created_users.get("IN-2019-042")
    creator_id = admin_user.id if admin_user else list(created_users.values())[0].id

    # Create scenarios
    for s_data in SCENARIOS:
        existing = db.query(Scenario).filter(Scenario.title == s_data["title"]).first()
        if existing:
            print(f"  [SKIP] Scenario exists: {s_data['title'][:60]}")
        else:
            scenario = Scenario(
                id=uuid.uuid4(),
                title=s_data["title"],
                domain=s_data["domain"],
                difficulty=s_data["difficulty"],
                doctrine_version=s_data["doctrine_version"],
                definition=s_data["definition"],
                created_by=creator_id,
                estimated_duration_minutes=s_data["estimated_duration_minutes"],
                tags=s_data["tags"],
                is_archived=False,
                created_at=_now(),
                updated_at=_now(),
            )
            db.add(scenario)
            print(f"  [OK]   Created scenario: {s_data['title'][:60]} ({s_data['domain']})")

    db.commit()

    # Create doctrine documents
    for d_data in DOCTRINE_DOCS:
        existing = (
            db.query(DoctrineDocument).filter(DoctrineDocument.title == d_data["title"]).first()
        )
        if existing:
            print(f"  [SKIP] Doctrine doc exists: {d_data['title']}")
        else:
            import hashlib

            content_hash = hashlib.sha256(d_data["content_text"].encode()).hexdigest()
            doc = DoctrineDocument(
                id=uuid.uuid4(),
                title=d_data["title"],
                domain=d_data["domain"],
                version=d_data["version"],
                content_hash=content_hash,
                content_text=d_data["content_text"],
                is_active=True,
                approved_by=creator_id,
                created_at=_now(),
                updated_at=_now(),
            )
            db.add(doc)
            print(f"  [OK]   Created doctrine doc: {d_data['title']} (v{d_data['version']})")

    db.commit()

    # Create documentation topics
    for t_data in DOCUMENTATION_TOPICS:
        existing = (
            db.query(DocumentationTopic).filter(DocumentationTopic.title == t_data["title"]).first()
        )
        if existing:
            existing.content_markdown = t_data["content_markdown"]
            existing.description = t_data["description"]
            db.add(existing)
            print(f"  [UPDATE] Updated documentation topic content: {t_data['title']}")
        else:
            topic = DocumentationTopic(
                id=uuid.uuid4(),
                title=t_data["title"],
                domain=t_data["domain"],
                description=t_data["description"],
                content_markdown=t_data["content_markdown"],
                example_interactive=t_data["example_interactive"],
                created_by=creator_id,
                is_active=True,
                created_at=_now(),
                updated_at=_now(),
            )
            db.add(topic)
            print(f"  [OK]   Created documentation topic: {t_data['title']} ({t_data['domain']})")

    db.commit()

    # Dump 100 training sessions managed by admin credentials (instructor_id = creator_id)
    existing_sessions_count = db.query(DBTrainingSession).count()
    if existing_sessions_count >= 100:
        print(f"  [SKIP] Database already contains {existing_sessions_count} sessions. Skipping dump.")
    else:
        # We need to ensure we have at least some scenarios and trainees
        all_scenarios = db.query(Scenario).all()
        all_trainees = db.query(User).filter(User.role == "trainee").all()
        
        if all_scenarios and all_trainees:
            import random
            from datetime import timedelta
            
            statuses = ["completed", "completed", "completed", "completed", "completed", "paused", "aborted"]
            notes_templates = {
                "bridge": [
                    "Officer showed exceptional navigational awareness under COLREGS narrow channel rules.",
                    "Proper Helm control exercised. Rudder responses aligned with voyage guidelines.",
                    "Excellent speed adjustment in restricted visibility during shipping lane transit.",
                    "Minor delay in sounding sound signals but overall stable navigation.",
                    "Outstanding watchkeeping. Successfully cleared the pilot boarding station."
                ],
                "cic": [
                    "Proper application of Identification Friend or Foe (IFF) cryptographical interrogations.",
                    "Demonstrated outstanding track threat classification speed under radar jamming.",
                    "Weapons free engagement sequence performed according to standard rules of engagement.",
                    "Good sensor alignment. Contacts monitored and designated correctly.",
                    "Satisfactory combat operations logging. Action state coordinated perfectly with Navigator."
                ],
                "engineering": [
                    "LM2500 compressor startup procedure executed safely without any thermal trip violations.",
                    "Auxiliary lube oil and fuel interlocks verified before cranks. Excellent safety oversight.",
                    "Swift containment of a minor fuel leak on exhaust turbine intake manifold.",
                    "Outstanding command of turbine start interlock criteria. Warm up curve monitored.",
                    "Pre-checks executed within standard checklist parameters. Steady state achieved."
                ],
                "damage_control": [
                    "Excellent tactical deployment of repair teams to forward compartment fire.",
                    "Shoring team acted quickly. Flooding isolated within 12 minutes of bulkhead rupture.",
                    "Good ballast allocation to correct ship stability and counter list.",
                    "Proper selection of carbon dioxide extinguishants on Class C electrical engine fire.",
                    "Satisfactory compartmentalization and boundary cooling procedures."
                ],
                "small_boats": [
                    "VBSS boarding operation executed under sea state 3 with high tactical safety.",
                    "Correct application of Rules of Engagement (ROE) when querying smuggler crew.",
                    "Excellent recovery of Rigid Hull Inflatable Boats under heavy winds.",
                    "Evidence handling and packaging conducted systematically.",
                    "Effective communications discipline maintained with mother ship."
                ]
            }

            print(f"  [OK]   Dumping {100 - existing_sessions_count} sessions managed by CMDE Sanjay Rao (Admin)...")
            for i in range(100 - existing_sessions_count):
                scenario = random.choice(all_scenarios)
                trainee = random.choice(all_trainees)
                
                status = random.choice(statuses)
                started_dt = _now() - timedelta(days=random.randint(1, 30), hours=random.randint(1, 23), minutes=random.randint(1, 59))
                duration = random.randint(25, 85)
                ended_dt = started_dt + timedelta(minutes=duration) if status == "completed" else None
                
                # Dynamic scoring
                overall = random.randint(72, 98)
                score_obj = {
                    "overall": overall,
                    "technical_execution": random.randint(70, 100),
                    "team_coordination": random.randint(65, 100),
                    "prioritisation": random.randint(70, 100)
                } if status == "completed" else None
                
                notes = random.choice(notes_templates.get(scenario.domain, ["Satisfactory performance across standard training modules."]))
                
                session = DBTrainingSession(
                    id=uuid.uuid4(),
                    scenario_id=scenario.id,
                    trainee_id=trainee.id,
                    instructor_id=creator_id, # CMDE Sanjay Rao (Admin)
                    status=status,
                    started_at=started_dt,
                    ended_at=ended_dt,
                    score=score_obj,
                    telemetry_log=[
                        {"timestamp": started_dt.isoformat(), "event_type": "session_started"},
                        {"timestamp": (started_dt + timedelta(minutes=5)).isoformat(), "event_type": "objective_aligned"},
                        {"timestamp": (started_dt + timedelta(minutes=random.randint(10, 20))).isoformat(), "event_type": "exercise_running"}
                    ],
                    replay_ref=f"/replays/{scenario.domain}_session_{i}.bin",
                    instructor_notes=notes,
                    created_at=started_dt
                )
                db.add(session)
            
            db.commit()
            print(f"  [OK]   Dumping complete: {100 - existing_sessions_count} sessions inserted.")

    print("\nSeed complete.")
    print(f"  Users seeded:          {len(USERS)}")
    print(f"  Scenarios seeded:      {len(SCENARIOS)}")
    print(f"  Doctrine docs seeded:  {len(DOCTRINE_DOCS)}")
    print(f"  Documentation topics seeded: {len(DOCUMENTATION_TOPICS)}")
    print(f"  Dumped training sessions: {db.query(DBTrainingSession).count()}")
    print("\nDefault credentials for all users: password = aegis123")
    print("\nUser summary:")
    for u in USERS:
        print(f"  {u['service_number']:20s}  {u['rank']:6s}  {u['role']:12s}  {u['name']}")


if __name__ == "__main__":
    # Create tables if they don't exist (useful for fresh dev environments)
    from app.database import create_all_tables

    print("Ensuring database tables exist...")
    create_all_tables()

    db = SessionLocal()
    try:
        seed(db)
    except Exception as exc:
        db.rollback()
        print(f"\n[ERROR] Seed failed: {exc}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()
