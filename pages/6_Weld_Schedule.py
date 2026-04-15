import streamlit as st
from data import *
from ui_components import *

st.set_page_config(layout="wide")

from login import require_auth
require_auth()

load_css('stylesheet.css')

tcol1, tcol2 = st.columns([1, 4])
tcol2.title("Weld Schedule")
render_logo(tcol1)

df = load_data_weld_sp()
df = remove_completed_jobs(df, "weld")

clean_df = clean_weld_data(df)
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

# apply site filter here (before chart but after kpis)
site_filter = st.toggle("Toggle Site")
if site_filter:
    site="Ballymena"
else:
    site="Kilrea"
st.markdown(f"""<h3>Currently showing: {site}<h3>""", unsafe_allow_html=True)

# chart by week
weekly, y_max = build_weld_chart_data(clean_df, site)
render_weld_chart(weekly, y_max)

render_weld_table(clean_df, site)
    