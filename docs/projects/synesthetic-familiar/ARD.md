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
| YT-T2-2 | Notice stress before wearer feels it | Host inference | P1 |
| NG-T2-1 | Drive animation from host sensor data | BLE/SDK | P0 |
| NG-T2-2 | On-device sensor events (IMU peak) | Lua hooks | P1 |
| JUANITA-T2-1 | Animation graceful degradation | Lua render | P1 |
| JUANITA-T2-2 | Offline mode when cloud fails | Host inference | P0 |
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
│  │ (motion peaks)    │  (optional: supplement host mood)            │
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

1. **Host captures** mic audio + IMU from phone (or Halo BLE relay)
2. **Host computes** mood vector: `{ energy: 0-1, valence: 0-1, tension: 0-1 }`
3. **Host applies** confidence gate: if confidence < 0.7, hold current state
4. **Host sends** BLE message: `FAMILIAR_UPDATE { mood_enum, intensity, confidence }`
5. **Device receives** message, interpolates to new state over 200-500ms
6. **Device renders** sprite at 15-30fps, updates breathing/color/position
7. **Device optionally** supplements with local IMU peak events (jump-on-motion)

### Autonomy Tier Decision

**Tier: Hybrid Host-Primary**

| Component | Location | Rationale |
|-----------|----------|-----------|
| Sensor capture | Host (phone mic/IMU) or device relay | Phone has better mic; device IMU is supplementary |
| Mood inference | **Host (local heuristic)** | M55 NPU is for gate-keeping, not inference (LIBRARIAN finding). Latency budget 200-500ms acceptable. Cloud deferred to Phase 2. |
| Confidence gating | **Host** | "Silence is safer than wrong" (LIBRARIAN-T2-5-ERROR). **Host is the single authority; any device-side gating is optional defense-in-depth, not required behavior.** |
| State interpolation | **Device** | Smooth animation must be local; BLE latency too high |
| Sprite rendering | **Device** | Display is on-device; Lua render loop |
| Fallback on BLE drop | **Device** | Local IMU-only inference, then neutral state after 10s |

**Why not on-device ML? Why not cloud?** The M55 NPU is optimized for wake-word detection and simple gating, not real-time multimodal inference. Cloud latency (500-2000ms) breaks the "alive" illusion for an ambient display. We follow Brilliant's architecture and keep inference on host locally. Phase 2 can explore cloud refinement for longer-term insights.

---

## 5. Component Requirements

### 5.1 On-Device (Lua)

**File:** `main.lua` (≈300 lines)

**Responsibilities:**
- Receive `FAMILIAR_UPDATE` messages via BLE
- Interpolate mood state smoothly (200-500ms transitions)
- Render sprite at 15-30fps depending on complexity
- Handle local IMU events (`on_imu_peak`) for motion-triggered reactions
- Manage graceful degradation: if no BLE update for 10s, enter neutral state
- Respect heap budget: <80% usage triggers reduced animation complexity; safe-halt at 95%. **Heap management is device-local; not reflected in any host-bound message** — FAMILIAR_ACK carries seq only, no heap flag.

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
                   └─▶ ATTENTION (event triggered, 500ms)
