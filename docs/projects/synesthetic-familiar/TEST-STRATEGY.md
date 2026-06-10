# Test Strategy: The Synesthetic Familiar

| Field | Value |
|-------|-------|
| **Status** | REVISED |
| **Date** | 2026-06-09 |
| **Author** | Juanita (Tester / QA) |
| **ARD reference** | docs/projects/synesthetic-familiar/ARD.md (approved 2026-06-07, amended 2026-06-09) |
| **School** | London (mockist) TDD — outside-in, Red→Green→Refactor; DELIBERATELY classicist for pure-function units |

---

## Revision History

| Date | Author | Summary |
|------|--------|---------|
| 2026-06-09 | Juanita | **Rev 3** — Persona-review remediation wave. I10: `hypothesis` property test on `compute_mood` replaced with `@pytest.mark.parametrize` fixture table; `lupa` Python→Lua cross-validation path removed/deferred; `busted` sole Lua authority; `--cov-fail-under=90` global CI gate removed (selective 95% on `familiar_protocol.py` retained). I1: ATTENTION overlay-and-restore busted test added (§7.2). I2: ~30s confidence-hold timeout test added (FakeClock-driven, §6.4); stuck-creature scenario moved to Phase-1. I3: CALM 60s sustain busted timing test added (§7.2). I5: YT-T2-2 restated as deferred Phase-2 (no v1 test/DoD) in §5; Rev 2 "removed" claim corrected. I8: `compute_mood` output-shape unit test added (§4.1). I11: Deterministic FakeClock-driven interpolation test specified (§6.5). M3: No-network assertion noted (§6.10). M5: Week-1 programmatic emulator gate added (§7.5). |
| 2026-06-08 | Juanita | **Rev 2** — Advisory review findings applied. Wire format aligned to resolved ARD (LE endianness, signed-16 wraparound dedup, `FAMILIAR_RESET` opcode 0x01 Device→Host, ACK every 10 accepted packets). Heap ownership corrected to device-only (Lua tier); host/wire heap protocol removed throughout. False-positive bug in `test_low_confidence_frame_below_neutral_band_also_suppressed` fixed (single shared transport). Acceptance tests decoupled from heuristic internals via `inference_fn` injection. Honest mixed-methodology framing added (London-school acceptance, deliberate classicist for pure-function units). `busted` declared authoritative Lua test runner. Quick-reset seam corrected (device-originated). Confidence gating ownership clarified (host = sole authority; device optional). Appendix A ARD gaps updated: wire-format and ownership items marked RESOLVED; genuine open items retained. Story mapping reconciled (YT-T2-2 predictive-inference story restated as deferred Phase-2, no v1 test/DoD; RAVEN-T2-1 automated protocol assertion added). Jitter seam and biometric-privacy protocol test added. |
| 2026-06-08 | Juanita | **Rev 1** — Initial test strategy authored. |

---

## Table of Contents

