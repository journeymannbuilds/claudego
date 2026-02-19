"""
Transform script that connects to Databricks and runs a query
using the provided origin and destination parameters.

Customize the SQL query in `build_query()` to match your Databricks
table schema and desired transformation logic.
"""

import os
from databricks import sql as databricks_sql


def get_connection():
    """Create a connection to the Databricks SQL warehouse."""
    server_hostname = os.environ.get("DATABRICKS_SERVER_HOSTNAME")
    http_path = os.environ.get("DATABRICKS_HTTP_PATH")
    access_token = os.environ.get("DATABRICKS_ACCESS_TOKEN")

    if not all([server_hostname, http_path, access_token]):
        raise ValueError(
            "Missing Databricks connection settings. "
            "Set DATABRICKS_SERVER_HOSTNAME, DATABRICKS_HTTP_PATH, "
            "and DATABRICKS_ACCESS_TOKEN in your .env file."
        )

    return databricks_sql.connect(
        server_hostname=server_hostname,
        http_path=http_path,
        access_token=access_token,
    )


def build_query(origin: str, destination: str) -> tuple[str, list]:
    """
    Build the SQL query for the transform.

    Customize this function to match your table and transformation needs.
    The default assumes a 'trips' table with 'origin' and 'destination' columns.
    Uses parameterized queries to prevent SQL injection.
    """
    catalog = os.environ.get("DATABRICKS_CATALOG", "main")
    schema = os.environ.get("DATABRICKS_SCHEMA", "default")

    query = f"""
        SELECT *
        FROM {catalog}.{schema}.trips
        WHERE origin = %(origin)s
          AND destination = %(destination)s
        ORDER BY 1
        LIMIT 1000
    """
    params = {"origin": origin, "destination": destination}
    return query, params


def run_transform(origin: str, destination: str) -> dict:
    """
    Execute the transform query on Databricks and return the results
    as a dict with 'columns' and 'rows' keys.
    """
    query, params = build_query(origin, destination)

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(query, parameters=params)

        columns = [desc[0] for desc in cursor.description]
        raw_rows = cursor.fetchall()

        rows = []
        for row in raw_rows:
            rows.append(dict(zip(columns, row)))

        cursor.close()
    finally:
        connection.close()

    return {
        "columns": columns,
        "rows": rows,
        "query": query.strip(),
        "params": {"origin": origin, "destination": destination},
    }
