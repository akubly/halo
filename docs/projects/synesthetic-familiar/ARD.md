# Architecture Requirements Document: The Synesthetic Familiar

| Field | Value |
|-------|-------|
| **Status** | APPROVED |
| **Date** | 2026-06-07 |
| **Decisions approved by Aaron** | 2026-06-07 |
| **Owner** | Hiro (Architect) |
| **Source** | Theme-2 user stories + ideation pass 2 |
| **Project Type** | Playground demo (throwaway-OK) |

### Document History

| Date | Change | Author |
|------|--------|--------|
| 2026-06-07 | Initial ARD authored and approved | Hiro |
| 2026-06-08 | Architecture clarifications (heap ownership, quick-reset ownership, confidence-gating authority) — post-test-strategy review | Hiro |
| 2026-06-08 | BLE wire-format spec finalized (endianness, seq wraparound/dedup, FAMILIAR_RESET as device→host, ACK cadence) — Ng |
| 2026-06-09 | Persona-review fixes: topology → desktop mic + Halo IMU relay; ATTENTION as transient overlay; confidence-hold timeout; fallback neutral-only (no device IMU inference); SDK gaps → explicit go/no-go gates; YT-T2-2 deferred to Phase 2; jitter honesty; mic buffer constraint; structured logging; baseline persistence locked; minor M1–M5 | Hiro |

---

## 1. Overview & Goal

**What it is:** A tiny reactive creature living in the wearer's peripheral vision on Halo's 256×256 round monocular display. Its form and motion mirror the wearer's internal state—stress, calm, attention—inferred from mic + IMU. No numbers, no metrics, no literal UI. A companion that breathes faster when you're stressed, settles when you're calm, reacts when something notable happens.

**One-sentence thesis:** The Familiar is a felt metric, not a stat—a friend who shows how you're doing through motion, not words.

**Success bar:** "Feels alive, not a metric display." The wearer glances up and *understands* their internal state without reading anything. After 7 days, the creature feels like a companion, not a widget.

**Convergence citation:** Four agents independently landed on "shared experience, not metrics":
- Y.T. #1 (Pet Familiar): "reactive creature in corner vision"
- Librarian #2 (Synesthetic AI): "abstract concepts as visual metaphors"
- Da5id pass-2 mashup: "the creature becomes a felt metric, not a stat"
- Enzo-T2-*: "the familiar isn't productive; it's relational"

---

## 2. Scope

### IN SCOPE (Phase 1 — buildable in 2-3 weeks)

1. **Idle/ambient behavior** — creature rests in peripheral vision with gentle breathing animation (DASID-T2-1)
2. **Stress/calm state reflection** — creature breathing, color, and edge-fraying respond to inferred mood (DASID-T2-2, DASID-T2-3, LIBRARIAN-T2-1)
3. **First-launch bonding** — onboarding flow that introduces the creature and its meaning (YT-T2-1)
4. **Attention moments** — creature "jumps" or reacts when something significant happens (DASID-T2-4)
5. **Host-driven mood inference** — mood computed locally on host app from mic + IMU, sent to device via BLE (NG-T2-1, LIBRARIAN-T2-1)
6. **Quick-reset gesture** — double-tap to tell creature "I'm actually fine" (JUANITA-T2-5)
7. **Graceful degradation** — creature doesn't freeze if sensors fail or BLE drops (HIRO-T2-2, JUANITA-T2-2)
8. **Privacy by design** — creature animation is abstract/opaque to bystanders (RAVEN-T2-1)

### OUT OF SCOPE (Phase 2+ / explicitly not building)

| Feature | Why deferred | Source |
|---------|--------------|--------|
| On-device sensor fusion (true ML) | Requires M55 NPU TensorFlow Lite integration; months of work | NG-T2-5 |
| Peer-to-peer mood sharing | Requires BLE mesh + encryption layer; distracts from v1 | LIBRARIAN-T2-4, RAVEN-T2-2 |
| Cross-device roaming profile | Requires sync layer + device attestation | HIRO-T2-3 |
| Evolution over time (growth) | Week-long baseline learning needed; adds complexity | YT-T2-4, LIBRARIAN-T2-5 |
| Custom sprite upload (community remix) | SDK sandbox needed; Phase 2 community feature | NG-T2-3, LAGOS-T2-1 |
| Personality sliders (sleepy vs. energetic) | Requires preference storage; polish feature | YT-T2-3 |
| Distributed mood computation (multiplayer) | Consensus + sync; research project | HIRO-T2-4 |

**Playground = throwaway-OK:** This is a demo, not production infrastructure. If something doesn't ship cleanly in 2-3 weeks, defer it.

---

## 3. User Stories Traceability

### Phase 1 Stories (committed)

