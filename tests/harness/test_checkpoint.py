import pytest
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from harness.checkpoint import make_async_saver, make_sync_saver


def test_make_sync_saver_returns_sqlite_saver(tmp_path):
    saver = make_sync_saver(tmp_path / "cp.db")
    assert isinstance(saver, SqliteSaver)


def test_make_sync_saver_accepts_string_path(tmp_path):
    saver = make_sync_saver(str(tmp_path / "cp.db"))
    assert isinstance(saver, SqliteSaver)


@pytest.mark.anyio
async def test_make_async_saver_returns_async_sqlite_saver(tmp_path):
    async with make_async_saver(tmp_path / "cp.db") as saver:
        assert isinstance(saver, AsyncSqliteSaver)
