import streamlit as st
from data import *
from ui_components import *

page_setup("Machining Schedule")

if st.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()

df = load_data_machine_sp()
df = remove_finished_jobs(df, "machine")
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
# render row by row (titles, then each KPI) so rows stay aligned when a title wraps
for kpi_group in [["After Weld Machining", "CNC Milling", "CNC Turning"], ["Csking/Drilling", "Manual Turning"]]:
    for kpicol, operation in zip(st.columns(len(kpi_group)), kpi_group):
        kpicol.title(operation)
    for period in ["late", "this", "next"]:
        for kpicol, operation in zip(st.columns(len(kpi_group)), kpi_group):
            render_machine_kpi(kpi_df, operation, period, kpicol)

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
    cap_col, _ = st.columns([1, 5])
    machining_capacity = capacity_input("machining", cap_col)
    render_weekly_bar_chart(weekly, "Week Label", "Hours Plan", y_max=y_max, capacity=machining_capacity, overdue_col="Overdue Hours")
    render_machine_table(filtered_df)
