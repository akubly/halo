# Ideation Pass 2: SDK Engine & Hardware Integration
**Date:** 2026-06-02  
**Agent:** Ng (SDK Engineer)  
**Mode:** Cross-pollinated PIE-IN-THE-SKY — stretching hardware + SDK surfaces together  

---

## 🔥 Resonance — Ideas That Excite the Hardware Whisperer

### **Hiro #7 — Embodied Microservices Topology**
Every Halo app as a node on a visible graph; nodes claim/release capabilities; topology rendered as a 3D constellation. This fires SDK instincts hard: the BLE Central-mode mesh becomes *the* distributed compute pattern. I see this as a Lua runtime + SDK feature: each device advertises capability hashes; Lua event loop registers capabilities; BLE scanner discovers peer topology. Framework-level pattern that every app inherits. Multi-device coordination becomes a solved problem at the SDK layer.

### **Librarian #4 — Local World Model + Planning**
On-device lightweight world model (occupancy grid, object permanence, physics priors) for 1–3 second prediction. This is Lua-territory gold. I see a thin Lua library wrapping libmpix frame buffer + IMU sensor fusion; on-device model lives in the Lua VM, not on the host. The camera becomes a first-class sensor in prediction loops. SDK gains a *spatial reasoning primitive*.

### **Juanita #2 — BLE Stutter-Fest**
Deliberately drop every 3rd Bluetooth packet to stress reassembly logic + ACK flow control. This excites me because it reveals gaps in the current SDK's error recovery. Every real-world deployment hits this in the wild (congested 2.4 GHz, interference). A chaos-test harness for the BLE layer becomes table-stakes for the SDK. Validates robustness; uncaps latency budgets.

---

## 🔀 Mash-Ups — Novel Combinations

### **Ng #1 × Da5id #6 = Gyro-Paced Radial Time Display**
Spatial Audio Beamforming (IMU + speaker) meets Radial Time (orbiting dot on rim). Mash-up: the time-dot orbits at variable *speed* based on head-motion intensity (gyro magnitude). Stationary head = slow orbit (30 Hz refresh). Fast head tracking = fast orbit (120 Hz). The *motion* of the clock face becomes an IMU-responsive sensor loop. SDK gain: `frame.imu.gyro_magnitude()` → `frame.display.refresh_rate_sync()`. One SDK call per frame unlocks kinetic time perception on the circular canvas.

### **Ng #3 × Y.T. #7 = Micro-Haptic Feedback via Display Flicker + Gesture Recognition**
Display Flicker Pattern (240–500 Hz micro-vibration) meets Gesture-Based Draw Duel (IMU patterns + button). Mash-up: button press triggers a *silent* haptic buzz (flicker below threshold), but the flicker pattern encodes *which* gesture won the duel (rapid pulse = win, slow pulse = loss, off-beat pulse = tie). User feels the result via imperceptible frame rate changes. SDK gain: `frame.display.haptic_pulse(pattern_code)` + `frame.imu.detect_gesture(duel_context)`. First SDK-level "haptic" API that costs zero mechanical hardware.

### **Ng #2 × Librarian #7 = On-Device Episodic Lua Recorder + Host Stitching**
Real-Time Computer Vision Object Tracking (on-device Lua) meets Episodic Context Stitching (host LLM stitches micro-moments into narrative). Mash-up: Every time Lua completes an object-tracking loop, it emits a *frame event* (object ID, centroid, timestamp, heading). Host app collects these events across 8-hour session, runs LLM at night: "You tracked 47 birds today; here's your birdwatching journey." On-device tracking stays lightweight; host LLM does narrative sense-making. SDK gain: `frame.on_tracking_event(callback)` hook for event emission + metadata packing.

