"""Databricks connection helper using Personal Access Token (PAT)."""

import os

from databricks import sql


def get_connection():
    """Return a new Databricks SQL connection."""
    return sql.connect(
        server_hostname=os.environ["DATABRICKS_HOST"],
        http_path=os.environ["DATABRICKS_HTTP_PATH"],
        access_token=os.environ["DATABRICKS_ACCESS_TOKEN"],
    )
