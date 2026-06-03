# Halo Ideation Pass 2 — 2026-06-02
**Enzo, Product/PM**

After cross-pollinating with all 8 agents, here's what moved the needle for the roadmap.

---

## 🔥 Resonance — Ideas That Matter Most for the Product Narrative

### **Librarian #1: Persistent Embodied Memory Agents**
This is the Category Killer idea. If Halo can answer "where were my keys?" by rewinding its own vision + audio, we're not building a camera+AI demo—we're building *personal infrastructure*. It reframes Halo from "consume content" to "persistent witness to your life." Every Phase-1 project (Workout Coach, Bird Watcher, Time Tracker) becomes a *training data collection vehicle* for this future capability. This idea locks the narrative thread: every app the community builds feeds the Memory Ledger.

**Implication for roadmap:** Phase-1 projects should include telemetry hooks for future memory querying. Bird Watcher's persistent sighting log is the prototype; Workout Coach's session replays are prototype data. We're building the infrastructure *now*.

### **Da5id #3: Compass Rose Navigation** + **Da5id #6: Radial Time**
These two ideas solve the "glance vs. read" problem for the circular display in a completely different way than we've been thinking. Instead of text/numbers, *position* becomes the information channel. Orientation = direction. Position on the rim = time. This is not UX decoration—this is a new *interaction language* for round displays. The Phase-1 Time Tracker currently plans to show elapsed seconds as text; pivoting to "radial dot position" would be the first real proof that monocular circular design is its own thing, not a "mobile app squished into a circle."

**Implication for roadmap:** Time Tracker should demonstrate radial time, not numeric display. Bird Watcher could show compass bearing to recorded sightings.

### **Raven #3: Selective Blur on Wearer's Terms**
Privacy isn't a legal checkbox—it's a *product advantage*. If Halo can let users pre-register faces/addresses to blur, the device becomes a tool for protecting *others* from their own gaze, not just hiding from Big Brother. This flips the entire privacy-narrative. Combined with Raven's other ideas (ephemeral mode, social signals), Halo becomes the *privacy-forward* wearable in a sea of surveillance devices. 

**Implication for roadmap:** Our Phase-1 projects should visibly *show* privacy controls (recording indicators, blur overlays). Bird Watcher especially—if users can blur faces before logging, it signals "we're thinking about others."

---

## 🔀 Mash-ups — Combinations That Unlock New Directions

### **Enzo #4 × Librarian #1 → Memory Ledger + Persistent Embodied Profile**
Memory Ledger (what you saw + heard + did) + Persistent Embodied Memory Agents (Halo learns *you*) = **Halo as Your Augmented Autobiography**. Over 3 months, your Halo becomes an increasingly accurate model of your attention, habits, pain points, and decisions. Query the device: "Show me moments I was most focused," "When was I happiest?" Halo doesn't just rewind video—it *interprets* your life through your own patterns. Community builds apps that query this graph (mood timeline, serendipity detector, habit correlator). By year 2, Halo's killer feature is "I know you better than you know yourself"—in a privacy-first way.

**Build order:** Phase-1 collects raw data (Bird Watcher logs, Workout sessions). Phase-2 (future) adds interpretation layer.

### **Enzo #6 × YT #3 → Micro-Habit Accelerator + Skeleton Pose Mirror**
Combine micro-habit recognition (environmental trigger detection) with real-time pose inference (mirror your exaggerated movements). Result: **Embodied Habit Affirmation**. You define a habit (stretch every 30min). Halo detects the stretch via camera+IMU, then *celebrates* it by overlaying an exaggerated skeleton copy that bounces around. Micro-reward via visual absurdity, not notifications. Community could build "Gesture Streaks"—daily movement challenges where your skeleton goes on fire if you maintain 90-day consistency.

**Build order:** Skeleton Mirror could launch Phase-2. Connects naturally to Workout Coach (real-time feedback).

### **Librarian #6 × Da5id #1 → Hallucination-as-Content + Breathing Halo**
Render the LLM's uncertainty as *visual breathing*. When Claude/GPT-4o is confident, the breathing ring is steady. When uncertain, it pulses erratically. When hallucinatory (model detects self-contradiction), it hyperventilates. User sees the *intelligence landscape*, not just answers. First-time developer looking at Noa notices: "Oh, the AI is *unsure* about this—I should verify." Privacy-first: you see confidence, not data traces.

**Build order:** Advanced UX feature for Y2. Core for any Halo+LLM app.

### **YT #2 × NG #2 → Real-Time Object Tracking + Live Camera Peek**
Combine on-device computer vision object tracking (centroid + compass bearing) with peek-window (64×64 camera preview in corner). Result: **Spatial Threat Assessment for Workers**. Construction supervisor points Halo at a crane; the app continuously tracks crane position + bearing; peek window shows crane hook; if crane rotates toward the wearer, audio alert. Zero latency to the cloud. Extends beyond safety: warehouse worker tracks inventory shelf position without full capture.

**Build order:** Medium-term engineering challenge. Competitive moat vs. other smart glasses.

---

## ✏️ Amendments to Round-1 Ideation