| Story ID | Title | Component | Priority |
|----------|-------|-----------|----------|
| DASID-T2-1 | Idle Familiar — peripheral companion | Lua render, HUD | P0 |
| DASID-T2-2 | Stress State — breathing faster, fraying | Lua render | P0 |
| DASID-T2-3 | Calm State — settles and glows | Lua render | P0 |
| DASID-T2-4 | Attention Moment — creature leaps | Lua render | P1 |
| DASID-T2-5 | Bystander perception — friendly, not surveillance | Design constraint | P0 |
| LIBRARIAN-T2-1 | Show internal state without asking | Host inference | P0 |
| LIBRARIAN-T2-2 | Learn wearer baseline | Host inference | P1 |
| LIBRARIAN-T2-5-ERROR | Don't hallucinate mood (silence > wrong) | Confidence gating | P0 |
| YT-T2-1 | First launch — meet your Familiar | Host app UX | P0 |
| NG-T2-1 | Drive animation from host sensor data | BLE/SDK | P0 |
| NG-T2-2 | On-device sensor events (IMU peak) | Lua hooks | P1 |
| JUANITA-T2-1 | Animation graceful degradation | Lua render | P1 |
| JUANITA-T2-2 | Resilient mode on sensor/BLE loss or degraded inference | Host inference | P0 |
| JUANITA-T2-3 | Lua heap exhaustion handling | Lua runtime | P2 |
| JUANITA-T2-5 | Quick-reset gesture | Lua input — device-owned | P1 |
| RAVEN-T2-1 | Abstract visuals — no biometric leak | Design constraint | P0 |
| HIRO-T2-1 | Mood/render decoupling | Architecture | P0 |
| HIRO-T2-2 | Graceful sensor degradation | Architecture | P0 |
| ENZO-T2-1 | Mood mirror for remote workers | Product validation | P0 |
| ENZO-T2-2 | Social barometer for anxious/ND wearers | Product validation | P1 |

### Deferred Stories (Phase 2+)

| Story ID | Reason |
|----------|--------|
| YT-T2-2 | **Phase 2 — deferred.** Predictive/early-warning stress inference requires a stable personal baseline and extended longitudinal validation not feasible in v1. No v1 test or Definition of Done. |
| YT-T2-3, YT-T2-4, YT-T2-5 | Personality/evolution/surprises require baseline learning |
| NG-T2-3, NG-T2-4 | Sprite upload + test harness are Phase 2 polish |
| NG-T2-5 | True sensor fusion requires ML infrastructure |
| LIBRARIAN-T2-4, LIBRARIAN-T2-5 | Peer sharing + growth are Phase 2 |
| HIRO-T2-3, HIRO-T2-4 | Cross-device sync + distributed mood are research |
| RAVEN-T2-2, RAVEN-T2-3 | Privacy audit tooling is Phase 2 |
| LAGOS-T2-* | Licensing/lineage tooling is Phase 2 |
| ENZO-T2-3, ENZO-T2-4, ENZO-T2-5 | Habit celebration, learning, grief are Phase 2+ |

---

## 4. System Architecture

### Host-Peripheral Model

**CRITICAL:** Halo is a peripheral, not an OS. The host app (phone/laptop/browser) drives logic; the device runs a thin Lua render loop. This is non-negotiable per Brilliant's architecture.

