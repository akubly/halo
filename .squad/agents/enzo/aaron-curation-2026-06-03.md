# Aaron's Ideation Curation — 2026-06-03
**Synthesized by:** Uncle Enzo (Product/PM)  
**Date:** 2026-06-03  
**Source:** Round-1 ideation (9 agents) + Round-2 mash-ups + Aaron's verbal curation (via copilot-directive-2026-06-03T0651Z-aaron-favorites.md)

---

## I. Aaron's 11 Favorite Individual Ideas

| # | Idea | Agent | Description |
|---|------|-------|-------------|
| 1 | Skill Atomizer | Enzo #3 | Real-time task decomposition that learns your pace; predicts next move after day 3 |
| 2 | Memory Ledger | Enzo #4 | 12-hour on-device rolling buffer (no cloud); query "where were my keys?" and rewind |
| 3 | Live Camera Peek Window | Ng #4 | Always-on 64×64 corner view of what's off-screen; instant visual context without full handshake |
| 4 | Pet Digital Familiar | Y.T. #1 | Tiny reactive creature in corner vision; responds to motion, evolves behaviors over days |
| 5 | Skeleton Pose Mirror | Y.T. #2 | Exaggerated dancing skeleton mirrors your movement; cartoonish real-time feedback |
| 6 | Forehead Fortune Teller | Y.T. #4 | Tap button → cryptic reading from pixel chaos; hilarious, absurdist oracle |
| 7 | Breathing Halo | Da5id #1 | Ring expands/contracts to pace breathing; peripheral-only, non-intrusive guidance |
| 8 | Orbital Notifications | Da5id #2 | Messages orbit rim like moons; drift to center only on glance-up; peripheral-first UX |
| 9 | Peripheral Sense Augmentation / Synesthetic AI | Librarian #2 | Abstract concepts (emotion, uncertainty) rendered as felt/visual metaphors; LLM-augmented perception |
| 10 | Local World Model + Planning | Librarian #4 | On-device occupancy grid + physics priors; predicts object motion 1–3 seconds ahead |
| 11 | Cryptographic Attention Proofs | Raven #4 | Hash-only proof you "looked at X"; verifiable accountability without storing image data |

---

## II. Aaron's Three Ranked Convergent Themes

### 🥇 Theme 1: Consent-Aware Memory (USEFUL)

**Definition:**  
The glasses become a *privacy-forward recording device* that captures your first-person experience (12-hour rolling buffer, all on-device) but enforces **consent as a first-class design constraint**. Before episodic moments become persistent memory, every person who appears must explicitly consent to storage. Bystanders can revoke consent retroactively; their faces/voices auto-blur. The device shifts from "passive recorder → lawsuit risk" to "collaborative memory engine where privacy is non-negotiable infrastructure."

**Aaron's 11 Favorites That Are Component Parts:**
- **Enzo #2 (Memory Ledger)** — The 12-hour buffer foundation
- **Raven #4 (Cryptographic Attention Proofs)** — Verifiable proof of observation without data leaks
- **Librarian #4 (Local World Model)** — Enables predictive pre-processing before consent gates

**Relevant Pass-2 Mash-ups:**
- **Librarian × Enzo × Raven** — Consent-Gated Memory Ledger (Librarian pass-2): episodic stitching with mandatory per-person consent negotiation
- **Raven #7 × Librarian #1** — Consent-Aware Embodied Memory (Raven pass-2): memory tiers (Public/Private/Ephemeral) with automatic privacy-tier gating
- **Da5id × Raven** — Consent Bloom (pass-2): consent events render as petals blooming from center (visual feedback for consent negotiation)

**Out-of-Scope Tensions to Flag:**
- **On-Device Storage Limits:** 12-hour full video buffer on M55 + 256KB Lua VM is a physical constraint. Persistent storage requires *aggressive* compression or off-device sync—contradicting "privacy-first local" thesis.
- **Bystander Notification Cost:** Real-time consent negotiation (sending encrypted summaries to bystanders, waiting for responses) adds latency. If async, the system feels slow and frustrating.
- **Revocation Asynchrony:** If a bystander revokes consent *after* episodic stitching has processed (12 hours later), redacting their data becomes expensive (LLM re-processing). Version control of memory becomes a nightmare.

---

### 🥈 Theme 2: The Synesthetic Familiar (FUN)

