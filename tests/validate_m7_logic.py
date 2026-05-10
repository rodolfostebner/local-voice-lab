
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.text_sanitizer import sanitize_for_tts
from src.api.main import chunk_for_tts, MIN_CHUNK_CHARS, MAX_CHUNK_CHARS

def test_sanitizer_complex_markdown():
    print("\n--- Testing Sanitizer with Complex Markdown ---")
    complex_text = """
# Header 1
Aqui está uma lista:
* Item 1 com **negrito**
* Item 2 com *itálico* e `código`
* [Link para Google](https://google.com)

1. Passo um
2. Passo dois

```python
print("Isso deve ser removido")
```

Emojis: 🚀🔥😊
Longo link: https://verylonglink.com/path?query=123
    """
    sanitized = sanitize_for_tts(complex_text)
    print(f"Original length: {len(complex_text)}")
    print(f"Sanitized length: {len(sanitized)}")
    print("--- Sanitized Output ---")
    print(sanitized)
    print("------------------------")
    
    # Assertions
    assert "# Header" not in sanitized
    assert "**negrito**" not in sanitized
    assert "negrito" in sanitized
    assert "print(\"Isso deve ser removido\")" not in sanitized
    assert "🚀" not in sanitized
    assert "https://google.com" not in sanitized
    assert "Link para Google" in sanitized
    print("DONE Sanitizer test passed!")

def test_natural_chunking():
    print("\n--- Testing Natural Chunking ---")
    text = "Esta é uma frase curta. E esta é outra frase um pouco mais longa que deve ser mantida junto com a anterior se for muito pequena. " \
           "Aqui temos uma frase extremamente longa que ultrapassa o limite máximo de caracteres definido para o chunking para testar se o sistema consegue dividir corretamente em pontos de pausa naturais sem quebrar a fluidez da fala do assistente de voz."
    
    chunks = chunk_for_tts(text)
    print(f"Number of chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1} ({len(chunk)} chars): {chunk}")
        assert len(chunk) <= MAX_CHUNK_CHARS + 50 # Allow some buffer
        if i < len(chunks) - 1:
            assert len(chunk) >= MIN_CHUNK_CHARS
            
    print("DONE Chunking test passed!")

if __name__ == "__main__":
    try:
        test_sanitizer_complex_markdown()
        test_natural_chunking()
        print("\nAll backend logic validations passed!")
    except AssertionError as e:
        print(f"\nFAILED Validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nFAILED An error occurred: {e}")
        sys.exit(1)
