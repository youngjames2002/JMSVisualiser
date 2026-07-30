import json
import os
import streamlit as st
from data import *
from ui_components import *

page_setup("Weld Schedule")

OVERRIDES_PATH = os.path.join(os.path.dirname(__file__), "..", "weld_site_overrides.json")

def load_overrides():
    try:
        with open(OVERRIDES_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


if st.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()

df = load_data_weld_sp()
df = remove_completed_jobs_statii(df, "weld")

clean_df = clean_weld_saw_machine_data(df)

# apply site overrides from file
overrides = load_overrides()
for so_num, override_site in overrides.items():
    mask = clean_df["S.O. No."] == so_num
    if mask.any():
        clean_df.loc[mask, "Site"] = override_site

kpi_df = build_weld_kpis(clean_df)
outsourced_hours = total_hours_for_group(clean_df, "Site", "Outsourced", "Hours Plan")

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

if outsourced_hours > 0:
    st.title("Outsourced")
    render_total_kpi(outsourced_hours, "Total Outsourced Hours", st)

BMENA_CAPACITY = 256
KILREA_CAPACITY = 288

# apply site filter here (before chart but after kpis)
site_option = st.selectbox("Site", ["Kilrea", "Ballymena", "Outsourced", "Both Sites", "Total"])
if site_option == "Total":
    site = None
    capacity = BMENA_CAPACITY + KILREA_CAPACITY
elif site_option == "Both Sites":
    site = ["Kilrea", "Ballymena"]
    capacity = BMENA_CAPACITY + KILREA_CAPACITY
elif site_option == "Outsourced":
    site = site_option
    capacity = None
else:
    site = site_option
    capacity = BMENA_CAPACITY if site == "Ballymena" else KILREA_CAPACITY
st.markdown(f"""<h3>Currently showing: {site_option}<h3>""", unsafe_allow_html=True)

# chart by week
weekly, y_max = build_weld_chart_data(clean_df, site)
render_weekly_bar_chart(weekly, "Week Label", "Hours Plan", y_max=y_max, capacity=capacity, overdue_col="Overdue Hours")

render_weld_table(clean_df, site)
