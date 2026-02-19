import pandas as pd
from databricks import sql


def get_connection():
    return sql.connect(
        server_hostname="dbc-871ad75e-3eed.cloud.databricks.com",
        http_path="/sql/1.0/warehouses/d490a228b5b077b3",
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
