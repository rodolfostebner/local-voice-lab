# Research Brief: Local Voice Assistant & Multi-Agent Governance

## Frameworks & Methodologies
- **Sequential Pipeline Orchestration:** Decoupled STT -> LLM -> TTS services.
- **Hierarchical Agent Governance:** Supervisor (Executive Lead) -> Specialized Workers.
- **Modular Evolution:** Building functionality in layers (Core -> Voice -> Logic -> Integrations).

## Output Examples (Architecture Patterns)
- **FastAPI/Wyoming Protocol wrappers** for local model serving.
- **Streaming Handlers** to bridge Ollama output to Piper input without full sentence wait times.
- **JSON Tool Manifests** for structured interaction between agents and local environment.

## Common Mistakes (Anti-Patterns)
- **Monolithic Bloat:** Coupling the STT, LLM, and TTS in a single script.
- **Cold-Start Delays:** Forgetting to keep models resident in VRAM.
- **Governance Chaos:** Allowing specialist agents to modify core orchestrator logic without oversight.
- **TTS Fragmentation:** Sending overly long or markdown-heavy strings to TTS engines.

## Quality Benchmarks
- **Latency:** Target < 1s for STT transcription and < 500ms for first-token TTS.
- **Accuracy:** Word Error Rate (WER) < 10% for transcription.
- **Relevance:** LLM responses tailored for voice (concise, no emojis).

## Domain Vocabulary
- **STT:** Speech-to-Text (Transcription).
- **TTS:** Text-to-Speech (Synthesis).
- **Inference:** The process of running a model to get an output.
- **VRAM:** Video RAM (essential for GPU acceleration).
- **Quantization:** Reducing model size/precision for faster local execution.
- **Wake Word:** Trigger phrase to activate the system.
- **Orchestrator:** The central logic controlling the data flow.