```
┌─────────────────────────────────────────────────────────────────────┐
│                           HOST APP (Python)                          │
│  ┌──────────────┐   ┌─────────────────┐   ┌───────────────────────┐ │
│  │ Sensor Input │   │ Mood Inference  │   │ Familiar State        │ │
│  │ (mic + IMU)  │──▶│ (local heuristic│──▶│ { mood, intensity,    │ │
│  │              │   │  on host)       │   │   confidence }        │ │
│  └──────────────┘   └─────────────────┘   └───────────┬───────────┘ │
└───────────────────────────────────────────────────────┼─────────────┘
                                                        │ BLE
                                                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      HALO DEVICE (Lua on M55)                        │
│  ┌───────────────────┐   ┌─────────────────┐   ┌─────────────────┐  │
│  │ BLE Rx            │   │ Familiar State  │   │ Sprite Renderer │  │
│  │ (mood updates)    │──▶│ Machine         │──▶│ (24×24 sprite,  │  │
│  └───────────────────┘   │ (smooth interp) │   │  breathing, bob)│  │
│                          └─────────────────┘   └────────┬────────┘  │
│  ┌───────────────────┐                                  │           │
│  │ Local IMU Events  │──────────────────────────────────┘           │
│  │ (motion peaks)    │  (ATTENTION trigger: jump-on-peak only)      │
│  └───────────────────┘                                              │
│                                    │                                │
│                                    ▼                                │
│                          ┌─────────────────┐                        │
│                          │ 256×256 OLED    │                        │
│                          │ (round viewport)│                        │
│                          └─────────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow (per cycle, 10Hz)

1. **Host captures** mic audio from desktop mic + IMU relayed from Halo via BLE
2. **Host computes** mood vector: `{ energy: 0-1, valence: 0-1, tension: 0-1 }`
3. **Host applies** confidence gate: if confidence < 0.7, hold current state
4. **Host sends** BLE message: `FAMILIAR_UPDATE { mood_enum, intensity, confidence }`
5. **Device receives** message, interpolates to new state over 200-500ms
6. **Device renders** sprite at 15-30fps, updates breathing/color/position
7. **Device triggers** ATTENTION overlay on local IMU peak events (jump-on-motion); no device-side mood inference

### Autonomy Tier Decision

**Tier: Hybrid Host-Primary**

| Component | Location | Rationale |
|-----------|----------|-----------|
| Sensor capture | Desktop mic (host) + Halo IMU relay via BLE | Desktop mic captures audio; Halo relays IMU to host via BLE |
| Mood inference | **Host (local heuristic)** | M55 NPU is for gate-keeping, not inference (LIBRARIAN finding). Latency budget 200-500ms acceptable. Cloud deferred to Phase 2. |
| Confidence gating | **Host** | "Silence is safer than wrong" (LIBRARIAN-T2-5-ERROR). **Host is the single authority; any device-side gating is optional defense-in-depth, not required behavior.** |
| State interpolation | **Device** | Smooth animation must be local; BLE latency too high |
| Sprite rendering | **Device** | Display is on-device; Lua render loop |
| Fallback on BLE drop | **Device** | Neutral-only state after 10s; no device-side IMU-only inference |

**Why not on-device ML? Why not cloud?** The M55 NPU is optimized for wake-word detection and simple gating, not real-time multimodal inference. Cloud latency (500-2000ms) breaks the "alive" illusion for an ambient display. We follow Brilliant's architecture and keep inference on host locally. Phase 2 can explore cloud refinement for longer-term insights.

---

## 5. Component Requirements

### 5.1 On-Device (Lua)

**File:** `main.lua` (≈300 lines)

**Responsibilities:**
- Receive `FAMILIAR_UPDATE` messages via BLE
- Interpolate mood state smoothly (200-500ms transitions)
- Render sprite at 15-30fps depending on complexity
- Handle local IMU events (`on_imu_peak`) for motion-triggered ATTENTION reactions only — no mood inference on device
- Manage graceful degradation: if no BLE update for 10s, enter neutral state (no IMU-only mood inference fallback)
- Respect heap budget: <80% usage triggers reduced animation complexity; safe-halt at 95%. *(Thresholds 80%/95% are initial estimates; tune on real device.)* **Heap management is device-local; not reflected in any host-bound message** — FAMILIAR_ACK carries seq only, no heap flag.

**Sprite specification (per DASID-T2-1):**
- Size: 24×24 pixels (expandable to 48×48 in Phase 2)
- Position: 7 o'clock on rim, 80% radius from center
- Palette: 4 colors (dark body, bright eye, accent, shadow)
- Idle animation: bob ±2px at 0.25Hz (4-second cycle)
- Lit pixels: ~1.5% of canvas (well under 30% budget)

**State machine:**
```
NEUTRAL (default) ─┬─▶ CALM (low tension, sustained 60s)
                   └─▶ STRESSED (high tension, threshold breach)

Any state ──────────▶ ATTENTION overlay (500ms) ──▶ previous_state
                      (not a peer state; does not reset to NEUTRAL)
```

**SDK go/no-go gates (resolved Week 3, per decisions.md 2026-06-12 & 2026-06-13):**

| Gap | Critical Path | Verdict | Implementation |
|-----|---------------|---------|--------------------|
| IMU interrupt callback — `frame.imu.on_tap` / `frame.on_imu_peak` | Week 3 (double-tap FAMILIAR_RESET; ATTENTION trigger) | ✅ **RESOLVED GO (2026-06-12)** — `frame.imu.tap_callback(func)` confirmed available; no N-count discriminator; Lua double-tap debounce 350ms window. ATTENTION-on-IMU-peak via render-loop poll of `frame.imu.raw()` at 20fps (≤50ms latency), threshold `IMU_PEAK_THRESH_G = 1.8`. | Shipped Week 3: double-tap detection on-device (Lua debounce accumulator), FAMILIAR_RESET opcode 0x01 sent to host; IMU peak poll in render loop triggers ATTENTION state [3] for 500ms with white eye, gray body, 180ms jump animation (+4px), 500ms overlay then restore-to-previous-mood. |
| Sprite pixel-buffer format for `bitmap()` (indexed 4-bit, RGB565, or RLE) | Week 1 (rendering; asset pipeline) | ✅ **RESOLVED (2026-06-09)** — `frame.display.circle()` confirmed available; Bresenham fallback unnecessary | Shipped Week 1: `set_pixel()` per-pixel baseline; Week 3 refactor uses `frame.display.circle()` for halo glow (3 concentric rings), 8× reduction in API calls per ring. |
| Heap monitoring: `frame.system.get_heap_usage()` | Week 3 (heap guard 80%/95%) | ❌ **RESOLVED NO-GO (2026-06-12)** — `frame.system` sub-namespace does NOT exist in current Halo Lua stdlib; no `get_heap_usage()` available | Shipped Week 3 fallback as v1 design: manual `heap_fraction()` proxy (sprite rows 24×25B + BLE buffer 244B, budget 40KB). Thresholds: ≥80% reduce (skip glow), ≥95% safe-halt. Firmware-swap hook documented in main.lua for future hardware validation. |

These are **explicit go/no-go gates**: if a gap cannot be resolved before its milestone, the dependent feature is blocked until the gap is closed or the fallback is accepted as the v1 design. (See also §10 for investigation assignments.)

**Frame→Halo gotchas (per decisions.md):**
- Call `frame.display.power_save(false)` at startup
- Use `upload_stdlua_libs()` to ensure wire format compatibility
- IMU values are float32, not int16 — handle correctly

### 5.2 BLE / SDK Layer

**Message types needed:**

| Direction | Message | Opcode | Payload | Frequency |
|-----------|---------|--------|---------|-----------|
| Host → Device | `FAMILIAR_UPDATE` | `0x80` | mood_enum (0–3), intensity (0–100), confidence (0–100), seq (uint16 LE) | 10Hz max |
| Device → Host | `FAMILIAR_ACK` | `0x02` | last_received_seq (uint16 LE) | Every 10 accepted updates |
| Device → Host | `FAMILIAR_RESET` | `0x01` | (none) | On double-tap gesture |

> **Quick-reset ownership (decided 2026-06-08):** Double-tap is detected **on-device** (Lua IMU/tap input) and handled locally — device snaps to NEUTRAL immediately, no host round-trip required. `FAMILIAR_RESET` is a **Device→Host notification** (not a host command). No Host→Device reset opcode exists or is needed.
>
> **Heap management is device-local; not reflected in any host-bound message.** `FAMILIAR_ACK` carries last received seq only — no heap field.

**Opcode space:**

| Range | Direction | Notes |
|-------|-----------|-------|
| `0x00–0x7F` | Device → Host | Notifications and ACKs originating on device |
| `0x80–0xFF` | Host → Device | Commands originating on host |

**Endianness:** All multi-byte fields are **little-endian (LE)**. This is idiomatic for BLE (ATT layer is LE) and for the ARM Cortex-M55 on Halo. Host Python uses `struct.pack('<H', seq)` for a single uint16 field; device Lua uses `string.pack('<I2', seq)` / `string.unpack('<I2', data, offset)`.

**Wire formats (all fit in a single BLE packet):**
```
FAMILIAR_UPDATE (Host → Device, opcode 0x80):
  byte 0:   opcode (0x80)
  byte 1:   mood_enum (0=neutral, 1=calm, 2=stressed, 3=attention)
  byte 2:   intensity (0–100)
  byte 3:   confidence (0–100)
  byte 4–5: sequence number (uint16, little-endian)
  Total: 6 bytes

