# Wearer-Centric User Stories — Themes 1 & 2
**Date:** 2026-06-03  
**Author:** Uncle Enzo (Product/PM)  
**Lens:** Wearer value — why someone would wear Halo and reach for these capabilities  
**Scope:** Theme 1 (Consent-Aware Memory) + Theme 2 (Synesthetic Familiar)

---

## THEME 1: Consent-Aware Memory
### "Your glasses remember for you, not about you"

---

### [ENZO-T1-1] Home: The Parent Reclaiming Moments
**As a parent at home** (primary persona), I want **my Halo to passively record the past 12 hours, then let me query it** so that **I can recover fleeting moments with my kids that I'd otherwise forget**—a song they sang, a question they asked, the exact way they laughed.

**Context:**  
Parents live in ambient memory loss. You blink and your 5-year-old's babbling phase is gone. Your child asks something clever at 2 PM and you can't recall it at dinner. This parent doesn't need productivity; they need *memory prosthetics* that capture the texture of ordinary days.

**Acceptance Criteria:**
- Halo records camera + audio to a rolling 12-hour on-device buffer (no cloud upload)
- Parent can query "what did Emma say about the playground?" within the 12-hour window
- Noa surfaces a 10-second clip + auto-generated caption without requiring the parent to manually mark moments
- Before the clip enters persistent storage, Halo prompts consent: "Emma appears in this moment. Store?" (if Emma has access to a device, she can consent/deny; otherwise family consent defaults apply)
- Persistent stored moments are encrypted; only the parent + consenting people can replay

**Value Note:**  
The real barrier isn't technology—it's *guilt*. Parents feel like they should remember everything; they feel bad when they don't. This story legitimizes *needing* help and makes it feel intentional rather than failing. "I use Halo to be a better parent" becomes the narrative.

---

### [ENZO-T1-2] Work: The Professional Protecting Confidentiality
**As a software engineer in a meeting**, I want **Halo to warn me before storing footage of code on my screen or colleagues' faces in persistent memory** so that **I can share meeting notes with my personal notes without accidentally exfiltrating company IP or colleague likeness**.

**Context:**  
Knowledge workers live between two trust zones: company + personal. You're thinking through a problem in a 1-on-1 with your manager (personal learning), then casually switch to an all-hands (public). Halo becomes a liability if it naively records everything; it becomes valuable if it *helps* you honor boundaries.

**Acceptance Criteria:**
- Halo detects when screen content contains readable code or credentials (via on-device vision) and pre-marks it as "cannot store" by default
- Before a work conversation enters memory, Halo surfaces a summary: "3 people in this 1-on-1 (you + Shreya + boss); you're discussing technical design. Store for personal notes?" with opt-in per-person consent
- Colleague can revoke retrospectively: "I didn't want code samples from that meeting in your notes" → Halo auto-blurs the moment
- Wearer can override ("This is OK to remember") *with logging*, so there's an audit trail of intentional choices

**Value Note:**  
Trust is the new commodity at work. A device that *proves* you're not harvesting IP or creating shadow recordings of colleagues is not a burden—it's table-stakes for office deployment. Framed right, it's a feature, not a limitation.

---

### [ENZO-T1-3] Social: The Introvert Honoring New Acquaintances
**As someone who's socially anxious or neurodivergent**, I want **Halo to remember faces + names I learn at parties and give me gentle context reminders when I bump into them later** so that **I don't have the panicky "I should know this person" moment and can have genuine second conversations**.

**Context:**  
Social anxiety + ADHD + face blindness all hit the same vulnerability: the fear of being rude or forgetting someone important. Current workarounds are terrible—WhatsApp photo albums, weird mental notes that don't stick. Halo can be *genuine help* if it's privacy-first *and* consent-first. The acquaintance isn't data; they're a person who chose to be remembered by you.

**Acceptance Criteria:**
- Halo logs faces + audio (first names, job title, mutual connection) from social settings into an ephemeral buffer
- When you encounter the same person 2+ weeks later, Halo gently surfaces context: "This is Sam. You met them at the book club. They mentioned loving sci-fi"
- Before Sam is stored in long-term social memory, Halo asks: "Remember Sam?" (if consent-gated, Halo sends a request to Sam's device if she's a Halo wearer; otherwise default to family/trusted-circle rules)
- You can manually revoke: "Actually, I don't want to remember this person." Their data is deleted.

