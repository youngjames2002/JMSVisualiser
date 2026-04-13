import streamlit as st
from data import *
from ui_components import *

st.set_page_config(layout="wide")

from login import require_auth
require_auth()

load_css('stylesheet.css')

tcol1, tcol2 = st.columns([1, 4])
tcol2.title("Saw Schedule")
render_logo(tcol1)

df = load_data_saw_sp()
df = remove_completed_jobs(df, "saw")

clean_df = clean_weld_data(df)
kpi_df = build_saw_kpis(clean_df)

# KPIS HERE
st.title("Overview")
render_saw_machine_kpi(kpi_df, "this")
render_saw_machine_kpi(kpi_df, "next")


# chart by week
weekly = build_saw_chart_data(clean_df)
render_weld_chart(weekly)

filtered_df = weld_table_filters(clean_df)
st.dataframe(filtered_df)
    