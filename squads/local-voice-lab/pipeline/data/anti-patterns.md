# Anti-Patterns: Local Voice Assistant Lab

## Engineering Mistakes
- **Cloud Dependency:** Integrating an API key for OpenAI or ElevenLabs "just for testing". (Violates Locality principle).
- **Thread Blocking:** Running STT or TTS on the main loop, causing the whole system to hang while processing.
- **VRAM Competition:** Loading a 70B model while Whisper is trying to run on the same GPU without enough memory.
- **Complex Abstractions:** Creating a "VoicePluginManager" before having a single voice engine working. (Overengineering).

## Governance Mistakes
- **Strategic Drift:** Specialist agents proposing new product features instead of executing the technical task.
- **Domain Crossing:** The Voice agent modifying the LLM prompt to "help" the response quality.
- **Alternative Overload:** Presenting 3 different ways to implement a class. (Violates Linearity principle).
- **Implicit Knowledge:** Relying on global variables instead of explicit parameters between modules.

## Communication Mistakes
- **Theoretical Verbosity:** Explaining the history of Transformers when asked to fix a bug in a Python script.
- **Repetitive Reporting:** Restating the goal 3 times before showing the result.
- **Non-Actionable Feedback:** Saying "the audio is bad" without measuring latency or providing logs.
