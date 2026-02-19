import os

import pandas as pd
from databricks import sql
from databricks.sdk.core import Config, oauth_service_principal


def get_connection():
    server = os.environ.get(
        "DATABRICKS_HOST", "dbc-871ad75e-3eed.cloud.databricks.com"
    )
    http_path = os.environ.get(
        "DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/d490a228b5b077b3"
    )
    client_id = os.environ.get("DATABRICKS_CLIENT_ID")
    client_secret = os.environ.get("DATABRICKS_CLIENT_SECRET")

    if client_id and client_secret:
        # OAuth M2M — used in Cloud Run / headless environments
        cfg = Config(
            host=f"https://{server}",
            client_id=client_id,
            client_secret=client_secret,
        )
        return sql.connect(
            server_hostname=server,
            http_path=http_path,
            credentials_provider=oauth_service_principal(cfg),
        )
    else:
        # Browser-based OAuth — used for local development
        return sql.connect(
            server_hostname=server,
            http_path=http_path,
            auth_type="databricks-oauth",
        )


def load_od(origin: str, destination: str) -> pd.DataFrame:
    query = """
        SELECT *
        FROM travel_insight_flight_search_pricing_longtail.travel_insight.flight_search_pricing_granular
        WHERE origin_iata = '{origin}' AND destination_iata = '{destination}'
        LIMIT 10000
    """.format(origin=origin.upper(), destination=destination.upper())
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall_arrow().to_pandas()
