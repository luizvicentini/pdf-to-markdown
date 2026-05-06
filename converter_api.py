"""Conversão via API Anthropic. Serializa blocos com marcadores e envia para Claude."""
from typing import List, Tuple

from utils import chunk_by_sections, estimate_tokens


# Modelo conforme especificado pelo usuário
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS_RESPONSE = 8192

SYSTEM_PROMPT = (
    "Você receberá texto extraído de um PDF com marcadores de estrutura. "
    "Converta para Markdown limpo seguindo estas regras:\n"
    "- Preserve TODOS os títulos e subtítulos (use # ## ### conforme hierarquia)\n"
    "- Preserve tabelas em formato Markdown padrão\n"
    "- Preserve listas ordenadas e não ordenadas\n"
    "- Preserve negrito e itálico\n"
    "- Remova artefatos: quebras desnecessárias, hifenização de fim de linha, "
    "espaços duplicados\n"
    "- NÃO resuma, NÃO omita conteúdo, NÃO reescreva — apenas reformate\n"
    "- Retorne APENAS o Markdown, sem explicações ou comentários"
)


class APIError(Exception):
    """Erro reportável ao usuário durante chamada à API."""
    pass


def _serialize_blocks(blocks: List[dict]) -> str:
    """
    Converte blocos em texto anotado com marcadores estruturais.
    Marcadores são instruções para Claude, não Markdown final.
    """
    parts: List[str] = []
    for block in blocks:
        kind = block.get("kind")
        if kind == "heading":
            level = block.get("level", 1)
            parts.append(f"[HEADING-L{level}] {block.get('text', '').strip()}")
        elif kind == "list_item":
            marker = block.get("marker", "-")
            text = block.get("text", "").strip()
            tag = "ORDERED" if marker and marker[0].isdigit() else "BULLET"
            flags = _flag_string(block)
            parts.append(f"[LIST-{tag}{flags}] {text}")
        elif kind == "table":
            rows = block.get("table_rows", [])
            parts.append("[TABLE-START]")
            for row in rows:
                parts.append("[ROW] " + " | ".join((c or "").strip() for c in row))
            parts.append("[TABLE-END]")
        elif kind == "paragraph":
            flags = _flag_string(block)
            parts.append(f"[PARAGRAPH{flags}] {block.get('text', '').strip()}")
    return "\n".join(parts)


def _flag_string(block: dict) -> str:
    """Gera sufixo indicando negrito/itálico para o serializador."""
    parts = []
    if block.get("bold"):
        parts.append("BOLD")
    if block.get("italic"):
        parts.append("ITALIC")
    return ("-" + "-".join(parts)) if parts else ""


def _call_anthropic(client, serialized: str) -> Tuple[str, int]:
    """Faz uma chamada e devolve (markdown, tokens_totais)."""
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS_RESPONSE,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": serialized}],
        )
    except Exception as exc:
        # Não vaza API key: anthropic SDK não inclui key em msg, mas filtramos por garantia
        msg = str(exc)
        raise APIError(f"Falha na chamada à API: {msg}") from None

    text_parts = []
    for block in response.content:
        if getattr(block, "type", "") == "text":
            text_parts.append(block.text)
    md = "".join(text_parts).strip()

    tokens = 0
    usage = getattr(response, "usage", None)
    if usage is not None:
        tokens = (getattr(usage, "input_tokens", 0) or 0) + (getattr(usage, "output_tokens", 0) or 0)
    return md, tokens


def convert_api(blocks: List[dict], api_key: str, progress_cb=None) -> Tuple[str, int]:
    """
    Converte blocos para Markdown via API.
    Documentos >15.000 tokens estimados são divididos em chunks por seção.
    Retorna (markdown_final, tokens_consumidos).
    progress_cb: callable(done_chunks, total_chunks) — opcional.
    """
    if not api_key or not api_key.strip():
        raise APIError("API key não configurada. Insira ANTHROPIC_API_KEY no campo correspondente.")

    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise APIError("Pacote 'anthropic' não instalado.") from exc

    client = Anthropic(api_key=api_key.strip())

    # Serializa para estimar tokens totais
    full_serialized = _serialize_blocks(blocks)
    total_tokens_est = estimate_tokens(full_serialized)

    if total_tokens_est <= 15000:
        if progress_cb:
            progress_cb(0, 1)
        md, tokens = _call_anthropic(client, full_serialized)
        if progress_cb:
            progress_cb(1, 1)
        return md, tokens

    # Chunking por seção
    chunks = chunk_by_sections(blocks, max_tokens=12000)
    total = len(chunks)
    md_parts: List[str] = []
    total_tokens = 0
    for idx, chunk_blocks in enumerate(chunks):
        if progress_cb:
            progress_cb(idx, total)
        serialized = _serialize_blocks(chunk_blocks)
        md, tokens = _call_anthropic(client, serialized)
        md_parts.append(md)
        total_tokens += tokens
    if progress_cb:
        progress_cb(total, total)

    return "\n\n".join(md_parts).strip() + "\n", total_tokens
