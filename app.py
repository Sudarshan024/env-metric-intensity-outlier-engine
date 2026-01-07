import streamlit as st
import pandas as pd
import altair as alt
from src.validation import run_validation

import streamlit as st

st.markdown("""
<style>
/* Page max width (nice “canvas” centered layout) */
.block-container {
    max-width: 1100px;
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Headings */
h1, h2, h3 {
    letter-spacing: -0.02em;
}

/* Make metric cards feel cleaner */
[data-testid="stMetric"] {
    border: 1px solid rgba(0,0,0,0.08);
    border-radius: 16px;
    padding: 12px;
}

/* Cleaner dataframe container */
[data-testid="stDataFrame"] {
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid rgba(0,0,0,0.08);
}

/* Tabs style */
.stTabs [data-baseweb="tab"] {
    font-size: 16px;
    padding: 10px 14px;
}

/* Remove extra top padding around main content */
section.main > div { padding-top: 0rem; }
</style>
""", unsafe_allow_html=True)


st.set_page_config(page_title="ESG Validation Engine", layout="wide")
st.title("ESG Data Validation Engine")
st.caption("Flag → Explain → Decide | Decision-ready ESG data validation")

uploaded = st.file_uploader("Upload ESG asset data (CSV)", type=["csv"])

@st.cache_data
def load_sample():
    return pd.read_csv("data/sample_raw.csv")

@st.cache_data
def validate(df: pd.DataFrame) -> pd.DataFrame:
    return run_validation(df)

if uploaded:
    df_raw = pd.read_csv(uploaded)
else:
    st.info("No file uploaded — using sample dataset: data/sample_raw.csv")
    df_raw = load_sample()

tabs = st.tabs(["Overview", "Asset Drill-down", "Validation Table"])

with tabs[0]:
    st.subheader("Raw data preview")
    st.dataframe(df_raw.head(20), use_container_width=True)

    results = validate(df_raw)

    st.subheader("Portfolio overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Raw rows", len(df_raw))
    c2.metric("Validation records", len(results))
    c3.metric("Flagged/Invalid", int((results["status"] != "ACCEPTED").sum()))

    status_counts = results["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]

    chart = alt.Chart(status_counts).mark_bar().encode(
        x=alt.X("status:N", sort="-y"),
        y="count:Q",
        tooltip=["status", "count"]
    ).properties(height=250)

    st.altair_chart(chart, use_container_width=True)

    st.subheader("Top reason codes")
    top_reasons = (results[results["status"] != "ACCEPTED"]
                   .groupby("reason_code").size()
                   .reset_index(name="count")
                   .sort_values("count", ascending=False)
                   .head(12))

    chart2 = alt.Chart(top_reasons).mark_bar().encode(
        x=alt.X("count:Q"),
        y=alt.Y("reason_code:N", sort="-x"),
        tooltip=["reason_code", "count"]
    ).properties(height=350)

    st.altair_chart(chart2, use_container_width=True)

with tabs[1]:
    results = validate(df_raw)

    st.subheader("Asset drill-down")
    assets = results[["asset_id", "asset_name"]].drop_duplicates()
    asset_labels = assets.apply(lambda r: f"{r['asset_id']} — {r['asset_name']}", axis=1).tolist()
    asset_map = dict(zip(asset_labels, assets["asset_id"].tolist()))

    selected_asset = st.selectbox("Select asset", options=asset_labels)
    asset_id = asset_map[selected_asset]

    asset_res = results[results["asset_id"] == asset_id].copy()
    metric = st.selectbox("Metric", options=sorted(asset_res["metric"].unique()))

    asset_res_m = asset_res[asset_res["metric"] == metric].sort_values("year")

    left, right = st.columns([1.2, 1])

    with left:
        st.markdown("### Value trend")
        chart_val = alt.Chart(asset_res_m).mark_line(point=True).encode(
            x=alt.X("year:O"),
            y=alt.Y("value:Q"),
            tooltip=["year", "value", "intensity", "status", "reason_code"]
        ).properties(height=250)
        st.altair_chart(chart_val, use_container_width=True)

        st.markdown("### Intensity trend")
        chart_int = alt.Chart(asset_res_m).mark_line(point=True).encode(
            x=alt.X("year:O"),
            y=alt.Y("intensity:Q"),
            tooltip=["year", "value", "intensity", "status", "reason_code"]
        ).properties(height=250)
        st.altair_chart(chart_int, use_container_width=True)

    with right:
        st.markdown("### Validation details")
        st.dataframe(asset_res_m[[
            "year","metric","value","intensity","status","reason_code","explanation","decision"
        ]], use_container_width=True, height=540)

with tabs[2]:
    results = validate(df_raw)
    st.subheader("Full validation table")
    st.dataframe(results, use_container_width=True, height=500)

    csv = results.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download validation_results.csv",
        data=csv,
        file_name="validation_results.csv",
        mime="text/csv"
    )
