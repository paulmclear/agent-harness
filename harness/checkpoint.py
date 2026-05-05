from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import aiosqlite
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


def make_sync_saver(db_path: str | Path) -> SqliteSaver:
    """Create a synchronous SQLite checkpoint saver.

    Args:
        db_path: Path to the SQLite database file (string or Path object).

    Returns:
        SqliteSaver: A configured synchronous checkpoint saver.
    """
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    saver = SqliteSaver(conn=conn)
    saver.setup()
    return saver


async def _make_async_saver_impl(db_path: str | Path) -> AsyncSqliteSaver:
    """Internal async implementation for creating an async saver."""
    conn = await aiosqlite.connect(str(db_path))
    saver = AsyncSqliteSaver(conn)
    await saver.setup()
    return saver


def make_async_saver(db_path: str | Path) -> AsyncSqliteSaver:
    """Create an asynchronous SQLite checkpoint saver.

    Args:
        db_path: Path to the SQLite database file (string or Path object).

    Returns:
        AsyncSqliteSaver: A configured asynchronous checkpoint saver.
    """
    return asyncio.run(_make_async_saver_impl(db_path))