FAMILIAR_ACK (Device → Host, opcode 0x02):
  byte 0:   opcode (0x02)
  byte 1–2: last_received_seq (uint16, little-endian)
  Total: 3 bytes

FAMILIAR_RESET (Device → Host, opcode 0x01):
  byte 0:   opcode (0x01)
  Total: 1 byte  (occurrence is the signal; no payload)
```

**Sequence number semantics:**

- **Range:** uint16 (0x0000–0xFFFF); wraps 0xFFFF → 0x0000.
- **Host responsibility:** increment seq monotonically on each outgoing `FAMILIAR_UPDATE`; restart at 0x0000 after reconnect.
- **Device dedup / ordering (wraparound-aware):** On receipt of a packet carrying `received_seq`, the device computes:

  ```
  delta = (received_seq - last_accepted_seq) mod 65536
  ```

  Interpret `delta` as a **signed 16-bit integer** (if delta > 32767, treat as negative):

  | delta value | Interpretation | Action |
  |-------------|----------------|--------|
  | `0` | Duplicate | Drop silently |
  | `1 – 32767` | Newer (including wraparound) | Accept; set `last_accepted_seq = received_seq` |
  | `32768 – 65535` (i.e. signed negative) | Stale or out-of-order | Drop silently |

  The acceptance window (half the uint16 space = 32 767 packets) is far beyond any practical 10 Hz use case; there is no ambiguity at normal operating rates.

- **On reconnect:** host resets seq to 0x0000; device resets `last_accepted_seq` to 0xFFFF so that the first received seq=0x0000 yields delta=1 and is accepted.

**ACK cadence:**

The device sends `FAMILIAR_ACK` automatically after every **10 accepted `FAMILIAR_UPDATE` packets** — no host-initiated request message is needed. At 10 Hz this yields approximately one ACK per second, giving the host sufficient signal to detect sustained packet loss. The device also sends an unsolicited `FAMILIAR_ACK` immediately on BLE reconnect (reporting the current `last_accepted_seq`).

**SDK packages:**
- `brilliant-ble` (Python): BLE connection, message transport
- `brilliant-msg` (Python): Message encoding/decoding
- **Version pinning:** Use latest stable; test for wire format compatibility

**Host reconnect policy (M1):** After N consecutive `FAMILIAR_UPDATE` packets sent without a corresponding `FAMILIAR_ACK` (suggested N=30, ≈3s at 10Hz), the host logs a warning, reduces send rate, and initiates BLE reconnection.

**Known gaps:**
- No `FAMILIAR_UPDATE` opcode exists — must define custom message type
- No sprite animation primitive — Lua must implement keyframe logic

### 5.3 Host App

**Platform choice: Python desktop (locked)**

**Rationale:**
- Python is Brilliant's "testing reference implementation" per decisions.md
- Fastest iteration for playground demo
- Emulator-first testing possible
- Web Bluetooth is Chromium-only (limits audience)
- Flutter requires mobile device (adds friction for devs)

**Structure:**
```
projects/synesthetic-familiar/
├── host/
│   ├── main.py              # Entry point, BLE connection
│   ├── sensors.py           # Mic capture, IMU relay (mic + IMU only)
│   ├── inference.py         # Local mood heuristic (no cloud)
│   └── familiar_protocol.py # FAMILIAR_UPDATE encoding
├── device/
│   ├── main.lua             # On-device render loop
│   └── sprites/             # Sprite assets (abstract-with-eyes)
└── tests/
    ├── test_inference.py    # Unit tests for mood heuristic
    └── test_protocol.py     # BLE message tests
