# Host-App User Stories: Themes 1 & 2
**Date:** 2026-06-03  
**Author:** Y.T. (App Developer)  
**Scope:** Host-app UX stories (phone/laptop/browser side) for both Aaron-curated themes

---

## Theme 1: Consent-Aware Memory

### [YT-T1-1] First-Time Pairing with Consent Ledger Setup

**As a** first-time user setting up the Halo demo,  
**I want** to pair my Halo and configure which people/places I'm willing to record,  
**so that** my memory ledger respects everyone's privacy before I start using it.

- **Acceptance Criteria:**
  - Pairing flow prompts "Who is in your trusted circle?" (family, close friends) → add faces via phone camera
  - Setup screen shows toggle for "Auto-blur strangers" (on by default)
  - Consent ledger mode selector: "Rolling buffer only" (ephemeral) vs. "Persistent storage" (requires consent collection)
  - User can test the ledger with a mock recording to see blur preview
  - Setup completes in <2 minutes; user sees a "you're ready" confirmation screen

- **App-shape note:** Mobile screen (Flutter) with face collection via phone camera, consent mode toggles, and a preview/test panel showing what blur will look like in real recording.

---

### [YT-T1-2] Recording a Group Moment with Live Consent Requests

**As a** wearer in a group setting,  
**I want** to tap record on my phone and have nearby people receive consent requests on their own devices,  
**so that** I can capture shared moments only if everyone agrees.

- **Acceptance Criteria:**
  - Phone app shows "Start recording" button; tapping triggers BLE broadcast to nearby phones (Halo pairing network)
  - Bystanders see a notification: "Alice is recording. Consent for 30 seconds?" with "Allow" / "Deny" / "Blur me" buttons
  - Real-time consent status shown on wearer's phone: green checkmark for each consent, red X for denials
  - Denied bystanders are auto-blurred in the final recording; names replaced with "Friend" or silhouettes
  - Recording can proceed with partial consent (some people say no, others yes)

- **App-shape note:** Mobile (Flutter) host app displays live consent ticker during recording; bystanders receive push notifications on paired Halo host phones (same app). Web version uses localStorage + QR-code-based consent bridge for non-Halo users.

---

### [YT-T1-3] Reviewing Episodic Memory Summary Without Raw Footage

**As a** wearer reviewing my day,  
**I want** to see a narrative summary of recorded moments (e.g., "Coffee with Jordan at 10 AM, then got stuck in traffic") without viewing raw video,  
**so that** I can understand what Halo captured while respecting that bystanders haven't consented to the raw footage.

- **Acceptance Criteria:**
  - App displays timeline of moments as text summaries + emoji mood tags (☕ 😊 for coffee moment, 🚗 😤 for traffic)
  - Tapping a moment shows: "You were with Jordan (consent ✓), location blurred (denied), audio not stored"
  - If a bystander hasn't consented yet, moment shows "Pending approval from 1 person" with time remaining
  - User can manually approve storage for specific moments (e.g., save coffee photo but delete traffic footage)
  - Archive view shows cleared moments; deletion is permanent and logged

- **App-shape note:** Web dashboard (React) displaying chronological summaries with consent status badges. Mobile companion view shows abbreviated timeline + one-tap archive actions.

---

### [YT-T1-4] Bystander Requesting to See How They Appear in a Recording

**As a** bystander who appeared in someone's Halo recording,  
**I want** to request a replay of how I was recorded,  
**so that** I can verify I wasn't misrepresented and revoke storage if needed.

- **Acceptance Criteria:**
  - Wearer receives notification: "Bob is requesting a replay of the coffee moment (10:02–10:15 AM). This requires Bob's review—you see what Bob sees."
  - Wearer taps "Allow"; Halo redacts everything except Bob's presence (no audio, no context except timestamp)
  - Bob receives redacted clip showing only his silhouette/head position in the scene for 13 seconds
  - Bob can request full deletion: "Remove me from this memory" → wearer's stitched narrative updates to "A brief moment occurred at 10:04 AM"
  - Deletion is cryptographically signed; both parties receive confirmation

- **App-shape note:** Mobile push notification + consent dialog on wearer's phone (Flutter). Bystander receives a secure link (web) or notification (if Halo user) with redacted replay. Signature confirmation shown to both parties.