1. [Philosophy — London School TDD](#1-philosophy--london-school-tdd)
2. [Test Pyramid & Layers](#2-test-pyramid--layers)
3. [Test Doubles & Seams](#3-test-doubles--seams)
4. [Outside-In Walkthrough](#4-outside-in-walkthrough)
5. [Story → Test Mapping](#5-story--test-mapping)
6. [Edge Cases & Flake Tolerance](#6-edge-cases--flake-tolerance)
7. [Lua / On-Device Testing](#7-lua--on-device-testing)
8. [Tooling & CI](#8-tooling--ci)
9. [Definition of Done Per Story](#9-definition-of-done-per-story)

---

## 1. Philosophy — London School TDD

### The London (Mockist) School

London-school TDD, also called "mockist" or "outside-in" TDD, works from the
outside boundary of the system inward. You begin with an **acceptance test**
that describes the behavior the system must exhibit at its highest seam — in
our case, a test that drives the whole host app through a fake BLE transport
and observes what lands on the "wire." That acceptance test fails immediately
(Red). You then ask: "what collaborators must exist for this test to pass?"
The test **discovers** the interface design, not a pre-designed class diagram.
You mock those collaborators, implement the minimum code to satisfy the
acceptance test (Green), then refactor.

**Tell-Don't-Ask**: Because you mock collaborators and assert on *interactions*
(calls, messages sent) rather than internal state, you are forced into
Tell-Don't-Ask designs. `FamiliarApp` orchestrates: it reads from
`SensorSourcePort`, calls the injected `inference_fn`, and **tells** the
`TransportPort` to send — nobody reaches inside anyone else's internals.
Critically: inference does NOT tell the protocol to encode. Orchestration lives
in `FamiliarApp`, not in `inference.py`. The test naturally surfaces clean
interface contracts.

### Honest Mixed Methodology

Not every test in this strategy is London-school. This is intentional:

| Test category | School | Rationale |
|---------------|--------|-----------|
| Acceptance tests (`test_host_drives_animation.py`, `test_confidence_gating.py`, …) | **London / mockist** | Outside-in; mock collaborators; discover contracts |
| `inference.py` unit tests | **Deliberately classicist** | Pure function — takes floats, returns a dict. No collaborators to mock. State-based assertion is exactly right here. |
| `familiar_protocol.py` unit tests | **Deliberately classicist** | Wire encoding is a value transformation. Correct output is the contract; interaction mocking adds nothing. |
| `sensors.py` failure-mode tests | Mostly classicist, seam-based where needed | Pure data paths are classicist; BLE/hardware seams use fakes. |

Claiming everything is mockist would be dishonest and would force unnecessary
mock machinery onto pure-function tests. The classicist choice for
`inference.py` and `familiar_protocol.py` is not a concession — it is
architecturally correct.

**Red→Green→Refactor as operating rhythm:**

```
RED    Write the smallest failing test that describes one behavior.
       It must fail for the right reason — not a missing import, but a
       missing behavior. Verify the failure message before moving on.

GREEN  Write the *minimum* code to make it pass. No gold-plating.
       It can be ugly. It must not touch tests.

REFACTOR  Clean up: rename, extract, DRY. Tests stay green throughout.
          This is the only phase where design improves.
```

No production code is written without a failing test. No test is deleted or
modified to hide a failure. Refactoring only happens under green.

### Contrast with Detroit (Classicist) School

The Detroit/classicist school tests observable *state*: call a function,
inspect the return value or an object's fields. It prefers real objects and
avoids mocks unless unavoidable. It's excellent for pure-function-heavy
codebases, data pipelines, and domains where collaborator contracts are
stable.

**Why London fits The Synesthetic Familiar:**

1. **BLE is a collaborator, not an implementation detail.** `brilliant-ble`
   is an external SDK we do not control. Mocking it is not laziness; it is
   the architecturally honest seam. Testing against a real BLE stack would
   make every host-side unit test hardware-dependent, slow, and flaky.

2. **The device is a collaborator.** The Lua render loop runs on hardware
   we cannot introspect cheaply. A mockist approach lets us assert that
   `familiar_protocol.py` produces the correct 6-byte wire payload without
   requiring a physical Halo device in CI.

3. **Sensors are injected environment, not implementation.** Mic audio and
   IMU data arrive from the outside world. Injecting fake sensor streams via
   test doubles lets us drive the inference pipeline deterministically —
   critical for thresholding and confidence-gating tests.

4. **The clock is a hidden collaborator.** Breathing interpolation, BLE
   timeout (10s → neutral), and confidence-hold timing all depend on wall
   time. London school makes the clock visible by injecting it, enabling
   deterministic timing tests without `time.sleep()`.

5. **Interface discovery drives architecture.** We don't fully know the
   shape of `sensors.py`, `inference.py`, or `familiar_protocol.py` yet.
   Writing acceptance tests first forces us to name the boundaries before
   coding them, which produces better interfaces than designing first and
   testing second.

---

## 2. Test Pyramid & Layers

```
         ▲  Fewer, slower, more trust
         │
    ┌────┴────────────────────────────────────────────────────────────┐
    │  TIER 4 — MANUAL / REAL DEVICE                                  │
    │  Real Halo, real BLE, real mic/IMU, human eyes on display.     │
    │  Run per-milestone (Weeks 1, 2, 3). Not in CI.                  │
    └─────────────────────────────────────────────────────────────────┘
    ┌────────────────────────────────────────────────────────────────┐
    │  TIER 3 — INTEGRATION (halo-emulator + emulated BLE)           │
    │  Real Python SDK code against halo-emulator.                   │
    │  Device-side Lua running in emulator, not on hardware.         │
    │  BLE transport is the emulator's loopback — no physical radio. │
    │  Slow (~30-120s). Run on PR, not on every commit.              │
    └────────────────────────────────────────────────────────────────┘
    ┌────────────────────────────────────────────────────────────────┐
    │  TIER 2 — ACCEPTANCE (outside-in, whole host app)              │
    │  Drives main.py through FakeTransport + FakeSensorSource.      │
    │  No real BLE, no real mic, no real device.                     │
    │  Asserts on wire-format bytes sent to FakeTransport.           │
    │  Medium speed (~1-10s). Run on every commit.                   │
    └────────────────────────────────────────────────────────────────┘
    ┌────────────────────────────────────────────────────────────────┐
    │  TIER 1 — UNIT (fast, isolated, mockist)                       │
    │  inference.py: pure mood heuristic, confidence gating.         │
    │  familiar_protocol.py: wire encoding/decoding.                 │
    │  sensors.py: sensor source interface, failure modes.           │
    │  Lua state machine: extracted pure logic, tested via Python    │
    │  simulation or busted.                                          │
    │  Fast (<100ms per test). Run on every save.                    │
    └────────────────────────────────────────────────────────────────┘
         │
         ▼  More, faster, more isolation
```

### What is Mocked at Each Layer

| Layer | What is Real | What is Mocked / Faked |
|-------|-------------|------------------------|
| Unit | The function under test | Collaborators (BLE, sensors, clock, logger) |
| Acceptance | All host-side Python code | BLE transport (FakeTransport), sensor source (FakeSensorSource), clock (FakeClock), device-side Lua (not involved) |
| Integration | Python SDK + halo-emulator Lua runtime | Physical Halo hardware; real radio |
| Manual / Device | Everything | Nothing |

### Ports & Adapters Seams

The following are the architectural seams where test doubles plug in:

| Seam | Port Name | Real Adapter | Test Double |
|------|-----------|-------------|-------------|
| BLE transport | `TransportPort` | `BrilliantBLETransport` (brilliant-ble) | `FakeTransport` (records sent bytes, injectable errors) |
| Sensor source (mic+IMU) | `SensorSourcePort` | `SounddeviceMicSource` + `HaloIMURelay` | `FakeSensorSource` (yields pre-scripted frames) |
| Clock / time | `ClockPort` | `time.monotonic` | `FakeClock` (manually advanceable) |
| Device display | None (we don't own it) | Halo OLED via Lua | halo-emulator framebuffer |
| Confidence gate | Inline in `inference.py` | — | Parameterized threshold injectable |

These seams **must** be reflected in the constructor signatures of
`main.py`, `sensors.py`, `inference.py`, and `familiar_protocol.py`:

```python
# main.py — dependency injection example
class FamiliarApp:
    def __init__(
        self,
        transport: TransportPort,
        sensor_source: SensorSourcePort,
        clock: ClockPort,
        inference_fn=compute_mood,   # injectable for testing
    ):
        ...
```

If a class instantiates its own BLE connection or calls `time.monotonic()`
directly, it is untestable at the acceptance layer. These are defects in
design, not gaps in test coverage.

---

## 3. Test Doubles & Seams

### 3.1 FakeTransport

Replaces `brilliant-ble`'s BLE connection. The single most important double
in the project — every host-side test that cares about the wire goes through
here.

```python
class FakeTransport:
    def __init__(self):
        self.sent: list[bytes] = []
        self.should_fail: bool = False
        self.fail_after_n: int | None = None  # drop the Nth packet

    def send(self, data: bytes) -> None:
        if self.should_fail:
            raise BLETransportError("simulated BLE drop")
        if self.fail_after_n is not None and len(self.sent) >= self.fail_after_n:
            raise BLETransportError("simulated mid-session drop")
        self.sent.append(data)

    def last_packet(self) -> bytes:
        return self.sent[-1]

    def packet_count(self) -> int:
        return len(self.sent)
```

**Seam requirement:** `main.py` / `familiar_protocol.py` must accept a
transport instance, never import `brilliant-ble` at module level without
injection.

### 3.2 FakeSensorSource

Replaces the mic + IMU capture pipeline. Yields pre-scripted sensor frames,
including failure scenarios.

```python
class FakeSensorSource:
    def __init__(self, frames: list[SensorFrame]):
        self._frames = iter(frames)

    def read_frame(self) -> SensorFrame:
        try:
            return next(self._frames)
        except StopIteration:
            raise SensorExhaustedError("no more scripted frames")

# SensorFrame carries: audio_rms, audio_pitch_variance, imu_accel, imu_rot
# Special variants:
# SensorFrame.mic_failure()  -> audio fields None, imu fields populated
# SensorFrame.imu_failure()  -> imu fields None, audio fields populated
# SensorFrame.both_failure() -> all fields None
```

### 3.3 FakeClock

Replaces `time.monotonic()`. Allows test to advance time programmatically,
testing BLE timeout (10s → neutral), interpolation timing (200-500ms), and
confidence hold windows without any `time.sleep()`.

```python
class FakeClock:
    def __init__(self, start: float = 0.0):
        self._now = start

    def now(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds
```

**Critical tests enabled by FakeClock:**
- BLE 10s timeout: advance 10.1s, assert device enters neutral
- Interpolation: assert state transitions complete in 200-500ms window
- Confidence hold: assert stale state persists through low-confidence window

### 3.4 Device-Side (Lua) Double Strategy

The Lua render loop (`main.lua`) is not a Python object we can mock directly.
Three strategies, in order of priority:

1. **Emulator framebuffer** (integration tier): halo-emulator provides a
   `get_framebuffer()` call that returns pixel data. Assert on lit-pixel
   counts, specific pixel positions, color palette presence.

2. **Extracted Lua state machine** (unit tier): Pull the pure state-machine
   logic (transition table, interpolation math) into a separate `state_machine.lua`
   module. Test that module with `busted` (Lua test framework) independently
   of the render loop and BLE.

3. **Python simulation** (unit tier, fallback): Reimplement the state machine
   transitions in Python for cross-validation. Not the production code, but
   a behavioral oracle. See Section 7 for detail.

---

## 4. Outside-In Walkthrough

### 4.1 Story: NG-T2-1 — Drive Animation from Host Sensor Data

**Goal:** Host sends a `FAMILIAR_UPDATE` message when sensor data changes mood.

#### Red — Acceptance Test

Acceptance tests inject an `inference_fn` seam so orchestration is tested
independently of heuristic tuning. Specific sensor values and confidence
thresholds belong in `tests/unit/test_inference.py`, not here.

> **London-school discipline:** Before writing this test, create a minimal
> stub `FamiliarApp` that accepts the constructor signature and implements
> `run_cycle()` as a no-op. The test then **fails for missing behavior**
> (`transport.packet_count() == 0` when 1 is expected) — not for a missing
> import. A `NameError` is not a meaningful Red; silence when a packet was
> expected is.

```python
# tests/acceptance/test_host_drives_animation.py

def test_stressed_sensor_data_sends_familiar_update_stressed():
    """
    GIVEN an inference_fn that deterministically returns STRESSED/high-confidence
    WHEN the FamiliarApp runs one inference cycle
    THEN a FAMILIAR_UPDATE with mood=STRESSED lands on FakeTransport
    """
    transport = FakeTransport()
    sensor_source = FakeSensorSource(frames=[
        SensorFrame(audio_rms=0.8, audio_pitch_variance=0.9,
                    imu_accel=0.7, imu_rot=0.5)
    ])
    clock = FakeClock()

    def stub_inference(frame):
        return {"mood": "stressed", "intensity": 85, "confidence": 82}

    app = FamiliarApp(
        transport=transport,
        sensor_source=sensor_source,
        clock=clock,
        inference_fn=stub_inference,
    )
    app.run_cycle()

    assert transport.packet_count() == 1
    packet = transport.last_packet()
    assert packet[0] == 0x80          # FAMILIAR_UPDATE opcode
    assert packet[1] == 2             # mood_enum: STRESSED
    assert packet[2] == 85            # intensity
    assert packet[3] == 82            # confidence
    seq = struct.unpack("<H", packet[4:6])[0]   # seq: uint16 LITTLE-ENDIAN
    assert seq == 1
```

**This test fails because `run_cycle()` sends nothing.** `FamiliarApp` exists
as a stub; the Red is behavioral (packet not sent), not structural.

#### Collaborators Discovered by Acceptance Test

- `FamiliarApp` — the orchestrator (constructor seam confirmed)
- `SensorSourcePort` — sensor abstraction
- `TransportPort` — BLE abstraction
- `inference_fn` — injectable callable, signature `(SensorFrame) → dict`
- `encode_familiar_update()` — encoding function (needs to exist in `familiar_protocol.py`)

#### Green — Driving Unit Tests Downward

The acceptance test drives us to define `compute_mood()` in `inference.py`.
These unit tests are **deliberately classicist** — pure function, no mocks:

```python
# tests/unit/test_inference.py

def test_high_pitch_variance_and_acceleration_yields_stressed():
    result = compute_mood(
        audio_rms=0.8, audio_pitch_variance=0.9,
        imu_acceleration=0.7, imu_rotation=0.5
    )
    assert result["mood"] == "stressed"
    assert result["confidence"] >= 0.8

def test_low_tension_yields_calm():
    result = compute_mood(
        audio_rms=0.2, audio_pitch_variance=0.1,
        imu_acceleration=0.1, imu_rotation=0.05
    )
    assert result["mood"] == "calm"
    assert result["confidence"] >= 0.8
```

And drives us to define `encode_familiar_update()` in `familiar_protocol.py`.
Also **deliberately classicist** — pure byte-transformation, no mocks:

```python
# tests/unit/test_protocol.py

def test_encode_familiar_update_wire_format():
    payload = encode_familiar_update(
        mood=Mood.STRESSED, intensity=85, confidence=82, seq=1
    )
    assert len(payload) == 6
    assert payload[0] == 0x80         # opcode
    assert payload[1] == 2            # STRESSED = 2
    assert payload[2] == 85           # intensity
    assert payload[3] == 82           # confidence
    seq = struct.unpack("<H", payload[4:6])[0]  # uint16 LITTLE-ENDIAN (BLE ATT native)
    assert seq == 1

def test_encode_familiar_update_all_mood_values():
    for mood, expected_enum in [
        (Mood.NEUTRAL, 0), (Mood.CALM, 1),
        (Mood.STRESSED, 2), (Mood.ATTENTION, 3)
    ]:
        payload = encode_familiar_update(mood=mood, intensity=50, confidence=75, seq=0)
        assert payload[1] == expected_enum

def test_familiar_update_carries_no_raw_biometric_values():
    """Privacy: payload must contain only mood_enum/intensity/confidence/seq — no
    raw audio RMS, pitch variance, IMU accel, or any biometric sensor reading."""
    # encode_familiar_update only accepts the processed fields; this test confirms
    # the function signature itself cannot leak raw sensor data
    import inspect
    params = inspect.signature(encode_familiar_update).parameters
    raw_biometric_params = {"audio_rms", "pitch_variance", "imu_accel", "imu_rot"}
    assert raw_biometric_params.isdisjoint(params.keys()), (
        f"encode_familiar_update must not accept raw biometric params; got {params.keys()}"
    )

def test_compute_mood_returns_only_expected_keys():
    """I8/RAVEN-T2-1 inference-output shape: compute_mood must return EXACTLY
    {mood, intensity, confidence}. No raw sensor values may leak past inference."""
    result = compute_mood(
        audio_rms=0.8, audio_pitch_variance=0.9,
        imu_acceleration=0.7, imu_rotation=0.5
    )
    assert set(result.keys()) == {"mood", "intensity", "confidence"}, (
        f"compute_mood must return only {{mood, intensity, confidence}}; "
        f"got {set(result.keys())}"
    )
```

**Refactor phase:** Once tests are green, extract `STRESS_THRESHOLD` and
`CALM_THRESHOLD` as named constants in `inference.py`. Extract packet
validation logic into a shared `validate_familiar_update()` helper.
All tests stay green.

---

### 4.2 Story: LIBRARIAN-T2-5-ERROR — Confidence Gating (Silence > Wrong)

**Goal:** If confidence < 0.7, host holds current state and does NOT send an update.

#### Red — Acceptance Test

Acceptance tests inject `inference_fn` so the gate logic is tested
independently of heuristic tuning. Raw sensor values in acceptance tests would
couple these tests to `compute_mood` internals — don't do that.

```python
# tests/acceptance/test_confidence_gating.py

def test_low_confidence_does_not_send_update():
    """
    GIVEN inference_fn returns high-confidence STRESSED on call 1,
          then low-confidence (0.60) on call 2
    WHEN the FamiliarApp runs two inference cycles
    THEN only ONE packet is sent (the first); second cycle is suppressed
    """
    transport = FakeTransport()
    clock = FakeClock()
    call_count = [0]

    def controlled_inference(frame):
        call_count[0] += 1
        if call_count[0] == 1:
            return {"mood": "stressed", "intensity": 80, "confidence": 82}
        return {"mood": "calm", "intensity": 40, "confidence": 60}  # below gate

    sensor_source = FakeSensorSource(frames=[
        SensorFrame(audio_rms=0.8, audio_pitch_variance=0.9,
                    imu_accel=0.7, imu_rot=0.5),
        SensorFrame(audio_rms=0.3, audio_pitch_variance=0.2,
                    imu_accel=0.4, imu_rot=0.4),
    ])
    app = FamiliarApp(transport=transport, sensor_source=sensor_source,
                      clock=clock, inference_fn=controlled_inference)

    app.run_cycle()  # cycle 1 — high confidence STRESSED → packet sent
    initial_count = transport.packet_count()
    assert initial_count == 1

    app.run_cycle()  # cycle 2 — low confidence → NO packet
    assert transport.packet_count() == initial_count  # unchanged


def test_low_confidence_frame_below_neutral_band_also_suppressed():
    """Confidence gate applies to ALL moods, not just stressed."""
    transport = FakeTransport()   # ONE instance — both constructor arg and assertion target
    sensor_source = FakeSensorSource(frames=[
        SensorFrame(audio_rms=0.35, audio_pitch_variance=0.35,
                    imu_accel=0.35, imu_rot=0.35),
    ])

    def low_conf_inference(frame):
        return {"mood": "neutral", "intensity": 50, "confidence": 60}

    app = FamiliarApp(transport=transport, sensor_source=sensor_source,
                      clock=FakeClock(), inference_fn=low_conf_inference)
    app.run_cycle()
    assert transport.packet_count() == 0   # assert on the SAME transport instance
```

**This test fails.** There is no gating logic in `FamiliarApp.run_cycle()`.

#### Collaborators Discovered

The test drives us to wire confidence-gating into `run_cycle()`:
the injected `inference_fn` returns a `confidence` field. The gate
belongs in `FamiliarApp.run_cycle()`, not inside `inference_fn` — Tell-Don't-Ask
means the orchestrator makes the send/skip decision.

#### Unit Tests Driven Downward

```python
# tests/unit/test_inference.py (additions — classicist, no mocks)

def test_ambiguous_tension_yields_low_confidence():
    """Mid-band input must produce confidence < 0.7 to trigger gate."""
    result = compute_mood(
        audio_rms=0.35, audio_pitch_variance=0.35,
        imu_acceleration=0.35, imu_rotation=0.35
    )
    assert result["confidence"] < 0.7  # gate threshold
    assert result["mood"] == "neutral"

def test_confidence_gate_constant_is_0_7():
    """Verify the confidence threshold constant matches ARD spec."""
    assert CONFIDENCE_GATE == 0.7
```

---

### 4.3 Story: JUANITA-T2-2 — Offline Fallback (Mic Fail, IMU Fail, Both Fail)

**Goal:** When sensors degrade, system falls back gracefully. When both fail
for 10s, device returns to neutral. Creature never freezes or loops stale stress.

#### Red — Acceptance Test

```python
# tests/acceptance/test_offline_fallback.py

def test_mic_failure_uses_imu_only_reduced_confidence():
    """
    GIVEN mic returns None (hardware fault)
    WHEN inference runs
    THEN update is sent with reduced confidence (< 0.8); no exception raised
    """
    sensor_source = FakeSensorSource(frames=[SensorFrame.mic_failure(
        imu_accel=0.5, imu_rot=0.3
    )])
    transport = FakeTransport()
    app = FamiliarApp(transport=transport, sensor_source=sensor_source,
                      clock=FakeClock(),
                      inference_fn=lambda frame: {"mood": "calm", "intensity": 40,
                                                   "confidence": 70})

    app.run_cycle()  # must not raise

    assert transport.packet_count() <= 1  # may send with reduced confidence
    if transport.packet_count() == 1:
        packet = transport.last_packet()
        assert packet[3] < 80          # reduced confidence < 0.8


def test_both_sensors_fail_holds_state_for_10s_then_neutral():
    """
    GIVEN both mic and IMU are unavailable (SensorFrame.both_failure)
    WHEN the clock advances past 10 seconds
    THEN a FAMILIAR_UPDATE with mood=NEUTRAL is sent
    """
    transport = FakeTransport()
    clock = FakeClock(start=0.0)
    # Pre-seed a STRESSED state first
    stressed_frame = SensorFrame(audio_rms=0.9, audio_pitch_variance=0.9,
                                 imu_accel=0.8, imu_rot=0.8)
    fail_frame = SensorFrame.both_failure()
    sensor_source = FakeSensorSource(frames=[stressed_frame] + [fail_frame] * 20)

    call_count = [0]
    def fallback_inference(frame):
        call_count[0] += 1
        if call_count[0] == 1:
            return {"mood": "stressed", "intensity": 85, "confidence": 82}
        raise SensorDataUnavailableError("both sensors failed")

    app = FamiliarApp(transport=transport, sensor_source=sensor_source,
                      clock=clock, inference_fn=fallback_inference)
    app.run_cycle()  # establishes STRESSED state

    # Simulate 10 cycles of both-failure at ~1s each
    for _ in range(10):
        clock.advance(1.0)
        app.run_cycle()

    # After 10+ seconds of both-fail, next cycle must reset to NEUTRAL
    clock.advance(0.5)
    app.run_cycle()

    last_packet = transport.last_packet()
    assert last_packet[0] == 0x80
    assert last_packet[1] == 0         # mood_enum NEUTRAL
```

#### Collaborators Discovered

`SensorFrame.both_failure()` drives creation of a typed null-object pattern
in `sensors.py`. `FamiliarApp` needs an internal `last_update_time` tracking
collaborating with `ClockPort` to implement the 10s hold → neutral logic.
The clock injection seam is now load-bearing.

---

## 5. Story → Test Mapping

| Story ID | Priority | Primary Layer | Test Intent |
|----------|----------|---------------|-------------|
| DASID-T2-1 | P0 | Integration / Manual | Emulator shows sprite at 7-o'clock position bobbing at 0.25Hz with ~1.5% lit pixels |
| DASID-T2-2 | P0 | Integration + Unit | STRESSED state: breathing at 0.75Hz, warm-amber palette sent; visual confirmed in emulator |
| DASID-T2-3 | P0 | Integration + Unit | CALM state: 0.15Hz breathing, cool-teal palette, halo-glow circle elements present |
| DASID-T2-4 | P1 | Integration + Unit | ATTENTION triggers 15px jump animation; returns to base position within 500ms |
| DASID-T2-5 | P0 | Manual (visual audit) | Bystander screenshot shows no labeled emotion; jitter present; abstract form only |
| LIBRARIAN-T2-1 | P0 | Acceptance | `run_cycle()` sends FAMILIAR_UPDATE derived from sensor data without explicit query |
| LIBRARIAN-T2-2 | P1 | Unit | After 3 days of simulated frames, thresholds shift to personal mean±1.5σ |
| LIBRARIAN-T2-5-ERROR | P0 | Acceptance + Unit | Confidence < 0.7 suppresses send; stale state held; no thrash on ambiguous input |
| YT-T2-1 | P0 | Acceptance | First-launch flow drives `FamiliarApp` through onboarding sequence; creature appears on emulator before inference starts |
| YT-T2-2 | P2 — Deferred Phase-2 | — | *(Deferred Phase-2; no v1 test/DoD. Baseline-adaptation / predictive-inference: after accumulating history, `compute_mood` thresholds shift toward personal mean. Out of scope for v1.)* |
| NG-T2-1 | P0 | Acceptance + Unit | Host sensor data produces correct wire-format FAMILIAR_UPDATE (opcode 0x80, mood_enum 0-3, intensity, confidence, seq) |
| NG-T2-2 | P1 | Integration | `on_imu_peak` callback triggers ATTENTION mood; emulator IMU injection → jump animation observed in framebuffer |
| JUANITA-T2-1 | P1 | Integration + Manual | Frame-skipping under load: at >50ms/frame, Lua drops to 15fps without visual freeze; emulator timing |
| JUANITA-T2-2 | P0 | Acceptance | Mic-only / IMU-only / both-fail paths each produce correct degraded output; 10s both-fail → NEUTRAL send |
| JUANITA-T2-3 | P2 | Device (Lua/emulator) | Heap at 80%: `state_machine.lua` reduces sprite complexity locally (emulator + busted); heap at 95%: safe halt; NO host involvement |
| JUANITA-T2-5 | P1 | Acceptance + Integration | Device detects double-tap → Lua snaps to NEUTRAL locally; host receives FAMILIAR_RESET notification (opcode 0x01, 1 byte, no payload); integration confirms reset in emulator |
| RAVEN-T2-1 | P0 | Acceptance (protocol) + Manual (visual) | Protocol: automated test asserts FAMILIAR_UPDATE payload contains NO raw biometric bytes (6-byte format confirmed); visual: non-wearer inspection confirms abstract form only |
| HIRO-T2-1 | P0 | Acceptance | Mood inference and render loop are decoupled: `FamiliarApp` can run `run_cycle()` without a live device/transport |
| HIRO-T2-2 | P0 | Acceptance | BLE transport error mid-session does not crash host; `FakeTransport.should_fail=True` → graceful retry or hold |
| ENZO-T2-1 | P0 | Manual | Milestone demo: wearer raises voice → STRESSED within 500ms; settles → CALM within 60s |
| ENZO-T2-2 | P1 | Manual | Informal usability: anxious/ND wearer reports creature feels accurate and non-intrusive after 20min session |

---

## 6. Edge Cases & Flake Tolerance

### 6.1 BLE Drop Mid-Session

**Failure mode:** `brilliant-ble` raises `BLETransportError` on a send() after
N packets — e.g., wearer walks out of BLE range.

**Test approach:**
```python
def test_ble_drop_mid_session_does_not_crash_host():
    transport = FakeTransport()
    transport.fail_after_n = 3   # drop on 4th packet
    sensor_source = FakeSensorSource(frames=[stressed_frame()] * 10)
    app = FamiliarApp(transport=transport, sensor_source=sensor_source, clock=FakeClock())

    for _ in range(10):
        app.run_cycle()  # must not raise past 3rd packet

    # Host should enter retry/hold mode, not crash
    # After drop, last sent packet was seq=3; app records reconnect-needed state
    assert app.transport_status == TransportStatus.DISCONNECTED
```

**Assertion:** No exception propagates out of `run_cycle()`. Host enters a
reconnect-pending state. Device-side: after 10s without update, device
independently transitions to NEUTRAL (tested separately in integration tier).

**This is not flaky.** By injecting the failure via `FakeTransport`, the
failure is deterministic. Flake tolerance means: we do not test this against
a real BLE radio (which *is* flaky); we test it via injected failure, which
always reproduces.

### 6.2 Sensor Failure Modes (All Combinations)

| Failure Scenario | Expected Behavior | Test Layer |
|-----------------|-------------------|------------|
| Mic only (IMU available) | Run with IMU-only heuristic; confidence < 0.8 | Unit + Acceptance |
| IMU only (mic available) | Run with mic-only heuristic; confidence < 0.8 | Unit + Acceptance |
| Both fail, < 10s | Hold last-known state; no new send | Acceptance |
| Both fail, > 10s | Send FAMILIAR_UPDATE NEUTRAL (mood_enum=0) | Acceptance |
| Mic returns silence (rms ≈ 0) | Treated as valid mic data, not failure; may yield calm | Unit |
| IMU returns zeros | Treated as valid (wearer at rest), not failure | Unit |

**Test naming convention:** `test_{sensor_scenario}_yields_{expected_outcome}`

### 6.3 Lua Heap Exhaustion

**Ownership:** Heap management is **entirely device-local**. The host does not
participate; nothing heap-related appears on the wire. `FAMILIAR_ACK` is
seq-only (no heap flag). Tests for heap behavior live at the Lua/emulator tier.

**Behavior under test (ARD-specified):**
- At 80% heap: `state_machine.lua` reduces sprite complexity (fewer keyframes,
  simpler palette) — detected via emulator framebuffer.
- At 95% heap: Lua enters safe-halt (NEUTRAL minimal sprite), no OOM crash,
  no watchdog reset.

```lua
-- tests/lua/test_heap_behavior.lua (busted)

describe("heap management", function()
  it("reduces animation complexity at 80% heap", function()
    -- Requires emulator set_heap_usage API; skip if unavailable
    if not emulator or not emulator.set_heap_usage then
      pending("blocked: emulator set_heap_usage API unconfirmed (Appendix A #2)")
      return
    end
    emulator.set_heap_usage(0.82)
    sm:tick()
    assert.is_true(sm:is_reduced_complexity())
  end)

  it("enters safe-halt at 95% heap — no crash, NEUTRAL sprite", function()
    if not emulator or not emulator.set_heap_usage then
      pending("blocked: emulator set_heap_usage API unconfirmed (Appendix A #2)")
      return
    end
    emulator.set_heap_usage(0.96)
    sm:tick()
    assert.equals("neutral", sm:current_mood())
    assert.is_true(sm:is_safe_halted())
  end)
end)
```

**Python integration test (halo-emulator tier):**
```python
@pytest.mark.integration
@pytest.mark.skipif(not hasattr(HaloEmulator, "set_heap_usage"),
                    reason="blocked: emulator set_heap_usage API unconfirmed (Appendix A #2)")
def test_heap_critical_triggers_safe_halt():
    """At 95% heap, Lua must not OOM-crash; must enter safe-halt state."""
    emulator = HaloEmulator()
    emulator.load_lua("device/main.lua")
    emulator.set_heap_usage(0.96)
    emulator.tick(frames=10)
    fb = emulator.get_framebuffer()
    # Safe-halt = NEUTRAL sprite only; assert display is quiet
    assert lit_pixel_percentage(fb) < 3.0
```

**What is NOT tested here:** Any host-side heap behavior — there is none.
Host-side tests never reference heap state.

### 6.4 Low-Confidence Thrashing

**Failure mode:** Sensor input oscillates around the neutral band, causing
confidence to hover at 0.65-0.69. Each cycle: no send. But the wearer
notices the creature is "stuck."

```python
def test_prolonged_low_confidence_does_not_thrash():
    """20 consecutive low-confidence cycles → no packets sent → creature holds."""
    transport = FakeTransport()

    def always_low_conf(frame):
        return {"mood": "neutral", "intensity": 50, "confidence": 65}

    frames = [SensorFrame(audio_rms=0.35, audio_pitch_variance=0.34,
                          imu_accel=0.34, imu_rot=0.33)] * 20
    sensor_source = FakeSensorSource(frames=frames)
    app = FamiliarApp(transport=transport, sensor_source=sensor_source,
                      clock=FakeClock(), inference_fn=always_low_conf)
    for _ in range(20):
        app.run_cycle()
    assert transport.packet_count() == 0  # silence > hallucination
```

**Confidence-hold timeout (Phase-1, ARD §5.4):** After ~30 seconds of gated
silence (sustained sub-0.7 confidence), the host re-sends the last confirmed
mood rather than leaving the creature stuck. This is the confirmed fix for the
"stuck creature" scenario — moved to Phase-1 per Aaron's decision 2026-06-09.
The `test_prolonged_low_confidence_does_not_thrash` test above documents
correct hold behavior during the window; the test below covers the timeout.

```python
def test_confidence_hold_timeout_resends_last_mood_after_30s():
    """
    I2 — Confidence-hold timeout (FakeClock-driven).
    GIVEN host established STRESSED (high-confidence), then enters ~30s of sub-0.7
    WHEN FakeClock advances past ~30s of gated silence
    THEN host re-sends the last computed mood (STRESSED) rather than staying silent.
    Creature must not stay "stuck" forever on a confident wearer.
    """
    transport = FakeTransport()
    clock = FakeClock(start=0.0)
    call_count = [0]

    def confidence_scenario(frame):
        call_count[0] += 1
        if call_count[0] == 1:
            return {"mood": "stressed", "intensity": 80, "confidence": 82}
        return {"mood": "stressed", "intensity": 78, "confidence": 65}  # sub-0.7

    frames = [SensorFrame(audio_rms=0.8, audio_pitch_variance=0.9,
                          imu_accel=0.7, imu_rot=0.5)]
    frames += [SensorFrame(audio_rms=0.35, audio_pitch_variance=0.35,
                           imu_accel=0.34, imu_rot=0.33)] * 35
    sensor_source = FakeSensorSource(frames=frames)
    app = FamiliarApp(transport=transport, sensor_source=sensor_source,
                      clock=clock, inference_fn=confidence_scenario)

    app.run_cycle()                        # establishes STRESSED confidence=82
    initial_count = transport.packet_count()
    assert initial_count == 1

    for _ in range(29):                    # 29s of sub-0.7 — still held
        clock.advance(1.0)
        app.run_cycle()
    assert transport.packet_count() == initial_count  # no re-send yet

    clock.advance(1.1)                     # cross the ~30s threshold
    app.run_cycle()
    assert transport.packet_count() > initial_count   # last mood re-sent
    last = transport.last_packet()
    assert last[1] == 2                    # mood_enum STRESSED — not wiped to NEUTRAL
```

### 6.5 Interpolation Timing

**Failure mode:** Device receives two `STRESSED` updates 50ms apart, then a
`CALM` update. The 200-500ms interpolation is mid-flight when the CALM
arrives. Does the creature snap or blend correctly?

**Deterministic FakeClock-driven test (I11):** The ARD specifies 200-500ms
interpolation. This test uses the `StateMachine` seam with an injectable clock
to assert concrete intermediate values — not just "no snap" but exact frame
counts and progress ratios.

```lua
-- tests/lua/test_state_machine.lua (busted) — I11 interpolation timing
describe("mood interpolation timing", function()

  it("200ms budget: intensity reaches target within 2 ticks at 10Hz", function()
    -- ARD §5.1: interpolation completes in 200–500ms.
    -- StateMachine is driven at 10Hz (100ms/tick).
    -- After 2 ticks (200ms) intensity must be >= 90% of target.
    local clock = FakeClock.new(0.0)
    local sm = StateMachine.new_with_clock(clock)
    sm:receive({mood=0, intensity=50, confidence=80, seq=1})   -- NEUTRAL baseline

    sm:receive({mood=2, intensity=100, confidence=85, seq=2})  -- STRESSED target
    clock:advance(0.1)  -- tick 1 (100ms)
    sm:tick()
    local progress_1 = sm:current_intensity()
    assert.is_true(progress_1 > 50,
      string.format("after 100ms intensity should rise from 50; got %d", progress_1))

    clock:advance(0.1)  -- tick 2 (200ms total)
    sm:tick()
    local progress_2 = sm:current_intensity()
    assert.is_true(progress_2 >= 90,
      string.format("after 200ms intensity must be >=90/100; got %d", progress_2))
  end)

  it("500ms budget: full transition complete within 5 ticks at 10Hz", function()
    local clock = FakeClock.new(0.0)
    local sm = StateMachine.new_with_clock(clock)
    sm:receive({mood=2, intensity=100, confidence=85, seq=1})  -- STRESSED
    sm:receive({mood=1, intensity=20, confidence=82, seq=2})   -- CALM target

    for _ = 1, 5 do
      clock:advance(0.1)
      sm:tick()
    end
    -- After 500ms, interpolation must be complete (at or very near target)
    assert.is_true(sm:current_intensity() <= 25,
      string.format("after 500ms should be near CALM intensity=20; got %d",
        sm:current_intensity()))
    assert.equals("calm", sm:current_mood())
  end)

  it("rapid update mid-interpolation blends, does not snap", function()
    -- Two STRESSED updates 50ms apart, then CALM at 100ms.
    -- At 200ms, creature must not show a hard snap to CALM.
    local clock = FakeClock.new(0.0)
    local sm = StateMachine.new_with_clock(clock)
    sm:receive({mood=2, intensity=85, confidence=85, seq=1})   -- STRESSED t=0
    clock:advance(0.05)
    sm:tick()
    sm:receive({mood=2, intensity=85, confidence=85, seq=2})   -- STRESSED t=50ms
    clock:advance(0.05)
    sm:tick()
    local before_calm_intensity = sm:current_intensity()
    sm:receive({mood=1, intensity=20, confidence=82, seq=3})   -- CALM t=100ms
    clock:advance(0.1)
    sm:tick()
    local after_calm_intensity = sm:current_intensity()
    -- Must blend, not snap: intensity may not drop by more than 50% in one tick
    local delta = before_calm_intensity - after_calm_intensity
    assert.is_true(delta < before_calm_intensity * 0.5,
      string.format("snap detected: intensity dropped %d in one tick (from %d to %d)",
        delta, before_calm_intensity, after_calm_intensity))
  end)

end)
```

### 6.6 Sequence Number Ordering / Dedup

**Spec (resolved — see ARD §5.2 and `.squad/decisions/decisions.md` "2026-06-08: VESPER BLE Wire-Format Specification"):**
- uint16, wraps 0xFFFF → 0x0000.
- Dedup rule: `delta = (received_seq - last_accepted_seq) mod 65536`, interpret
  as **signed 16-bit**.
  - delta 0 → duplicate, drop silently.
  - delta 1..32767 → newer (accept); this is wraparound-safe.
  - delta 32768..65535 (signed negative) → stale/out-of-order, drop silently.
- **Do NOT use** `received_seq > last_accepted_seq` — breaks at wraparound.

**Protocol unit tests (`familiar_protocol.py` / `test_protocol.py` — classicist):**

```python
def test_decode_familiar_ack_little_endian():
    """FAMILIAR_ACK: opcode 0x02, last_received_seq uint16 LE."""
    raw = bytes([0x02, 0x0A, 0x00])   # seq = 10 in little-endian
    opcode, seq = decode_familiar_ack(raw)
    assert opcode == 0x02
    assert seq == 10

def test_familiar_reset_notification_no_payload():
    """FAMILIAR_RESET (Device→Host): opcode 0x01, 1 byte total."""
    raw = bytes([0x01])
    opcode = decode_familiar_reset(raw)
    assert opcode == 0x01
    assert len(raw) == 1
```

**Device-side dedup tests (`state_machine.lua` — busted, authoritative):**

```lua
describe("sequence dedup (wraparound-aware)", function()

  it("accepts a fresh packet (delta = 1)", function()
    local sm = StateMachine.new()
    sm:receive({mood=2, intensity=85, confidence=82, seq=1})
    assert.equals("stressed", sm:current_mood())
  end)

  it("drops a duplicate packet (delta = 0)", function()
    local sm = StateMachine.new()
    sm:receive({mood=2, intensity=85, confidence=82, seq=1})
    local before = sm:transition_count()
    sm:receive({mood=1, intensity=50, confidence=80, seq=1})  -- dup
    assert.equals(before, sm:transition_count())
  end)

  it("drops a stale/out-of-order packet (delta >= 32768)", function()
    local sm = StateMachine.new()
    sm:receive({mood=2, intensity=85, confidence=82, seq=5})
    sm:receive({mood=1, intensity=50, confidence=80, seq=4})  -- stale: delta = (4-5) mod 65536 = 65535
    assert.equals("stressed", sm:current_mood())
  end)

  it("accepts packet after wraparound (0xFFFF → 0x0000)", function()
    -- Reconnect reset: device last_accepted_seq = 0xFFFF, host sends seq=0x0000
    -- delta = (0x0000 - 0xFFFF) mod 65536 = 1  → should ACCEPT
    local sm = StateMachine.new_with_last_seq(0xFFFF)
    sm:receive({mood=1, intensity=60, confidence=80, seq=0x0000})
    assert.equals("calm", sm:current_mood())
  end)

  it("rejects stale packet one step below last_seq near wraparound boundary", function()
    -- last_accepted_seq = 0x0001, incoming seq = 0xFFFF
    -- delta = (0xFFFF - 0x0001) mod 65536 = 65534 (signed: -2) → stale
    local sm = StateMachine.new_with_last_seq(0x0001)
    sm:receive({mood=3, intensity=90, confidence=85, seq=0xFFFF})
    assert.equals("neutral", sm:current_mood())  -- state unchanged
  end)

end)
```

**FAMILIAR_ACK cadence tests (emulator / integration tier):**

```python
@pytest.mark.integration
def test_familiar_ack_sent_every_10_accepted_packets():
    """Device sends FAMILIAR_ACK automatically after every 10 accepted updates."""
    emulator = HaloEmulator()
    emulator.load_lua("device/main.lua")
    received_acks = []
    emulator.on_message(0x02, lambda data: received_acks.append(data))

    for i in range(10):
        emulator.send_message(encode_familiar_update(Mood.CALM, 50, 80, seq=i+1))

    emulator.tick(frames=5)
    assert len(received_acks) >= 1  # ACK within 10 accepted (allow 12 for jitter per spec)

    ack_seq = struct.unpack("<H", received_acks[-1][1:3])[0]
    assert ack_seq == 10  # last_received_seq

@pytest.mark.integration
def test_familiar_ack_not_sent_for_dropped_packets():
    """Dropped (duplicate/stale) packets must NOT trigger an ACK."""
    emulator = HaloEmulator()
    emulator.load_lua("device/main.lua")
    received_acks = []
    emulator.on_message(0x02, lambda data: received_acks.append(data))

    # Send 5 packets, then resend seq=3 (stale)
    for i in range(1, 6):
        emulator.send_message(encode_familiar_update(Mood.CALM, 50, 80, seq=i))
    emulator.send_message(encode_familiar_update(Mood.STRESSED, 80, 82, seq=3))  # stale

    emulator.tick(frames=5)
    # Only 5 accepted updates — no ACK threshold reached yet
    assert len(received_acks) == 0
```

### 6.7 Deterministic Failure Injection (The Golden Rule)

**Every edge case is tested via injected failure, never by hoping for real
hardware failure.** This is what makes edge case tests non-flaky:

| Real flake | Deterministic test equivalent |
|-----------|-------------------------------|
| BLE radio drops randomly | `FakeTransport.fail_after_n = 3` |
| Mic hardware disconnects | `SensorFrame.mic_failure()` injected in frame sequence |
| Device runs out of Lua heap | `emulator.set_heap_usage(0.82)` (if API available) |
| Clock skew on host | `FakeClock.advance(10.5)` |
| Out-of-order BLE packets | Explicit seq injection in Lua state machine tests (busted) |

### 6.8 Animation Jitter — Seeded RNG Seam

ARD §5.6 specifies animation jitter of 5–10% to prevent the creature looking
robotic. Jitter must be **testable without real-time randomness**. Lua's
animation module must accept a seeded RNG so tests can assert on bounds
deterministically (or statistically with a fixed seed).

**Lua seam:**
```lua
-- state_machine.lua: animation_jitter(rng_fn) uses injected rng_fn or math.random
-- Test seam: pass a controlled function returning a fixed sequence
```

**Lua test (busted):**
```lua
describe("animation jitter bounds", function()

  it("jitter stays within 5–10% of base rate per ARD §5.6", function()
    -- Fixed RNG seed → deterministic sequence
    math.randomseed(42)
    local sm = StateMachine.new()
    sm:receive({mood=0, intensity=50, confidence=80, seq=1})

    local jitter_samples = {}
    for i = 1, 100 do
      table.insert(jitter_samples, sm:get_animation_jitter_pct())
      sm:tick()
    end

    for _, j in ipairs(jitter_samples) do
      assert.is_true(j >= 0.05 and j <= 0.10,
        string.format("jitter %f outside 5–10%% range", j))
    end
  end)

end)
```

**Open item:** Whether `state_machine.lua` exposes a seedable RNG seam is
genuinely open (Appendix A #5). If Lua uses `math.random` globally, seed
injection requires wrapping. Track in Appendix A until confirmed.

### 6.9 Privacy: No Raw Biometrics on Wire

The `FAMILIAR_UPDATE` payload is 6 bytes: opcode, mood_enum, intensity,
confidence, seq (uint16 LE). It carries **no raw sensor readings**.

Protocol unit test for this lives in `§4.1` (`test_familiar_update_carries_no_raw_biometric_values`).
The manual RAVEN-T2-1 visual audit confirms the abstraction at the display layer.

### 6.10 No-Network Assertion (M3)

**Invariant:** `FamiliarApp` and the entire host-side pipeline must never open
a network connection. No cloud calls, no telemetry, no `requests`/`urllib`/
`httpx` imports anywhere in `projects/synesthetic-familiar/host/`.

**Phase-1 approach — trust-by-review + lightweight import-graph check:**

```python
# tests/unit/test_no_network.py
import importlib
import sys

def test_familiar_app_import_graph_excludes_network_packages():
    """M3 / Privacy: FamiliarApp must not import any network library.
    No cloud calls, no telemetry. Local heuristic only (ARD §5.3 Decision 2)."""
    network_packages = {"requests", "urllib3", "httpx", "aiohttp", "boto3",
                        "google.cloud", "openai", "anthropic"}
    # Import the host package in a clean slate; check what landed in sys.modules
    import host.main  # noqa: F401
    loaded = set(sys.modules.keys())
    # Full dotted-prefix match: "google.cloud" catches "google.cloud.storage"
    # without over-matching unrelated "google.*" packages.
    leaks = {pkg for pkg in network_packages
             if any(m == pkg or m.startswith(pkg + ".") for m in loaded)}
    assert not leaks, (
        f"Network packages imported by host pipeline (must not exist): {leaks}"
    )
```

If the import-graph check is too brittle for the current project layout, note
it explicitly as **Phase-1 trust-by-review**: `requirements.txt` contains no
cloud-SDK packages (enforced by Raven's Week-1 self-verification checklist).

---

## 7. Lua / On-Device Testing

### Pragmatic Constraint

Lua on the Halo M55 has no interactive test harness. We cannot run `pytest`
against `main.lua`. The approach is three-layered:

### 7.1 Extract Pure State Machine Logic

Create `device/state_machine.lua` containing only:
- State transition table (NEUTRAL ↔ CALM ↔ STRESSED ↔ ATTENTION)
- Interpolation math (linear lerp over 200-500ms)
- Sequence number tracking and wraparound-aware dedup
- Heap-usage threshold checks (80% → reduce complexity; 95% → safe-halt)
- Animation jitter (RNG-seam injectable)

This module has **no** display calls, no BLE calls, no frame rate logic. It
is pure data transformation. Heap logic lives here (device-local), not in
any host-facing module.

### 7.2 Busted Unit Tests for state_machine.lua

`busted` is the **authoritative unit check for Lua logic**. All device-side
state transitions, dedup, interpolation, heap behavior, and quick-reset must
pass `busted` before any emulator or hardware test is considered meaningful.
See §6.6 for the full sequence-dedup test suite and §6.3 for heap tests.

```lua
-- tests/lua/test_state_machine.lua (busted)
describe("state machine", function()
  it("transitions from NEUTRAL to STRESSED on high-tension update", function()
    local sm = StateMachine.new()
    sm:receive({mood=2, intensity=85, confidence=82, seq=1})
    assert.equals("stressed", sm:current_mood())
  end)

  it("device-side confidence gate: optional defense-in-depth only", function()
    -- NOTE: Host is the sole authority for confidence gating (ARD §5.4).
    -- Device-side gating is NOT required behavior — it is optional defense-in-depth.
    -- This test documents the device's optional behavior; it must NOT be used
    -- as the primary confidence gate test (that belongs in host acceptance tests).
    local sm = StateMachine.new()
    sm:receive({mood=2, intensity=85, confidence=65, seq=1})  -- host should never send this
    -- Device may or may not apply a secondary gate; either outcome is acceptable
    -- This test simply confirms no crash and no invalid state
    assert.is_not_nil(sm:current_mood())
  end)

  it("double-tap resets to NEUTRAL locally (device-originated)", function()
    local sm = StateMachine.new()
    sm:receive({mood=2, intensity=85, confidence=82, seq=1})
    assert.equals("stressed", sm:current_mood())
    sm:on_double_tap()                  -- Lua IMU input, no host round-trip
    assert.equals("neutral", sm:current_mood())
    -- After reset, device queues FAMILIAR_RESET notification (opcode 0x01)
    assert.equals(0x01, sm:pending_notification_opcode())
  end)

  -- I1: ATTENTION overlay — on_imu_peak() triggers ATTENTION for <=500ms,
  -- then restores the previous mood (NOT resets to neutral).
  it("on_imu_peak overlays ATTENTION then restores previous mood", function()
    local clock = FakeClock.new(0.0)
    local sm = StateMachine.new_with_clock(clock)
    sm:receive({mood=2, intensity=85, confidence=82, seq=1})
    assert.equals("stressed", sm:current_mood())

    sm:on_imu_peak()                    -- trigger ATTENTION overlay
    assert.equals("attention", sm:current_mood())

    clock:advance(0.3)                  -- 300ms — still within overlay window
    sm:tick()
    assert.equals("attention", sm:current_mood())

    clock:advance(0.21)                 -- cross 500ms total (0.3 + 0.21 = 0.51s)
    sm:tick()
    assert.equals("stressed", sm:current_mood(),  -- restored to STRESSED, not neutral
      "ATTENTION overlay must restore to previous mood, not reset to neutral")
  end)

  it("on_imu_peak overlay restores within 500ms (upper bound)", function()
    local clock = FakeClock.new(0.0)
    local sm = StateMachine.new_with_clock(clock)
    sm:receive({mood=1, intensity=40, confidence=80, seq=1})   -- CALM
    sm:on_imu_peak()
    assert.equals("attention", sm:current_mood())
    clock:advance(0.5)
    sm:tick()
    assert.equals("calm", sm:current_mood(),
      "ATTENTION overlay must restore within 500ms")
  end)

  -- I3: CALM 60s sustain — creature must stay NEUTRAL for a full 60s of calm
  -- signal before transitioning to CALM. ~590 packets (59s) still NEUTRAL;
  -- 600 packets (60s) triggers CALM.
  it("requires 60s sustained calm signal before transitioning to CALM", function()
    local clock = FakeClock.new(0.0)
    local sm = StateMachine.new_with_clock(clock)
    -- Feed 590 calm-signal packets at 10Hz (1 per 100ms) — 59s total
    for i = 1, 590 do
      sm:receive({mood=1, intensity=30, confidence=82, seq=i})
      clock:advance(0.1)
      sm:tick()
    end
    assert.equals("neutral", sm:current_mood(),
      "590 calm packets (59s) must still be NEUTRAL — 60s threshold not reached")

    -- 10 more packets = 60s total — now transition should fire
    for i = 591, 600 do
      sm:receive({mood=1, intensity=30, confidence=82, seq=i})
      clock:advance(0.1)
      sm:tick()
    end
    assert.equals("calm", sm:current_mood(),
      "600 calm packets (60s) must transition to CALM")
  end)
end)
```

### 7.3 Lua Testing Authority — `busted` is the Sole Ground Truth

**`busted` runs real Lua** — it is the ground truth for `state_machine.lua`
behavior. No Python simulation or cross-validation path substitutes for it.
A pure-Python reimplementation that agrees with itself proves the Python model
is self-consistent — it says nothing about whether the Lua production code matches.

**The `lupa` Python→Lua cross-validation path is deferred / out of scope for
Phase-1.** It adds a LuaJIT runtime dependency that is not confirmed available
in CI, and the parametrize fixture table below already covers the boundary
cases that motivated the property-test approach. Revisit in Phase-2 if
property-based fuzz of the Lua state machine becomes necessary.

**Property-test replacement — `@pytest.mark.parametrize` fixture table (~8 rows):**

The `hypothesis` strategy is replaced with an explicit fixture table covering
each threshold boundary and one nominal case per mood state. This is
classicist: pure inputs → expected output, no generators.

```python
# tests/unit/test_inference_parametrize.py

import pytest
from host.inference import compute_mood

@pytest.mark.parametrize("audio_rms,audio_pv,imu_accel,imu_rot,expected_mood,min_conf", [
    # Nominal STRESSED — all signals high
    (0.85, 0.90, 0.75, 0.60, "stressed",  0.80),
    # Threshold boundary STRESSED — just above stress floor
    (0.65, 0.66, 0.61, 0.55, "stressed",  0.70),
    # Nominal CALM — all signals low
    (0.10, 0.08, 0.08, 0.04, "calm",      0.80),
    # Threshold boundary CALM — just below calm ceiling
    (0.25, 0.22, 0.20, 0.15, "calm",      0.70),
    # Nominal NEUTRAL — mid-band ambiguous
    (0.38, 0.35, 0.36, 0.32, "neutral",   0.00),   # confidence < 0.7 expected
    # Low-confidence mid-band — must not exceed gate
    (0.40, 0.40, 0.40, 0.40, "neutral",   0.00),   # sub-threshold, gate fires
    # IMU-dominant stress (mic low, IMU high)
    (0.20, 0.15, 0.80, 0.70, "stressed",  0.60),   # reduced confidence (IMU-only path)
    # Mic-dominant calm (IMU low, mic low)
    (0.12, 0.10, 0.05, 0.03, "calm",      0.75),
], ids=[
    "stressed-nominal", "stressed-boundary",
    "calm-nominal", "calm-boundary",
    "neutral-nominal", "neutral-low-conf",
    "imu-dominant-stressed", "mic-dominant-calm",
])
def test_compute_mood_boundary_table(audio_rms, audio_pv, imu_accel, imu_rot,
                                      expected_mood, min_conf):
    result = compute_mood(
        audio_rms=audio_rms, audio_pitch_variance=audio_pv,
        imu_acceleration=imu_accel, imu_rotation=imu_rot,
    )
    assert result["mood"] == expected_mood, (
        f"Expected mood={expected_mood!r}, got {result['mood']!r} "
        f"(inputs: rms={audio_rms}, pv={audio_pv}, accel={imu_accel}, rot={imu_rot})"
    )
    if min_conf > 0:
        assert result["confidence"] >= min_conf, (
            f"Expected confidence>={min_conf}, got {result['confidence']}"
        )
```

### 7.3a (Deferred) Python Simulation — Out of Scope Phase-1

A Python `LuaStateMachineSim` was previously discussed as a behavioral oracle.
This path is **deferred**: a Python-only simulation that agrees with itself
validates the Python model's internal consistency — not the production Lua.
If Phase-2 introduces fuzz testing of `state_machine.lua`, drive it through
a real Lua interpreter (`busted` with generated fixture files or `subprocess`
invoking `lua state_machine_fuzz.lua`) — never via a Python clone.

### 7.4 Emulator Integration Tests (halo-emulator)

The `halo-emulator` loads `main.lua` directly and exposes a framebuffer API.
Integration tests at this tier:

```python
# tests/integration/test_lua_render.py

def test_neutral_sprite_at_7_oclock_position():
    """Sprite must be at 80% radius, 7-o'clock position on 256×256 canvas."""
    emulator = HaloEmulator()
    emulator.load_lua("device/main.lua")
    emulator.send_message(encode_familiar_update(Mood.NEUTRAL, 50, 80, seq=1))
    emulator.tick(frames=30)

    fb = emulator.get_framebuffer()
    assert lit_pixel_percentage(fb) < 5.0       # under 5% idle budget
    assert sprite_center_in_region(fb, region="7_oclock_rim")

def test_stressed_sprite_has_warm_color_pixels():
    """Stressed state should have amber/orange palette pixels, not blue/teal."""
    emulator = HaloEmulator()
    emulator.load_lua("device/main.lua")
    emulator.send_message(encode_familiar_update(Mood.STRESSED, 85, 82, seq=1))
    emulator.tick(frames=30)

    fb = emulator.get_framebuffer()
    warm_count = count_warm_pixels(fb)   # R > G, R > B threshold
    cool_count = count_cool_pixels(fb)   # B > R, B > G threshold
    assert warm_count > cool_count
```

### 7.5 What Must Be Verified Manually Per Milestone

| Milestone | Manual Check | Success Criterion |
|-----------|-------------|-------------------|
| Week 1 — "It moves" | Aaron sees creature bobbing on real Halo | Smooth bob at ~0.25Hz; jitter present but subtle; BLE log shows clean packets |
| Week 2 — "It reacts" | Aaron raises voice → creature stress response | STRESSED visual within 500ms; warm color shift visible; returns to NEUTRAL within 60s of settling |
| Week 3 — "It's alive" | 1-hour wear session + gesture test | No OOM or BLE freeze; double-tap locally snaps NEUTRAL on device; host sees FAMILIAR_RESET notification; creature feels "alive not robotic" |
| Week 3 — Privacy audit | Non-wearer observes creature for 5 min | Cannot infer stress/calm state from visual alone; no labeled text visible |

#### M5 — Week-1 Programmatic Acceptance Gate

Before merging the Week-1 "It moves" sprint, the following **automated gate**
must be green in addition to the manual check above. It uses the emulator
(busted or pytest integration tier) and confirms the render loop + BLE protocol
work end-to-end without hardware.

```python
# tests/integration/test_week1_acceptance_gate.py
# M5 — Week-1 gate: emulator renders bobbing sprite from mock FAMILIAR_UPDATE packets.
# Must pass before Week-1 branch merges (in addition to manual device check).

@pytest.mark.integration
def test_week1_emulator_sprite_bobs_from_mock_packets():
    """
    M5 Week-1 gate: drive N mock FAMILIAR_UPDATE packets into the emulator.
    Assert: (1) lit pixels visible (sprite rendered), (2) pixel centroid is in
    the 7-o'clock region, (3) BLE receive log shows no errors or malformed packets.
    """
    emulator = HaloEmulator()
    emulator.load_lua("device/main.lua")
    ble_errors = []
    emulator.on_ble_error(lambda e: ble_errors.append(e))

    # Send 10 NEUTRAL packets (1 second at 10Hz) — enough for at least one bob cycle
    for seq in range(1, 11):
        emulator.send_message(encode_familiar_update(Mood.NEUTRAL, 50, 80, seq=seq))
        emulator.tick(frames=3)           # ~3 render frames per packet at 30fps

    fb = emulator.get_framebuffer()
    assert lit_pixel_percentage(fb) > 0.5,   "Sprite must be visible (>0.5% lit pixels)"
    assert sprite_center_in_region(fb, region="7_oclock_rim"), \
        "Sprite center must be in 7-o'clock rim region"
    assert ble_errors == [], f"BLE log must be clean; got errors: {ble_errors}"
```

```lua
-- tests/lua/test_week1_gate.lua (busted alternative — runs without Python emulator)
-- M5 Week-1 gate: state machine processes NEUTRAL packets without error.
describe("Week-1 acceptance gate", function()
  it("processes 10 mock FAMILIAR_UPDATE packets cleanly", function()
    local sm = StateMachine.new()
    for seq = 1, 10 do
      sm:receive({mood=0, intensity=50, confidence=80, seq=seq})
      sm:tick()
    end
    assert.equals("neutral", sm:current_mood())
    assert.is_nil(sm:last_error(), "State machine must process packets without error")
  end)
end)
```

### 7.6 What Can ONLY Be Verified on Real Hardware

The following behaviors cannot be validated by emulator, busted, or host-side
tests. They are hardware-only, manual-only, and must be executed per milestone:

| Behavior | Why emulator/busted cannot cover it |
|----------|-------------------------------------|
| Real BLE flake / drop recovery | Emulator uses loopback; real radio has real packet loss |
| True IMU tap detection under motion | Emulator can inject tap events; real device tap threshold varies with orientation and motion |
| Camera JPEG output | Emulator mocks camera; real JPEG quality/timing is hardware-specific |
| Firmware upgrade survival | Cannot emulate partial firmware flash |
| Actual device pairing window | Emulator doesn't have pairing mode with real timeout |
| Animation smoothness (human perception) | Framebuffer pixel counts don't capture perceived smoothness |
| Privacy audit (bystander perception) | No automated test can judge "looks abstract enough" |

---

## 8. Tooling & CI

### Host-Side (Python)

| Tool | Purpose |
|------|---------|
| `pytest` | Test runner for all Python tiers |
| `pytest-mock` / `unittest.mock` | Mock collaborators in unit tests |
| `pytest-cov` | Coverage measurement |
| `pytest -m "unit"` | Fast unit suite (< 5s) |
| `pytest -m "acceptance"` | Acceptance suite (< 30s) |
| `pytest -m "integration"` | Integration suite (requires emulator, ~2min) |

**Test markers in `pyproject.toml`:**
```toml
[tool.pytest.ini_options]
markers = [
    "unit: fast, isolated, no hardware",
    "acceptance: outside-in, fake transport + sensors",
    "integration: requires halo-emulator",
    "device: requires real Halo hardware — NOT in CI",
]
```

**Coverage targets:**
- `inference.py`: 95% line coverage (pure heuristic logic)
- `familiar_protocol.py`: 95% line coverage (wire format is safety-critical; 95% enforced as CI gate)
- `sensors.py`: 85% line coverage (hardware paths are integration-tested)
- `main.py`: 80% line coverage (orchestration; harder to cover all reconnect paths)
- No global coverage gate in CI — selective 95% enforced on `familiar_protocol.py` only (see CI pipeline below)

### Lua / On-Device

| Tool | Purpose |
|------|---------|
| `busted` | Lua unit test framework for `state_machine.lua` |
| `halo-emulator` | Load + run `main.lua` in Python test process |
| Manual session | Real device per milestone |

### CI Pipeline

```
on: push, pull_request

jobs:
  fast:                     # Every commit, ~30s
    - pytest -m "unit"
    - pytest -m "acceptance"
    - busted tests/lua/

  slow:                     # PR merge gate, ~3min
    - pytest -m "integration"   # requires halo-emulator
    - pytest --cov --cov-report=term-missing
    - pytest --cov=host/familiar_protocol --cov-fail-under=95 tests/test_protocol.py  # selective gate: wire format only

  device:                   # Manual trigger only
    # pytest -m "device"    # NOT in automated CI
    # Requires physical Halo hardware
```

### Run Unit Tests Before Device Tests (Discipline)

Per my prior learning (history.md): unit tests take seconds; device tests
take minutes (and require hardware). The rule:

> **Never run a device test before the unit + acceptance suite is green.**

If `pytest -m "unit acceptance"` is failing, a real-device test cannot tell
you more. Unit first always.

---

## 9. Definition of Done Per Story

A story is **Done** when ALL of the following are true. No exceptions.

### Checklist

- [ ] **Red exists and failed first.** A test was written *before* the
      implementation. The test failure message is meaningful — it describes
      the missing behavior, not a missing import or syntax error.

- [ ] **Green is passing.** All tests for this story pass with minimum
      production code. No production code exists that is not covered by a test.

- [ ] **Refactored under green.** After going green, at least one refactoring
      pass was completed: named constants extracted, magic numbers eliminated,
      collaborator interfaces named clearly. Tests remained green throughout.

- [ ] **Edge cases are covered.** The story's failure modes (sensor fail,
      BLE drop, low confidence, out-of-order seq, clock timing) each have a
      test in the appropriate tier. Edge-case tests use injected failures, not
      hope.

- [ ] **Traceability updated.** The story ID is linked to its tests via
      `# STORY: <ID>` comment in the test file or in this document's
      Story → Test Mapping table (Section 5).

- [ ] **No `time.sleep()` in tests.** All timing-dependent tests use
      `FakeClock.advance()`. A `time.sleep()` in a test is a defect.

- [ ] **No real hardware dependency in unit/acceptance tests.** If a
      unit or acceptance test requires a physical Halo device or real BLE
      radio, it is mis-tiered. Move it to integration or device tier.

- [ ] **Milestone manual check passed** (for P0 stories at their milestone
      boundary). Success criteria from ARD §9 confirmed on real hardware.

### Per-Story Minimum Test Count Guidance

| Story Priority | Minimum Tests |
|----------------|---------------|
| P0 | ≥ 1 acceptance + ≥ 2 unit + ≥ 1 edge case |
| P1 | ≥ 1 acceptance or integration + ≥ 1 unit + ≥ 1 edge case |
| P2 | ≥ 1 unit + ≥ 1 edge case |

### P0 Story DoD Reconciliation

The following P0 stories have non-standard DoD application:

| Story | DoD exception | Rationale |
|-------|---------------|-----------|
| RAVEN-T2-1 | Automated protocol assertion (§4.1 biometric test) + manual visual audit | Protocol layer is fully automated; "abstract form" perception requires human judgment |
| DASID-T2-5 | Manual-only (visual privacy audit) | No automated test can judge perceived abstraction — this is an explicit product-validation exception |
| ENZO-T2-1, ENZO-T2-2 | Manual/usability only | Product-validation stories; automated tests cannot measure wearer perception or 500ms felt-latency |

No P0 story that has an automatable correctness assertion is permitted to be
manual-only. RAVEN-T2-1's protocol assertion must be in CI; only the visual
component is manual. ENZO-T2-1/T2-2 and DASID-T2-5 are explicit product-
validation exceptions where the acceptance criterion is inherently human.

---

## Appendix A: ARD Gap Status

### RESOLVED — No Longer Blockers

The following items were open in Rev 1 and are now settled by the ARD amendment
(ARD §§3–5 / §5.2) and the decisions recorded in `.squad/decisions/decisions.md`
("2026-06-06: Aaron Approved Architecture" and "2026-06-08: VESPER BLE Wire-Format Specification"):

| # | Item | Resolution |
|---|------|------------|
| R1 | **Endianness** | LITTLE-ENDIAN for all multi-byte fields. Python `struct '<H'`; Lua `string.pack '<I2'`. All big-endian test fixtures are wrong and must be fixed. |
| R2 | **`FAMILIAR_ACK` trigger + payload** | Device sends ACK automatically every 10 accepted `FAMILIAR_UPDATE` packets (~1 ACK/sec). Payload = `last_received_seq` (uint16 LE). No heap field. No host request opcode. |
| R3 | **Seq wraparound and dedup rule** | Signed-16 delta window: `(received - last) mod 65536`, interpreted as signed. delta 0 = dup (drop), 1–32767 = accept, 32768–65535 = stale (drop). Naive `>` comparison is WRONG. |
| R4 | **`FAMILIAR_RESET` direction, opcode, payload** | Device→Host ONLY. Opcode `0x01`. No payload (1 byte total). No Host→Device reset opcode exists. |
| R5 | **Heap ownership** | Entirely device-local (Lua). Host does NOT participate. Nothing heap-related on the wire. Tests for heap behavior live at Lua/emulator tier only. |
| R6 | **Confidence gating authority** | Host is the SINGLE authority. Device-side gating is optional defense-in-depth, NOT required behavior. |
| R7 | **Quick-reset ownership** | Device-originated. Lua detects double-tap, snaps to NEUTRAL locally (no host round-trip), then notifies host via `FAMILIAR_RESET` (opcode `0x01`). |

### OPEN — Still Blocking or Uncertain

The following items remain genuinely unresolved and require API confirmation
before the corresponding tests can be enabled:

| # | Gap | Impact | Ref |
|---|-----|--------|-----|
| 1 | `frame.system.get_heap_usage()` emulator API existence unconfirmed | Heap exhaustion tests (§6.3) are gated behind `@pytest.mark.skip` / `pending()` | ARD §10 Q3 |
| 2 | `emulator.set_heap_usage()` API availability | Required for integration-tier heap tests; blocked until halo-emulator confirms | halo-emulator SDK |
| 3 | `frame.on_imu_peak(callback)` is polling-only in current SDK | NG-T2-2 attention-moment tests must use polling simulation, not interrupt-style callback | ARD §5.1 |
| 4 | ~~Baseline persistence medium~~ — **RESOLVED:** Host filesystem (`~/.vesper/baseline.json`), locked in ARD §5.4 / ARD §10 Q4. LIBRARIAN-T2-2 persistence tests may proceed against that path. | n/a | ARD §5.4 |
| 5 | Lua animation jitter: whether `state_machine.lua` exposes a seedable RNG seam | Jitter bound tests (§6.8) require injectable RNG; if not supported, `math.randomseed` global must be used | ARD §5.6 |
| 6 | Canonical sprite pixel-buffer format (bit depth, row-major vs column-major, palette encoding) | Framebuffer assertions in §7.4 use assumed format; pixel-count helpers may be wrong | halo-emulator SDK |
| 7 | IMU interrupt primitive — is there a tap-event subscription API or only polling? | Affects how JUANITA-T2-5 quick-reset is tested at integration tier | ARD §5.1, halo-emulator SDK |

These open items do **not** block Phase-1 development. Tests are written with
explicit `@pytest.mark.skip(reason="blocked: <item>")` or Lua `pending()` so
nothing is silently untested when the API is confirmed.

---

*"What happens when the BLE connection drops mid-call?" — I asked first.*
*— Juanita, 2026-06-08*
