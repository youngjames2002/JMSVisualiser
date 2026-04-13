# machining changes to weld page:
# site is done on operation i think? more complex logic
# different operations - might need their own charts or their own categories or something
import streamlit as st
from data import *
from ui_components import *

st.set_page_config(layout="wide")

from login import require_auth
require_auth()

load_css('stylesheet.css')

tcol1, tcol2 = st.columns([1, 4])
tcol2.title("Machining Schedule")
render_logo(tcol1)

df = load_data_machine_sp()
df = remove_completed_jobs(df, "machine")
clean_df = clean_weld_data(df)
kpi_df = build_machine_kpis(clean_df)

# KPIS HERE
kpicol1, kpicol2, kpicol3 = st.columns(3)
kpicol1.title("After Weld Machining")
render_machine_kpi(kpi_df, "After Weld Machining", "this", kpicol1)
render_machine_kpi(kpi_df, "After Weld Machining", "next", kpicol1)
kpicol2.title("CNC Milling")
render_machine_kpi(kpi_df, "CNC Milling", "this", kpicol2)
render_machine_kpi(kpi_df, "CNC Milling", "next", kpicol2)
kpicol3.title("CNC Turning")
render_machine_kpi(kpi_df, "CNC Turning", "this", kpicol3)
render_machine_kpi(kpi_df, "CNC Turning", "next", kpicol3)
kpicol4, kpicol5 = st.columns(2)
kpicol4.title("Csking/Drilling")
render_machine_kpi(kpi_df, "Csking/Drilling", "this", kpicol4)
render_machine_kpi(kpi_df, "Csking/Drilling", "next", kpicol4)
kpicol5.title("Manual Turning")
render_machine_kpi(kpi_df, "Manual Turning", "this", kpicol5)
render_machine_kpi(kpi_df, "Manual Turning", "next", kpicol5)

# apply operation filter here
operations = sorted(clean_df["Operation"].dropna().unique())
operation_filter = st.multiselect(
    "Select Operation(s)",
    operations,
    default=operations  # show all by default
)
filtered_df = clean_df[
    clean_df["Operation"].isin(operation_filter)
]

# chart by week
weekly = build_machine_chart_data(clean_df, operation_filter)
if weekly.empty:
    st.warning("No data selected")
else:
    render_weld_chart(weekly)
    st.dataframe(filtered_df)
