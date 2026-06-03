# User Stories: Themes 1 & 2 — OSS & Licensing Lens
**Date:** 2026-06-03  
**Author:** Lagos (OSS & Licensing)  
**Scope:** Contributor/forker user stories for **Theme 1 (Consent-Aware Memory)** and **Theme 2 (The Synesthetic Familiar)** playground demos.

---

## Theme 1: Consent-Aware Memory — High-Stakes Privacy Code

### [LAGOS-T1-1] A developer forks the demo and wants clear licensing for downstream use

**As a** developer who forks the `halo/examples/consent-aware-memory` demo to build a commercial product,  
**I want** a clear, machine-readable declaration of what I can do with the forked code and any privacy-forward dependencies it pulls in,  
**so that** I don't accidentally violate a copyleft license or republish bystander data without explicit consent terms in my product.

**Acceptance criteria:**
- README includes a "Licensing & Commercial Use" section naming every dependency and its SPDX identifier (Brilliant SDK: BSD-3-Clause, Gemini API: proprietary, etc.)
- A `DEPENDENCIES.md` file lists transitive dependencies with privacy-relevant ones flagged (e.g., "TensorFlow Lite: Apache-2.0, can be redistributed; uses no cloud telemetry")
- LICENSE file at root is MIT and includes attribution clause for Brilliant Labs (per their BSD-3-Clause requirement)
- Sample downstream product license template provided (e.g., "If you fork this, recommend MIT or Apache-2.0 for your derivative")
- CI/CD includes `licensee` or `license-report` that fails the build if a new copyleft dependency is added without explicit review

**License/posture note:**  
*Copyleft protection: GPL/AGPL dependencies would "poison" derivative products, forcing them open-source. MIT + BSD-3-Clause chain allows commercial variants without reciprocal licensing.*

---

### [LAGOS-T1-2] A privacy advocate reviews a forked consent-aware variant and wants to verify data handling claims

**As a** privacy researcher who discovers a fork of the consent-aware memory demo being used in a therapeutic setting,  
**I want** to audit the fork's LICENSE, NOTICE, and privacy-redaction behavior to verify it honors the original consent guarantees (no unredacted bystander faces in persistent storage),  
**so that** I can certify the fork as privacy-compliant or flag it as a violation to the maintainer and affected users.

**Acceptance criteria:**
- NOTICE file includes a "Privacy Invariants" section documenting consent requirements from original demo (e.g., "All faces must be redacted unless explicit consent is recorded via BLE signature")
- A `PRIVACY-AUDIT.md` checklist provided that auditors can copy, fill out, and commit as proof of compliance
- Original demo includes inline comments flagging privacy-critical functions (e.g., `// REDACT: faces auto-blurred unless consent_signature[face_id] exists`)
- Demo stores consent signatures in a `.halo_consent_log` file (JSON) that downstream forks should audit during QA
- GitHub issue template available: "Privacy Audit Request — certify this fork honors Consent-Aware Memory invariants"

**License/posture note:**  
*Transparency requirement: Forked privacy code carries downstream liability. NOTICE + inline docs create an auditable chain that protects both original authors (they documented intent) and downstream users (they can verify compliance).*

---

### [LAGOS-T1-3] A contributor submits a PR that adds new ML model integration and wants to document the attribution chain

**As a** contributor who adds a local on-device face-detection model (e.g., TensorFlow Lite) to the consent-aware memory demo to reduce cloud API calls,  
**I want** guidance on how to declare the model's license, document its training data provenance, and ensure the demo's overall attribution reflects the new dependency,  
**so that** downstream forkers inherit a clear, complete chain of attribution and don't accidentally violate the model's training-data copyright.

**Acceptance criteria:**
- CONTRIBUTING.md section: "Adding AI Models" includes a template for model LICENSE, training dataset source, and model-card (arXiv 1810.03993)
- PR checklist asks: "Does this model's training dataset require attribution? Do terms forbid commercial use?"
- NOTICE file auto-updated by CI/CD: new model entry added with license, date added, contributor name
- README updated with section "Models in This Demo" listing each model's source, version, and copyright holder
- If model is GPL/AGPL, PR requires explicit squad sign-off (due to copyleft "viral" risk to entire repo)

**License/posture note:**  
*Model licensing is often overlooked. Training data copyright + model distribution rights are separate concerns. Documentation requirement prevents "dependency hell" downstream where a forker inherits a GPL model they didn't know about.*

---

### [LAGOS-T1-4] A new Halo developer reads the README for the first time and learns how NOT to republish bystander data (failure path)

**As a** new developer building on the consent-aware memory demo and reading the README,  
**I want** clear examples of "what goes wrong if you skip consent checks" — edge cases where the safe path is easy to miss,  
**so that** I don't accidentally ship a variant that stores faces without consent, leading to legal/privacy liability for anyone who inherits my fork.

