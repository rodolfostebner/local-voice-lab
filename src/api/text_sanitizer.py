"""
Text Sanitizer — Limpeza de texto para TTS.

Remove formatação markdown, emojis, listas numeradas e caracteres
que causam artefatos na síntese de voz. O texto original é preservado
no chat; apenas o TTS recebe a versão sanitizada.
"""
import re
import unicodedata


def sanitize_for_tts(text: str) -> str:
    """
    Converte texto formatado (markdown/LLM output) em texto limpo
    otimizado para síntese de voz natural.
    """
    t = text

    # Remove blocos de código
    t = re.sub(r'```[\s\S]*?```', '', t)
    t = re.sub(r'`([^`]+)`', r'\1', t)

    # Remove headers markdown
    t = re.sub(r'^#{1,6}\s+', '', t, flags=re.MULTILINE)

    # Remove bold/italic
    t = re.sub(r'\*\*([^*]+)\*\*', r'\1', t)
    t = re.sub(r'\*([^*]+)\*', r'\1', t)
    t = re.sub(r'__([^_]+)__', r'\1', t)
    t = re.sub(r'_([^_]+)_', r'\1', t)

    # Remove listas com marcadores (* - •)
    t = re.sub(r'^\s*[\*\-•]\s+', '', t, flags=re.MULTILINE)

    # Remove listas numeradas (1. 2. etc) — mantém o texto após o número
    t = re.sub(r'^\s*\d+\.\s+', '', t, flags=re.MULTILINE)

    # Remove emojis comuns
    t = re.sub(
        r'[\U0001F600-\U0001F64F'   # emoticons
        r'\U0001F300-\U0001F5FF'     # symbols & pictographs
        r'\U0001F680-\U0001F6FF'     # transport & map
        r'\U0001F1E0-\U0001F1FF'     # flags
        r'\U00002702-\U000027B0'     # dingbats
        r'\U0000FE00-\U0000FE0F'     # variation selectors
        r'\U0001FA00-\U0001FA6F'     # chess symbols
        r'\U0001FA70-\U0001FAFF'     # symbols extended
        r'\U00002600-\U000026FF'     # misc symbols
        r']+', '', t
    )

    # Remove links markdown [text](url) → text
    t = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', t)

    # Normaliza aspas e hífens complexos
    t = t.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    t = t.replace('—', '-').replace('–', '-')

    # Normaliza unicode para caracteres pré-compostos (NFC)
    t = unicodedata.normalize('NFC', t)
    
    # Remove qualquer marca diacrítica combinante (como til solto) que não compôs um caractere válido
    t = re.sub(r'[\u0300-\u036f]', '', t)

    # Remove asteriscos residuais e outros símbolos que quebram phoneme map
    t = re.sub(r'[*#@~|^\\_<>]', '', t)

    # Remove URLs soltas
    t = re.sub(r'https?://\S+', '', t)

    # Remove linhas vazias múltiplas → uma pausa natural
    t = re.sub(r'\n{3,}', '\n\n', t)

    # Remove espaços extras
    t = re.sub(r'  +', ' ', t)

    # Trim
    t = t.strip()

    return t