```

**SDK gaps to address (per NG-T2-*):**
- Need `frame.on_imu_peak(callback)` for motion events (current SDK is polling-only)
- Need sprite animation sequencing primitive (workaround: pre-baked keyframes)
- Need heap monitoring: `frame.system.get_heap_usage()`

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

**Endianness:** All multi-byte fields are **little-endian (LE)**. This is idiomatic for BLE (ATT layer is LE) and for the ARM Cortex-M55 on Halo. Host Python uses `struct.pack('<HH', ...)` ; device Lua uses `string.pack('<I2', seq)` / `string.unpack('<I2', data, offset)`.

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
synesthetic-familiar/
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

**Sensor capture (Mic + IMU only):**
- Mic: PyAudio or sounddevice, 16kHz, mono (from host phone)
- IMU: Relay from Halo via BLE (existing SDK support)
- Camera: Explicitly deferred to Phase 2 (no v1 scope)

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

**Baseline learning (Phase 1 simplified):**
- First 3 days: use population defaults
- After day 3: compute wearer's personal mean/stddev
- Stress threshold = personal_mean + 1.5σ

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

2. **No biometric leak:** Visual pattern includes 5-10% random jitter to prevent statistical inference of wearer state by observers.

3. **On-device inference:** Mood calculation runs on host app; raw audio/IMU never leaves the host→device BLE pipe. No cloud telemetry of embodied signals. Camera explicitly deferred to Phase 2.

4. **Mic recording indicator (phone-side):** v1 captures mic on host phone, not Halo — recording indicator is on phone during audio capture, not on glasses. This satisfies privacy mandate for microphone use.

5. **BLE privacy:** FAMILIAR_UPDATE messages contain only mood enum + intensity — no raw biometric values. Message is not encrypted (low sensitivity), but also not broadcast (point-to-point BLE).

**Privacy audit checklist:**
- [ ] No raw audio samples leave host app
- [ ] No IMU streams stored persistently
- [ ] FAMILIAR_UPDATE contains no PII
- [ ] Creature animation is abstract (no emotion labels visible)
- [ ] Phone mic indicator active during capture

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
| **Model unavailable** — local inference fails | Very low (local only) | Medium | Fallback to IMU-only heuristic; hold last-known state for 10s then neutral; no cloud dependency in v1 |
| **State leaks to bystanders** — creature reveals wearer stress visibly | Medium | High | Abstract visuals (RAVEN-T2-1); add 5-10% jitter; cap brightness at 50% indoors; eye-based form (not face) limits readability |
| **Lua heap fills** — long session OOMs device | Low | High | Monitor heap at 80%; reduce animation complexity; safe-halt at 95% (JUANITA-T2-3) |
| **BLE drops mid-session** — creature freezes | Medium | Medium | Device-side timeout (10s); local IMU fallback; graceful neutral state |
| **Mood hallucination** — creature thrashes when wearer is calm | Medium | Medium | Confidence gating (LIBRARIAN); quick-reset gesture (JUANITA-T2-5); baseline learning after day 3 |
| **Mic capture noise** — inference confused by background sounds | Medium | Low | Confidence gating suppresses updates on low-confidence frames; silence > hallucination |

---

## 9. Phase 1 Milestone Sequence (2-3 weeks, locked)

**Build Sequence with Locked Decisions**

| Week | Milestone | Deliverable | Technical Scope |
|------|-----------|-------------|-----------------|
| **Week 1** | **"It moves"** | Lua sprite renders on device; host sends mock FAMILIAR_UPDATE; creature bobs | Python harness + Lua render loop on device; abstract sprite (24×24 geometric form with eye); test BLE wire format |
| Week 1 | BLE protocol | FAMILIAR_UPDATE message defined and working | Opcode 0x80, mood_enum (0-3), intensity (0-100), confidence (0-100), sequence number |
| **Week 2** | **"It reacts"** | Host captures mic + IMU (no camera); local heuristic inference; creature reflects mood | Python PyAudio + Halo IMU relay; tone/pitch variance + acceleration + rotation weighting; 10Hz updates to device |
| Week 2 | Stress/calm states | Visual states per DASID spec (breathing speed ±0.75Hz vs 0.15Hz, color shift warm↔cool) | Lua animation state machine: neutral ↔ calm ↔ stressed; smooth 200-500ms interpolation |
| **Week 3** | **"It's alive"** | First-launch UX; attention moments (jump-on-peak); quick-reset (double-tap); graceful fallback | Host onboarding flow in Python; device-side IMU-peak callback to `on_imu_peak`; BLE timeout + neutral fallback after 10s |
| Week 3 | Polish + test | Test on real device; tune confidence thresholds; document | Baseline learning (pop defaults days 1-3, personal mean+1.5σ after); privacy audit checklist ✅; heap monitoring at 80% |

**Success criteria (locked):**
- Week 1: Aaron can see creature bobbing on Halo display without jitter; BLE messages log cleanly
- Week 2: Aaron can trigger stress state by raising voice in quiet room; stressed visual (faster breathing, warm color) appears within 500ms
- Week 3: Aaron feels creature is "alive" (not robotic) after 1 hour of wear; gesture resets work; no OOM or BLE freeze during session

---

## 10. Open Questions

*Not decisions for Aaron — requires team follow-up*

1. **IMU event primitive:** Does `brilliant-ble` support interrupt-style IMU callbacks, or must we poll? If polling-only, Lua must implement a debounced tap-detection loop; target latency ≤50ms. (NG to investigate with SDK team)

2. **Sprite format:** What is the canonical pixel-buffer format for Lua `bitmap()` calls — indexed 4-bit, raw RGB565, or run-length encoded? Determines sprite asset pipeline. (NG to document from SDK source / Brilliant docs)

3. **Heap monitoring:** Is `frame.system.get_heap_usage()` available in current Lua stdlib? If absent, safe-halt threshold must be approximated by tracking allocation sites manually. (NG to verify against current Halo firmware)

4. **Baseline learning persistence:** Where do we store the wearer's personal baseline (mean, stddev) between sessions — on-device flash, host filesystem, or cloud? Phase 1 can use host filesystem; Phase 2 needs a durable strategy. (Aaron + Hiro to decide before Phase 2)

5. **Cross-platform parity:** If Phase 2 adds Web Bluetooth, how do we maintain parity with the Python host? Shared mood calculation logic requires a JS port or a shared native library. (Deferred to Phase 2 scoping)

6. **Accessibility:** How does a wearer with colorblindness perceive stress vs. calm? (Da5id to propose alternative visual encoding)

> **Resolved (2026-06-08, Ng):** Wire-format items previously listed here — endianness, sequence wraparound/dedup, FAMILIAR_RESET direction and opcode, ACK cadence — are now fully specified in §5.2. No further open questions on BLE wire format.

---

---

*This is the first official Halo playground project. Build it fast, learn from it, iterate.*

---

**Document history:**
- 2026-06-07: Initial draft (Hiro)
- 2026-06-07: Approved by Aaron — Decisions 1, 2, 3 locked; ARD finalized
