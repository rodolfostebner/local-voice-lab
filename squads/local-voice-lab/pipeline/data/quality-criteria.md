# Quality Criteria: Local Voice Assistant Lab

## Technical Benchmarks
- **Local Sovereignty:** 100% of execution must happen locally. No external API calls allowed without explicit user permission.
- **Modularity:** Each component (STT, LLM, TTS) must be swappable. No hard-coded logic between domains.
- **Latency:**
  - Transcription (STT): < 1.0s for short phrases.
  - LLM Time-to-First-Token: < 500ms.
  - TTS Synthesis Start: < 400ms.
- **Memory Efficiency:** System must stay within the user's notebook VRAM limits (Ollama + Whisper concurrent).

## Governance Standards
- **Restrictive Access:** Specialist agents only modify files within their domain.
- **Linearity:** One objective per milestone. No feature creep.
- **Pragmatism:** Code must be debuggable and documented minimally but effectively.

## Evaluation Rubric (1-10)
| Criterion | 1-4 (Reject) | 5-7 (Needs Work) | 8-10 (Pass) |
|---|---|---|---|
| **Modularity** | Monolithic code. | Some coupling between layers. | Clean, decoupled interfaces. |
| **Locality** | Uses cloud APIs. | Local but depends on heavy blobs. | Optimized local execution. |
| **Simplicity** | Overengineered abstractions. | Moderate complexity. | Simplest code that works. |
| **Governance** | Unclear responsibilities. | Specialist drift identified. | Perfect role isolation. |
