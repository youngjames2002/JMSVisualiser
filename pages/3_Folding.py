import streamlit as st
from data import *
from metrics import *
from ui_components import *

import plotly.io as pio
pio.templates.default = "simple_white"

from login import require_auth
require_auth()

st.set_page_config(layout="wide")

#load css
load_css('stylesheet.css')

tcol1, tcol2 = st.columns([1,4])
tcol2.title("Folding")
render_logo(tcol1)

df = load_data_sp()
df = df[df["Folding Required?"]=="Yes"]

clean_df = clean_fold_data(df)
kpi_df = build_fold_kpis(clean_df)

# render KPIS here
kpicol1, kpicol2 = st.columns(2)
kpicol1.title("Kilrea")
render_weld_kpi(kpi_df, "Kilrea", "late", kpicol1)
render_weld_kpi(kpi_df, "Kilrea", "this", kpicol1)
render_weld_kpi(kpi_df, "Kilrea", "next", kpicol1)
kpicol2.title("Ballymena")
render_weld_kpi(kpi_df, "Ballymena", "late", kpicol2)
render_weld_kpi(kpi_df, "Ballymena", "this", kpicol2)
render_weld_kpi(kpi_df, "Ballymena", "next", kpicol2)

capacity_ballymena = int(capacity_hours("Folding") * 0.6)
capacity_kilrea = int(capacity_hours("Folding") * 0.4)

max_capacity = max(capacity_ballymena, capacity_kilrea)

# site toggle
site_filter = st.toggle("Toggle Site")
if site_filter:
    site="Ballymena"
    capacity = capacity_ballymena
else:
    site="Kilrea"
    capacity = capacity_kilrea
st.markdown(f"""<h3>Currently showing: {site}<h3>""", unsafe_allow_html=True)

# chart here
weekly, y_max = build_fold_chart_data(clean_df, site)
y_max = max(y_max, max_capacity)
render_fold_chart(weekly, capacity, y_max)# rework chart render same reason

# table
render_fold_table(clean_df, site)