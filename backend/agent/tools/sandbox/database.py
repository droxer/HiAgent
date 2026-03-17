"""SQLite database tools for creating, querying, and inspecting databases in the sandbox."""

from __future__ import annotations

import json
from typing import Any

from agent.tools.base import (
    ExecutionContext,
    SandboxTool,
    ToolDefinition,
    ToolResult,
)

_SCRIPT_PATH = "/tmp/_db_script.py"
_CONFIG_PATH = "/tmp/_db_config.json"

_MAX_ROWS = 500
_MAX_OUTPUT_CHARS = 50000


class DbCreate(SandboxTool):
    """Create a new SQLite database with an optional schema."""

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="database_create",
            description=(
                "Create a new SQLite database in the sandbox. Optionally execute "
                "SQL statements to set up the schema (CREATE TABLE, etc.)."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path for the database file.",
                        "default": "/workspace/data.db",
                    },
                    "sql": {
                        "type": "string",
                        "description": (
                            "Optional SQL statements to execute after creation "
                            "(e.g., CREATE TABLE statements). Multiple statements "
                            "separated by semicolons."
                        ),
                    },
                },
                "required": [],
            },
            execution_context=ExecutionContext.SANDBOX,
            tags=("database", "sqlite", "sandbox"),
        )

    async def execute(self, session: Any, **kwargs: Any) -> ToolResult:
        path: str = kwargs.get("path", "/workspace/data.db")
        sql: str = kwargs.get("sql", "")

        config = json.dumps({"path": path, "sql": sql})
        await session.write_file(_CONFIG_PATH, config)

        script = """\
import sqlite3
import json

config = json.load(open("/tmp/_db_config.json"))
db_path = config["path"]
sql = config["sql"]

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

results = []

if sql.strip():
    for statement in sql.split(';'):
        statement = statement.strip()
        if statement:
            try:
                cursor.execute(statement)
                results.append(f"OK: {statement[:80]}")
            except Exception as e:
                results.append(f"ERROR: {e} — {statement[:80]}")

conn.commit()

# Get table list
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]

conn.close()

output = {
    "database": db_path,
    "tables": tables,
    "statements_executed": len(results),
    "details": results,
}
print(json.dumps(output))
"""
        await session.write_file(_SCRIPT_PATH, script)
        result = await session.exec(f"python3 {_SCRIPT_PATH}", timeout=30)

        if result.exit_code != 0:
            error = result.stderr or result.stdout or "Unknown error"
            return ToolResult.fail(f"Database creation failed: {error}")

        try:
            output = json.loads(result.stdout)
            tables = output.get("tables", [])
            detail = (
                f"Database created at {path}. "
                f"Tables: {', '.join(tables) if tables else '(none)'}"
            )
            return ToolResult.ok(detail, metadata=output)
        except json.JSONDecodeError:
            return ToolResult.ok(result.stdout.strip())


class DbQuery(SandboxTool):
    """Execute a SQL query against a SQLite database."""

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="database_query",
            description=(
                "Execute a SQL query against a SQLite database in the sandbox. "
                "Returns results as a JSON array of objects (for SELECT) or "
                "affected row count (for INSERT/UPDATE/DELETE)."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the SQLite database file.",
                        "default": "/workspace/data.db",
                    },
                    "sql": {
                        "type": "string",
                        "description": "SQL query to execute.",
                    },
                    "params": {
                        "type": "array",
                        "description": (
                            "Optional query parameters for parameterized queries."
                        ),
                        "items": {},
                    },
                },
                "required": ["sql"],
            },
            execution_context=ExecutionContext.SANDBOX,
            tags=("database", "sqlite", "sandbox"),
        )

    async def execute(self, session: Any, **kwargs: Any) -> ToolResult:
        path: str = kwargs.get("path", "/workspace/data.db")
        sql: str = kwargs.get("sql", "")
        params: list = kwargs.get("params", [])

        if not sql.strip():
            return ToolResult.fail("SQL query must not be empty")

        config = json.dumps({
            "path": path,
            "sql": sql,
            "params": params,
            "max_rows": _MAX_ROWS,
        })
        await session.write_file(_CONFIG_PATH, config)

        script = """\
import sqlite3
import json

config = json.load(open("/tmp/_db_config.json"))
db_path = config["path"]
sql = config["sql"]
params = config["params"]
max_rows = config["max_rows"]

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

try:
    cursor.execute(sql, params)

    # Check if it's a SELECT-like query
    if cursor.description is not None:
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchmany(max_rows)
        results = [dict(zip(columns, row)) for row in rows]
        has_more = cursor.fetchone() is not None
        output = {
            "type": "select",
            "columns": columns,
            "rows": results,
            "row_count": len(results),
            "has_more": has_more,
        }
    else:
        conn.commit()
        output = {
            "type": "modify",
            "rows_affected": cursor.rowcount,
        }

    print(json.dumps(output, default=str))
except Exception as e:
    print(json.dumps({"type": "error", "error": str(e)}))
finally:
    conn.close()
"""
        await session.write_file(_SCRIPT_PATH, script)
        result = await session.exec(f"python3 {_SCRIPT_PATH}", timeout=30)

        if result.exit_code != 0:
            error = result.stderr or result.stdout or "Unknown error"
            return ToolResult.fail(f"Query execution failed: {error}")

        output_str = result.stdout.strip()
        if len(output_str) > _MAX_OUTPUT_CHARS:
            output_str = output_str[:_MAX_OUTPUT_CHARS] + "\n... (truncated)"

        try:
            parsed = json.loads(result.stdout.strip())
            if parsed.get("type") == "error":
                return ToolResult.fail(f"SQL error: {parsed['error']}")

            if parsed.get("type") == "select":
                row_count = parsed["row_count"]
                has_more = parsed.get("has_more", False)
                summary = f"Query returned {row_count} row(s)"
                if has_more:
                    summary += f" (limit {_MAX_ROWS}, more rows available)"
                return ToolResult.ok(
                    f"{summary}\n{json.dumps(parsed['rows'], indent=2, default=str)}",
                    metadata={
                        "row_count": row_count,
                        "columns": parsed["columns"],
                    },
                )
            else:
                return ToolResult.ok(
                    f"Query executed. Rows affected: {parsed['rows_affected']}",
                    metadata={"rows_affected": parsed["rows_affected"]},
                )
        except json.JSONDecodeError:
            return ToolResult.ok(output_str)


