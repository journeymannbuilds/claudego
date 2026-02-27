"""Databricks connection helper using Service Principal (OAuth M2M)."""

import os

from databricks import sql
from databricks.sdk.core import Config, oauth_service_principal


def _credential_provider():
    config = Config(
        host=f"https://{os.environ['DATABRICKS_HOST']}",
        client_id=os.environ["DATABRICKS_CLIENT_ID"],
        client_secret=os.environ["DATABRICKS_CLIENT_SECRET"],
    )
    return oauth_service_principal(config)


def get_connection():
    """Return a new Databricks SQL connection."""
    return sql.connect(
        server_hostname=os.environ["DATABRICKS_HOST"],
        http_path=os.environ["DATABRICKS_HTTP_PATH"],
        credentials_provider=_credential_provider(),
    )
