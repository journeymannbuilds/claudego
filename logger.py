"""Append-only SQLite logger for MCP tool calls."""

import json
import sqlite3
import sys
import time
from uuid import uuid4


DB_PATH = "/tmp/server_log.db"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS tool_calls (
    call_id TEXT PRIMARY KEY,
    ts TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    input_params TEXT,
    output_row_count INTEGER,
    output_bytes INTEGER,
    latency_ms INTEGER,
    success INTEGER NOT NULL,
    error_message TEXT,
    session_id TEXT
);
"""


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(_CREATE_TABLE)
    return conn


def log_tool_call(
    tool_name: str,
    input_params: dict | None = None,
    output_row_count: int | None = None,
    output_bytes: int | None = None,
    latency_ms: int | None = None,
    success: bool = True,
    error_message: str | None = None,
    session_id: str | None = None,
) -> None:
    """Log a tool invocation. Never raises — prints to stderr on failure."""
    try:
        conn = _get_db()
        conn.execute(
            """
            INSERT INTO tool_calls
                (call_id, ts, tool_name, input_params, output_row_count,
                 output_bytes, latency_ms, success, error_message, session_id)
            VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                tool_name,
                json.dumps(input_params) if input_params else None,
                output_row_count,
                output_bytes,
                latency_ms,
                1 if success else 0,
                error_message,
                session_id,
            ),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        print(f"[logger] failed to log tool call: {exc}", file=sys.stderr)


class ToolLogger:
    """Context-manager that times a tool call and logs the result."""

    def __init__(self, tool_name: str, input_params: dict | None = None):
        self.tool_name = tool_name
        self.input_params = input_params
        self.row_count: int | None = None
        self.output_bytes: int | None = None
        self._start: float = 0

    def __enter__(self):
        self._start = time.monotonic()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        latency_ms = int((time.monotonic() - self._start) * 1000)
        if exc_type is not None:
            log_tool_call(
                tool_name=self.tool_name,
                input_params=self.input_params,
                output_row_count=self.row_count,
                output_bytes=self.output_bytes,
                latency_ms=latency_ms,
                success=False,
                error_message=str(exc_val),
            )
        else:
            log_tool_call(
                tool_name=self.tool_name,
                input_params=self.input_params,
                output_row_count=self.row_count,
                output_bytes=self.output_bytes,
                latency_ms=latency_ms,
                success=True,
            )
        # Never suppress the exception
        return False
