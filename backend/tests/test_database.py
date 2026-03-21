"""Tests for database module."""

import pytest

from agent.state.database import get_engine, get_session_factory

from .conftest import TEST_DB_URL


def test_get_engine_returns_async_engine() -> None:
    from sqlalchemy.ext.asyncio import AsyncEngine

    engine = get_engine(TEST_DB_URL)
    assert isinstance(engine, AsyncEngine)


def test_get_session_factory_returns_callable() -> None:
    engine = get_engine(TEST_DB_URL)
    factory = get_session_factory(engine)
    assert callable(factory)


def test_get_engine_invalid_url_raises() -> None:
    with pytest.raises(Exception):
        get_engine("")
