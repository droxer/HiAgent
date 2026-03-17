"""Tests for persistent memory tools (backward compatibility)."""

from __future__ import annotations

import json

from agent.tools.local.memory_store import MemoryStore
from agent.tools.local.memory_recall import MemoryRecall
from agent.tools.local.memory_list import MemoryList


class TestMemoryStoreBackcompat:
    """Verify backward compatibility with dict-only constructor."""

    async def test_dict_only(self) -> None:
        store: dict[str, str] = {}
        tool = MemoryStore(store=store)
        result = await tool.execute(key="k", value="v")
        assert result.success
        assert store["default:k"] == "v"

    async def test_with_none_persistent(self) -> None:
        store: dict[str, str] = {}
        tool = MemoryStore(store=store, persistent_store=None)
        result = await tool.execute(key="k", value="v")
        assert result.success

    async def test_empty_key_fails(self) -> None:
        tool = MemoryStore(store={})
        result = await tool.execute(key="", value="v")
        assert not result.success

    async def test_empty_value_fails(self) -> None:
        tool = MemoryStore(store={})
        result = await tool.execute(key="k", value="")
        assert not result.success

    async def test_namespace(self) -> None:
        store: dict[str, str] = {}
        tool = MemoryStore(store=store)
        await tool.execute(key="k", value="v", namespace="ns")
        assert "ns:k" in store


class TestMemoryRecallBackcompat:
    async def test_dict_only(self) -> None:
        store = {"default:hello": "world"}
        tool = MemoryRecall(store=store)
        result = await tool.execute(query="hello")
        assert result.success
        data = json.loads(result.output)
        assert "default:hello" in data

    async def test_empty_query_fails(self) -> None:
        tool = MemoryRecall(store={})
        result = await tool.execute(query="")
        assert not result.success

    async def test_no_matches(self) -> None:
        tool = MemoryRecall(store={"default:a": "b"})
        result = await tool.execute(query="xyz")
        assert result.success
        data = json.loads(result.output)
        assert len(data) == 0


class TestMemoryList:
    async def test_empty(self) -> None:
        tool = MemoryList(store={})
        result = await tool.execute()
        assert result.success
        assert result.metadata["count"] == 0

    async def test_list_entries(self) -> None:
        store = {"default:a": "1", "default:b": "2", "other:c": "3"}
        tool = MemoryList(store=store)
        result = await tool.execute(namespace="default")
        assert result.success
        data = json.loads(result.output)
        assert len(data) == 2
