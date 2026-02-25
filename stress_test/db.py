import os
import pandas as pd
from databricks import sql


def run_query(query: str) -> pd.DataFrame:
    """Execute a SQL query against Databricks and return results as a DataFrame.

    Raises an exception on failure so callers can handle errors.
    """
    connection = sql.connect(
        server_hostname=os.getenv("DATABRICKS_HOST"),
        http_path=os.getenv("DATABRICKS_HTTP_PATH"),
        access_token=os.getenv("DATABRICKS_TOKEN"),
    )
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(query, timeout=30)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return pd.DataFrame(rows, columns=columns)
        finally:
            cursor.close()
    finally:
        connection.close()
