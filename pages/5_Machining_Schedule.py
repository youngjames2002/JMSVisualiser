import streamlit as st
from data import *
from ui_components import *

page_setup("Machining Schedule")

if st.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()

df = load_data_machine_sp()
df = remove_completed_jobs_statii(df, "machine")
clean_df = clean_weld_saw_machine_data(df)

# site logic from teams labels
site_option = st.selectbox("Site", ["Both Sites", "No Site Assigned", "Ballymena", "Kilrea"], key="statii_site")
clean_df = clean_df.drop(columns=["Site"])  # drop the old Bamford-based Site
clean_df = clean_df.merge(get_machine_schedule_labels(), on=["S.O. No.", "Operation"], how="left")
clean_df["Site"] = clean_df["Site"].fillna("No Site Assigned")
if site_option != "Both Sites":
    clean_df = clean_df[clean_df["Site"] == site_option]

# KPIS HERE
kpi_df = build_machine_kpis(clean_df)
kpicol1, kpicol2, kpicol3 = st.columns(3)
kpicol1.title("After Weld Machining")
render_machine_kpi(kpi_df, "After Weld Machining", "late", kpicol1)
render_machine_kpi(kpi_df, "After Weld Machining", "this", kpicol1)
render_machine_kpi(kpi_df, "After Weld Machining", "next", kpicol1)
kpicol2.title("CNC Milling")
render_machine_kpi(kpi_df, "CNC Milling", "late", kpicol2)
render_machine_kpi(kpi_df, "CNC Milling", "this", kpicol2)
render_machine_kpi(kpi_df, "CNC Milling", "next", kpicol2)
kpicol3.title("CNC Turning")
render_machine_kpi(kpi_df, "CNC Turning", "late", kpicol3)
render_machine_kpi(kpi_df, "CNC Turning", "this", kpicol3)
render_machine_kpi(kpi_df, "CNC Turning", "next", kpicol3)
kpicol4, kpicol5 = st.columns(2)
kpicol4.title("Csking/Drilling")
render_machine_kpi(kpi_df, "Csking/Drilling", "late", kpicol4)
render_machine_kpi(kpi_df, "Csking/Drilling", "this", kpicol4)
render_machine_kpi(kpi_df, "Csking/Drilling", "next", kpicol4)
kpicol5.title("Manual Turning")
render_machine_kpi(kpi_df, "Manual Turning", "late", kpicol5)
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
weekly, y_max = build_machine_chart_data(clean_df, operation_filter)
if weekly.empty:
    st.warning("No data selected")
else:
    render_weekly_bar_chart(weekly, "Week Label", "Hours Plan", y_max=y_max, capacity=114, overdue_col="Overdue Hours")
    render_machine_table(filtered_df)
