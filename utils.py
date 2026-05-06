"""Funções auxiliares: normalização de texto, chunking por seção, estimativa de tokens."""
import re
from typing import List


# Regex usados em normalização
RE_HYPHEN_LINEBREAK = re.compile(r"-\n(?=\w)")     # "exem-\nplo" -> "exemplo"
RE_MULTI_SPACE = re.compile(r"[ \t]{2,}")
RE_MULTI_NEWLINE = re.compile(r"\n{3,}")
RE_TRAILING_WS = re.compile(r"[ \t]+\n")


def normalize_text(text: str) -> str:
    """Remove hifenização de fim de linha, espaços duplicados e quebras espúrias."""
    if not text:
        return ""
    text = RE_HYPHEN_LINEBREAK.sub("", text)
    text = RE_TRAILING_WS.sub("\n", text)
    text = RE_MULTI_SPACE.sub(" ", text)
    text = RE_MULTI_NEWLINE.sub("\n\n", text)
    return text.strip()


def estimate_tokens(text: str) -> int:
    """Estimativa grosseira de tokens. ~4 caracteres por token (heurística Anthropic)."""
    return max(1, len(text) // 4)


def chunk_by_sections(blocks: List[dict], max_tokens: int = 12000) -> List[List[dict]]:
    """
    Divide lista de blocos em chunks respeitando limites de seção.
    Quebra preferencial em blocos do tipo 'heading'. Cada chunk fica abaixo de max_tokens.
    """
    chunks: List[List[dict]] = []
    current: List[dict] = []
    current_tokens = 0

    for block in blocks:
        block_text = block.get("text", "")
        block_tokens = estimate_tokens(block_text)
        is_heading = block.get("kind") == "heading"

        # Se chunk cheio e bloco é heading, quebra aqui
        if current and is_heading and current_tokens + block_tokens > max_tokens:
            chunks.append(current)
            current = []
            current_tokens = 0

        # Se um único bloco já estoura, força fechar
        if current_tokens + block_tokens > max_tokens and current:
            chunks.append(current)
            current = []
            current_tokens = 0

        current.append(block)
        current_tokens += block_tokens

    if current:
        chunks.append(current)
    return chunks


def sanitize_for_log(message: str, api_key: str = "") -> str:
    """Remove API key de qualquer string antes de logar."""
    if not api_key:
        return message
    return message.replace(api_key, "[REDACTED]")
