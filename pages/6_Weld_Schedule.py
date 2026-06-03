import streamlit as st
from data import *
from ui_components import *

page_setup("Weld Schedule")

if st.button("Refresh Statii Data"):
    statii_completed_jobs.clear()
    st.rerun()

df = load_data_weld_sp()
df = remove_completed_jobs_statii(df, "weld")

clean_df = clean_weld_saw_machine_data(df)
kpi_df = build_weld_kpis(clean_df)

# KPIS HERE
kpicol1, kpicol2 = st.columns(2)
kpicol1.title("Kilrea")
render_weld_kpi(kpi_df, "Kilrea", "late", kpicol1)
render_weld_kpi(kpi_df, "Kilrea", "this", kpicol1)
render_weld_kpi(kpi_df, "Kilrea", "next", kpicol1)
kpicol2.title("Ballymena")
render_weld_kpi(kpi_df, "Ballymena", "late", kpicol2)
render_weld_kpi(kpi_df, "Ballymena", "this", kpicol2)
render_weld_kpi(kpi_df, "Ballymena", "next", kpicol2)

BMENA_CAPACITY = 238
KILREA_CAPACITY = 322

# apply site filter here (before chart but after kpis)
site_option = st.selectbox("Site", ["Kilrea", "Ballymena", "Both Sites"])
if site_option == "Both Sites":
    site = None
    capacity = BMENA_CAPACITY + KILREA_CAPACITY
else:
    site = site_option
    capacity = BMENA_CAPACITY if site == "Ballymena" else KILREA_CAPACITY
st.markdown(f"""<h3>Currently showing: {site_option}<h3>""", unsafe_allow_html=True)

# chart by week
weekly, y_max = build_weld_chart_data(clean_df, site)
render_weekly_bar_chart(weekly, "Week Label", "Hours Plan", y_max=y_max, capacity=capacity, overdue_col="Overdue Hours")

render_weld_table(clean_df, site)
    