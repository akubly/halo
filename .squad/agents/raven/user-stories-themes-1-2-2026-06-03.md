# User Stories: Themes 1 & 2 — Consent-Aware Memory & The Synesthetic Familiar
**Date:** 2026-06-03  
**Author:** Raven (Security & Privacy)  
**Scope:** 9 user stories across 2 themes (6 Theme 1, 3 Theme 2)  
**Personas:** Bystander (primary for T1), Wearer, Auditor, Revoked-consent Ex-Friend

---

## THEME 1: CONSENT-AWARE MEMORY
*Heavy lift — the privacy contract for persistent memory on Halo must be encoded concretely enough to test and enforce. These stories translate Enzo's Memory Ledger + Librarian's Episodic Stitching into privacy obligations the system must enforce, not just document.*

---

### [RAVEN-T1-1] As a **bystander**, I want **a persistent, non-dismissible consent notification when I appear in a wearer's rolling memory buffer**, so that **I know I'm being recorded and can take action (opt-out, leave, ask the wearer) before moments become persistent storage.**

**Acceptance Criteria:**
- Every time the wearer's Halo detects a bystander's face (via on-device ML), the bystander's **phone or Halo receives a cryptographically signed notification** within 2 seconds: "Alice's Halo recorded your face at 2:47 PM at [location]; consent status: pending."
- The notification **cannot be dismissed silently**; bystander must explicitly tap "OK" or "Revoke Consent" — silence is not consent.
- Notification includes a **24-hour countdown** — if bystander takes no action, footage auto-redacts (face blurred) before wearer's Memory Ledger persists it.
- Notification payload includes: wearer's identity, timestamp, approximate location (GPS if available, otherwise "indoors"), and a **6-second audio+video preview** of the moment (wearer's view, auto-blurred except bystander).
- If bystander revokes consent, **within 5 seconds** a "revocation proof" is sent back to wearer's device. Wearer cannot override; face is permanently blurred in that Memory Ledger entry.

**Threat Note:**  
*Mitigates silent surveillance and uninformed inclusion in persistent digital memory. Without this, Halo becomes a passive recording platform that captures bystanders indefinitely. The 24-hour window and revocation mechanism ensure bystanders retain agency.*

---

### [RAVEN-T1-2] As a **wearer**, I want **to review and manually approve each unique person before their face is stored in persistent Memory Ledger**, so that **I retain control over whose identity is linked to my recorded moments, and I can redact or blur people I didn't intend to record.**

