import json
import time

import pandas as pd
import plotly.express as px
import streamlit as st

from connector import load_od
from transform import transform

# ---------------------------------------------------------------------------
# Global styles — dark terminal / green-screen aesthetic
# ---------------------------------------------------------------------------
DARK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fira+Mono&display=swap');

html, body, [class*="css"] {
    font-family: 'Fira Mono', 'Courier New', monospace;
    background-color: #0d0d0d;
    color: #00ff41;
}

/* Streamlit main container */
.stApp {
    background-color: #0d0d0d;
}

/* Text inputs */
input, textarea {
    background-color: #1a1a1a !important;
    color: #00ff41 !important;
    border: 1px solid #00ff41 !important;
    font-family: 'Fira Mono', 'Courier New', monospace !important;
}

/* Buttons */
.stButton > button {
    background-color: #0d0d0d;
    color: #00ff41;
    border: 2px solid #00ff41;
    font-family: 'Fira Mono', 'Courier New', monospace;
    font-weight: bold;
    padding: 0.6rem 2rem;
    transition: all 0.2s;
}
.stButton > button:hover {
    background-color: #00ff41;
    color: #0d0d0d;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #111111;
}
section[data-testid="stSidebar"] * {
    color: #00ff41;
}

/* Multiselect */
.stMultiSelect [data-baseweb="tag"] {
    background-color: #00ff41 !important;
    color: #0d0d0d !important;
}
.stMultiSelect [data-baseweb="select"] > div {
    background-color: #1a1a1a !important;
    border-color: #00ff41 !important;
}

/* Slider */
.stSlider [data-baseweb="slider"] div {
    background-color: #00ff41 !important;
}

/* Dataframe */
.stDataFrame {
    border: 1px solid #00ff41;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    background-color: #1a1a1a;
    color: #00ff41;
    border: 1px solid #00ff41;
    font-family: 'Fira Mono', 'Courier New', monospace;
}
.stTabs [aria-selected="true"] {
    background-color: #00ff41 !important;
    color: #0d0d0d !important;
}

/* Headings & markdown */
h1, h2, h3, h4, h5, h6, p, li, span, label, .stMarkdown {
    color: #00ff41 !important;
}

/* Radio buttons */
.stRadio > div {
    color: #00ff41;
}

