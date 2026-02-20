"""
src/db/connection.py
====================
Singleton thread-safe para la conexión DuckDB.
Un solo archivo .duckdb, una sola conexión.
"""

import logging
import os
from typing import Optional

import duckdb

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_connection: Optional[duckdb.DuckDBPyConnection] = None


def get_db() -> duckdb.DuckDBPyConnection:
    """Retorna la conexión activa. Lanza RuntimeError si no está inicializada."""
    if _connection is None:
        raise RuntimeError("DuckDB no inicializado. Llama a init_db() primero.")
    return _connection


def init_db() -> duckdb.DuckDBPyConnection:
    """
    Inicializa la conexión DuckDB.
    Crea el directorio y el archivo si no existen.
    """
    global _connection

    db_path = settings.duckdb_path
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    logger.info(f"Conectando a DuckDB en: {db_path}")

    _connection = duckdb.connect(
        db_path,
        config={
            "memory_limit": settings.duckdb_memory_limit,
            "threads": settings.duckdb_threads,
        }
    )

    logger.info("DuckDB conectado correctamente")
    return _connection


def close_db():
    """Cierra la conexión limpiamente."""
    global _connection
    if _connection:
        _connection.close()
        _connection = None
        logger.info("DuckDB desconectado")
