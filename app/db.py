"""
Database helpers for SQLite with a compatibility shim.

Exports:
- get_db(): async context manager yielding a connection-like wrapper
- get_db_dep(): FastAPI dependency yielding the same wrapper

The wrapper adapts common asyncpg-style calls used in this codebase to
SQLite via aiosqlite by:
- Translating $1, $2... placeholders to ?
- Removing PostgreSQL-specific casts like ::jsonb
- Converting dict parameters to JSON strings
- Returning dict rows (supporting .get and [key])
"""

import os
import re
import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, List, Dict, Any

import aiosqlite

from app.utils.logging import get_logger

logger = get_logger(__name__)


def _sqlite_path_from_env() -> str:
    url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_PATH")
    if url and url.startswith("sqlite"):  # e.g., sqlite+aiosqlite:///data/reality_checker.db
        # Strip driver and scheme
        # Accept forms: sqlite+aiosqlite:///path or sqlite:///path
        parts = url.split("///", 1)
        if len(parts) == 2:
            return parts[1]
    if url and not url.startswith("sqlite"):
        # Unexpected URL type; fall back to default path to honor user's request for SQLite
        logger.warning(f"Ignoring non-sqlite DATABASE_URL for SQLite mode: {url}")
    # Default path
    return os.getenv("DATABASE_PATH", "data/reality_checker.db")


def _translate_sql(sql: str) -> str:
    # Replace $1, $2, ... with ? for SQLite
    sql = re.sub(r"\$(\d+)", "?", sql)
    # Remove ::jsonb casts
    sql = re.sub(r"::jsonb", "", sql, flags=re.IGNORECASE)
    return sql


def _prepare_params(params: List[Any]) -> List[Any]:
    prepped: List[Any] = []
    for p in params:
        if isinstance(p, (dict, list)):
            prepped.append(json.dumps(p))
        else:
            prepped.append(p)
    return prepped


async def _ensure_schema(conn: aiosqlite.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL CHECK (source IN ('web_upload','whatsapp')),
            score REAL,
            verdict TEXT,
            details_json TEXT,
            file_name TEXT,
            message_sid TEXT,
            phone_number TEXT,
            user_id TEXT,
            session_id TEXT,
            correlation_id TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """
    )
    # Helpful indexes
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_results_created_at_desc ON analysis_results (created_at DESC)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_results_source ON analysis_results (source)")
    await conn.commit()


class SqliteCompatConnection:
    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn

    async def fetch(self, sql: str, *params: Any) -> List[Dict[str, Any]]:
        sql_t = _translate_sql(sql)
        ps = _prepare_params(list(params))
        cur = await self._conn.execute(sql_t, ps)
        rows = await cur.fetchall()
        await cur.close()
        # aiosqlite.Row -> dict and JSON decode for details_json
        out: List[Dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            if "details_json" in d and isinstance(d["details_json"], str):
                try:
                    d["details_json"] = json.loads(d["details_json"]) if d["details_json"] else {}
                except Exception:
                    pass
            out.append(d)
        return out

    async def fetchrow(self, sql: str, *params: Any) -> Optional[Dict[str, Any]]:
        sql_upper = sql.upper()
        # Handle INSERT ... RETURNING id for SQLite by emulation if needed
        if "INSERT" in sql_upper and "RETURNING" in sql_upper:
            # Remove RETURNING clause and use lastrowid
            sql_no_returning = re.sub(r"\s+RETURNING\s+.+$", "", sql, flags=re.IGNORECASE | re.DOTALL)
            sql_t = _translate_sql(sql_no_returning)
            ps = _prepare_params(list(params))
            cur = await self._conn.execute(sql_t, ps)
            last_id = cur.lastrowid
            await self._conn.commit()
            await cur.close()
            return {"id": last_id}

        sql_t = _translate_sql(sql)
        ps = _prepare_params(list(params))
        cur = await self._conn.execute(sql_t, ps)
        row = await cur.fetchone()
        await cur.close()
        if row is None:
            return None
        d = dict(row)
        if "details_json" in d and isinstance(d["details_json"], str):
            try:
                d["details_json"] = json.loads(d["details_json"]) if d["details_json"] else {}
            except Exception:
                pass
        return d

    async def execute(self, sql: str, *params: Any) -> None:
        sql_t = _translate_sql(sql)
        ps = _prepare_params(list(params))
        await self._conn.execute(sql_t, ps)
        await self._conn.commit()

    # Provide context manager compatibility if someone uses `async with conn:`
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        # Underlying connection is managed by outer context manager
        return False


@asynccontextmanager
async def get_db() -> AsyncGenerator[SqliteCompatConnection, None]:
    db_path = _sqlite_path_from_env()
    dir_name = os.path.dirname(db_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        # Pragmas for better performance
        try:
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.execute("PRAGMA synchronous=NORMAL")
        except Exception:
            pass
        await _ensure_schema(conn)
        yield SqliteCompatConnection(conn)


async def get_db_dep() -> AsyncGenerator[SqliteCompatConnection, None]:
    async with get_db() as conn:
        yield conn
