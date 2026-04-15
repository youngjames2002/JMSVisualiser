import streamlit as st
from data import *
from ui_components import *

page_setup("Saw Schedule")

df = load_data_saw_sp()
df = remove_completed_jobs(df, "saw")

clean_df = clean_weld_saw_machine_data(df)
kpi_df = build_saw_kpis(clean_df)

# KPIS HERE
st.title("Overview")
render_saw_bundle_kpi(kpi_df, "late")
render_saw_bundle_kpi(kpi_df, "this")
render_saw_bundle_kpi(kpi_df, "next")

# chart by week
weekly = build_saw_chart_data(clean_df)
render_weld_chart(weekly, weekly["Hours Plan"].max())

filtered_df = weld_table_filters(clean_df)
st.dataframe(filtered_df)
    