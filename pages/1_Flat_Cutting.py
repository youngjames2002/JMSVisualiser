import streamlit as st
from data_v2 import load_scheduling_data, load_bundles_table
from metrics import *
from ui_components import *

page_setup("Flat Cutting")

capacity=capacity_hours("Flat Cutting")

if st.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()


df = load_scheduling_data()
# df = df[~df["completed"].isna()]
df = df[df["process"] == "Flat Laser"]

df["weekending"] = df["weekending"].dt.normalize()

# build and render kpis
this_week, next_week = this_and_next_friday()
late_hours = df[df["weekending"] < this_week]["processtime"].sum()
grouped = df[df["weekending"].isin([this_week, next_week])].groupby("weekending")["processtime"].sum()

kpi_df = pd.DataFrame({
    "Late Hours": [late_hours],
    "This Week Hours": [grouped.get(this_week, 0)],
    "Next Week Hours": [grouped.get(next_week, 0)],
})
for col in ["Late Hours", "This Week Hours", "Next Week Hours"]:
    kpi_df[col] = kpi_df[col].apply(format_hours)

render_saw_bundle_kpi(kpi_df, "late")
render_saw_bundle_kpi(kpi_df, "this")
render_saw_bundle_kpi(kpi_df, "next")

# build and render chart
df = df.rename(columns={"weekending": "Week Ending", "processtime": "Hours Plan"})
weekly, y_max = build_saw_chart_data(df)
render_weekly_bar_chart(
    weekly, "Week Label", "Hours Plan",
    capacity=capacity, show_75_line=True,
    y_max=y_max, text_col="Hours", overdue_col="Overdue Hours",
)

# build and render table
weeks_dt = sorted(
    pd.to_datetime(df["Week Ending"], dayfirst=True).dropna().unique()
)

weeks = [d.strftime("%d/%m/%Y") for d in weeks_dt]
today = pd.Timestamp.today().normalize()
this_week = (today + pd.offsets.Week(weekday=4)).strftime("%d/%m/%Y")
default_week = [this_week] if this_week in weeks else []
selected_weeks = st.multiselect(
    "Filter By Week(s)",
    options=weeks,
    default=default_week,
    key="week_filter"
)
filtered_df = df[df["Week Ending"].isin(selected_weeks)]
# rename columns and remove useless ones here
st.dataframe(filtered_df, column_config={"Date Requested": st.column_config.DateColumn("Date Requested", format="DD/MM/YY")})