**Acceptance Criteria:**
- Before any Memory Ledger entry transitions from ephemeral (30-second auto-delete) to persistent (encrypted on-device storage), Halo displays a **mandatory review workflow** listing all detected faces + identified people (via on-device face-matching to wearer's contact list or prior recordings).
- For each unique person, wearer chooses one of: (1) **Store identity + face** (record this person's name and appearance), (2) **Store blurred only** (record moment but blur this person's face in all future replays), (3) **Delete entirely** (don't store anything containing this person).
- Wearer's choice is **logged with timestamp + reason** (optional voice note). This log becomes an audit trail — any reviewer can see "You chose to blur Sarah on 2026-06-02 at 14:30."
- If wearer attempts to export Memory Ledger to host app or cloud, the export **rejects if any person has status "store identity" but *did not* send consent approval** (via RAVEN-T1-1 notification). Export shows a dry-run: "3 faces need consent before export; 1 face is auto-blurred (your choice); 2 faces are from your trusted list (auto-approved)."
- After 7 days without explicit storage decision, **default is auto-blur** (not default-delete, not default-store). System err on side of privacy.

**Threat Note:**  
*Prevents wearer from unconsciously building an unaccountable video dossier of bystanders. The mandatory review friction ensures wearer considers each person's privacy and their own intent. The audit trail provides evidence of good-faith effort for future legal review.*

---

### [RAVEN-T1-3] As a **bystander who previously revoked consent**, I want **the wearer's Halo to respect my revocation as a persistent "do not record me" signal**, so that **even if the wearer later re-encounters me, my face is automatically blurred in all future recordings, and I remain forgotten.**

**Acceptance Criteria:**
- Bystander's revocation (via RAVEN-T1-1) generates a **cryptographic revocation token** (`revoke_proof = HMAC(bystander_id, wearer_id, timestamp, salt)`) stored on wearer's device.
- This token is **locally persistent** — if wearer uninstalls/reinstalls Halo app, revocation tokens are recovered from encrypted backup or marked as "unknown" and re-requested.
- On each subsequent camera capture, Halo checks: **if detected face matches a revoked bystander's biometric profile**, that face is **automatically blurred at capture time** (before Memory Ledger entry is created, not as post-processing).
- If wearer attempts to manually override blur for a revoked bystander, system logs the override attempt + timestamp, **rejects the override**, and displays: "Revocation for [bystander] is in effect until [expiry date]. You cannot override. Contact [bystander] to request consent lift."
- Revocation token **expires after 1 year by default** or sooner if bystander explicitly requests revocation lift (via app, re-sends consent approval).
- **Multidevice scope:** If bystander revokes on wearer's Halo, the revocation does **NOT** automatically propagate to other wearers' Halos. Privacy is bilateral, not broadcast. (Each wearer-bystander pair has independent consent state.)

**Threat Note:**  
*Implements the "right to be forgotten" in a peer-to-peer context. Without persistent revocation, a wearer could repeatedly record a bystander across weeks/months, defeating the purpose of revocation. This ensures bystanders maintain veto power.*

---

### [RAVEN-T1-4] As an **auditor reviewing a wearer's Memory Ledger for legal compliance**, I want **cryptographic proof that each stored face has valid, non-revoked consent**, so that **I can certify the Memory Ledger is compliant before the wearer uploads it to cloud or shares it with others.**

**Acceptance Criteria:**
- Every persistent Memory Ledger entry (stitched narrative moment or raw clip) includes a **consent manifest** — a list of all detected people + their consent status at capture + revocation status at audit time.
- Each person's entry includes: (1) **consent proof** (wearer says "yes, approved for storage"), (2) **notification timestamp** (when bystander was notified), (3) **bystander's response** (approved, revoked, silent/default-blurred), (4) **current revocation status** (active, expired, lifted).
- Auditor tool reads manifest + outputs a **compliance report**: "8 faces in this Memory Ledger. 6 have active consent + approval. 2 are auto-blurred (silent default, no consent needed). 0 are revoked. Audit: PASS."
- If any face is flagged as "stored identity without consent approval," audit tool **blocks export** and flags for wearer review.
- Manifest is **signed by wearer's device private key** — if any face or consent status is edited after signing, signature breaks and audit tool displays: "Manifest integrity check failed. This entry has been tampered with."
- Auditor can export a **zero-knowledge proof report** for third parties (e.g., legal review): "On 2026-06-02, wearer collected 8 faces; 6/8 had affirmative consent; 2/8 were auto-blurred per privacy default. All proofs verify." — without exposing the actual identities or faces.

**Threat Note:**  
*Prevents wearer from claiming retrospective consent or post-hoc approval of non-consensual recording. The signed manifest ensures auditors can detect tampering. This is critical for legal defensibility — Halo's competitive advantage is provable privacy, not just claimed privacy.*

---

### [RAVEN-T1-5] As a **revoked-consent ex-friend**, I want **the ability to request a full redaction of all my appearances in a wearer's long-term Memory Ledger**, so that **I can enforce my right to be forgotten even after consenting initially, then changing my mind.**

**Acceptance Criteria:**
- Revoked-consent ex-friend (someone who previously consented, now wishes to remove all record) initiates a **revocation request** via app or NFC tap to wearer's device: "Remove all appearances of [my face] from your Memory Ledger, effective immediately."
- Request includes optional **revocation window** (e.g., "remove appearances from 2026-05-01 to 2026-06-02") or "remove everything from me."
- Wearer's Halo receives request + displays prompt: "[ExFriend] is requesting you revoke consent for [N] stored moments containing their face. You can: (1) Accept (auto-blur all moments), (2) Partial redact (blur face but keep context), (3) Delete entirely."
- If wearer accepts: all moments are **re-encrypted with a zero-key** (wearer can no longer decrypt any content containing ex-friend). Moments are still stored on device, but inaccessible — a privacy tombstone.
- If wearer delays response >7 days, system **auto-applies acceptance** (assumption is consent once given can be revoked; wearer cannot use silence to deny revocation).
- Wearer receives a **revocation receipt** (timestamped, signed by both parties' keys) proving ex-friend's revocation was processed. Ex-friend receives identical receipt for their records.
- If wearer has already **exported a Memory Ledger to cloud** (before revocation request), wearer must **issue a cloud revocation notice** to the cloud service and any downstream viewers (e.g., "Withdraw all images of [person] from export ID xyz"). System tracks these notices in an immutable ledger.

**Threat Note:**  
*Addresses the most adversarial privacy scenario: relationships end, trust breaks, past consent becomes coercion. Without explicit revocation enforcement, memory becomes a tool for retribution. This story ensures ex-relationships don't create permanent digital damage.*

---

### [RAVEN-T1-6] As a **wearer**, I want **Halo to automatically generate a privacy receipt after each recording session**, so that **I have proof of what I recorded, who consented, who was blurred, and what storage decisions I made — for my own defense if a bystander later claims non-consensual recording.**

**Acceptance Criteria:**
- After each recording session (defined as a continuous stretch of camera/mic activity, or user-defined "end session"), Halo generates a **privacy receipt** — a JSON manifest + cryptographic signature.
- Receipt includes:
  - **Session metadata:** start time, end time, location (if GPS available), wearer's privacy mode (red/yellow/green).
  - **Detected participants:** list of all faces detected, with consent status per face (approved, auto-blurred, revoked).
  - **Storage decisions:** wearer's explicit choices (which faces to store identity, which to blur, which to delete).
  - **Auto-redactions:** count of faces auto-blurred due to privacy defaults or revocation enforcement.
  - **Cloud export status:** if exported, timestamp + export destination + hash of exported content.
- Receipt is **signed by wearer's device private key + timestamped by a trusted time server** (device clock is not tamper-proof; timestamp server proof is).
- Receipt is **automatically uploaded to wearer's personal encrypted backup** (optional: can be uploaded to a third-party privacy notary service, similar to a blockchain notary, to create an immutable record).
- If bystander later claims "you recorded me without consent," wearer can produce receipt showing: "At time of recording, bystander consent status was 'revoked' (so face was auto-blurred)" or "bystander sent approval notification" (with timestamped proof).

**Threat Note:**  
*Shifts burden of proof from reactive defense to proactive documentation. Without receipts, it's he-said-she-said. With receipts, the device's consent tracking becomes legally defensible evidence. This is the Halo differentiator: cameras that prove they played fairly.*

---

## THEME 2: THE SYNESTHETIC FAMILIAR
*Lighter lift — the Familiar is an ambient companion creature that evolves in peripheral vision, reflecting the wearer's internal state (stress, focus, mood) via abstract, synesthetic rendering. These stories ensure the Familiar doesn't inadvertently leak sensitive information to bystanders and that the wearer maintains control over what the creature reveals about them.*

---

### [RAVEN-T2-1] As a **bystander**, I want **the Familiar's on-screen appearance to NOT reveal sensitive information about the wearer** (e.g., wearer's stress level, emotional state, biometric data), so that **I don't gain uninvited insight into the wearer's private mental state.**

**Acceptance Criteria:**
- Familiar's on-screen animation uses **abstract, non-semantic visual patterns** — breathing (ring size), color temperature, motion smoothness — **not labeled, not interpreted**.
- Bystander viewing wearer's Halo display **cannot infer** (without domain expertise) what internal state the Familiar's animation represents. Visual pattern is beautiful but opaque.
- System avoids any **representational biology** that encodes biometric state (e.g., no pulse visualization on wrist, no breath-wave geometry). Use abstract motion (orbit, bloom, pulse) instead.
- If Familiar is labeled (e.g., "Calm" state displayed on HUD for wearer), label is **visible only to wearer**, not on shared display. Bystander sees unlabeled animation.
- Familiar's animation loop **includes deliberate visual noise/jitter** (5-10% random variation) to prevent bystanders from deriving statistical patterns of the wearer's state across time.

**Threat Note:**  
*Prevents Familiar from becoming an unintended biometric leak. A wearer showing stress via Familiar's animation teaches bystanders/observers facts about the wearer's internal state. This story enforces opacity — beauty without revelation.*

---

### [RAVEN-T2-2] As a **wearer**, I want **full control over whether the Familiar's internal-state representation is synced to other wearers' devices when we're in proximity**, so that **I can choose privacy (Familiar hides my state) or connection (Familiar broadcasts my mood to my social group).**

**Acceptance Criteria:**
- Wearer has a **Privacy Toggle for Familiar Sync:** On-device setting (default: OFF / private).
- **When Sync = OFF (private):**
  - Familiar's animation represents wearer's internal state *only on their own Halo display*.
  - If other wearers' Halos come into BLE range, Familiar animation **does not transmit** state data via BLE. Other wearers see a *static, neutral familiar* on wearer's Halo display (or no Familiar at all, if wearer chooses).
  - Wearer's biometric data (stress, heart rate proxy, IMU-derived mood) **never leaves the device**.
- **When Sync = ON (connected):**
  - Familiar broadcasts wearer's internal-state abstract pattern to nearby wearers' Halos via encrypted BLE.
  - Other wearers see a **mirrored Familiar animation** on their own displays, labeled with wearer's name + state (e.g., "Alice is calm" / "Bob is stressed").
  - Wearer can **revoke Sync at any time** (toggle OFF) — in-flight broadcasts stop; other wearers' mirrored Familiars freeze or fade to gray.
- Wearer receives a **notification log** showing: who received Familiar state, when, for how long. Wearer can audit their state-sharing history.
- Wearer can set **per-contact Sync rules** (e.g., "share Familiar state with Alice always, with Bob only during work hours, never with strangers").

**Threat Note:**  
*Prevents wearer from involuntarily broadcasting their emotional state. Without control, Familiar becomes a forced vulnerability — coworkers, family, strangers all infer wearer's mood in real-time. This story ensures transparency + agency.*

---

### [RAVEN-T2-3] As an **auditor reviewing wearer's Halo settings**, I want **a privacy audit of Familiar's internal-state data retention and transmission**, so that **I can verify Familiar is not silently logging wearer's stress/mood history to a remote server or storing it in plaintext.**

**Acceptance Criteria:**
- Halo provides a **Familiar Privacy Report** accessible via device settings + exportable.
- Report includes:
  - **Internal-state retention policy:** Familiar stress/mood/biometric signals are stored **only in RAM, never persisted to flash storage**. (Session restarts clear all data.)
  - **Transmission log:** Every BLE sync event is timestamped + recipient-logged. Auditor can see "Familiar broadcast to [Alice] 47 times, [Bob] 3 times" with duration + date ranges.
  - **Encryption status:** All BLE transmissions use **AES-256-GCM** (encrypted, authenticated, device-to-device). No cleartext internal-state data leaves the device.
  - **Third-party data flow:** Report confirms Familiar data is **never sent to cloud services, AI providers, or analytics services**. (Familiar state may be input to *local* on-device inference, but never exported.)
- Auditor tool can **verify cryptographic bindings** — every BLE sync message is signed by wearer's device + recipient's device, preventing injection/tampering.
- If any plaintext or unencrypted internal-state data is detected in device logs, audit tool **flags as FAIL** + recommends factory reset.

**Threat Note:**  
*Prevents Familiar from becoming a silent surveillance tool. If mood data is logged server-side or shared with analytics partners without user knowledge, Familiar becomes a biometric time-series leakage. This story ensures Familiar data stays on-device and locally controlled.*

---

## Summary Table

| Story | Theme | Persona | Privacy Mechanism | Threat Mitigated |
|-------|-------|---------|-------------------|------------------|
| RAVEN-T1-1 | Memory | Bystander | 24h consent notification + revocation window | Silent bystander recording |
| RAVEN-T1-2 | Memory | Wearer | Mandatory pre-storage review + audit trail | Unconscious dossier building |
| RAVEN-T1-3 | Memory | Bystander | Persistent do-not-record token | Revocation circumvention |
| RAVEN-T1-4 | Memory | Auditor | Consent manifest + cryptographic proof | Fake/retroactive consent claims |
| RAVEN-T1-5 | Memory | Ex-Friend | Right-to-be-forgotten revocation + cloud notice | Relationship coercion via stored footage |
| RAVEN-T1-6 | Memory | Wearer | Privacy receipt + timestamp proof | Legal defensibility gap |
| RAVEN-T2-1 | Familiar | Bystander | Abstract, opaque visual patterns | Unwanted biometric inference |
| RAVEN-T2-2 | Familiar | Wearer | Sync toggle + per-contact rules | Forced mood broadcasting |
| RAVEN-T2-3 | Familiar | Auditor | Privacy audit + encryption verification | Silent server-side logging |

---

## Implementation Roadmap Notes

**T1 Stories (Consent-Aware Memory):**
- **T1-1, T1-2:** Core consent flow — **critical path**. Requires: on-device ML face detection, BLE notification layer, Memory Ledger storage schema with consent metadata.
- **T1-3:** Requires: persistent revocation token storage + local face matching at capture time (not post-processing).
- **T1-4:** Audit tooling — **post-MVP**, but critical for community trust + legal compliance demos.
- **T1-5:** Right-to-be-forgotten — complex distributed state. Requires: cloud export notice framework + zero-key re-encryption. **Lower priority initially**, but foundational for relationships/trust.
- **T1-6:** Privacy receipts — **detective work on existing systems** (time servers, notary services). Medium lift, high trust-value.

**T2 Stories (Familiar):**
- **T2-1, T2-2:** HUD privacy + wearer control — straightforward. Pairs with Da5id's circular display + Librarian's mood inference.
- **T2-3:** Audit tooling — deferred, but necessary for compliance trust.

**Cross-Cutting Concerns:**
- BLE encryption layer (must support consent metadata + signatures)
- On-device cryptographic signing (device private key management)
- Time-server integration (tamper-proof timestamps)
- Cloud export + revocation notice protocol (async, reliable notification)
