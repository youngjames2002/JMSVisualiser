import streamlit as st
from data import *
from metrics import *
from ui_components import *

page_setup("Flat Cutting")

statii_toggle = st.toggle("Toggle Bundled Data and Statii Data")
if statii_toggle:
    if st.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    st.title("Overview - Statii Data")
    df = statii_bundle_jobs("Laser - Flat")
    df = df[df["customer_po_no"].str.contains("Link Arms") == False]
    df = clean_statii_bundle_data(df)
    df["Site"] = "Ballymena"

    # build and render kpis
    kpi_df = build_saw_kpis(df)
    render_saw_bundle_kpi(kpi_df, "late")
    render_saw_bundle_kpi(kpi_df, "this")
    render_saw_bundle_kpi(kpi_df, "next")

    # build and render chart
    weekly, y_max = build_saw_chart_data(df)
    cap_col, _ = st.columns([1, 5])
    capacity = capacity_input("flat_cutting", cap_col)
    render_weekly_bar_chart(
        weekly, "Week Label", "Hours Plan",
        capacity=capacity, show_75_line=True,
        y_max=y_max, text_col="Hours", overdue_col="Overdue Hours",
    )

    # table
    filtered_df = weld_table_filters(df)
    st.dataframe(filtered_df, column_config={"Date Requested": st.column_config.DateColumn("Date Requested", format="DD/MM/YY")}, hide_index=True)
else:
    st.title("Overview - Bundled Data")
    df = load_data_sp()
    df = df[df["Type"]=="FLAT"]
    df = clean_flat_data(df)
    df["Site"] = "Ballymena"
    df["Machine Group"] = None
    for machine in ["Regius", "Ensis"]:
        df.loc[df["Machine"].str.contains(machine, case=False, na=False), "Machine Group"] = machine

    # KPIS HERE
    kpi_df = build_flat_machine_kpis(df)
    for kpicol, machine in zip(st.columns(2), ["Regius", "Ensis"]):
        kpicol.title(machine)
        for period in ["late", "this", "next"]:
            render_kpi_card(kpi_df, "Machine Group", machine, period, kpicol)

    # fixed graph scale from both machines (before machine filter)
    _, y_max = build_tube_chart_data(df)
    machine_option = st.selectbox("Machine", ["Both", "Regius", "Ensis"], key="bundle_machine")
    if machine_option != "Both":
        df = df[df["Machine Group"] == machine_option]
    weekly, _ = build_tube_chart_data(df)

    # chart here
    cap_col, _ = st.columns([1, 5])
    capacity = capacity_input("flat_cutting", cap_col)
    y_max = max(y_max, capacity)
    if machine_option != "Both":
        capacity = int(capacity // 2)
    render_weekly_bar_chart(
        weekly, "Week Label", "Estimated Bundle Time (Hours)",
        capacity=capacity, show_75_line=True,
        y_max=y_max, text_col="Hours", overdue_col="Overdue Hours",
    )

    # table
    render_tube_table(df)