**Acceptance criteria:**
- README includes a "Common Pitfalls" section with 3 runnable code examples: (1) storing footage before checking consent_log, (2) exporting cloud API inferences without redacting raw footage, (3) inheriting consent_log from another device without re-verifying
- Each pitfall links to a specific test case in the demo's test suite (e.g., `tests/test_unauthorized_export.py` that *fails* if consent is missing)
- Comment in main demo code: "# ⚠️ CONSENT GATE: footage cannot enter persistent_memory until consent_signatures are verified (see README: Common Pitfalls)"
- Optional: "Privacy-First Checklist for Forks" — a markdown form contributors can copy, fill, and commit to show they've audited the consent flow

**License/posture note:**  
*Normalization via documentation: Forking a privacy-critical demo without understanding the consent model is the highest-stakes mistake. Making edge cases explicit (in code comments, README, and tests) lowers the liability surface for both original authors and downstream forks.*

---

## Theme 2: The Synesthetic Familiar — Creative Remix Culture

### [LAGOS-T2-1] A developer forks the familiar demo and wants to know how to share their custom creature variant while crediting the original

**As a** developer who extends the pet familiar demo to create a bioluminescent variant (adds glow effects, new emotional states),  
**I want** clear guidance on licensing the variant (can I use CC-BY? MIT? Can I commercialize?), and how to declare attribution to the original creator in a way that's both legal and culturally respectful,  
**so that** I can share my variant with confidence, knowing downstream forks will credit me AND the original author in an attribution chain.

**Acceptance criteria:**
- README includes "Licensing Your Familiar Variant" section with 3 license options: MIT (minimal attribution), CC-BY-SA (requires remixes to stay CC-BY-SA), Apache-2.0 (commercial + derivatives OK, must credit all contributors)
- NOTICE file template provided for derivatives: `[Variant Name] by [Your Name], derivative of [Original Creature] by [Original Author], licensed under [License]`
- Optional metadata file: `.familiar-lineage.json` (CC0) that tracks: original creator, variant creator, license of each, timestamp, link to source repo
- GitHub issue template: "Publish My Familiar Variant" with prefilled NOTICE section, CI/CD check that validates metadata before merging
- Community hub suggestion: "Add your variant to the Attribution Wall of Awesomeness at community.halo-docs.com/familiars"

**License/posture note:**  
*Copyleft choice is cultural: CC-BY-SA creates a "remix commons" where all derivatives stay open; MIT maximizes forks but dilutes attribution. Documentation lets each variant choose its own posture, making licensing visible as a design decision, not hidden compliance.*

---

### [LAGOS-T2-2] A downstream user discovers a forked familiar variant in the wild and wants to trace its lineage and license

**As a** Halo user who discovers a beautiful glitch-art familiar variant running on someone else's device at a meetup,  
**I want** to tap a "Fork Info" button and see: (1) the lineage of creators (original → first remix → this variant), (2) the license of each version, (3) where to find the source code, (4) how to share my own variant of it,  
**so that** I can fork the fork, credit everyone properly, and add my own twist without accidentally violating anyone's licensing intent.

**Acceptance criteria:**
- Familiar Lua script includes a `.fork_metadata` comment block with: `original_author`, `license_spdx`, `source_repo_url`, `variant_creators` (list of names + dates)
- Mobile companion app (Flutter) includes a "Familiar Info" screen accessible via long-press on the creature; displays metadata + link to source
- Halo display includes a "credit" glyph (orbit indicator) that briefly shows 1-2 creator names when tapped (on-device attribution)
- README section "Understanding Familiar Lineage" with examples of 2-generation and 3-generation remixes, showing how `.fork_metadata` evolves
- CI/CD test: Build fails if `.fork_metadata` is missing or has empty `original_author` field (enforces attribution)

**License/posture note:**  
*Transparency creates trust: If every familiar variant includes its lineage (on-device and in source), forking becomes traceable. Users see themselves as part of a creative chain, not anonymous remixers. Enforcing metadata via CI/CD makes attribution a build requirement, not a suggestion.*

---

### [LAGOS-T2-3] A community artist submits creative asset packs (sprites, animations) as CC-licensed resources and wants contributors to understand the attribution flow

**As a** community visual artist contributing a library of CC-BY-licensed creature animations (idle, alert, happy states) for use in any Halo familiar fork,  
**I want** a clear guide showing: (1) what attribution looks like when someone uses my assets, (2) how my CC-BY license interacts with forks that use MIT or other licenses, (3) how commercial products can use my assets legally,  
**so that** my creative contribution is properly credited across an unlimited chain of remixes, and I build a portfolio of work that follows me into derivative projects.