**Definition:**  
Halo becomes a *companion device* where a tiny reactive creature lives in your peripheral vision all day, evolving based on your behavior, emotional state, and habit streaks. The creature is not a UI widget—it's a **synesthetic rendering of your internal state** (stress = faster breathing, focus = calm idle, habit win = celebratory dance). The familiar learns *you* over weeks; interactions become asymptotically more delightful as the device predicts your needs and responds before you ask.

**Aaron's 11 Favorites That Are Component Parts:**
- **Y.T. #1 (Pet Digital Familiar)** — The creature foundation; responsive sprite, state machine
- **Librarian #2 (Synesthetic AI)** — Render abstract concepts (mood, confidence, energy) as visual metaphors
- **Da5id #1 (Breathing Halo)** — Peripheral-vision motion grammar (the ring as companion's heartbeat, not just guidance)
- **Enzo #6 (Micro-Habit Accelerator)** — Environmental trigger detection; familiar celebrates micro-habit wins

**Relevant Pass-2 Mash-ups:**
- **Y.T. × Enzo × Da5id** — Bloom Habit Tracker (Y.T. pass-2): familiar celebrates habit confirmation with visual bloom
- **Da5id × Librarian × Y.T.** — Synesthetic Familiar (Da5id pass-2): creature's form (breathing, fraying, color temp) reflects mood inferred by LLM
- **Y.T. × Lagos × Enzo** — Evolving Companion Remix Kit (Y.T. pass-2): Lua-based creature genome; community forks breeding new variants

**Out-of-Scope Tensions to Flag:**
- **Display Budget Conflict:** A companion occupying corner-vision + breathing ring + notifications orbiting rim = 3 UI surfaces fighting for 256×256 pixels + 30% power budget. Risk of visual congestion or aesthetic collapse.
- **Personality Bloat:** If the familiar "learns you" (Librarian's persistent memory + Y.T. state machine), the creature's behavior becomes unpredictable. After 1 month, only Aaron understands why the creature behaves the way it does—poor UX for newcomers.
- **Affective Computing Liability:** Rendering emotion as creature state implies the device is *sensing* emotion (IMU + audio + camera inference). False positives (misidentifying stress as excitement) erode trust fast. Medical/mental-health liability in some jurisdictions.

---

### 🥉 Theme 3: Radial / Kinetic Interaction Language (NEAT)

**Definition:**  
Smart glasses are **round, monocular, peripheral-vision devices**—not tiny phones. A new *interaction grammar* emerges where **position = information** and **motion = control**. Radial time (dot position on rim = time); compass navigation (bearing rotates with head); depth rings (pulsing inward = approaching). This is not decoration; it's a new *design language* that treats the circular canvas as the primary interaction surface, not a constraint. Apps using this language feel native to the device; apps ignoring it feel ported.

**Aaron's 11 Favorites That Are Component Parts:**
- **Da5id #1 (Breathing Halo)** — Motion on the rim becomes communication channel
- **Da5id #2 (Orbital Notifications)** — Orbital mechanics as information architecture
- **Ng #4 (Live Camera Peek Window)** — Spatial positioning conveys "off-screen context"
- **Enzo #3 (Skill Atomizer)** — Guides real-time task flow; radial progress indicator fits naturally

**Relevant Pass-2 Mash-ups:**
- **Ng × Da5id** — Gyro-Paced Radial Time (Ng pass-2): time-dot orbits at variable speed based on head-motion intensity (IMU gyro)
- **Da5id** — Memory Ledger Scrubber (Da5id pass-2): coiled filmstrip around rim; button taps scrub through timeline
- **Da5id × Y.T. × Ng** — Draw-Duel Eclipse (Da5id pass-2): circular display becomes theatrical arena; eclipse transitions = countdown + outcome

**Out-of-Scope Tensions to Flag:**
- **Circular Display Limitation:** This grammar *only* works on circular displays. If future Halo variants move to rectangular, wide-angle, or multi-display form factors, all this vocabulary breaks. Locks us into circular form factor as permanent commitment.
- **Motion Sickness Risk:** Gyro-paced motion (Ng × Da5id mash-up) means display updates are tied to head rotation speed. Fast head tracking + high refresh could induce vestibular discomfort in some users; accessibility concern.
- **Glance-Budget Saturation:** Breathing ring + orbiting notifications + radial time + peek window = 4 simultaneous radial elements competing for attention. At some point, the elegance collapses into visual chaos. No clear design hierarchy.

---

## III. The Curation Signal — What Aaron's Picks Reveal

**Through the product lens, Aaron's curation pattern tells us:**

### He Skipped Hiro Entirely (No Multi-Device Mesh Thinking)  
**Implication:**  
Halo's thesis is *personal embodied experience*, not *collective reasoning infrastructure*. Multi-device meshes, distributed compute, gaze-driven tracing across wearers—all architecturally interesting but strategically secondary. Aaron's silence on Hiro suggests: *"We're not building a platform for coordinated teams yet. We're building a device that knows YOU, stands alone, and delights in isolation before it delights in crowds."* This is a **solo-device-first prioritization**; multi-wearer features are Y2+, not Y1Q3.

### He Skipped Lagos's Community-Meta Layer  
**Implication:**  
Community governance (townhall voting, fork lineage tracking, attribution walls) are *cultural infrastructure*, not *product*. Aaron's omission suggests: *"We don't lead with community ceremonies. We lead with apps so delightful that community forms *around* them, not by design mandate."* This is a **bottom-up culture bet**, not top-down. Ship the 11 ideas well; the community will emerge organically. Remix kits, Lua poetry slams, and governance rituals are opportunities *after* the core playground lands.

### He Skipped Juanita's Chaos Testing Entirely  
**Implication:**  
Resilience and failure-mode documentation are engineering concerns, not product narratives. Aaron's silence on chaos suggests: *"We're not shipping 'here's how it breaks' stories in Phase 1. We're shipping 'here's what it does' stories."* This is a **confidence bet on MVP fidelity**. Chaos testing informs SDK design (for Hiro + Ng's benefit) but doesn't become a playground demo. Later, when Halo is battle-tested, failure modes become features ("Reliability Playbook," per Enzo pass-2).

