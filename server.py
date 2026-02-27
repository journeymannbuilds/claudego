"""Remote MCP server exposing Databricks tools over Streamable HTTP."""

import json
import os
import re

import anyio
import hmac
import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from db import get_connection
from logger import ToolLogger

# ---------------------------------------------------------------------------
# Bearer-token auth middleware (optional — enable via MCP_AUTH_TOKEN env var)
# ---------------------------------------------------------------------------
# Uses 403 (not 401) on failure so Claude Code's MCP client won't kick off
# an OAuth discovery flow.
# ---------------------------------------------------------------------------
_AUTH_TOKEN: str | None = os.environ.get("MCP_AUTH_TOKEN")


class BearerTokenMiddleware:
    """ASGI middleware that validates an Authorization: Bearer <token> header."""

    def __init__(self, app: ASGIApp, token: str) -> None:
        self.app = app
        self.token = token

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            auth = headers.get(b"authorization", b"").decode()
            expected = f"Bearer {self.token}"
            if not (
                len(auth) == len(expected)
                and hmac.compare_digest(auth.encode(), expected.encode())
            ):
                resp = Response("Forbidden", status_code=403)
                await resp(scope, receive, send)
                return
        await self.app(scope, receive, send)

# ---------------------------------------------------------------------------
# Read-only SQL allowlist — only these statement types are permitted
# ---------------------------------------------------------------------------
_READONLY_PATTERN = re.compile(
    r"^\s*(SELECT|SHOW|DESCRIBE|DESC|EXPLAIN|WITH)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Identifier validation — only allow safe characters in catalog/schema/table
# ---------------------------------------------------------------------------
_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9_]+$")

# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------
server = FastMCP(
    name="longtail-mcp",
    host="0.0.0.0",
    port=8080,
)


# ---------------------------------------------------------------------------
# Helpers — run sync Databricks calls in a thread
# ---------------------------------------------------------------------------
def _execute_query(sql_text: str) -> list[dict]:
    """Execute a SQL query and return rows as list of dicts."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql_text)
        columns = [desc[0] for desc in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return rows
    finally:
        conn.close()


def _execute_query_no_results(sql_text: str) -> list[list]:
    """Execute a SQL query and return raw rows (for SHOW commands)."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql_text)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [columns, rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Tool 1: query
# ---------------------------------------------------------------------------
@server.tool(description="Execute a read-only SQL query against Databricks.")
async def query(sql: str) -> str:
    """Execute a read-only SQL query and return results as JSON."""
    with ToolLogger("query", {"sql": sql}) as log:
        # Safety: only allow read-only statements
        if not _READONLY_PATTERN.match(sql):
            raise ValueError(
                "Only read-only queries are allowed "
                "(SELECT, SHOW, DESCRIBE, EXPLAIN, WITH)."
            )

        rows = await anyio.to_thread.run_sync(lambda: _execute_query(sql))
        result = json.dumps(rows, default=str)
        log.row_count = len(rows)
        log.output_bytes = len(result.encode())
        return result


# ---------------------------------------------------------------------------
# Tool 2: list_tables
# ---------------------------------------------------------------------------
@server.tool(description="List all fully-qualified table names in a catalog.")
async def list_tables(catalog: str = "longtail") -> str:
    """List tables across all schemas in the given catalog."""
    with ToolLogger("list_tables", {"catalog": catalog}) as log:
        if not _SAFE_IDENTIFIER.match(catalog):
            raise ValueError("Catalog name contains invalid characters.")

        # Get schemas
        schema_data = await anyio.to_thread.run_sync(
            lambda: _execute_query(f"SHOW SCHEMAS IN `{catalog}`")
        )

        tables: list[str] = []
        for schema_row in schema_data:
            schema_name = schema_row.get("databaseName") or schema_row.get("namespace")
            if not schema_name:
                # Fallback: take first value
                schema_name = next(iter(schema_row.values()))

            table_data = await anyio.to_thread.run_sync(
                lambda sn=schema_name: _execute_query(
                    f"SHOW TABLES IN `{catalog}`.`{sn}`"
                )
            )
            for table_row in table_data:
                table_name = table_row.get("tableName") or table_row.get("table")
                if not table_name:
                    table_name = next(iter(table_row.values()))
                tables.append(f"{catalog}.{schema_name}.{table_name}")

        result = json.dumps(tables)
        log.row_count = len(tables)
        log.output_bytes = len(result.encode())
        return result


# ---------------------------------------------------------------------------
# Tool 3: describe_table
# ---------------------------------------------------------------------------
@server.tool(description="Describe columns of a fully-qualified table.")
async def describe_table(table: str) -> str:
    """Describe a table. Pass a fully-qualified name like catalog.schema.table."""
    with ToolLogger("describe_table", {"table": table}) as log:
        # Validate format: expect catalog.schema.table
        parts = table.split(".")
        if len(parts) != 3:
            raise ValueError(
                "Table must be fully qualified: catalog.schema.table"
            )
        if not all(_SAFE_IDENTIFIER.match(p) for p in parts):
            raise ValueError("Table name parts contain invalid characters.")
        safe_name = ".".join(f"`{p}`" for p in parts)

        rows = await anyio.to_thread.run_sync(
            lambda: _execute_query(f"DESCRIBE TABLE {safe_name}")
        )

        result = json.dumps(rows, default=str)
        log.row_count = len(rows)
        log.output_bytes = len(result.encode())
        return result


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = server.streamable_http_app()

    if _AUTH_TOKEN:
        app = BearerTokenMiddleware(app, _AUTH_TOKEN)
        print("Starting longtail-mcp on http://0.0.0.0:8080 (bearer auth enabled)")
    else:
        print("Starting longtail-mcp on http://0.0.0.0:8080 (no auth)")

    config = uvicorn.Config(app, host="0.0.0.0", port=8080, log_level="info")
    uv_server = uvicorn.Server(config)
    anyio.run(uv_server.serve)