**Acceptance criteria:**
- `.squad/resources/ASSET-ATTRIBUTION-GUIDE.md` provided, showing real examples: "If you use Artist-A's CC-BY animations in your familiar, your derivative is MIT, and you fork it under Apache-2.0, what's the lineage?"
- NOTICE file for asset pack includes: `[Asset Pack Name] by [Artist], CC-BY-4.0. You may use in any project (commercial or open-source). You must credit: [Artist Name] — [Link to original work]`
- GitHub issue label: `cc-assets` for PRs adding creative assets; automated message thanks artist + explains attribution requirements
- Optional: "Asset Pack Registry" at `community.halo-docs.com/assets` showing artists' portfolios (avatar, name, license, samples)
- Build check: Demo fails to build if CC-BY assets are used but artist credit is missing from README or NOTICE

**License/posture note:**  
*Creative licensing is distinct from code licensing: CC-BY requires attribution in output, not just source. By documenting the flow (code can be MIT, assets must be CC-BY, both travel downstream), we normalize mixed-license projects and protect artists' attribution rights.*

---

### [LAGOS-T2-4] A fork becomes commercially successful and a new maintainer wants to ensure downstream users understand the original CC-licensed assets (risk path)

**As a** startup that forks the familiar demo, creates a beautiful variant, and wants to build a consumer app from it,  
**I want** to understand my licensing obligations when I include CC-licensed community assets in a commercial product, and what disclosures my app must include,  
**so that** I ship a product that's legally compliant, properly credits the original artists, and doesn't accidentally violate their CC-BY terms.

**Acceptance criteria:**
- CONTRIBUTING.md section "Commercializing Derivatives" explicitly covers: "Any fork using CC-BY assets must include attribution in app UI (not just source), in app store listing (description), and in user-facing credits screen"
- Legal template provided: "Required Disclosures for CC-BY Assets in Commercial Apps" with 3 disclosure methods ranked by compliance rigor (best: in-app credits screen + app store listing; acceptable: README in source repo + app store listing; avoid: source-only, not user-facing)
- Example: If a commercial app uses `artist-alice-cc-by-animations`, the app's "Credits" screen must list "Animations by Alice, CC-BY-4.0, https://github.com/alice-art" — this is a legal requirement, not optional
- README note: "CC-BY is permissive for *use* but strict on *attribution*. You may commercialize. You may not remove attribution." Link to Creative Commons FAQ on commercial use
- CI/CD warning (not failure): Flags when CC-BY assets are added; asks maintainer to confirm they understand CC-BY attribution requirements

**License/posture note:**  
*Copyleft trap: CC-BY looks permissive ("do whatever you want") but has teeth in attribution requirements. Clear documentation prevents the most common downstream mistake: shipping a successful app, then discovering (too late) that artist credits were buried in source code instead of visible to users. Proper disclosure protects both startup and artists.*

---

## Summary: Key Themes Across All Stories

| Story ID | Theme | Licensing Lever | Downstream Risk |
|----------|-------|-----------------|-----------------|
| **T1-1** | Consent-Aware Memory | Dependency declaration | Commercial variant unknowingly inherits copyleft |
| **T1-2** | Consent-Aware Memory | Privacy audit trail | Fork violates consent invariants; liability spreads to original authors |
| **T1-3** | Consent-Aware Memory | Model attribution | Training data copyright violation; GPL model "poisons" repo |
| **T1-4** | Consent-Aware Memory | Privacy pitfall documentation | Developer ships variant that republishes bystander data without consent |
| **T2-1** | Synesthetic Familiar | Creative licensing choice | Attribution chain is unclear; downstream remixer can't credit properly |
| **T2-2** | Synesthetic Familiar | Lineage transparency | User forks without understanding license implications; creates unattributed variant |
| **T2-3** | Synesthetic Familiar | Asset attribution | Artist's CC-BY work credited in source but invisible to end users |
| **T2-4** | Synesthetic Familiar | Commercial disclosure | Startup unknowingly violates CC-BY artist attribution in shipped app |

---

## Next Steps

1. **Theme 1 (Consent-Aware Memory):** Prioritize T1-4 (README pitfalls); add `tests/test_unauthorized_export.py` to demo's test suite. High impact for new developers.

2. **Theme 2 (Synesthetic Familiar):** Prioritize T2-1 (licensing variant guidance); create `.familiar-lineage.json` template in the demo's source.

3. **Cross-Theme:** Create `.squad/templates/NOTICE-template.md` and `.squad/templates/DEPENDENCIES.md` for use in both themes' documentation.

4. **CI/CD:** Add `licensee` check to both demos' GitHub Actions workflows; fail build if license/attribution fields are missing.

5. **Community Hub:** Set up `community.halo-docs.com/familiars` + `community.halo-docs.com/forks` registries (low lift; auto-generated from GitHub metadata).