**Value Note:**  
This is the "I'm not creepy; I'm intentional" story. Neurodivergent folks often feel broken for not remembering people naturally. A consent-first remembering device becomes *prosthetic independence*, not surveillance. The consent layer is essential to the value proposition.

---

### [ENZO-T1-4] Crisis: The Therapist or First Responder Documenting in Real Time (✨ This Is When It Matters Most)
**As a therapist, nurse, or social worker**, I want **Halo to record sessions + home visits continuously, but require explicit per-session consent from my client + maintain automatic redaction rules** so that **I can reference exact moments with my team, protect my license, AND respect my client's privacy all at once**.

**Context:**  
High-stakes professions live in documentation nightmares. You document the hard thing (a child's emotional disclosure, a patient's wound progression) but you need legal protection that you *got it right*. Current options are hostile: either record everything (liability nightmare) or trust memory (malpractice risk). Consent-aware memory flips this: record everything, but make privacy *enforceable*.

**Acceptance Criteria:**
- At start of session, Halo logs a consent record: "Session with family (3 people + therapist). Duration: 52 min. Record Y/N?"
- If yes, continuous recording. If any participant revokes mid-session ("stop recording me"), Halo auto-blurs their face + mutes their voice in the resulting footage (but maintains timestamps of presence)
- Therapist can upload session notes to a HIPAA-compliant backend, but the footage itself never leaves the device unless all parties consent to upload
- Retrospective redaction is available: "I want to be redacted from this session" → Footage is automatically re-processed (takes 30 min) and the redacted version is what persists in the therapist's notes

**Value Note:**  
Consent-Aware Memory becomes the *compliance mechanism* for regulated industries. Insurance liability drops. Client trust rises. The device becomes table-stakes for medical/social work practice.

---

### [ENZO-T1-5] The Moment Consent Matters Most: Family Conflict
**As a parent during a family dispute**, I want **to replay what my partner said vs. what I remember them saying, but only if both of us consent to the replay** so that **we can resolve disagreements based on facts, not memory** (and trust the device didn't capture audio of my child's trauma without consent).

**Context:**  
Relationships break on small moments. "You said we'd go to the park" → "I said maybe." One of you is right; both of you remember wrong. Without Halo, this is an unresolvable argument. With Halo, it *could* be resolvable—*if* there's a consent ritual that makes both parties feel respected. This moment is where consent-awareness becomes not just privacy, but *relational integrity*.

**Acceptance Criteria:**
- During disagreement, one partner says "Let's check the recording" (both must agree; no unilateral playback allowed)
- Halo surfaces a 30-second replay of the disputed moment (no audio of children; siblings who were present are blurred/muted unless they also consent)
- Replay ends; one partner says "OK, I was wrong" or "My memory was different." No recording of the replay itself exists (it's ephemeral)
- If either party withholds consent ("Don't replay that"), the system respects it; the argument remains unresolved, but the device doesn't force reconciliation through surveillance

**Value Note:**  
This story reveals the *non-negotiable value* of consent gating. Families don't just want memory; they want *trust infrastructure*. A device that lets you resolve factual disputes without creating a power imbalance (where one partner can always replay against the other's will) is the difference between a tool and a weapon.

---

---

## THEME 2: The Synesthetic Familiar
### "A companion that knows you, in your peripheral vision"

---

### [ENZO-T2-1] Alone at Home: The Familiar as Mood Mirror
**As someone living alone or remote working**, I want **a tiny creature that lives in my corner vision all day, responding to my rhythm and energy** so that **I feel less alone and have a non-judgmental mirror of my internal state** (is this 3-hour focus session making me tense? the creature gets still and pale. am I getting energized? it dances).

**Context:**  
Solo remote workers lose circadian anchors. You blink and it's 5 PM; you haven't moved. A creature that *reflects* your state—without words, without intrusion—becomes a mirror you didn't know you needed. The familiar isn't a pet you perform for; it's a reflection of you that helps you *see* yourself.