### 3 of 4 Y.T. Picks → Joy is Non-Negotiable  
**Implication:**  
Aaron's ideation aesthetic is *playful + weird, not productive + optimized*. Of Y.T.'s 8 joyful ideas, he picked 3 (Pet Familiar, Skeleton Mirror, Fortune Teller). None optimize workflow. All make you smile. This signals: *"Our first playground isn't Workout Coach or Bird Watcher. It's Pet + Skeleton + Fortune—the apps that announce 'Halo is a playground for delight, and you can build that delight.'"* The productivity apps (Workout Coach, Bird Watcher, Time Tracker) become *downstream* validation of infrastructure, not *primary narrative*. **Phase 1 order shifts?**

### 2 of 11 Picks from Da5id → HUD as Primary Design Surface  
**Implication:**  
The display is no longer a "constraint to work around"; it's the *primary design surface*. Da5id's ideas (Breathing Halo, Orbital Notifications) aren't features—they're a **new interaction grammar** that redefines what "glance" means on a wearable. Aaron's picks signal: *"We're not porting iPhone UX to a round screen. We're inventing round-screen UX."* This is a **design-led product strategy**; every app must speak the radial language or it feels foreign.

### Memory + Privacy + On-Device AI All Selected → Architecture Implications  
**Implication:**  
The stack is **local-first, user-centric, edge-aware**. Aaron picked:
- **Memory Ledger** (local recording)
- **Cryptographic Attention Proofs** (privacy-verifiable, not cloud-verifiable)
- **Local World Model** (on-device inference)
- **Synesthetic AI** (LLM rendering, but constrained to HUD metaphors)

This is a signal: *"We don't upstream everything to the cloud. We don't treat the user as data. We build a *personal agent* on the device that reasons *for you*, not about you."* This reframes the mono-repo architecture: the SDK is a **personal AI runtime**, not a "thin client to Brilliant's backend." Implications:
1. **Lua VM is the primary reasoning engine**, not just a display renderer
2. **LLM calls are sparing and purposeful** (not streaming-first)
3. **On-device models** (pose, object tracking, depth) are table-stakes, not luxuries
4. **Privacy policy is hardcoded into the SDK**, not bolted on

---

## IV. Recommended Next Moves

Three options for steering Phase-1 + Phase-2:

### Option A: Pick One Theme, Prototype End-to-End ✅ **(RECOMMENDED)**

