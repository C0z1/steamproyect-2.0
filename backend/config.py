"""
config.py
=========
Configuración central del proyecto.
Todas las variables de entorno se leen aquí — en ningún otro lugar.
"""

import os
from functools import lru_cache


class Settings:
    # ── IsThereAnyDeal ──────────────────────────────────────────
    itad_api_key: str = os.getenv("ITAD_API_KEY", "")
    itad_base_url: str = os.getenv("ITAD_BASE_URL", "https://api.isthereanydeal.com")
    itad_country: str = os.getenv("ITAD_COUNTRY", "US")
    itad_history_since: str = os.getenv("ITAD_HISTORY_SINCE", "2022-01-01T00:00:00Z")

    # ── DuckDB ──────────────────────────────────────────────────
    duckdb_path: str = os.getenv("DUCKDB_PATH", "./data/steamsense.duckdb")
    duckdb_memory_limit: str = os.getenv("DUCKDB_MEMORY_LIMIT", "512MB")
    duckdb_threads: int = int(os.getenv("DUCKDB_THREADS", "2"))

    # ── API ─────────────────────────────────────────────────────
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")

    # ── Comportamiento ──────────────────────────────────────────
    env: str = os.getenv("ENV", "development")
    top_n_games: int = int(os.getenv("TOP_N_GAMES", "200"))
    request_batch_size: int = int(os.getenv("REQUEST_BATCH_SIZE", "10"))
    request_delay: float = float(os.getenv("REQUEST_DELAY", "0.5"))

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    def __init__(self):
        # Load .env file if it exists
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, val = line.partition("=")
                        os.environ.setdefault(key.strip(), val.strip())
        # Re-read after .env loaded
        self.itad_api_key = os.getenv("ITAD_API_KEY", "")
        self.itad_base_url = os.getenv("ITAD_BASE_URL", "https://api.isthereanydeal.com")
        self.itad_country = os.getenv("ITAD_COUNTRY", "US")
        self.itad_history_since = os.getenv("ITAD_HISTORY_SINCE", "2022-01-01T00:00:00Z")
        self.duckdb_path = os.getenv("DUCKDB_PATH", "./data/steamsense.duckdb")
        self.duckdb_memory_limit = os.getenv("DUCKDB_MEMORY_LIMIT", "512MB")
        self.duckdb_threads = int(os.getenv("DUCKDB_THREADS", "2"))
        self.cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
        self.env = os.getenv("ENV", "development")
        self.top_n_games = int(os.getenv("TOP_N_GAMES", "200"))
        self.request_batch_size = int(os.getenv("REQUEST_BATCH_SIZE", "10"))
        self.request_delay = float(os.getenv("REQUEST_DELAY", "0.5"))


_settings = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
