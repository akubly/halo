# Orchestration Log — Round A: GitHub Survey

**Agent:** librarian-1 (AI/ML)  
**Timestamp:** 2026-06-02T07:00Z (UTC)  
**Round:** A (GitHub survey)  
**Task:** Validate "only Gemini ships" hypothesis against GitHub empirical data

**Outcome:** ✅ COMPLETED  
**Artifact:** `.squad/agents/librarian/github-ai-on-halo-2026-06-02.md`  
**Decision Filed:** `.squad/decisions/inbox/librarian-gemini-validated.md` (merged to decisions.md)

**Summary:**
- Analyzed 13 public repos with identifiable AI model choice on Brilliant hardware
- **Finding:** Gemini dominates 92% (12/13); no Claude/GPT-4o/Whisper in production code
- Canonical pattern: `frame_realtime_gemini_voicevision` (80★, official)
- **Root cause:** Gemini Live API is only major LLM with true multimodal streaming
- Claude/GPT-4o request-reply only (higher latency perceived)
- Community inertia favors reference implementation

**Confidence:** Increased from HIGH to VERY HIGH  
**Implication:** Halo will likely follow same pattern; recommend Gemini for Playground MVP.