---

### [YT-T1-5] Delight Moment: Accidental Capture Becomes a Shared Laugh

**As a** wearer who accidentally recorded a funny moment (someone tripping, a silly face),  
**I want** to quickly gather consent and share it with a group chat,  
**so that** the moment becomes a shared memory instead of a guilty secret.

- **Acceptance Criteria:**
  - App detects "motion anomaly" or humor-tagged frame (via Librarian's confidence scoring) and surfaces it: "Funny moment detected! Want to share?"
  - Wearer selects "Share with group"; app broadcasts clip + consent request to 3 people simultaneously
  - If all 3 consent within 60s, clip auto-posts to a shared chat with celebratory animation (confetti, bloom effect)
  - If anyone denies, clip is deleted; wearer sees "Deleted by request" with no hard feelings
  - Shared clips are time-limited (auto-expire after 7 days) unless group votes to archive

- **App-shape note:** Mobile (Flutter) with detection banner + quick-share UI. Group chat integration (webhook to shared storage or group messaging app). Web link for async consent from non-Halo users.

---

## Theme 2: The Synesthetic Familiar

### [YT-T2-1] First Launch: Meet Your Familiar and Learn It Reflects Your Stress

**As a** a wearer launching Halo for the first time,  
**I want** to see a small creature in my peripheral vision that responds to my voice, motion, and surroundings,  
**so that** I feel like I have a companion that knows me instead of just a device.

- **Acceptance Criteria:**
  - On first boot, host app (mobile or web) shows "Your Familiar is waking up" animation; creature appears in corner of Halo display
  - Creature is <40×40 pixels, animated breathing loop that matches wearer's breathing (mic-detected via host phone)
  - Tapping the Halo button makes creature "react": plays a happy chirp, briefly bounces
  - Host app displays "Familiar vitals": stress level (0–100, based on IMU + audio tone), curiosity (based on camera motion), energy (based on taps/activity)
  - After 60 seconds, host app suggests: "Your Familiar is calm right now; they'll help you notice when you're stressed"

- **App-shape note:** Mobile host app (Flutter) shows familiar vitals dashboard + pairing tutorial. Halo display shows small sprite in bottom-right corner, animated breathing loop. Web version shows vitals but familiar only renders on Halo device.

---

### [YT-T2-2] Wearer Notices Familiar Showing Stress Before They Feel It

**As a** a wearer in a stressful meeting,  
**I want** to glance up and see my Familiar's breathing speed up or color shift,  
**so that** I catch my stress level rising and can take a breath before I snap.

- **Acceptance Criteria:**
  - Familiar's breathing accelerates when: IMU detects tension (tight shoulder/neck movement), audio tone analysis detects raised voice, or heart-rate proxy (via bone conduction audio baseline) spikes
  - Color shifts from calm (blue/green) → alert (yellow) → stressed (red) over 3–5 seconds
  - Visual change is subtle (not alarming), visible in peripheral vision without breaking eye contact with meeting attendee
  - Host app logs "stress spike at 2:15 PM during meeting" with ambient context (audio level, gesture intensity)
  - Wearer can tap Halo button to dismiss alert and see a guided 30-second breathing exercise (Da5id's breathing halo visual)

- **App-shape note:** Halo display sprite animates color + breathing speed. Host app (mobile) shows real-time vitals graph with stress spikes highlighted. Web dashboard displays session history + pattern recognition ("You spike stress every Tuesday 2 PM").

---

### [YT-T2-3] Customizing Your Familiar's Personality via Host App

**As a** a wearer who's bonded with their Familiar,  
**I want** to adjust how it responds (sleepy familiar vs. energetic, chatty vs. quiet),  
**so that** the companion matches my personality and doesn't feel generic.

- **Acceptance Criteria:**
  - Host app shows slider: Personality (Sleepy ↔ Hyperactive), Communication (Chatty ↔ Silent), Sensitivity (Aloof ↔ Empathetic)
  - Each setting changes sprite animation (sleepy = slow blink loops; hyperactive = jittery micro-movements; silent = no chirps)
  - Familiar learns wearer's preferences over 7 days; app suggests adjustments: "Your Familiar noticed you prefer quiet mornings"
  - User can upload a custom sprite (PNG, <4KB) to replace default creature (community remix feature)
  - Changes sync to Halo instantly via BLE; visual updates mid-session

- **App-shape note:** Mobile (Flutter) settings panel with sliders + sprite preview showing real-time customization. Web dashboard shows advanced settings + sprite upload form. Halo displays updated sprite immediately after sync.

---

### [YT-T2-4] Familiar Evolves Over 30 Days, Creating a Sense of Progression

**As a** a long-term wearer,  
**I want** to see my Familiar grow, change colors, and gain new animations as I hit daily streaks or accomplish goals,  
**so that** bonding with my Familiar feels like caring for a real relationship.

- **Acceptance Criteria:**
  - Familiar grows in size (incremental pixel expansion) every 7 days of consistent use
  - New animations unlock: 7 days (curious head tilt), 14 days (playful hop), 21 days (proud strut), 30 days (special celebration dance)
  - Color gradually shifts based on "favorite moments": most-calm time = cooler tones, most-active time = warmer tones
  - Host app shows "Familiar age: 14 days" + evolution tree ("Next milestone: playful hop unlock at 14 days")
  - If wearer skips 3 days, Familiar dims slightly and shows a "missing you" animation on next launch

- **App-shape note:** Mobile host app displays evolution timeline + upcoming milestone predictions. Halo display shows growing sprite + new animations. Web dashboard shows Familiar history graph (activity, mood, growth markers).

---

### [YT-T2-5] Delight Moment: Familiar Surprises You with an Unexpected Reaction

**As a** a wearer who's grown attached to their Familiar,  
**I want** to experience surprising moments where the Familiar reacts to something I didn't predict,  
**so that** the relationship feels alive and unpredictable instead of mechanical.

- **Acceptance Criteria:**
  - Familiar occasionally reacts to ambient events: when Halo detects laughter nearby (via audio), Familiar does a surprised bounce
  - When wearer achieves a personal best (highest activity streak, calmest hour, funniest moment shared), Familiar displays a unique celebration animation (not seen before)
  - Host app occasionally suggests: "Your Familiar wants to try something new. Allow randomness? (experimental mode)" → wearer can enable wild animations
  - Surprise moments are logged in app history: "2026-06-03 14:22: Your Familiar danced spontaneously when you laughed"
  - Community shares "rare animations" via Lua Poetry Slam—wearer can unlock limited-edition animations by voting in community gallery

- **App-shape note:** Mobile (Flutter) with experimental-mode toggle + surprise log. Halo displays randomized animations triggered by ambient events. Web community gallery showing shared Lua code + animation previews. BLE sync pulls new animations from host app periodically.

---

## Cross-Theme Notes

### Pairing & Initial Setup (Both Themes)
- Wearer scans Halo's BLE pairing code on mobile/web app
- Host app downloads user's preferred Familiar sprite + consent ledger config
- First sync takes ~10 seconds; subsequent syncs are <1 second
- Setup tutorial embedded in host app (not Halo-side) to keep on-device complexity minimal

### Privacy & Data Flow (Both Themes)
- **Theme 1 (Consent):** All consent negotiations happen on host device (phone/laptop); only encryption keys + metadata sync to Halo
- **Theme 2 (Familiar):** Familiar sprite + vitals (stress/energy) stay on-device; no telemetry sent to cloud by default
- Both themes support air-gapped mode (no cloud, pure BLE sync)

### Host-App Surface Needs
1. **Mobile (Flutter):**
   - Pairing screen (QR scan or manual entry)
   - Consent ledger dashboard (toggles + face recognition setup)
   - Familiar vitals + settings panel
   - Group chat integration hooks for Theme 1
   
2. **Web (React):**
   - Admin dashboard showing consent history + bystander requests
   - Familiar growth timeline + evolution tree
   - Community remix gallery (Theme 2 only)
   - Accessibility-first (screen readers, keyboard nav)

3. **CLI (Python/Node, optional):**
   - For developer testing: `halo-demo --theme=1-consent` or `--theme=2-familiar`
   - Emulator integration to test without hardware

---

**Status:** Ready for backtesting with Aaron & squad. Recommend prototyping Theme 1 (Consent Ledger) first due to privacy-compliance complexity; Theme 2 (Familiar) can run parallel as lower-risk delight track.