```

**Sensor capture (Desktop mic + Halo IMU relay):**
- Mic: PyAudio or sounddevice, 16kHz, mono (desktop mic on host machine)
- IMU: Relay from Halo via BLE (existing SDK support)
- Camera: Explicitly deferred to Phase 2 (no v1 scope)

**Mic buffer constraint (privacy):**
- `sensors.py` holds ≤1s rolling audio window; buffer is zeroed immediately after feature extraction
- `SensorSourcePort` returns only extracted features (RMS, pitch variance) — never raw audio samples
- Raw audio logging and `.wav` dumps are prohibited; no audio data may be written to disk or transmitted over any network

**Structured logging requirement:**
- Host emits structured `DEBUG` log per inference cycle: `{mood, intensity, confidence, action: sent|suppressed}`
- Host emits structured `DEBUG` log per BLE event: `{event: send|error|reconnect, seq, timestamp}`

**Dependencies:**
- `brilliant-ble` (BSD-3-Clause, compatible)
- `brilliant-msg` (BSD-3-Clause, compatible)
- `numpy` (BSD, for signal processing)
- `sounddevice` (MIT, for mic capture)

### 5.4 AI / Mood Inference (Local Heuristic)

**Model tier: Local heuristic on host (no cloud for v1)**

**Rationale:**
- Latency budget is 200-500ms — cloud round-trip adds 500-2000ms
- Familiar is always-on ambient display — can't depend on network
- Privacy: embodied signals (voice, movement) should not leave device
- Simplicity: heuristic is sufficient for "feels alive" bar
- Cloud refinement deferred to Phase 2 for longer-term insights

**Inference pipeline (locked):**
```python
def compute_mood(audio_rms, audio_pitch_variance, imu_acceleration, imu_rotation):
    """
    Returns: { mood: str, intensity: float, confidence: float }
    """
    tension = weighted_sum(
        audio_pitch_variance * 0.4,  # High pitch variance = stress
        imu_acceleration * 0.3,       # Fast movement = arousal
        imu_rotation * 0.3            # Head turning = alertness
    )
    
    if tension > STRESS_THRESHOLD:
        return { "mood": "stressed", "intensity": tension, "confidence": 0.8 }
    elif tension < CALM_THRESHOLD:
        return { "mood": "calm", "intensity": 1 - tension, "confidence": 0.8 }
    else:
        return { "mood": "neutral", "intensity": 0.5, "confidence": 0.6 }
