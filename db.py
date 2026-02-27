"""Databricks connection helper using OAuth M2M (service principal)."""

import os

from databricks import sql


def get_connection():
    """Return a new Databricks SQL connection."""
    return sql.connect(
        server_hostname=os.environ["DATABRICKS_HOST"],
        http_path=os.environ["DATABRICKS_HTTP_PATH"],
        auth_type="databricks-oauth",
        oauth_client_id=os.environ["DATABRICKS_CLIENT_ID"],
        oauth_client_secret=os.environ["DATABRICKS_CLIENT_SECRET"],
    )