**What we'd do:**  
Select **Theme 1 (Consent-Aware Memory)** as the flagship North Star for all Phase-1 projects. Every playground demo (Workout Coach, Bird Watcher, Time Tracker) becomes a *data collection instrument* for future memory queries. Bird Watcher logs sightings + context; Workout Coach logs form + biometrics; Time Tracker logs time-use patterns. Phase-1 ships fully functional apps *and* builds the memory ledger infrastructure in parallel.

**Why this one:**  
- **Highest leverage:** Memory + Privacy + On-device AI are all selected by Aaron; they converge here.
- **Differentiates from Brilliant:** Noa (the current baseline) doesn't do consent-aware memory. This becomes Halo's flagship narrative: *"Your glasses remember *for you*, not *about you*."*
- **Unblocks downstream:** Once memory infrastructure is live (even in MVP form), Theme 2 (Synesthetic Familiar) becomes a trivial extension (familiar reacts to memory data). Theme 3 (Radial Language) becomes the UX layer on top.
- **Community hook:** "Build apps that feed the memory ledger" becomes the developer pitch. Forks naturally extend the query language.

**Rationale:**  
Consent-Aware Memory is the **deepest bet on privacy as competitive advantage**. It requires changes across the SDK (Raven's consent layer), the data model (Librarian's episodic stitching), and the hardware (on-device LLM reasoning + storage). By leading with this, we force the entire architecture to be privacy-first from day 1. Easier to relax privacy later than to bolt it on retroactively.

---

### Option B: Sketch All Three Themes in Parallel

**What we'd do:**  
Staff three independent workstreams:
1. **Theme 1 (Consent-Aware Memory)** — Enzo + Raven + Librarian own memory ledger architecture
2. **Theme 2 (Synesthetic Familiar)** — Y.T. + Da5id + Librarian own familiar creature + visual grammar
3. **Theme 3 (Radial Language)** — Da5id + Ng + Y.T. own interaction vocabulary + ecosystem

Each workstream delivers a prototype by 2026-06-22. Roadmap decisions defer until we see which themes resonate with early testers + community feedback.

**Why this approach:**  
- **Risk hedging:** If consent-aware memory hits architectural blocker, we have backup themes to ship.
- **Parallel learning:** Testing all three simultaneously reveals design conflicts (e.g., familiar + notifications competing for rim real estate).
- **Team autonomy:** Each agent leads their domain without blocking others.

**Risk:**  
- **Diffusion:** Three parallel efforts = context fragmentation. Easy to lose coherence and ship three half-baked demos instead of one laser-focused narrative.
- **Integration hell:** Merging three prototypes into a unified Phase-1 is messy if they weren't designed to compose.

---

### Option C: Spike the Riskiest Assumption First

**What we'd do:**  
Identify the highest-risk technical assumption across all three themes and timebox a 3–5 day research spike:

**The spike:** *"Can we implement consent-aware memory with <10% battery overhead on 12-hour spool?"*

