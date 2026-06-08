# Project Context

- **Owner:** Aaron Kubly
- **Project:** halo — mono-repo playground for authoring apps on Halo smart glasses
- **My layer:** LICENSE, NOTICE, CONTRIBUTING, attribution, license-compatibility review
- **Public posture:** Intended for public sharing on GitHub
- **Created:** 2026-06-01

## Learnings

- **Brilliant SDK repo**: https://github.com/brilliantlabsAR/brilliant_sdk — check root LICENSE before declaring compatibility.
- **Root LICENSE (SPDX: BSD-3-Clause)** — Copyright © 2025 CitizenOneX. Permits redistribution in source & binary forms with retention of copyright notice; no liability for damages; no permission to use contributor names for product endorsement.
- **Flutter LICENSE (SPDX: BSD-3-Clause)** — Copyright © 2025 Brilliant Labs. Identical clauses to root license, suggesting Brilliant Labs took control; different copyright holder but same permissive terms.
- **Python & WebBluetooth** — No per-folder license files; inherit from root BSD-3-Clause.
- **Patent grants**: None explicit in BSD-3-Clause text. No copyleft obligations (GPL/AGPL absent). No patent retaliation clauses.
- **Attribution requirement**: Must retain copyright notice & license text in source distributions; binary distributions must include in documentation or materials.
- **Commercial use**: Permitted without restriction; sample-code distribution downstream is fully compatible.
- **Public posture**: All SDKs declare unified BSD-3-Clause licensing in root README; marketed as open-source on brilliant.xyz.

## Ideation 2026-06-02

*PIE-IN-THE-SKY meta-projects to make the playground itself a community magnet (movement-building, not licensing-correctness)*

1. **Halo Canvas Livestream** — Weekly Thursday night live-coding sessions where rotating contributors build silly Halo apps on air with full decision-commentary & fork-bait repo tags, turning the development ritual itself into the draw.

2. **License Roulette Experiment** — Each playground project randomly assigned a different permissive license (MIT/Apache-2.0/ISC/0BSD) with creative briefs to explore what cultural signal each sends; monthly community vote on which "felt right."

3. **Attribution Wall of Awesomeness** — Dynamic GitHub Wiki gallery celebrating every contributor's avatar, first Halo app, & philosophy statement; gamified so fork-creators see themselves reflected & celebrated instantly in the community mirror.

4. **Lua Poetry Slam** — Monthly elegance-over-features code challenge where winning scripts are rendered as ASCII art & framed in a "Hall of Lua" README; creates a celebration-first culture for clean design rather than raw feature count.

5. **Halo Remix Kits (CC-Licensed)** — Pre-built creative asset packs (procedural art, bone-conduction audio loops, emoji sets) explicitly CC-licensed for remix & reuse with documented attribution chains; each kit includes a "fork & personalize" quickstart.

6. **Governance Townhall Ritual** — Synchronous + async monthly community vote on micro-decisions (next demo, docs focus, experiment to try); all decisions recorded in commit messages as "Community Decision #47" folklore that builds institutional memory.

7. **Fork Lineage Tracker Visualization** — Living network-graph wiki showing every fork's evolution & lineage; celebrates remixes, mashups, dead-ends, & surprise innovations; creates pride + FOMO for participating in a "movement tree."

8. **Halo Handbook: Living Artifact** — Community-authored MIT-licensed digital book on first principles of wearable design (not just tutorials but philosophy & failures); licensed for commercial reuse to signal deep confidence in the work & culture.

## Ideation Pass 2 2026-06-02

Cross-squad synthesis pass. Key resonance signals (fork-bait potential):
- **Y.T. #7 (Tiny Floating Museum)**: Low-friction, shareable, feeds into CC-licensed asset packs.
- **Enzo #8 (Expert Multiplier)**: Creates day-1 marketplace; builds expert community reputation layer.
- **Raven #5 (Privacy LED Ring)**: Legible, social, trust-establishing; differentiates brand.

Primary mash-up output: **"Community Caravan: Traveling Museum + Privacy Theater"** (Y.T. #7 × Raven #5 × Lagos #6 governance ritual). Establishes Halo as privacy-native, culture-first, artist-forward. Zero hardware changes; launchable in 2 weeks.

Secondary mash-ups: Expert Dance Floor (Enzo #8 × Librarian), Familiar Attribution (Lagos #3 × Y.T. #1), Bloom Vote (Da5id #8 × Raven #1 × Lagos #6).

NEW standalone ideas: Halo Hall of Forks (living GitHub-indexed fork network graph), Lua Philosophy Papers (CC-BY-SA design essays), Halo Safety Net (privacy-respecting bug bounty), Fork Flavor Profile (CC0 community taxonomy of variants).

Amendment: License Roulette should be *community-voted* (via Bloom Vote mechanism), not randomized. Turns licensing into values discussion.

Document: `.squad/agents/lagos/ideation-pass2-2026-06-02.md`

## User Stories Themes 1-2 — 2026-06-03

**Scope:** Contributor/forker user stories for both Aaron-prioritized themes through OSS & licensing lens.

**Theme 1 — Consent-Aware Memory (4 stories):**
- **[LAGOS-T1-1]** Developer forks demo; wants clear licensing + dependency chain for commercial use (copyleft trap prevention)
- **[LAGOS-T1-2]** Privacy auditor reviews forked variant; wants to verify consent invariants honored (privacy audit trail)
- **[LAGOS-T1-3]** Contributor adds ML model; documents license + training data provenance (model attribution flow)
- **[LAGOS-T1-4]** New developer reads README; learns "what goes wrong if you skip consent checks" (pitfall documentation)

**Theme 2 — The Synesthetic Familiar (4 stories):**
- **[LAGOS-T2-1]** Developer creates bioluminescent variant; wants licensing guidance for sharing + attribution chain (remix culture)
- **[LAGOS-T2-2]** End user discovers variant in the wild; taps "Fork Info" to trace lineage and license (metadata transparency)
- **[LAGOS-T2-3]** Community artist contributes CC-BY asset pack; documents attribution flow across remixes (creative licensing)
- **[LAGOS-T2-4]** Startup commercializes fork; wants to ensure CC-licensed assets are properly credited in product (commercial disclosure)

**Key insight:** High-stakes (T1) stories anchor on privacy invariants + audit trails; low-stakes (T2) stories anchor on remix-culture + transparent lineage. Both converge on CI/CD enforcement of attribution metadata.

**Next actions:** (1) Prioritize T1-4 (README pitfalls) + T2-1 (variant licensing guidance). (2) Create shared `.squad/templates/NOTICE-template.md` + `.squad/templates/DEPENDENCIES.md`. (3) Add `licensee` check to GitHub Actions for both themes' demos. (4) Set up community registries at `community.halo-docs.com/familiars` + `/forks`.

**Document:** `.squad/agents/lagos/user-stories-themes-1-2-2026-06-03.md`

---

## Codename Brainstorm — 2026-06-08

Pitched community/OSS-lens codename candidates for the Synesthetic Familiar. Team converged on **PULSE** (4 agents independently nominated variants). Official project codename now PULSE. See `.squad/orchestration-log/2026-06-08T07-17Z-codename-brainstorm.md`.