### **Ng #7 × Raven #7 = Privacy-Respecting Adaptive Frame Rate via Face-Gating**
Dynamic Display Refresh Rate (IMU gyro senses motion, adjusts frame rate) meets Automated Face-Gating (refuse to record when others in frame). Mash-up: when face-gating detects *other people* in camera, the SDK *automatically downgrades* display refresh to 30 Hz as a privacy signal (to the wearer's brain + battery). Fewer display updates = less power consumed for surveillance-adjacent states. Wearer subconsciously realizes "others are present; conserve power." SDK gain: `frame.display.privacy_aware_refresh()` — ties camera-privacy to display power budget. Privacy becomes *felt* in hardware behavior.

---

## ✏️ Amendments to My Original Ideas

### **Ng #2 → Enhanced Real-Time Tracking Loop**
Original: "on-device Lua motion detection + centroid tracking → IMU heading sync → display crosshair."

Amendment: Add a *confidence threshold* parameter. Lua emits track events only when centroid confidence > 75%. This prevents noise from false positives cluttering the display. Also: emit `track_lost()` events for brief occlusions (< 500ms), allowing host app to interpolate motion seamlessly. SDK amendment: `frame.on_tracking_event(confidence_threshold=0.75)`.

### **Ng #5 → BLE Mesh with Capability Advertisement**
Original: "On-device Lua runs Bluetooth Central mode scanner; display shows ID, signal strength, battery."

Amendment: Each discovered peer broadcasts a *capability vector* in its BLE advertisement payload (e.g., "can process vision: true, can transcode audio: false"). Lua event loop filters peers by capability, allowing app-level discovery ("find all vision-capable Halos within 30m"). This turns the mesh into a *capability-driven* swarm. SDK amendment: Add `frame.ble.discover_peers_with_capability(capability_string)` + `frame.on_peer_capability_change(callback)`.

### **Ng #8 → Multi-Tap + Head-Pose Composition**
Original: "Button press + simultaneous IMU pattern (shake, roll, nod) recognized in Lua as compound gestures."

Amendment: Head-pose adds *spatial context* to gestures. Example: button press + roll while looking UP-LEFT triggers a different command than roll while looking DOWN. The gesture recognizer gains a *head-attitude dimension*. This unlocks eyes-free 3D command palette (button + IMU pattern + gaze quadrant). SDK amendment: `frame.imu.detect_gesture_with_gaze_context()` — bind gesture recognition to camera-space gaze frame.

---

## 🌟 NEW Ideas — Cross-Pollinated

### **1. SDK-Level Sensor Fusion Pipeline**
Librarian #2 (Synesthetic AI) + Ng #7 (Display Refresh Sync): Build a first-class SDK sensor-fusion primitive that *fuses* camera + audio + IMU into a single `SensorFusionContext` object. The host app calls `frame.sensor_fusion.get_context()` once per frame; it returns a bundle:
```
{
  camera_frame: libmpix_buffer,
  audio_spectral: FFT(mic_raw),
  imu_pose: (pitch, roll, heading),
  confidence_score: float,
  timestamp: uint64
}
```
This decouples sensor *integration* from app logic. Display refresh rate automatically adapts to fusion confidence (high confidence = smooth 120 Hz; low = conservative 30 Hz). SDK gain: one API call replaces 8 ad-hoc sensor polls.

### **2. Lua Event Priority Queue with Backpressure**
Juanita #4 (Button Mash Chaos) + Ng #8 (Gesture Recognition): Currently, Lua event callbacks fire synchronously. Under high button-tap rates, the callback queue overflows. Mash-up: Implement a *priority queue* in the Lua runtime where gesture callbacks are "high priority" (interrupt-like) and meter-reading callbacks are "low priority" (batched). When the queue hits 80% capacity, low-priority events are silently dropped; high-priority events are guaranteed delivery. Host app can query `frame.lua.queue_saturation()` to detect and throttle input.

SDK gain: Apps built on this never crash during chaos input; they *gracefully degrade*. Juanita's chaos tests become acceptance criteria.

### **3. Cross-Device Lua Library Sync Protocol**
Hiro #7 (Embodied Microservices) + Lagos #7 (Fork Lineage Tracker): When multiple Halos are in proximity, they auto-negotiate which device is the "canonical" Lua library publisher. Device A's app uploads `lib_v2.lua`; Device B auto-fetches it, validates hash, and uses it locally without re-uploading. This turns a Halo cluster into a *peer-to-peer library CDN*. Applications built on swarms auto-scale Lua library distribution. 

SDK gain: `frame.ble.sync_lua_libraries_with_peers()` — one call handles cluster-wide consistency. Enables true P2P app deployment.

---

## Summary

**Top mash-up:** Ng #1 × Da5id #6 — Gyro-paced radial time creates the first *kinetic clock interface*, unlocking IMU as a primary display-control sensor. This changes how apps think about head motion: not just for interaction, but for *information density modulation*. Small change; massive SDK pattern unlock.
