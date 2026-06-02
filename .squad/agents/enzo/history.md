# Project Context

- **Owner:** Aaron Kubly
- **Project:** halo — mono-repo playground for authoring apps on Halo smart glasses using the Brilliant SDK
- **Stack:** TBD per package; SDK languages are Python, Flutter (Dart), Web Bluetooth (JS/TS).
- **Created:** 2026-06-01

## Current Session: GitHub Landscape Scan (2026-06-02)

**Task:** Validate Phase-1 roadmap against GitHub ecosystem signal.

**Outcome:** ✅ Phase-1 is strategically sound. No changes needed.

**Key Findings:**
- ~50 active projects (Frame-era, 2023–2025); 0 Halo community projects (device new; AnkiLens emerging at 1 star)
- Dominated by AI/LLM (noa-assistant 197★, frame_realtime_gemini_voicevision 80★, noa-flutter 78★)
- Critical gaps: audio output (0 projects), gesture/IMU (1 dead project), persistence (0 projects), web BLE (1 project)

**Phase-1 Validation:**
| Project | Gap Filled | Halo Differentiation | Confidence |
|---------|-----------|---------------------|----|
| **Workout Coach** | Audio output + IMU (0 projects do this) | Bone-conduction + stereo mics + IMU + always-on | ✅ High |
| **Bird Watcher** | Persistent vision logging | Adds persistence layer (sighting history, summaries) | ✅ High |
| **Time Tracker** | Web BLE examples (only 1 project) | Simplest possible HUD; proves always-on low-power | ✅ High |

**Verdict:** Each Phase-1 project fills a real gap. No direct conflicts. Likely to drive community fork + extend.

**Deliverable:** `.squad/agents/enzo/github-halo-landscape-2026-06-02.md` (full registry, category breakdown, standout repos).

---

## Ideation 2026-06-02

PIE-IN-THE-SKY MOONSHOTS (raw seeds, no constraints, not commitments):
- Social Reflex, Energy Cartography, Skill Atomizer, Local World Model, Multiplayer Personas, Hallucination-as-Content, Episodic Stitching, Agentic Loops

See `.squad/agents/enzo/ideation-2026-06-02.md` for full brainstorm.

4. **Memory Ledger** — Halo records 100% of what you see + hear (passive logging, 12-hour spool, on-device rolling buffer). When you forget where you put your keys, you ask Noa "where were my keys?" and Halo rewinds to that moment, plays audio/visual context, and future searches are instant. No cloud upload; all on-device. Privacy preserved; *your* memory.

5. **Presence Ghost** — Halo broadcasts your "real availability" (not calendar availability) to your team via a tiny always-on overlay widget on their screens (or their Halos). Are you heads-down in flow? They see amber. Distracted/available? Green. In a meeting? Red. No notifications—just always-true signals. Meetings start 5min faster; interruptions drop 80%.

6. **Micro-Habit Accelerator** — You define a habit (drink water, stretch, move position every 30min). Halo detects environmental triggers (water bottle in view, standing position, chair detected) and sends *single-tap* confirmations—no popups, no friction. You build the habit through micro-rewards. Track 90-day streaks via subtle display fireworks. The barrier to habits drops from "willpower" to "tap acknowledgment."

7. **Ambient Wellness Coach** — Halo continuously monitors posture (via camera + IMU), breathing (via bone-conduction audio sensing), and vocal stress (pitch/tone). Before you realize you're stressed, it nudges you with a 3-second grounding exercise via voice (bone-conduction whispers instruction directly to you, not loud). Over a month, anxiety drops measurably; you build new neural pathways without "trying."

8. **Expert Multiplier** — Point Halo at any problem (broken car part, infected plant, coding error on screen) and trigger "Expert Session." Noa connects you live to a human expert (community or paid) who sees *exactly* what you see in real-time, talks you through it step-by-step. First-expert-connection is free, then $0.50/min. Turns anyone into an expert on anything; expert market emerges on day 1.