/* Metric */
[data-testid="stMetricValue"] {
    color: #00ff41 !important;
}
</style>
"""

st.set_page_config(page_title="LONGTAIL // RETAIL OBSERVER", layout="wide")
st.markdown(DARK_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
if "screen" not in st.session_state:
    st.session_state["screen"] = "loader"
if "data" not in st.session_state:
    st.session_state["data"] = None
if "od" not in st.session_state:
    st.session_state["od"] = ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _parse_array_col(series: pd.Series) -> pd.Series:
    """Parse a JSON-encoded array column, returning lists."""

    def _parse(val):
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return []
        if isinstance(val, list):
            return val
        try:
            parsed = json.loads(val)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []

    return series.apply(_parse)


def _explode_carriers(df: pd.DataFrame, col: str) -> list[str]:
    """Return sorted unique carriers from an array column."""
    parsed = _parse_array_col(df[col])
    exploded = parsed.explode().dropna().unique()
    return sorted([c for c in exploded if c])


def _first_carrier(val) -> str:
    """Extract first carrier from a JSON-encoded array or list."""
    if isinstance(val, list):
        return val[0] if val else "Unknown"
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "Unknown"
    try:
        parsed = json.loads(val)
        if isinstance(parsed, list) and parsed:
            return parsed[0]
    except (json.JSONDecodeError, TypeError):
        pass
    return "Unknown"


# ---------------------------------------------------------------------------
# Screen 1: Market Loader
# ---------------------------------------------------------------------------
def screen_loader():
    st.markdown("# LONGTAIL // RETAIL OBSERVER")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        origin = st.text_input("ORIGIN", max_chars=3, placeholder="e.g. BCN").upper().strip()
    with col2:
        destination = st.text_input("DESTINATION", max_chars=3, placeholder="e.g. DXB").upper().strip()

    st.markdown("")
    load_clicked = st.button("LOAD MARKET", use_container_width=True)

    if load_clicked:
        if not origin or not destination or len(origin) != 3 or len(destination) != 3:
            st.markdown(
                '<span style="color:#ff4444;font-family:monospace;">'
                ">> ERROR: Enter valid 3-letter IATA codes for both origin and destination."
                "</span>",
                unsafe_allow_html=True,
            )
            return

        status = st.empty()
        try:
            steps = [
                ">> Connecting to Databricks...",
                ">> Authenticating via OAuth...",
                f">> Querying: {origin} \u2192 {destination}",
            ]
            for step in steps:
                status.markdown(
                    f'<span style="color:#00ff41;font-family:monospace;">{step}</span>',
                    unsafe_allow_html=True,
                )
                time.sleep(0.4)

            raw_df = load_od(origin, destination)

            status.markdown(
                f'<span style="color:#00ff41;font-family:monospace;">'
                f">> Rows fetched: {len(raw_df)}</span>",
                unsafe_allow_html=True,
            )
            time.sleep(0.3)

            status.markdown(
                '<span style="color:#00ff41;font-family:monospace;">'
                ">> Running transform...</span>",
                unsafe_allow_html=True,
            )
            time.sleep(0.2)

            df = transform(raw_df)

            status.markdown(
                '<span style="color:#00ff41;font-family:monospace;">>> Ready.</span>',
                unsafe_allow_html=True,
            )
            time.sleep(0.3)

            st.session_state["data"] = df
            st.session_state["od"] = f"{origin}-{destination}"
            st.session_state["screen"] = "explorer"
            st.rerun()

        except Exception as exc:
            status.markdown(
                f'<span style="color:#ff4444;font-family:monospace;">'
                f">> ERROR: {exc}</span>",
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Screen 2: Change-Log Explorer
# ---------------------------------------------------------------------------
def screen_explorer():
    df: pd.DataFrame = st.session_state["data"]
    od = st.session_state["od"]
    origin, destination = od.split("-")

    # ---- Top bar ----
    top1, top2, top3 = st.columns([1, 2, 1])
    with top1:
        if st.button("\u25c0 LOAD NEW MARKET"):
            st.session_state["screen"] = "loader"
            st.session_state["data"] = None
            st.session_state["od"] = ""
            st.rerun()
    with top2:
        st.markdown(
            f"<h2 style='text-align:center;'>{origin} \u2192 {destination}</h2>",
            unsafe_allow_html=True,
        )
    with top3:
        st.markdown(
            f"<p style='text-align:right;padding-top:1rem;'>{len(df):,} rows</p>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ---- Parse array columns once ----
    df = df.copy()
    df["_carriers"] = _parse_array_col(df["outbound_marketing_carriers"])
    df["_first_carrier"] = df["outbound_marketing_carriers"].apply(_first_carrier)

    # ---- Sidebar filters ----
    with st.sidebar:
        st.markdown("### FILTERS")

        all_carriers = _explode_carriers(df, "outbound_marketing_carriers")
        sel_carriers = st.multiselect("Carrier", all_carriers)

        trip_types = sorted(df["trip_type"].dropna().unique().tolist())
        sel_trip = st.multiselect("Trip Type", trip_types)

        cabins = sorted(df["cabin_class"].dropna().unique().tolist())
        sel_cabin = st.multiselect("Cabin Class", cabins)

        markets = sorted(df["market"].dropna().unique().tolist())
        sel_market = st.multiselect("Market", markets)

        # Date range
        if "dt" in df.columns and df["dt"].notna().any():
            dt_col = pd.to_datetime(df["dt"], errors="coerce")
            dt_min, dt_max = dt_col.min(), dt_col.max()
            if pd.notna(dt_min) and pd.notna(dt_max) and dt_min < dt_max:
                sel_dates = st.slider(
                    "Date Range",
                    min_value=dt_min.date(),
                    max_value=dt_max.date(),
                    value=(dt_min.date(), dt_max.date()),
                )
            else:
                sel_dates = None
        else:
            sel_dates = None

        # Booking horizon
        if "booking_horizon_days" in df.columns and df["booking_horizon_days"].notna().any():
            bh_min = int(df["booking_horizon_days"].min())
            bh_max = int(df["booking_horizon_days"].max())
            if bh_min < bh_max:
                sel_horizon = st.slider(
                    "Booking Horizon (days)",
                    min_value=bh_min,
                    max_value=bh_max,
                    value=(bh_min, bh_max),
                )
            else:
                sel_horizon = None
        else:
            sel_horizon = None

    # ---- Apply filters ----
    filtered = df.copy()

    if sel_carriers:
        filtered = filtered[
            filtered["_carriers"].apply(
                lambda arr: any(c in arr for c in sel_carriers)
            )
        ]

    if sel_trip:
        filtered = filtered[filtered["trip_type"].isin(sel_trip)]

    if sel_cabin:
        filtered = filtered[filtered["cabin_class"].isin(sel_cabin)]

    if sel_market:
        filtered = filtered[filtered["market"].isin(sel_market)]

    if sel_dates is not None:
        dt_series = pd.to_datetime(filtered["dt"], errors="coerce")
        filtered = filtered[
            (dt_series.dt.date >= sel_dates[0]) & (dt_series.dt.date <= sel_dates[1])
        ]

    if sel_horizon is not None:
        filtered = filtered[
            (filtered["booking_horizon_days"] >= sel_horizon[0])
            & (filtered["booking_horizon_days"] <= sel_horizon[1])
        ]

    st.markdown(f"**Filtered rows: {len(filtered):,}**")

    # ---- Main panel toggle ----
    view = st.radio("View", ["ROW VIEW", "AGGREGATED VIEW"], horizontal=True)

    row_view_cols = [
        "dt",
        "origin_iata",
        "destination_iata",
        "outbound_marketing_carriers",
        "airline_rank",
        "competition_size",
        "airline_total_price_amount",
        "avg_market_total_selling_price_amount",
        "min_market_total_selling_price_amount",
        "price_currency",
        "flight_quality_score",
        "booking_horizon_days",
    ]

    if view == "ROW VIEW":
        display_cols = [c for c in row_view_cols if c in filtered.columns]
        page_size = 50
        total_pages = max(1, (len(filtered) + page_size - 1) // page_size)
        page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
        start = (page - 1) * page_size
        end = start + page_size
        st.dataframe(filtered[display_cols].iloc[start:end], use_container_width=True)
        st.caption(f"Page {page} of {total_pages}")
    else:
        agg_df = (
            filtered.groupby(["dt", "_first_carrier"])
            .agg(
                avg_airline_price=("airline_total_price_amount", "mean"),
                avg_market_price=("avg_market_total_selling_price_amount", "mean"),
                avg_rank=("airline_rank", "mean"),
                row_count=("airline_total_price_amount", "count"),
            )
            .reset_index()
            .rename(columns={"_first_carrier": "carrier"})
        )
        st.dataframe(agg_df, use_container_width=True)

    # ---- Chart: avg airline price over dt by top-5 carriers ----
    st.markdown("---")
    st.markdown("### Avg Airline Price by Date & Carrier (Top 5)")

    chart_df = filtered.copy()
    chart_df["dt"] = pd.to_datetime(chart_df["dt"], errors="coerce")
    top_carriers = (
        chart_df["_first_carrier"]
        .value_counts()
        .head(5)
        .index.tolist()
    )
    chart_df = chart_df[chart_df["_first_carrier"].isin(top_carriers)]

    if chart_df.empty:
        st.info("No data available for chart.")
    else:
        chart_agg = (
            chart_df.groupby(["dt", "_first_carrier"])["airline_total_price_amount"]
            .mean()
            .reset_index()
        )
        fig = px.line(
            chart_agg,
            x="dt",
            y="airline_total_price_amount",
            color="_first_carrier",
            labels={
                "dt": "Date",
                "airline_total_price_amount": "Avg Airline Price",
                "_first_carrier": "Carrier",
            },
        )
        fig.update_layout(
            plot_bgcolor="#0d0d0d",
            paper_bgcolor="#0d0d0d",
            font=dict(family="Fira Mono, Courier New, monospace", color="#00ff41"),
            xaxis=dict(gridcolor="#1a1a1a", linecolor="#00ff41"),
            yaxis=dict(gridcolor="#1a1a1a", linecolor="#00ff41"),
            legend=dict(bgcolor="#0d0d0d"),
        )
        fig.update_traces(line=dict(width=2))
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
if st.session_state["screen"] == "loader":
    screen_loader()
else:
    screen_explorer()
