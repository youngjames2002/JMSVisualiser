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
tcol2.title("Flat Cutting")
render_logo(tcol1)

df = load_data_sp()
df = df[df["Type"]=="FLAT"]

clean_df = clean_flat_data(df)
kpi_df = build_flat_kpis(clean_df)

# KPIS HERE
kpicol1, kpicol2 = st.columns(2)
kpicol1.title("Kilrea")
render_weld_kpi(kpi_df, "Kilrea", "this", kpicol1)
render_weld_kpi(kpi_df, "Kilrea", "next", kpicol1)
kpicol2.title("Ballymena")
render_weld_kpi(kpi_df, "Ballymena", "this", kpicol2)
render_weld_kpi(kpi_df, "Ballymena", "next", kpicol2)

capacity_ballymena = int(capacity_hours("Flat Cutting") * 0.545)
capacity_kilrea   = int(capacity_hours("Flat Cutting") * 0.46)

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
weekly, y_max = build_flat_chart_data(clean_df, site)
y_max = max(y_max, max_capacity)
render_flat_chart(weekly, capacity, y_max)

# table
render_flat_table(clean_df, site)