### **Amendment 1: Memory Ledger Feasibility Cascade**
Round-1 positioned Memory Ledger as futuristic and distant. Librarian's persistent memory agents + NG's on-device tracking + Raven's privacy layer show this is *actually buildable* in phases:
- **Q3 2026:** Raw logging (Bird Watcher sightings, Workout sessions logged to device)
- **Q4 2026:** Local search ("Find workouts where HR > 150")
- **Q1 2027:** Agentic summaries (LLM synthesizes day's workouts into "You did 3 sprints + stretching")
- **Q2 2027:** Pattern detection (Halo learns "you're most focused 9–11am")

**Action:** Update roadmap to explicitly plan for this telescope.

### **Amendment 2: Phase-1 Ordering Still Holds But Time Tracker Needs Redesign**
Original Enzo priority (Workout Coach → Bird Watcher → Time Tracker) is sound. *But* Time Tracker should pivot from "elapsed seconds as text" to Da5id's "Radial Time" (dot position on rim = time). This isn't decoration—it's proof-of-concept for a new interaction language. The app becomes more interesting AND validates the circular HUD philosophy for the entire community.

**Action:** Coordinate with Da5id; update Time Tracker spec.

### **Amendment 3: Expert Multiplier Needs Privacy Rethink**
Enzo's Expert Multiplier (#8) is high-value but Raven's privacy ideas complicate it. If an expert sees exactly what you see, they see your home, your face, others in frame. Add to the Expert Multiplier spec:
- Pre-call blur registration (protect bystanders)
- Privacy mode toggle (expert sees obstacle zones but not faces)
- Ephemeral session recordings (expert sees live; clip auto-deletes after 7 days)

**Action:** Route Expert Multiplier through Raven for privacy audit before scoping.

---

## 🌟 NEW Ideas (Only Visible Now)

### **1. The Halo Remix Studio — Community App Lab**
Lagos's "Halo Remix Kits" is gold, but what if we go deeper? Create a **bi-weekly async community challenge** with a theme and pre-built asset pack. Week 1 (2026-06-08): "Breathing Halo"—Da5id's radial breathing + Librarian's synesthetic AI → build something that *breathes* with emotion. Community forks, builds, shares. Winning entry becomes a playground template. By month 6, we have 26 community-generated app templates, not 5 curated ones. This turns playground into a *creative incubator*, not just a tutorial ground.

**Why now:** Lagos & YT's ideation makes this obvious. Librarian's agentic loops mean community apps can be *smart*, not just pretty. Lagos's contribution culture (Attribution Wall, Lua Poetry Slam) gives us the social infrastructure.

**Roadmap slot:** Launch Y1Q3, run alongside Phase-1 projects.

### **2. Halo as Personal Sensor Array Marketplace**
Hiro's distributed compute mesh + NG's hardware-pushing ideas suggest a new category: **Halo as a Personal IoT Hub**. Wear Halo; nearby devices (other Halos, phones, smart home, wearables) auto-discover. You see a radial widget showing "devices near me"; tap to claim/share. Example: Bird Watcher on Halo #1 + Workout Coach on Halo #2 in the same gym → both wearers can opt-in to "shared activity plane" (leaderboard, form feedback). No cloud broker. Privacy-first P2P. By Y2, a small ecosystem of sensor-sharing apps emerges (shared breathwork, form coaching, location-free social gaming).

**Why now:** Hiro's mesh architecture + NG's BLE beacon ideas make this technically clean. Raven's privacy framework makes it *trustworthy*.

**Roadmap slot:** Spike in Y1Q4; don't block Phase-1, but light the signal for multi-device futures.

### **3. Failure & Chaos as Competitive Advantage**
Juanita's chaos-engineering ideas are typically relegated to QA. But here's the product insight: **Halo's reliability story is its demo story**. Instead of hiding failure modes, document them beautifully. "Here's what happens when BLE drops"—show the visual + audio degradation, explain recovery, celebrate the resilience. Bake failure modes into beginner tutorials ("Your first Halo app will lose packets; here's how"). Make robustness *visible* and *understood*, not invisible and *hoped for*. Community learns to build resilient apps faster because they understand the edge cases.

**Why now:** Juanita's test ideation reveals we're thinking about this more. Brilliant Labs' hardware is new; breakage is expected. Instead of masking it, lean into it as a *feature story*.

**Roadmap slot:** Create "Reliability Playbook" document for playground (Y1Q3). Include Juanita's chaos tests + recovery patterns.

---

## Summary of Mash-ups by Confidence Level

| Mash-up | Lead Agents | Confidence | Roadmap Slot |
|---------|-------------|-----------|--------------|
| Memory Ledger × Persistent Profile | Enzo #4 × Librarian #1 | 🟢 VERY HIGH | Phase-2+ |
| Micro-Habit × Skeleton Mirror | Enzo #6 × YT #3 | 🟢 HIGH | Phase-2 demo |
| Hallucination Breathing | Librarian #6 × Da5id #1 | 🟡 MEDIUM | Advanced UX (Y1Q4) |
| Spatial Tracking × Peek Window | YT #2 × NG #2 | 🟡 MEDIUM-HIGH | Engineering spike (Y1Q4) |
| **TOP PICK:** Remix Studio + Breathing Theme | Lagos vision × Da5id × Librarian | 🟢 VERY HIGH | **Launch Y1Q3** |

---

## Next Steps for Aaron

1. **Approve Time Tracker redesign** (radial time instead of numeric)
2. **Route Expert Multiplier through Raven** for privacy audit
3. **Signal interest in Remix Studio** as concurrent Phase-1 effort (Lagos can own community events; marketing value is high)
4. **Spike on P2P sensor mesh** in parallel track (Hiro + NG for technical validation)
5. **Task Juanita with Reliability Playbook** (package chaos tests as learning material)

All amendments are additive—they don't block Phase-1 (Workout Coach → Bird Watcher → Time Tracker). They *extend* it with narrative coherence and community leverage.

**Confidence in direction:** 🔥 HIGH. The cross-pollination revealed we're not building disparate features—we're building *infrastructure for persistent embodied identity on glass*. Every Phase-1 project feeds that thesis.
