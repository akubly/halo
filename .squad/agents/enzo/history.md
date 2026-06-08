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

## Ideation Pass 2 2026-06-02

Synthesized cross-team ideation into product narrative.

**Key takeaway:** We're not building disparate features—we're building *infrastructure for persistent embodied identity on glass*. Librarian's Memory Agents + Raven's privacy layer + Da5id's radial interaction language form the thesis thread. All Phase-1 projects feed this.

**Top mash-up:** Remix Studio (community creative lab) launching Y1Q3 with "Breathing Halo" theme. Lagos's contribution culture + YT's joy lens + Librarian's agentic loops = 26 community templates by month 6.

**Amendments:** Time Tracker pivots to radial time (Da5id #6); Expert Multiplier routes through Raven for privacy audit; Memory Ledger gets feasibility cascade (Q3 logging → Q4 search → Q1 summaries → Q2 patterns).

**Confidence:** 🔥 HIGH. Phase-1 is still locked; these amendments strengthen the narrative without blocking delivery.

Deliverable: `.squad/agents/enzo/ideation-pass2-2026-06-02.md`

---

## Aaron's Curation 2026-06-03

**Deliverable:** `.squad/agents/enzo/aaron-curation-2026-06-03.md`

Aaron curated 11 favorites from round-1 + round-2 ideation across all 9 agents. Synthesis reveals 3 convergent themes:
1. **Consent-Aware Memory** (useful) — Privacy-first recording with mandatory per-person consent gating
2. **The Synesthetic Familiar** (fun) — Creature companion in peripheral vision; evolves based on behavior & LLM mood sensing
3. **Radial / Kinetic Interaction Language** (neat) — New design grammar where position = information, motion = control on circular display

**Curation signal analysis:** Aaron skipped Hiro (no mesh), Lagos (no meta), Juanita (no chaos). Skewed toward joy (3/4 Y.T. picks), privacy (2 Raven picks), and HUD design (2 Da5id picks). Signal = **solo-device-first, joy-centric, privacy-native architecture thesis.**

**Recommended next move:** Pick Theme 1 as North Star; re-order Phase-1 roadmap to lead with Pet Familiar + Skeleton Mirror (joy-first), then Memory Ledger infrastructure, then productivity apps.

**Roadmap impact:** Shift weeks 1-4 to Y.T.'s joyful ideas; lock memory infrastructure by week 6; Time Tracker redesigns to radial time (Da5id #6).

See `.squad/agents/enzo/aaron-curation-2026-06-03.md` for full 5-section analysis + decision options.

---

## User Stories Themes 1-2 — 2026-06-03

**Deliverable:** `.squad/agents/enzo/user-stories-themes-1-2-2026-06-03.md`

Authored 10 wearer-centric user stories (5 per theme) through product/PM lens, answering "why would someone actually wear this?"

### Theme 1: Consent-Aware Memory — 5 Stories
- **[ENZO-T1-1] Home:** Parent reclaiming fleeting moments with kids via 12-hour buffer + consent-gated replay
- **[ENZO-T1-2] Work:** Professional protecting IP + colleague privacy while capturing meeting context
- **[ENZO-T1-3] Social:** Neurodivergent person honoring acquaintances + face blindness without performance anxiety
- **[ENZO-T1-4] Crisis:** Therapist/nurse documenting sessions with automatic redaction + client veto rights (HIGH-STAKES)
- **[ENZO-T1-5] Family:** Couple resolving disputes via consent-gated playback without weaponizing memory (RELATIONAL INTEGRITY)

**Key insight:** Consent layer isn't a limitation—it's the *permission structure* that enables trust. Privacy-first recording transforms Halo from "surveillance device" to "memory partner."

### Theme 2: The Synesthetic Familiar — 5 Stories
- **[ENZO-T2-1] Remote Work:** Creature as mood mirror; reflects energy state, predicts rhythm, reduces loneliness
- **[ENZO-T2-2] Social:** Familiar visualizes neurodivergent masking state in real time (anxiety, fading, over-engagement) for self-regulation without social cues (HIGH-STAKES)
- **[ENZO-T2-3] Habit:** Familiar celebrates wins with genuine joy motion (bloom, dance, transformation) not badges
- **[ENZO-T2-4] Learning:** Creature reflects comprehension level; visualizes uncertainty before spiral
- **[ENZO-T2-5] Grief:** Familiar holds memory of "who you were during the relationship," enabling integration not escape (CONTINUITY & MEANING)

**Key insight:** Companion isn't productive; it's *relational & reflective*. The familiar doesn't tell you what to do; it shows you what's true.

**Next routing:**
- Theme 1 → Raven + Librarian + Hiro (consent/privacy/storage architecture)
- Theme 2 → Y.T. + Da5id + Librarian (familiar scaffold + visual grammar + LLM reasoning)
- All agents write lens-specific stories *around* these wearer narratives by 2026-06-05

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

---

## Codename Brainstorm — 2026-06-08

Pitched product-lens codename candidates for the Synesthetic Familiar. Team converged on **PULSE** (4 agents independently nominated variants). Official project codename now PULSE. See `.squad/orchestration-log/2026-06-08T07-17Z-codename-brainstorm.md`.