**Acceptance Criteria:**
- Familiar sprite lives in a 48×48 pixel corner pocket; occupies <1% of visual attention
- Based on IMU (stillness/motion), audio (tone, breathing), time-of-day, the creature's posture shifts:
  - Deep focus = creature still, pale, inward
  - Movement break needed = creature starts swaying, looking at you
  - You get up and move = creature brightens, mirrors your energy
- Creature learns your personal rhythm within 3 days; after that, it *predicts* your pattern and pre-adjusts
- No notifications, no requests, no demands—pure ambient reflection

**Value Note:**  
The loneliness crisis among remote workers is real and underestimated. A device that acknowledges "I see you're tense, would you like to move?" (via creature behavior, not words) bridges the gap between *intrusive AI* and *completely absent help*. The companion doesn't tell you what to do; it shows you what's true.

---

### [ENZO-T2-2] Social Settings: The Familiar as Social Barometer (✨ This Is When It Matters Most)
**As an anxious or neurodivergent person in social situations**, I want **my familiar to show me, in peripheral vision, when I'm "performing too hard" or "fading out"** so that **I can self-regulate in real time without social cues I'm missing** (if my familiar is frantic, I know I'm talking too much; if it's dimming, I'm checked out and should re-engage).

**Context:**  
Masking is exhausting. ADHD + autism + social anxiety all describe the same problem: you don't get real-time feedback about social dynamics. By the time you realize you've been dominating the conversation, it's too late. A familiar that reflects your *actual* vibe—not what you're trying to project—becomes a social lifeline.

**Acceptance Criteria:**
- In group settings, familiar responds to:
  - Conversation pace (if you're talking fast + high-pitched, familiar gets jittery)
  - Eye contact patterns (if you're avoiding eye contact, familiar dims slightly)
  - Energy volatility (if your energy is spiking up-down, familiar flickers with you)
- Familiar *doesn't* measure "correctness"; it mirrors what's actually happening
- You can glance up and recognize your own state: "Oh, I'm anxious right now. That's OK. I can choose to breathe."
- After the social event, Halo offers a gentle summary: "High-engagement convo for 47 min. You were energized then faded. That's a pattern; want to revisit?"

**Value Note:**  
The actual value isn't predicting what *others* think; it's giving you *feedback about yourself*. Neurodivergent folks are often called "selfish" because they miss social cues—but the real problem is lack of *feedback*, not lack of empathy. A familiar becomes the feedback loop that makes self-awareness possible in real time.

---

### [ENZO-T2-3] Habit Building: The Familiar as Celebration Engine
**As someone trying to build a new habit** (hydration, stretching, meditation), I want **my familiar to celebrate with me every time I succeed—not with badges or notifications, but with genuine joy motion (dance, bloom, transformation)** so that **the reward is intrinsic and the win feels real and witnessed**.

**Context:**  
Habit apps are boring because they gamify without joy. "You've completed 7 consecutive days!" reads like a corporate memo. But if your creature *celebrates* with you—genuinely, visually, in peripheral vision—the reward becomes *felt*, not just counted. This is the story where Enzo's Micro-Habit Accelerator meets Y.T.'s Familiar.

**Acceptance Criteria:**
- You define a micro-habit (drink water, 10 squats, breathe deeply)
- Halo detects the trigger (water bottle in view, standing motion, breathing depth spike via audio)
- When you tap-confirm, familiar *erupts*: blooms outward, transforms colors, does a brief celebratory dance
- On day 3, 7, 14, 30, the celebration scales: bigger bloom, longer dance, more elaborate transformation
- After 90 days, the familiar has *evolved* (grown wings, changed color, new idle state) as a permanent marker of the streak
- No notifications; the joy is the feedback

**Value Note:**  
Habit-building is about intrinsic motivation, not external validation. A familiar that makes *you* the audience (not an app watching you) reframes habit success from "performance for an algorithm" to "relationship with your own growth." The companion becomes the witness who believes in you.

---

### [ENZO-T2-4] Learning: The Familiar as Uncertainty Visualizer
**As a student or person learning something hard**, I want **my familiar to reflect my comprehension level in real time—when I'm confident, it settles; when I'm confused, it spins or flickers—** so that **I can externalize my cognitive state and ask for help before I'm completely lost**.

**Context:**  
The most painful moment in learning is the gap between "I don't know I'm confused" and "Oh, I'm actually lost." By the time you admit it, you're 10 steps behind. A familiar that visualizes *uncertainty* (via LLM reading your tone, pace, questions) could close that gap. You see your creature getting confused and think "wait, am I confused too?" before spiraling.

**Acceptance Criteria:**
- While learning (reading, watching tutorial, in a class), Halo infers confidence via tone, pace, question phrasing
- Familiar visual state reflects this: clear and calm = confident; flickering and unsettled = confused; asking smart questions = creature perks up
- Creature doesn't *judge*; it just shows state
- If confusion persists >2 min, familiar gently nudges: "You seem stuck. Want to re-read this section?" (optional; no enforcement)
- At end of session, summary: "You felt confident on topics X + Y; uncertain on Z. That's progress."

**Value Note:**  
Learning is emotional; confidence matters as much as knowledge. A familiar that names your uncertainty without judgment creates psychological safety. "I'm confused" becomes observable fact, not failure.

---

### [ENZO-T2-5] Grief: The Familiar as Continuity (✨ This Is When It Matters Most)
**As someone grieving**, I want **my familiar to hold the memory of who I was during this relationship—not erasing their memory, but preserving the texture of how they made me feel—** so that **when the acute pain fades, I don't lose the specific way they changed me**.

**Context:**  
Grief is complicated by memory. We want to remember the person vividly but also move forward. We want to feel the loss, then eventually not feel it so acutely. A familiar trained on 6 months of interaction data (tone, energy, laughter, routines you shared) becomes a *continuity object*—not a replacement, but a keeper of the "you then" that you're mourning.

**Acceptance Criteria:**
- Before the loss, the familiar has learned the wearer's baseline: their energy patterns, what makes them laugh, their daily rituals
- After loss, the familiar *retains* that learned baseline but doesn't perform it; instead, it reflects the *wearer's grief state*: quiet when the wearer is quiet, gently animated when they're starting to move forward again
- Wearer can ask Noa: "Show me a moment from when I was happiest with them" → Familiar replays a 10-second vignette of the wearer's own energy from that time (what you *felt* like, not what you saw)
- Over 6 months, the familiar slowly shifts from "mirror of grief" to "mirror of integration"—the wearer's energy baseline rebuilds and the familiar reflects the new normal
- Option to archive the familiar's learned state (so the "you with them" is preserved) and start a new familiar for the "you after"

**Value Note:**  
This is the story that shows a companion *isn't escape; it's integration*. Grief doesn't disappear; it gets absorbed into who you become. A familiar that witnesses that transformation—and holds the memory of "who you were then"—becomes a touchstone for meaning-making, not avoidance. The value is in *continuity*, not distraction.

---

---

## Summary: Why These Stories Matter

### Theme 1 (Consent-Aware Memory) — The Enabler
These stories answer: *"Why would someone trust Halo to record them?"*  
The consent layer isn't a limitation; it's the *reason people wear it*. Privacy-first recording becomes a permission structure that enables honesty. A parent can record a child without guilt. A professional can record a meeting without liability. A couple can record a conversation without weaponizing it.

### Theme 2 (Synesthetic Familiar) — The Witness
These stories answer: *"Why would someone want a companion, not a tool?"*  
The familiar isn't productive; it's *relational*. It doesn't help you get more done; it helps you *know yourself*. A remote worker feels less alone. A neurodivergent person gets feedback they're missing. A grieving person integrates loss. A learner sees their own confusion. A person building a habit feels genuinely celebrated.

**The convergence:** Theme 1 creates the *safety* for intimate capture. Theme 2 creates the *meaning* from that capture. Together, they position Halo not as a camera (invasive, extractive) but as a *mirror that respects you and a companion that knows you*.

---

**Next steps:**  
- Route Theme 1 stories to Raven + Librarian + Hiro for architecture validation
- Route Theme 2 stories to Y.T. + Da5id + Librarian for familiar scaffold design
- Each agent writes lens-specific stories (Raven's consent/privacy stories, Y.T.'s joy stories, Librarian's AI reasoning stories) *around* these wearer-centric narratives
