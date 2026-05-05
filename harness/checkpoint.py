from __future__ import annotations

import sqlite3
from contextlib import AbstractAsyncContextManager
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


def make_sync_saver(db_path: str | Path) -> SqliteSaver:
    """Return a ready-to-use synchronous LangGraph SQLite checkpointer.

    Opens a persistent connection suitable for single-process CLI use.
    """
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    saver = SqliteSaver(conn=conn)
    saver.setup()
    return saver


def make_async_saver(db_path: str | Path) -> AbstractAsyncContextManager[AsyncSqliteSaver]:
    """Return an async context manager that yields an AsyncSqliteSaver.

    Use as::

        async with make_async_saver(db_path) as saver:
            graph = build_graph(checkpointer=saver)

    The caller's event loop drives connection setup and teardown, making
    this safe in FastAPI and any other async context.
    """
    return AsyncSqliteSaver.from_conn_string(str(db_path))
