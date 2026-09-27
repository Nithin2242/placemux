import os
from datetime import datetime

import pandas as pd
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Titanic Survival — Phase 1 Capstone",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONSTANTS
# ============================================================

DATA_PATH = "data/titanic_cleaned.csv"


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    """Load and validate the Phase-1 cleaned Titanic dataset."""

    df = pd.read_csv(path)

    required_columns = {
        "survived",
        "pclass",
        "sex",
        "embark_town",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    return df


# ============================================================
# FILTERING
# ============================================================

@st.cache_data
def filter_data(
    df: pd.DataFrame,
    selected_classes: tuple,
    selected_sexes: tuple,
    selected_ports: tuple,
) -> pd.DataFrame:
    """Apply the dashboard filters."""

    filtered = df[
        df["pclass"].isin(selected_classes)
        & df["sex"].isin(selected_sexes)
        & df["embark_town"].isin(selected_ports)
    ].copy()

    return filtered


# ============================================================
# SUMMARY FUNCTIONS
# ============================================================

def survival_rate(series: pd.Series) -> float:
    """Return survival rate safely as a proportion."""

    if len(series) == 0:
        return float("nan")

    return float(series.mean())


def get_class_summary(df: pd.DataFrame) -> pd.Series:
    """Survival rate by passenger class."""

    return (
        df.groupby("pclass")["survived"]
        .mean()
        .sort_index()
    )


def get_sex_summary(df: pd.DataFrame) -> pd.Series:
    """Survival rate by sex."""

    return (
        df.groupby("sex")["survived"]
        .mean()
        .sort_values(ascending=False)
    )


def get_port_summary(df: pd.DataFrame) -> pd.Series:
    """Survival rate by embarkation town."""

    return (
        df.groupby("embark_town")["survived"]
        .mean()
        .sort_values(ascending=False)
    )


def get_class_sex_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Survival rate and population by class and sex."""

    summary = (
        df.groupby(["pclass", "sex"])
        .agg(
            Passengers=("survived", "size"),
            Survival_Rate=("survived", "mean"),
        )
        .reset_index()
    )

    summary["Survival_Rate_%"] = (
        summary["Survival_Rate"] * 100
    )

    return summary


# ============================================================
# SEGMENT IDENTIFICATION
# ============================================================

def get_worst_class(df: pd.DataFrame):
    """Return worst class and its survival rate."""

    summary = get_class_summary(df)

    if summary.empty:
        return None, float("nan")

    worst_class = int(summary.idxmin())
    worst_rate = float(summary.min())

    return worst_class, worst_rate


def get_best_class(df: pd.DataFrame):
    """Return best class and its survival rate."""

    summary = get_class_summary(df)

    if summary.empty:
        return None, float("nan")

    best_class = int(summary.idxmax())
    best_rate = float(summary.max())

    return best_class, best_rate


def get_worst_segment(df: pd.DataFrame):
    """Find the lowest-survival class × sex segment."""

    summary = get_class_sex_summary(df)

    if summary.empty:
        return None

    row = summary.loc[
        summary["Survival_Rate"].idxmin()
    ]

    return {
        "class": int(row["pclass"]),
        "sex": str(row["sex"]),
        "passengers": int(row["Passengers"]),
        "rate": float(row["Survival_Rate"]),
    }


def get_best_segment(df: pd.DataFrame):
    """Find the highest-survival class × sex segment."""

    summary = get_class_sex_summary(df)

    if summary.empty:
        return None

    row = summary.loc[
        summary["Survival_Rate"].idxmax()
    ]

    return {
        "class": int(row["pclass"]),
        "sex": str(row["sex"]),
        "passengers": int(row["Passengers"]),
        "rate": float(row["Survival_Rate"]),
    }


# ============================================================
# LOAD DATA
# ============================================================

try:
    df = load_data(DATA_PATH)
except Exception as exc:
    st.error(f"Unable to load the dashboard dataset: {exc}")
    st.stop()


# ============================================================
# FRESHNESS
# ============================================================

try:
    modification_time = os.path.getmtime(DATA_PATH)
    freshness = datetime.fromtimestamp(
        modification_time
    ).strftime("%Y-%m-%d %H:%M")
except OSError:
    freshness = "Unavailable"


# ============================================================
# SIDEBAR — FILTERS
# ============================================================

st.sidebar.title("Dashboard Filters")
st.sidebar.caption(
    "Use these filters to explore how survival changes "
    "across passenger groups."
)

available_classes = sorted(
    df["pclass"].dropna().unique().tolist()
)

available_sexes = sorted(
    df["sex"].dropna().unique().tolist()
)

available_ports = sorted(
    df["embark_town"].dropna().unique().tolist()
)

selected_classes = st.sidebar.multiselect(
    "Passenger class",
    options=available_classes,
    default=available_classes,
    format_func=lambda value: f"Class {value}",
)

selected_sexes = st.sidebar.multiselect(
    "Sex",
    options=available_sexes,
    default=available_sexes,
)

selected_ports = st.sidebar.multiselect(
    "Port of embarkation",
    options=available_ports,
    default=available_ports,
)

# Use tuples so Streamlit's cache key stays deterministic.
filtered_df = filter_data(
    df,
    tuple(selected_classes),
    tuple(selected_sexes),
    tuple(selected_ports),
)


# ============================================================
# HEADER
# ============================================================

st.title("🚢 Titanic Survival — Phase 1 Capstone")

st.caption(
    f"Data source: `{DATA_PATH}` · "
    f"Records: {len(df):,} · "
    f"Last updated: {freshness}"
)

st.markdown(
    """
    ### Executive question

    **Who experienced the weakest survival outcomes, how large was the gap,
    and does that pattern change when we explore different passenger groups?**
    """
)

st.divider()


# ============================================================
# EMPTY-FILTER STATE
# ============================================================

if filtered_df.empty:

    st.warning(
        "No passengers match the current filter combination. "
        "Broaden at least one filter to continue the analysis."
    )

    st.info(
        "The dashboard remains stable under this filter state; "
        "no calculations or charts are generated from an empty dataset."
    )

    st.stop()


# ============================================================
# CORE METRICS
# ============================================================

overall_rate = survival_rate(filtered_df["survived"])

worst_class, worst_class_rate = get_worst_class(
    filtered_df
)

best_class, best_class_rate = get_best_class(
    filtered_df
)

# ============================================================
# COMPARISON STATE
# ============================================================

class_summary_for_filter = get_class_summary(
    filtered_df
)

segment_summary_for_filter = get_class_sex_summary(
    filtered_df
)

worst_segment = get_worst_segment(
    filtered_df
)

best_segment = get_best_segment(
    filtered_df
)

# A class gap is meaningful only when at least two classes remain.
if len(class_summary_for_filter) >= 2:
    survival_gap = (
        float(class_summary_for_filter.max())
        - float(class_summary_for_filter.min())
    )
else:
    survival_gap = float("nan")

# A strongest-vs-weakest segment comparison is meaningful
# only when at least two class × sex segments remain.
has_segment_comparison = (
    len(segment_summary_for_filter) >= 2
)


# ============================================================
# KPI ROW
# ============================================================

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric(
    "Filtered Survival Rate",
    f"{overall_rate:.1%}",
    help=(
        "Mean of the binary `survived` field among passengers "
        "matching the current filters."
    ),
)

if worst_class is not None and pd.notna(worst_class_rate):

    worst_class_delta = (
        (worst_class_rate - overall_rate) * 100
    )

    kpi2.metric(
        "Worst Class",
        f"Class {worst_class}",
        f"{worst_class_delta:+.1f} pp vs filtered rate",
        help=(
            "Passenger class with the lowest survival rate within "
            "the current filtered dataset."
        ),
    )
else:
    kpi2.metric("Worst Class", "N/A")

kpi3.metric(
    "Passengers Shown",
    f"{len(filtered_df):,}",
    help=(
        "Number of passengers matching the current filter selection."
    ),
)

if pd.notna(survival_gap):

    kpi4.metric(
        "Class Survival Gap",
        f"{survival_gap:.1%}",
        help=(
            "Difference between the highest and lowest class "
            "survival rates when at least two classes are present."
        ),
    )

else:

    kpi4.metric(
        "Class Survival Gap",
        "N/A",
        help=(
            "A class-to-class gap cannot be calculated when only "
            "one passenger class remains after filtering."
        ),
    )


# ============================================================
# GUIDED EXECUTIVE STORY
# ============================================================

st.subheader("📌 What the current data says")

if worst_segment:

    if has_segment_comparison:

        worst_label = (
            f"Class {worst_segment['class']} "
            f"{worst_segment['sex']}"
        )

        best_label = (
            f"Class {best_segment['class']} "
            f"{best_segment['sex']}"
        )

        segment_gap = (
            best_segment["rate"]
            - worst_segment["rate"]
        )

        st.info(
            f"**The weakest observed segment is {worst_label}**, "
            f"with a survival rate of **{worst_segment['rate']:.1%}** "
            f"across {worst_segment['passengers']:,} passengers. "
            f"The strongest observed segment is **{best_label}** "
            f"at **{best_segment['rate']:.1%}**, creating a "
            f"**{segment_gap:.1%} percentage-point gap**."
        )

    else:

        segment_label = (
            f"Class {worst_segment['class']} "
            f"{worst_segment['sex']}"
        )

        st.info(
            f"**The current filters isolate one class × sex segment: "
            f"{segment_label}.** Its observed survival rate is "
            f"**{worst_segment['rate']:.1%}** across "
            f"**{worst_segment['passengers']:,} passengers**. "
            f"A strongest-versus-weakest segment comparison is not "
            f"meaningful because only one segment remains."
        )

else:

    st.info(
        "There are not enough observations to identify a class × sex segment."
    )


# ============================================================
# MAIN EXPLORATION
# ============================================================

st.divider()

left, right = st.columns(2)

with left:

    st.subheader("Survival Rate by Class")

    class_summary = get_class_summary(
        filtered_df
    )

    st.bar_chart(
        class_summary,
        y_label="Survival rate",
    )

    st.caption(
        "Class survival rate = mean survival indicator within each "
        "passenger class."
    )


with right:

    st.subheader("Survival Rate by Sex")

    sex_summary = get_sex_summary(
        filtered_df
    )

    st.bar_chart(
        sex_summary,
        y_label="Survival rate",
    )

    st.caption(
        "Sex survival rate = mean survival indicator within each "
        "sex group."
    )


# ============================================================
# PORT VIEW
# ============================================================

st.subheader("Survival Rate by Port of Embarkation")

port_summary = get_port_summary(
    filtered_df
)

st.bar_chart(
    port_summary,
    y_label="Survival rate",
)

st.caption(
    "Port survival rate = mean survival indicator within each "
    "embarkation town."
)


# ============================================================
# CLASS × SEX DRILL-DOWN
# ============================================================

st.divider()

st.subheader("Class × Sex Segment Drill-Down")

segment_summary = get_class_sex_summary(
    filtered_df
)

segment_display = segment_summary[
    [
        "pclass",
        "sex",
        "Passengers",
        "Survival_Rate_%",
    ]
].copy()

segment_display = segment_display.rename(
    columns={
        "pclass": "Class",
        "sex": "Sex",
        "Survival_Rate_%": "Survival Rate (%)",
    }
)

segment_display["Survival Rate (%)"] = (
    segment_display["Survival Rate (%)"]
    .round(1)
)

segment_display = segment_display.sort_values(
    "Survival Rate (%)"
)

st.dataframe(
    segment_display,
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "The segment table identifies which class × sex combination "
    "has the weakest and strongest observed survival outcome."
)


# ============================================================
# DECISION PANEL
# ============================================================

st.divider()

st.subheader("🎯 Decision Focus")

if worst_segment and best_segment:

    st.markdown(
        f"""
        **Focus first on the weakest observed segment:**
        **Class {worst_segment['class']} {worst_segment['sex']}**
        with **{worst_segment['rate']:.1%} survival**
        across **{worst_segment['passengers']:,} passengers**.

        The dashboard evidence indicates that survival outcomes were
        not evenly distributed across passenger groups. Class and sex
        are particularly important dimensions to inspect together.

        These are observational historical results. They describe
        differences in the dataset and should not be interpreted as
        proof that one passenger characteristic caused the difference.
        """
    )


# ============================================================
# DATA + METRIC DEFINITIONS
# ============================================================

with st.expander("Data source, definitions and methodology"):

    st.markdown(
        f"""
        **Source**

        `{DATA_PATH}`

        **Dataset size**

        {len(df):,} passengers and {len(df.columns):,} fields.

        **Freshness**

        Last file modification: `{freshness}`

        **Survival Rate**

        Mean of the binary `survived` field.

        **Class Survival Gap**

        Best observed passenger-class survival rate minus the worst
        observed passenger-class survival rate within the current
        filtered population.

        **Worst Segment**

        The class × sex combination with the lowest observed survival
        rate within the current filtered population.

        **Filtering**

        Filters are applied to passenger class, sex and embarkation town
        before all dashboard metrics and charts are calculated.

        **Interpretation**

        This is an observational analysis of the historical Titanic
        dataset. Observed group differences are associations, not causal
        effects.
        """
    )


# ============================================================
# DOWNLOAD
# ============================================================

st.divider()

csv_data = filtered_df.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="⬇️ Download Current Filtered Data",
    data=csv_data,
    file_name="titanic_filtered_capstone.csv",
    mime="text/csv",
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "PlaceMux Phase 1 Capstone · Dynamic Dashboard & Data Story · "
    "Built from the validated Phase-1 cleaned Titanic dataset."
)