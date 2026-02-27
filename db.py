"""Databricks connection helper using OAuth M2M (service principal)."""

import os

from databricks import sql
from databricks.sdk.core import Config, oauth_service_principal


def get_connection():
    """Return a new Databricks SQL connection."""
    cfg = Config(
        host=os.environ["DATABRICKS_HOST"],
        client_id=os.environ["DATABRICKS_CLIENT_ID"],
        client_secret=os.environ["DATABRICKS_CLIENT_SECRET"],
    )

    return sql.connect(
        server_hostname=os.environ["DATABRICKS_HOST"],
        http_path=os.environ["DATABRICKS_HTTP_PATH"],
        credentials_provider=oauth_service_principal(cfg),
    )
