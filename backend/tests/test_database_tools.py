"""Tests for SQLite database tools."""

from __future__ import annotations

from agent.tools.base import ExecutionContext
from agent.tools.sandbox.database import DbCreate, DbQuery, DbSchema


class TestDbCreate:
    def test_definition(self) -> None:
        tool = DbCreate()
        defn = tool.definition()
        assert defn.name == "database_create"
        assert defn.execution_context == ExecutionContext.SANDBOX
        assert "database" in defn.tags or "sqlite" in defn.tags


class TestDbQuery:
    def test_definition(self) -> None:
        tool = DbQuery()
        defn = tool.definition()
        assert defn.name == "database_query"
        assert "sql" in defn.input_schema["required"]

    async def test_empty_sql_fails(self) -> None:
        tool = DbQuery()
        result = await tool.execute(session=None, sql="")
        assert not result.success
        assert "empty" in result.error.lower()


class TestDbSchema:
    def test_definition(self) -> None:
        tool = DbSchema()
        defn = tool.definition()
        assert defn.name == "database_schema"
        assert defn.execution_context == ExecutionContext.SANDBOX
