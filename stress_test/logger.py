import sqlite3
import csv
import io
from datetime import datetime, timezone
from typing import Optional, List, Dict

DB_PATH = "./stress_test_log.db"


def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS query_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            question TEXT,
            generated_sql TEXT,
            row_count INTEGER,
            success BOOLEAN,
            error_message TEXT,
            gap_flag TEXT
        )
        """
    )
    conn.commit()
    return conn


def log_query(
    question: str,
    generated_sql: str,
    row_count: int,
    success: bool,
    error_message: Optional[str],
    gap_flag: Optional[str],
):
    conn = _get_connection()
    try:
        conn.execute(
            """
            INSERT INTO query_log (timestamp, question, generated_sql, row_count, success, error_message, gap_flag)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                question,
                generated_sql,
                row_count,
                success,
                error_message,
                gap_flag,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_recent_logs(limit: int = 20) -> List[Dict]:
    conn = _get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT timestamp, question, success, gap_flag
            FROM query_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        conn.close()


def export_log_csv() -> str:
    conn = _get_connection()
    try:
        cursor = conn.execute(
            "SELECT id, timestamp, question, generated_sql, row_count, success, error_message, gap_flag FROM query_log ORDER BY id"
        )
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        writer.writerows(rows)
        return output.getvalue()
    finally:
        conn.close()
