"""Conversão algorítmica de blocos extraídos para Markdown — sem chamada externa."""
from typing import List

from utils import normalize_text


def _format_inline(text: str, bold: bool, italic: bool) -> str:
    """Aplica negrito/itálico Markdown ao texto se flags ativas."""
    text = text.strip()
    if not text:
        return ""
    if bold and italic:
        return f"***{text}***"
    if bold:
        return f"**{text}**"
    if italic:
        return f"*{text}*"
    return text


def _table_to_markdown(rows: List[List[str]]) -> str:
    """Converte matriz de células para tabela Markdown padrão."""
    if not rows:
        return ""
    # Normaliza nº de colunas
    width = max(len(r) for r in rows)
    norm = [r + [""] * (width - len(r)) for r in rows]
    header = norm[0]
    body = norm[1:]

    def esc(cell: str) -> str:
        return cell.replace("|", "\\|").strip()

    out = []
    out.append("| " + " | ".join(esc(c) for c in header) + " |")
    out.append("| " + " | ".join("---" for _ in header) + " |")
    for row in body:
        out.append("| " + " | ".join(esc(c) for c in row) + " |")
    return "\n".join(out)


def convert_local(blocks: List[dict]) -> str:
    """
    Converte blocos para Markdown usando heurísticas locais.
    Não consulta API. Aplica negrito, itálico, headings, listas, tabelas.
    """
    out_parts: List[str] = []
    prev_kind = None

    for block in blocks:
        kind = block.get("kind")

        if kind == "heading":
            level = max(1, min(3, block.get("level", 1)))
            text = normalize_text(block.get("text", ""))
            if not text:
                continue
            out_parts.append(f"{'#' * level} {text}")
            prev_kind = "heading"

        elif kind == "list_item":
            marker = block.get("marker") or "-"
            text = normalize_text(block.get("text", ""))
            if not text:
                continue
            text = _format_inline(text, block.get("bold", False), block.get("italic", False))
            out_parts.append(f"{marker} {text}")
            prev_kind = "list_item"

        elif kind == "table":
            rows = block.get("table_rows", [])
            md_table = _table_to_markdown(rows)
            if md_table:
                out_parts.append(md_table)
            prev_kind = "table"

        elif kind == "paragraph":
            text = normalize_text(block.get("text", ""))
            if not text:
                continue
            text = _format_inline(text, block.get("bold", False), block.get("italic", False))
            out_parts.append(text)
            prev_kind = "paragraph"

    # Junta parágrafos com linha em branco; itens de lista consecutivos sem linha extra
    result_lines: List[str] = []
    last_was_list = False
    for part in out_parts:
        is_list = part.lstrip().startswith(("- ", "* ", "1. "))
        if result_lines:
            if is_list and last_was_list:
                result_lines.append(part)
            else:
                result_lines.append("")
                result_lines.append(part)
        else:
            result_lines.append(part)
        last_was_list = is_list

    return "\n".join(result_lines).strip() + "\n"
