# Operational Framework: Local AI Voice Assistant Development

## Step-by-Step Methodology

1. **Milestone Goal Refinement**
   - Interpret user objective.
   - Analyze existing code and Git state.
   - Define a single, linear technical path.
   - *Outcome:* Milestone Definition Document.

2. **Technical Design & Prototyping**
   - Map dependencies (Whisper, Ollama, Piper).
   - Design modular interfaces for the new feature.
   - Validate commands via local CLI.
   - *Outcome:* Technical Design Spec.

3. **Incremental Implementation**
   - Write/update code in small, testable chunks.
   - Use local models for validation.
   - Maintain strict separation of concerns (Voz vs LLM).
   - *Outcome:* Pull Request / Code Update.

4. **Local Integration Testing**
   - Run end-to-end local test (Mic -> STT -> LLM -> TTS -> Speaker).
   - Measure latency and memory usage.
   - *Outcome:* Test Report.

5. **Governance & Quality Review**
   - Audit code for modularity breaches.
   - Verify no "strategic drift" (changes outside scope).
   - *Outcome:* Governance Verdict.

6. **User Validation**
   - Present result for feedback.
   - Confirm milestone completion.
   - *Outcome:* Approved Milestone.

## Decision Criteria
- **When to stop implementing:** Once the specific milestone goal is reached. Do not "fix" unrelated files unless critical for the milestone.
- **When to escalate:** If local VRAM/CPU constraints make the proposed solution non-viable.
- **When to modularize:** If a function exceeds 50 lines or handles two different domains (e.g., parsing LLM output AND playing audio).
