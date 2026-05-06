"""Leitura e gravação de config.json. Persiste último modo e API key."""
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"

DEFAULT_CONFIG = {
    "mode": "local",        # "local" ou "api"
    "api_key": "",          # ANTHROPIC_API_KEY
}


def load_config() -> dict:
    """Carrega config.json. Retorna defaults se arquivo não existir ou estiver corrompido."""
    if not CONFIG_PATH.exists():
        return dict(DEFAULT_CONFIG)
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        # Garante chaves obrigatórias
        merged = dict(DEFAULT_CONFIG)
        merged.update({k: v for k, v in data.items() if k in DEFAULT_CONFIG})
        return merged
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_CONFIG)


def save_config(cfg: dict) -> None:
    """Grava config.json. Falha silenciosa em caso de erro de escrita."""
    try:
        with CONFIG_PATH.open("w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except OSError:
        pass
