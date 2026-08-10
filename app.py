import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

st.set_page_config(page_title="Titanic Survival Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("data/titanic_cleaned.csv")
    return df

df = load_data()
data_mtime = datetime.fromtimestamp(os.path.getmtime("data/titanic_cleaned.csv"))

st.title("Titanic Survival — Executive Dashboard")
st.caption(f"Data source: `data/titanic_cleaned.csv` (n = {len(df)}) · Last updated: {data_mtime.strftime('%Y-%m-%d %H:%M')}")

# ---- Step 4: Filters ----
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

filtered_df = df[
    (df["pclass"].isin(class_filter)) &
    (df["sex"].isin(sex_filter)) &
    (df["embark_town"].isin(port_filter))
]

st.sidebar.caption(f"Showing {len(filtered_df)} of {len(df)} passengers")

# ---- Step 5: Headline tiles ----
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
st.divider()

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Survival Rate by Class")
    if len(filtered_df) > 0:
        fig, ax = plt.subplots(figsize=(5, 3.5))
        sns.barplot(data=filtered_df, x="pclass", y="survived", errorbar=None, ax=ax)
        ax.axhline(df["survived"].mean(), color="black", linestyle="--", linewidth=1, label="Unfiltered overall")
        ax.set_ylabel("Survival Rate")
        ax.set_xlabel("Passenger Class")
        ax.legend(fontsize=8)
        st.pyplot(fig)
    else:
        st.info("No passengers match the current filters.")

with col_b:
    st.subheader("Survival Rate by Sex")
    if len(filtered_df) > 0:
        fig2, ax2 = plt.subplots(figsize=(5, 3.5))
        sns.barplot(data=filtered_df, x="sex", y="survived", errorbar=None, ax=ax2)
        ax2.axhline(df["survived"].mean(), color="black", linestyle="--", linewidth=1, label="Unfiltered overall")
        ax2.set_ylabel("Survival Rate")
        ax2.set_xlabel("Sex")
        ax2.legend(fontsize=8)
        st.pyplot(fig2)
    else:
        st.info("No passengers match the current filters.")

st.divider()
st.subheader("Survival Rate by Port of Embarkation")
if len(filtered_df) > 0:
    fig3, ax3 = plt.subplots(figsize=(9, 3.5))
    sns.barplot(data=filtered_df, x="embark_town", y="survived", errorbar=None, ax=ax3)
    ax3.axhline(df["survived"].mean(), color="black", linestyle="--", linewidth=1, label="Unfiltered overall")
    ax3.set_ylabel("Survival Rate")
    ax3.set_xlabel("Port")
    ax3.legend(fontsize=8)
    st.pyplot(fig3)

    st.caption("💡 Dashed line = unfiltered overall survival rate (41.0%), shown for comparison across all charts. Hover over the (?) icons on metric tiles for exact definitions.")