This spike would:
1. Prototype on-device episodic stitching (Librarian #1) with Lua VM
2. Measure memory footprint + CPU cost for consent negotiation (Raven #6)
3. Validate whether 12-hour buffer is physically feasible without cloud offload

**Why this spike first:**  
If the battery math breaks, Theme 1 collapses. Knowing this in week 1 (vs. week 4) saves a lot of wasted effort.

**Who owns the spike:**  
Hiro (architect) + Librarian (AI/ML) + Ng (SDK engineer) team up for 5 days.

---

### **My Recommendation: Option A**

**Rationale:**  
Aaron's curation is *not* three equally weighted bets. He picked 11 ideas that strongly cluster around **privacy-first local reasoning**. Consent-Aware Memory is the convergence point. Pursuing Theme 1 first doesn't preclude Themes 2 + 3; it *enables* them. A memory-aware system naturally supports a familiar that learns from memory; a privacy-forward system naturally uses radial HUD patterns to signal consent states.

**Action:**  
1. **Week 1:** Lock Theme 1 as the Phase-1 North Star
2. **Week 2:** Decompose Memory Ledger into GitHub issues (Raven + Librarian + Hiro)
3. **Week 3–4:** Ship Workout Coach + Bird Watcher with memory telemetry hooks
4. **Week 5+:** Phase-2 designs leverage memory as the foundation layer

---

## V. Roadmap Status — Aaron's Curation Impact

### Original Phase-1 Roadmap (Per decisions.md)
1. **Workout Coach** (3–5 days) — Real-time form feedback via audio + IMU
2. **Bird Watcher** (1–2 days) — Vision pipeline + sighting log
3. **Time Tracker** (2–3 days) — Web Bluetooth + HUD overlay

### Updated Phase-1 Roadmap (Post-Aaron-Curation)

**Recommended Re-Prioritization:**

1. **Reorder for joy-first narrative:**
   - **Week 1-2:** Pet Digital Familiar (Y.T. #1) — simplest to ship, highest "wow" factor on first wear
   - **Week 3-4:** Skeleton Pose Mirror (Y.T. #2) — builds on familiar scaffolding; real-time camera loop
   - **Week 5-6:** Memory Ledger Infrastructure (Theme 1 foundation) — all three playgrounds feed this
   - **Week 7-8:** Workout Coach (Enzo #3 + Enzo #6 hybrid) — form coaching + micro-habit confirmation
   - **Week 9-10:** Bird Watcher (Theme 1 + Librarian #4) — sighting memory + world model predictions
   - **Week 11-12:** Time Tracker (Theme 3 + Da5id redesign) — radial time instead of numeric display

**Rationale for Reorder:**
- **Aaron picked 3/4 Y.T. ideas.** Leading with Pet + Skeleton signals "we're building delight, not optimization."
- **Memory Ledger infrastructure must go in early** (week 5-6) so subsequent apps can hook into it.
- **Radial Time Tracker is a design validation** for the interaction grammar (Theme 3); ship it late to benefit from Da5id's learnings.

**Hold/Replace?**
- **Hold:** Workout Coach remains core (proves audio I/O + IMU + microphone architecture). Shift to week 7 (after joy demos).
- **Hold:** Bird Watcher remains core (validates camera pipeline + persistence). Shift to week 9 (after memory infrastructure).
- **Hold:** Time Tracker remains core (proves always-on low-power HUD). Redesign to radial instead of numeric.
- **Add:** Pet Familiar + Skeleton Pose Mirror (Y.T.'s ideas) become playgrounds #1 and #2. Non-negotiable.

**Upstream Impact:**
- **Enzo's roadmap** now reads: **Joy First, Then Utility, Then Infrastructure**
  - Games + Delightful companions
  - Productivity + Learning foundations (memory + world model)
  - Serious apps + Community leverage (marketplace, governance)
- **Da5id's HUD grammar** is the *design constraint* for all 6 playgrounds, not an afterthought
- **Raven's consent layer** is built into Memory Ledger, shipped by week 6 (enables future expansions)

---

## Phase-1 Scope Confirmation

| Project | Phase | Duration | Aaron Stance |
|---------|-------|----------|--------------|
| Pet Digital Familiar | 1 | Week 1-2 | ✅ Picked (Y.T. #1) — Lead with joy |
| Skeleton Pose Mirror | 1 | Week 3-4 | ✅ Picked (Y.T. #2) — Validate joy scaffolding |
| Memory Ledger Infrastructure | 1 | Week 5-6 | ✅ Implicit (Enzo #2 + Raven #4 + Librarian #1) — Foundation for all future apps |
| Workout Coach | 1 | Week 7-8 | ✅ Holdover with Enzo #3 + #6 amendments — Skill atomizer + habit confirmation |
| Bird Watcher | 1 | Week 9-10 | ✅ Holdover with memory hooks — Add episodic sighting storage |
| Time Tracker | 1 | Week 11-12 | ✅ Redesigned as radial time (Da5id #6) — Interaction grammar validation |

**Verdict:** All Phase-1 projects survive. Reordered. All support the three convergent themes.

---

## Next Steps for Aaron

1. **Approve Theme 1 as North Star** → All Phase-1 planning flows from this decision
2. **Signal on joy-first reordering** → Pet + Skeleton shipped before productivity apps?
3. **Route Theme 2 (Synesthetic Familiar) to Y.T. + Da5id** for parallel Phase-2 prep
4. **Route Theme 3 (Radial Grammar) validation to Da5id + Ng** for Time Tracker redesign (week 11)
5. **Spike decision:** Run the memory-battery spike (Option C) in parallel to de-risk Theme 1

**Confidence:** 🔥 **HIGH**. Aaron's curation is coherent, ambitious, and actionable. The 11 picks form a constellation, not a laundry list.