class DbSchema(SandboxTool):
    """Inspect the schema of a SQLite database."""

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="database_schema",
            description=(
                "Inspect the schema of a SQLite database. Returns table names, "
                "column definitions, indexes, and row counts."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the SQLite database file.",
                        "default": "/workspace/data.db",
                    },
                    "table": {
                        "type": "string",
                        "description": "Optional: inspect a specific table only.",
                    },
                },
                "required": [],
            },
            execution_context=ExecutionContext.SANDBOX,
            tags=("database", "sqlite", "sandbox"),
        )

    async def execute(self, session: Any, **kwargs: Any) -> ToolResult:
        path: str = kwargs.get("path", "/workspace/data.db")
        table: str = kwargs.get("table", "")

        config = json.dumps({"path": path, "table": table})
        await session.write_file(_CONFIG_PATH, config)

        script = """\
import sqlite3
import json

config = json.load(open("/tmp/_db_config.json"))
db_path = config["path"]
target_table = config["table"]

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

schema = {"database": db_path, "tables": []}

# Get tables
if target_table:
    tables = [target_table]
else:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

for table_name in tables:
    # Column info
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [
        {
            "name": row[1],
            "type": row[2],
            "notnull": bool(row[3]),
            "default": row[4],
            "pk": bool(row[5]),
        }
        for row in cursor.fetchall()
    ]

    # Row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]

    # Indexes
    cursor.execute(f"PRAGMA index_list({table_name})")
    indexes = [row[1] for row in cursor.fetchall()]

    schema["tables"].append({
        "name": table_name,
        "columns": columns,
        "row_count": row_count,
        "indexes": indexes,
    })

conn.close()
print(json.dumps(schema, indent=2))
"""
        await session.write_file(_SCRIPT_PATH, script)
        result = await session.exec(f"python3 {_SCRIPT_PATH}", timeout=15)

        if result.exit_code != 0:
            error = result.stderr or result.stdout or "Unknown error"
            return ToolResult.fail(f"Schema inspection failed: {error}")

        try:
            parsed = json.loads(result.stdout.strip())
            tables_info = parsed.get("tables", [])

            lines = [f"Database: {path}", f"Tables: {len(tables_info)}", ""]
            for t in tables_info:
                lines.append(f"## {t['name']} ({t['row_count']} rows)")
                for col in t["columns"]:
                    pk = " [PK]" if col["pk"] else ""
                    nn = " NOT NULL" if col["notnull"] else ""
                    lines.append(
                        f"  - {col['name']}: {col['type']}{pk}{nn}"
                    )
                if t["indexes"]:
                    lines.append(f"  Indexes: {', '.join(t['indexes'])}")
                lines.append("")

            return ToolResult.ok(
                "\n".join(lines),
                metadata={
                    "table_count": len(tables_info),
                    "schema": parsed,
                },
            )
        except json.JSONDecodeError:
            return ToolResult.ok(result.stdout.strip())
