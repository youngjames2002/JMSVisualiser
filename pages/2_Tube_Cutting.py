import streamlit as st
from data import *
from metrics import *
from ui_components import *

page_setup("Tube Cutting")

df = load_data_sp()
df = df[df["Type"]=="TUBE"]

clean_df = clean_flat_data(df)
# strip Site - all tube is Kilrea
clean_df = clean_df.drop(["Site"], axis=1)
kpi_df = build_tube_kpis(clean_df)

# KPIS HERE
st.title("Overview")
render_saw_bundle_kpi(kpi_df, "late")
render_saw_bundle_kpi(kpi_df, "this")
render_saw_bundle_kpi(kpi_df, "next")

# chart by week
weekly = build_tube_chart_data(clean_df)
capacity=capacity_hours("Tube Cutting")
y_max = max(capacity, weekly["Estimated Bundle Time (Hours)"].max())
render_weekly_bar_chart(
    weekly, "Week Label", "Estimated Bundle Time (Hours)",
    capacity=capacity, show_75_line=True, capacity_borders=True,
    y_max=y_max, text_col="Hours",
)


# table
render_tube_table(clean_df)