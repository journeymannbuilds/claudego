import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from llm import generate_sql, assess_gap
from db import run_query
from logger import log_query, get_recent_logs, export_log_csv

st.set_page_config(page_title="Longtail Stress Test", layout="wide")

# Dark theme styling
st.markdown(
    """
    <style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Longtail Stress Test")

# --- Sidebar: Query Log ---
with st.sidebar:
    st.header("Query Log")
    logs = get_recent_logs(20)
    if logs:
        for entry in logs:
            status = "+" if entry["success"] else "-"
            gap = entry["gap_flag"] or ""
            ts = entry["timestamp"][:19]
            q = entry["question"][:60]
            st.markdown(f"`[{status}]` **{ts}**  \n{q}  \n_{gap}_")
            st.divider()
    else:
        st.caption("No queries logged yet.")

    csv_data = export_log_csv()
    st.download_button(
        label="Download Log",
        data=csv_data,
        file_name="stress_test_log.csv",
        mime="text/csv",
    )

# --- Main area ---
question = st.text_input("Ask a question about the data model")
run_button = st.button("Run")

if run_button and question:
    generated_sql = None
    row_count = 0
    success = False
    error_message = None
    gap_flag = None
    df = pd.DataFrame()

    # Step 1: Generate SQL
    with st.spinner("Generating SQL..."):
        try:
            generated_sql = generate_sql(question)
        except Exception as e:
            error_message = f"Claude API error: {e}"
            st.error(error_message)

    if generated_sql:
        st.subheader("Generated SQL")
        st.code(generated_sql, language="sql")

        # Warn if query doesn't look like a SELECT
        if not generated_sql.strip().upper().startswith("SELECT"):
            st.warning("Generated SQL does not start with SELECT — running anyway.")

        # Step 2: Execute query
        with st.spinner("Running query on Databricks..."):
            try:
                df = run_query(generated_sql)
                row_count = len(df)
                success = True
            except Exception as e:
                error_message = str(e)
                success = False
                st.error(f"Databricks error: {error_message}")

        # Step 3: Display results
        if success:
            st.subheader(f"Results ({row_count} rows)")
            st.dataframe(df, use_container_width=True)

        # Step 4: Gap assessment
        with st.spinner("Assessing data model gaps..."):
            try:
                gap_flag = assess_gap(question, generated_sql, row_count, success)
            except Exception as e:
                gap_flag = f"Gap assessment failed: {e}"

        st.subheader("Gap Flag")
        st.info(gap_flag)

    # Step 5: Log everything
    log_query(
        question=question,
        generated_sql=generated_sql or "",
        row_count=row_count,
        success=success,
        error_message=error_message,
        gap_flag=gap_flag,
    )
