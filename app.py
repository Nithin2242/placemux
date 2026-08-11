import streamlit as st
import pandas as pd
from datetime import datetime
import time
import os

st.set_page_config(page_title="Titanic Survival Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("data/titanic_cleaned.csv")
    return df

@st.cache_data
def filter_data(_df, classes, sexes, ports):
    return _df[
        (_df["pclass"].isin(classes)) &
        (_df["sex"].isin(sexes)) &
        (_df["embark_town"].isin(ports))
    ]

def get_class_summary(filtered_df):
    return filtered_df.groupby("pclass")["survived"].mean()

def get_sex_summary(filtered_df):
    return filtered_df.groupby("sex")["survived"].mean()

def get_port_summary(filtered_df):
    return filtered_df.groupby("embark_town")["survived"].mean()

# ---- Data load (timed) ----
t_load_start = time.time()
df = load_data()
t_load_end = time.time()
load_time_ms = (t_load_end - t_load_start) * 1000

data_mtime = datetime.fromtimestamp(os.path.getmtime("data/titanic_cleaned.csv"))

st.title("Titanic Survival — Executive Dashboard")
st.caption(f"Data source: `data/titanic_cleaned.csv` (n = {len(df)}) · Last updated: {data_mtime.strftime('%Y-%m-%d %H:%M')}")

# ---- Filters ----
st.sidebar.header("Filters")

class_filter = st.sidebar.multiselect(
    "Passenger class", options=sorted(df["pclass"].unique()), default=sorted(df["pclass"].unique())
)
sex_filter = st.sidebar.multiselect(
    "Sex", options=df["sex"].unique(), default=df["sex"].unique()
)
port_filter = st.sidebar.multiselect(
    "Port of embarkation", options=df["embark_town"].unique(), default=df["embark_town"].unique()
)

# ---- Filtering (timed, cached) ----
t_filter_start = time.time()
filtered_df = filter_data(df, class_filter, sex_filter, port_filter)
t_filter_end = time.time()
filter_time_ms = (t_filter_end - t_filter_start) * 1000

st.sidebar.caption(f"Showing {len(filtered_df)} of {len(df)} passengers")

overall_mean = df["survived"].mean()

# ---- Headline tiles (loaded first, per Step 5) ----
col1, col2, col3 = st.columns(3)

overall_rate = filtered_df["survived"].mean() if len(filtered_df) > 0 else 0
col1.metric(
    "Overall Survival Rate",
    f"{overall_rate:.1%}",
    help="Mean of the `survived` column for the currently filtered passengers. Source: titanic_cleaned.csv"
)

with_class_data = filtered_df.groupby("pclass")["survived"].mean()
worst_class = with_class_data.idxmin() if len(with_class_data) > 0 else "N/A"
col2.metric(
    "Worst-Performing Class",
    f"Class {worst_class}" if worst_class != "N/A" else "N/A",
    f"{with_class_data.min():.1%} survival" if len(with_class_data) > 0 else "",
    help="Passenger class with the lowest survival rate among currently filtered passengers."
)

col3.metric(
    "Passengers Shown",
    f"{len(filtered_df)}",
    help="Number of passengers matching the current filter selection."
)

# ---- Breakdown charts (deferred behind a spinner, per Step 5) ----
st.divider()

with st.spinner("Loading breakdown charts..."):
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Survival Rate by Class")
        if len(filtered_df) > 0:
            st.caption(f"Unfiltered overall: {overall_mean:.1%}")
            t_chart1_start = time.time()
            st.bar_chart(get_class_summary(filtered_df))
            t_chart1_end = time.time()
            chart1_time_ms = (t_chart1_end - t_chart1_start) * 1000
        else:
            st.info("No passengers match the current filters.")
            chart1_time_ms = 0

    with col_b:
        st.subheader("Survival Rate by Sex")
        if len(filtered_df) > 0:
            st.caption(f"Unfiltered overall: {overall_mean:.1%}")
            t_chart2_start = time.time()
            st.bar_chart(get_sex_summary(filtered_df))
            t_chart2_end = time.time()
            chart2_time_ms = (t_chart2_end - t_chart2_start) * 1000
        else:
            st.info("No passengers match the current filters.")
            chart2_time_ms = 0

    st.divider()
    st.subheader("Survival Rate by Port of Embarkation")
    if len(filtered_df) > 0:
        st.caption(f"Unfiltered overall: {overall_mean:.1%}")
        t_chart3_start = time.time()
        st.bar_chart(get_port_summary(filtered_df))
        t_chart3_end = time.time()
        chart3_time_ms = (t_chart3_end - t_chart3_start) * 1000
    else:
        chart3_time_ms = 0

st.caption("💡 Charts show survival rate per group. Compare against the unfiltered overall shown above each chart. Hover over the (?) icons on metric tiles for exact definitions.")

# ---- Performance timing (Day 13) ----
st.divider()
st.subheader("⏱ Performance")
timing_df = pd.DataFrame({
    "Step": ["Data load", "Filtering", "Chart 1 (class)", "Chart 2 (sex)", "Chart 3 (port)"],
    "Time (ms)": [
        round(load_time_ms, 2),
        round(filter_time_ms, 2),
        round(chart1_time_ms, 2),
        round(chart2_time_ms, 2),
        round(chart3_time_ms, 2),
    ]
})
st.dataframe(timing_df, hide_index=True)
st.caption(f"Total: {round(load_time_ms + filter_time_ms + chart1_time_ms + chart2_time_ms + chart3_time_ms, 2)} ms")