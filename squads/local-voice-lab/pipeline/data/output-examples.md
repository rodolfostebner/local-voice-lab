# Output Examples: Local Voice Assistant Lab

## Example 1: Milestone Definition (Eduardo Executivo)
**Objective:** Add local TTS output using Piper.
**Current State:** LLM generates text but it only prints to console.
**Linear Path:** Implement a `VoiceOutput` class in `src/audio/tts.py` that calls the Piper CLI.
**Task for Vitor Voz:** Create the `VoiceOutput` class and verify Piper execution with a sample WAV.
**Task for Mateus Modelos:** Add a `speak()` method to the main orchestrator that passes LLM output to `VoiceOutput`.

## Example 2: Implementation Report (Vitor Voz)
**Task:** Configure Piper TTS for streaming.
**Status:** Completed.
**Changes:**
- Added `piper_stream.py` to `src/audio/`.
- Configured voice `en_US-lessac-medium`.
**Metrics:**
- First token latency: 280ms.
- Local command used: `echo "Hello" | piper --model voice.onnx --output_raw | aplay`.
**Validation:** Tested with short and long sentences. Audio quality is clear and streaming works without lag.

## Example 3: Governance Review (Rebeca Revisao)
**Review of:** Milestone #3 - Whisper Integration.
**Veredito:** APPROVE.
**Justification:** O código de Vitor Voz está restrito ao diretório `src/stt/`. Nenhuma alteração foi feita na lógica central de decisão do LLM. O acoplamento é feito via uma interface de callback limpa.
**Note:** A latência está em 1.2s, ligeiramente acima do benchmark, mas aceitável para esta fase do MVP.