```

**Confidence gating (LIBRARIAN-T2-5-ERROR):**
- If confidence < 0.7, do NOT update Familiar state
- Better to show stale-but-correct than fresh-but-wrong
- "Silence is safer than hallucination"
- **The host is the single authority for confidence gating.** Device-side gating, if any, is optional defense-in-depth and not required behavior.
- Note: NEUTRAL is reachable by two distinct paths: (a) **Both-sensors-fail fallback** — if both mic and IMU fail for >10s, the host sends NEUTRAL explicitly (see §5.3 Fallback); (b) **Confidence-hold timeout** — after ~30s of gate-suppressed silence, the host resends the *last computed mood* (which may be neutral, calm, or stressed — not specifically NEUTRAL) at sub-threshold confidence. These paths are independent.

**Confidence-hold timeout (I2):**
- If confidence gating has suppressed all updates for ~30s continuously, the host sends the last computed mood even if confidence < 0.7. This prevents the creature being permanently frozen in a stale state (see §8: *Stuck-in-stressed* failure mode).
- The 30s timer resets on any successfully sent update.

**Baseline learning (Phase 1 simplified):**
- First 3 days: use population defaults
- After day 3: compute wearer's personal mean/stddev
- Stress threshold = personal_mean + 1.5σ

**Baseline persistence (Phase 1 — locked):** Wearer personal baseline (mean, stddev) is stored on **host filesystem** (e.g., `~/.vesper/baseline.json`). This is the canonical Phase-1 storage strategy; Phase-2 may migrate to on-device flash or cloud sync. *(Unblocks the dependent TEST-STRATEGY test.)*

> **Phase-1 cloud trust posture:** "No cloud" is enforced by code review — no cloud SDK imports in Phase-1 source. Juanita may add a light import guard in CI to prevent accidental cloud dependency creeping in.

**Fallback (JUANITA-T2-2):**
- If mic fails: use IMU-only (reduced confidence)
- If IMU fails: use mic-only (reduced confidence)
- If both fail: hold last-known state for 10s, then neutral

### 5.5 HUD / Render (Abstract-with-Eyes Form)

**Display constraints (per decisions.md):**
- 256×256 round viewport
- OLED: black pixels = zero power
- Lit pixel budget: <30% (aim for <5% for Familiar idle)
- Refresh: 25-30fps baseline; 15fps for power-efficient idle
- No double-buffer: incremental updates only

**Visual specification (abstract geometric with bright eye — locked):**

| State | Animation | Color | Breathing | Lit % |
|-------|-----------|-------|-----------|-------|
| Neutral | Slow bob, 0.25Hz | Cool (blue/teal) | 4s cycle | ~1.5% |
| Calm | Slower bob, 0.15Hz, halo glow | Cool teal | 7s cycle | ~3% |
| Stressed | Fast bob, 0.75Hz, edge fraying | Warm amber/orange | 1.3s cycle | ~2.5% |
| Attention | Jump 15px toward center, return | Bright (white eye) | — | ~2% peak |

**Form (locked to abstract-with-eyes per Decision 3):**
- Geometric shape (circle, rounded square, or organic blob) with a single bright eye
- No face, no mouth, no anthropomorphic features beyond the eye
- 24×24 sprite renders as a recognizable "creature" without literal emotion display
- Eye position and size convey attention; eye brightness conveys stress/calm through color shifts

**Rendering primitives:**
- `bitmap()` for indexed sprite (4-bit, 24×24)
- `circle()` for halo glow (3 concentric, decreasing brightness)
- `set_pixel()` for edge fraying (border noise)

**Animation budget:**
- Max 50ms per frame (20fps floor)
- Max 32 sprites per frame (complexity limit per HIRO-T2-5)
- Battery: <5mW target during idle

### 5.6 Privacy (Mic + IMU, No Camera in v1)

**Privacy requirements (per RAVEN-T2-*):**

1. **Abstract visuals:** Creature animation uses breathing/orbit/bloom — no labeled emotions visible to bystanders. "Calm" text is internal; bystander sees unlabeled motion.

2. **Anti-robotic jitter:** Visual animation includes 5-10% random jitter as visual polish to avoid mechanical, obviously-algorithmic motion — this is **not** a privacy protection mechanism. An informed observer who knows the creature is mood-linked can infer approximate mood state from behavior. Real privacy protection comes from: (a) **obscurity** — the creature is not obviously mood-linked to casual bystanders; and (b) **abstraction** — no text, numbers, or explicit emotion labels are ever displayed.

3. **Host-side inference:** Mood calculation runs on host app; raw audio/IMU never leaves the host at all — only the derived mood/intensity/confidence/seq is transmitted over BLE to the device. No cloud telemetry of embodied signals. Camera explicitly deferred to Phase 2.

4. **Desktop mic indicator:** v1 captures mic on the host desktop machine — recording indicator is OS-managed (e.g. macOS/Windows mic-in-use indicator in system tray). No additional in-app indicator is required for v1.

5. **BLE privacy:** `FAMILIAR_UPDATE` messages contain mood_enum, intensity, confidence, and seq — no raw biometric values. BLE is **unauthenticated and unencrypted**: mood state is readable and packets are injectable by a nearby BLE scanner. This is accepted for a single-user playground demo. Phase-2 should consider LESC (LE Secure Connections) pairing for production use.

**Mic buffer discipline (I7):** `sensors.py` holds ≤1s rolling audio window; buffer zeroed after feature extraction; `SensorSourcePort` exposes extracted features only; raw audio logging prohibited. (Full constraint spec in §5.3.)

**Privacy audit checklist:**
- [ ] No raw audio samples persist beyond 1s rolling window; buffer zeroed after feature extraction
- [ ] No IMU streams stored persistently
- [ ] FAMILIAR_UPDATE contains no PII
- [ ] Creature animation is abstract (no emotion labels visible)
- [ ] OS-managed desktop mic indicator active during capture
- [ ] No cloud SDK imports present (trust-by-code-review; see §5.4)

---

## 6. Tech Stack & Dependencies

| Layer | Technology | Version | License |
|-------|------------|---------|---------|
| Host app | Python 3.11+ | — | — |
| BLE SDK | `brilliant-ble` | latest | BSD-3-Clause |
| Message SDK | `brilliant-msg` | latest | BSD-3-Clause |
| Audio capture | `sounddevice` | 0.4+ | MIT |
| Signal processing | `numpy` | 1.24+ | BSD |
| On-device | Lua 5.3 | bundled | MIT |
| Display | Halo OLED (256×256) | — | — |
| Model | Local heuristic | — | N/A (no external model) |

**License posture (per Lagos):**
- Repo: MIT (most permissive)
- Dependencies: All BSD-3 or MIT (compatible)
- No copyleft (GPL/AGPL) dependencies
- Attribution: README credits Brilliant Labs

---

## 7. Resolved Decisions ✅

### Decision 1: Sensors for v1 — Mic + IMU ✅ RESOLVED

**Selected:** Mic + IMU (no camera in v1)

**Reasoning:**
- Mic + IMU provides good inference signal for stress/calm detection (voice tone + motion)
- No camera eliminates privacy overhead (recording indicator mandate) and complexity
- Camera deferred to Phase 2 for potential expression/eye-contact augmentation
- Phase 1 focus: prove "alive" feeling with voice + motion alone

**Alternatives considered (rejected):**
- Mic-only: Sufficient for stress, but misses motion context (wearer at desk may have low vocal signal but high tension)
- Mic + IMU + Camera: Excellent inference but adds privacy scrutiny, on-device recording indicator requirements, and dev complexity; not justified for v1 playground

### Decision 2: Cloud vs. Local Mood Model — Local Heuristic ✅ RESOLVED

**Selected:** Local heuristic on host (no cloud for v1)

**Reasoning:**
- Latency: Cloud round-trip (500-2000ms) breaks "alive" illusion for ambient display; 200-500ms local acceptable
- Privacy: Embodied signals (voice, movement) stay on host+device; no telemetry to cloud
- Simplicity: Heuristic (pitch variance, acceleration, rotation weights) is sufficient for "feels alive" bar
- Reliability: Familiar can't depend on network; always-on mood essential
- Cloud refinement: Deferred to Phase 2 for learning insights and remote-worker use cases

**Alternatives considered (rejected):**
- Cloud API (Gemini): Superior inference quality, but latency unacceptable for ambient display; network dependency risky
- Hybrid (local fast, cloud refine): Deferred to Phase 2 after proving local works

### Decision 3: Creature Form — Abstract-with-Eyes ✅ RESOLVED

**Selected:** Abstract geometric form with a single bright eye (no face, no literal anthropomorphic features)

**Reasoning:**
- Recognizable as "creature" (eye conveys agency) but abstract enough that bystanders cannot read internal state
- Eye becomes the locus of attention: eye position = attention direction, eye brightness = stress level (color shift)
- 24×24 sprite fits within Halo's peripheral vision without dominance; abstract form preserves privacy (RAVEN-T2-1)
- Eyes are universally expressive without being literal; allows asymptotic progression toward personality without requiring full face

**Alternatives considered (rejected):**
- Creature with face (eyes + mouth): Recognizable but risks literal emotion broadcast to bystanders; mouth animation adds dev complexity
- Particle system (emergent swarm): Impersonal; "aliveness" harder to perceive; no locus of attention

---

---

## 8. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Emotion inference lag** — creature shows stress 5s after wearer feels it | Medium | Medium | Use 10Hz update rate; tune thresholds for responsiveness over precision (LIBRARIAN-T2-5-ERROR: false negatives > false positives); optimize local heuristic weights |
| **Display can't keep up** — animation stutters under load | Low | Medium | Frame-skip gracefully (JUANITA-T2-1); cap at 15fps if needed; bound animation complexity to 32 sprites |
| **Model unavailable** — local inference fails | Very low (local only) | Medium | Hold last-known state for 10s then neutral; no cloud dependency in v1 |
| **State leaks to bystanders** — creature reveals wearer stress visibly | Medium | High | Abstract visuals (RAVEN-T2-1); add 5-10% jitter (anti-robotic polish); cap brightness at 50% indoors; eye-based form (not face) limits readability |
| **Lua heap fills** — long session OOMs device | Low | High | Monitor heap at 80%; reduce animation complexity; safe-halt at 95% (JUANITA-T2-3). *(Thresholds 80%/95% are initial estimates; tune on real device.)* |
| **BLE drops mid-session** — creature freezes | Medium | Medium | Device-side timeout (10s): if no BLE update received for 10s, device enters neutral state; no device-side IMU mood inference |
| **Mood hallucination** — creature thrashes when wearer is calm | Medium | Medium | Confidence gating (LIBRARIAN); quick-reset gesture (JUANITA-T2-5); baseline learning after day 3 |
| **Mic capture noise** — inference confused by background sounds | Medium | Low | Confidence gating suppresses updates on low-confidence frames; silence > hallucination |
| **Stuck-in-stressed** — tension drops but confidence stays below 0.7 gate; creature never returns to neutral | Medium | Medium | Confidence-hold timeout (~30s): after 30s of continuously suppressed updates, host sends last computed mood regardless of gate; creature unfreezes |

---

## 9. Phase 1 Milestone Sequence (2-3 weeks, locked)

**Build Sequence with Locked Decisions**

| Week | Milestone | Deliverable | Technical Scope |
|------|-----------|-------------|-----------------|
| **Week 1** | **"It moves"** | Lua sprite renders on device; host sends mock FAMILIAR_UPDATE; creature bobs | Python harness + Lua render loop on device; abstract sprite (24×24 geometric form with eye); test BLE wire format |
| Week 1 | BLE protocol | FAMILIAR_UPDATE message defined and working | Opcode 0x80, mood_enum (0-3), intensity (0-100), confidence (0-100), sequence number |
| Week 1 | **SDK gate: sprite format** | Ng confirms `bitmap()` pixel-buffer format with Brilliant SDK | If unconfirmed, Week 1 ships with `set_pixel()` fallback (correct for any firmware); `bitmap()` unlocked when format known |
| **Week 2** | **"It reacts"** | Host captures desktop mic + Halo IMU relay; local heuristic inference; creature reflects mood | Python sounddevice (desktop mic) + Halo IMU relay; tone/pitch variance + acceleration + rotation weighting; 10Hz updates to device |
| Week 2 | Stress/calm states | Visual states per DASID spec (breathing speed ±0.75Hz vs 0.15Hz, color shift warm↔cool) | Lua animation state machine: neutral ↔ calm ↔ stressed; smooth 200-500ms interpolation |
| **Week 3** | **"It's alive"** | Host onboarding flow + IMU-peak ATTENTION overlay + double-tap quick-reset + graceful fallback + baseline activation gate | ACTIVATION_THRESHOLD = 50 Welford samples (population defaults <50, personal mean+1.5σ ≥50); device IMU-peak poll (render loop 20fps) triggers ATTENTION state for 500ms (white eye, gray body, +4px jump 180ms); double-tap via `frame.imu.tap_callback()` debounce (350ms window) sends FAMILIAR_RESET on-device; host onboarding displays calibration status; heap proxy (80% reduce, 95% halt) in render loop; all graceful degradation (BLE timeout, sensor failure, confidence hold) verified on hardware |
| Week 3 | Polish + test | Test on real device; tune confidence thresholds; document | Baseline learning ACTIVATION_THRESHOLD = 50 fully implemented with `get_activation_info()` accessor; privacy audit checklist ✅; heap proxy established with firmware-swap hook documented in main.lua (TODO when `frame.system.get_heap_usage()` ships) |
| Week 3 | **SDK gates: IMU + heap** | Ng confirms `frame.imu.tap_callback` availability and heap fallback design | ✅ **RESOLVED (2026-06-12):** IMU interrupt GO (`frame.imu.tap_callback`); heap API NO-GO (fallback manual proxy as v1). See §5.1 gate table for implementation. Full Week 3 automated suite green. |

**Success criteria (locked):**
- Week 1: Emulator or real device renders bobbing sprite from ≥10 mock FAMILIAR_UPDATE packets; BLE send/receive log is clean with no errors; creature bobs without frame stutter or dropped-frame judder (intentional 5–10% anti-robotic jitter is expected and correct)
- Week 2: Aaron can trigger stress state by raising voice in quiet room; stressed visual (faster breathing, warm color) appears within 500ms
- Week 3: Aaron feels creature is "alive" (not robotic) after 1 hour of wear; gesture resets work; no OOM or BLE freeze during session

---

## 10. Open Questions

*Not decisions for Aaron — status tracking only*

> **SDK gaps Q1–Q3 are now RESOLVED** (2026-06-12, Ng). See §5.1 gate table above for implementation details and decision dates.

1. **IMU event primitive [RESOLVED GO: 2026-06-12]:** The real API is `frame.imu.tap_callback(func)`, not the ARD's assumed `frame.imu.on_tap(n, callback)`. No built-in N-count discriminator. Double-tap discrimination implemented via Lua debounce accumulator with 350ms window. IMU-peak ATTENTION trigger uses render-loop poll of `frame.imu.raw()` at 20fps (≤50ms latency), threshold `IMU_PEAK_THRESH_G = 1.8g`. *(Decision: decisions.md 2026-06-12 "SDK Gate Verdicts — Week 3 Go/No-Go")*

2. **Sprite format [RESOLVED: 2026-06-09]:** `frame.display.circle()` confirmed available in emulator and Halo Lua stdlib. Replaced Bresenham mid-point loop with direct `circle()` calls for halo glow (3 rings: 1 API call per ring, 8× reduction). No format ambiguity; `set_pixel()` fallback unnecessary. *(Decision: decisions.md 2026-06-09 "SDK Gaps & Decisions")*

3. **Heap monitoring [RESOLVED NO-GO: 2026-06-12]:** `frame.system.get_heap_usage()` does NOT exist in current Halo Lua stdlib. `frame.system` sub-namespace is not implemented. Fallback design accepted as v1: manual `heap_fraction()` proxy counting sprite rows (24×25B) + BLE buffer (244B) against ~40KB app budget. Thresholds: ≥80% reduce complexity (skip halo glow), ≥95% safe-halt (blank screen). Firmware-swap hook documented in main.lua for future hardware update. *(Decision: decisions.md 2026-06-12 "SDK Gate Verdicts — Week 3 Go/No-Go")*

4. **Baseline learning persistence:** **RESOLVED (Phase 1, 2026-06-10):** Host filesystem (`~/.vesper/baseline.json`). Welford online mean + stddev, saved at exit, loaded at startup. Activation threshold = 50 Welford samples (statistical minimum where SE(s) ≈ 10% of stddev). *(See §5.4.)*

5. **Cross-platform parity:** If Phase 2 adds Web Bluetooth, how do we maintain parity with the Python host? Shared mood calculation logic requires a JS port or a shared native library. (Deferred to Phase 2 scoping)

6. **Accessibility:** How does a wearer with colorblindness perceive stress vs. calm? (Da5id to propose alternative visual encoding)

> **Resolved wire-format items (2026-06-08, Ng):** Endianness (little-endian), sequence wraparound/dedup (uint16, signed delta window), FAMILIAR_RESET direction (Device→Host), FAMILIAR_RESET opcode (0x01), ACK cadence (every 10 packets), ACK opcode (0x02) — all fully specified in §5.2. No further open questions on BLE wire format.

---

---

*This is the first official Halo playground project. Build it fast, learn from it, iterate.*

---

**Document history:**
- 2026-06-07: Initial draft (Hiro)
- 2026-06-07: Approved by Aaron — Decisions 1, 2, 3 locked; ARD finalized
