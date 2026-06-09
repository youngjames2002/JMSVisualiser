import streamlit as st
from data import *
from ui_components import *

page_setup("Saw Schedule")

if st.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()

df = load_data_saw_sp()
df = remove_completed_jobs_statii(df, "saw")

clean_df = clean_weld_saw_machine_data(df)
kpi_df = build_saw_kpis(clean_df)

# KPIS HERE
st.title("Overview")
render_saw_bundle_kpi(kpi_df, "late")
render_saw_bundle_kpi(kpi_df, "this")
render_saw_bundle_kpi(kpi_df, "next")

# chart by week
weekly, y_max = build_saw_chart_data(clean_df)
render_weekly_bar_chart(weekly, "Week Label", "Hours Plan", y_max=y_max, overdue_col="Overdue Hours")

filtered_df = weld_table_filters(clean_df)
st.dataframe(filtered_df, column_config={"Date Requested": st.column_config.DateColumn("Date Requested", format="DD/MM/YY")})
    