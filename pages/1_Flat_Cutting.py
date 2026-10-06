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
    # Statii has no machine info, so borrow it from the bundle sheet via sales order number
    bundle_df = load_data_sp()
    df = assign_statii_flat_machine(df, bundle_df[bundle_df["Type"] == "FLAT"])

    machine_groups = FLAT_MACHINES + [FLAT_NOT_BUNDLED]
    machine_colours = {"Regius": "#1F3B57", "Ensis": "#2A9D8F", FLAT_NOT_BUNDLED: "#95A5A6"}

    # KPIS HERE
    kpi_df = build_flat_statii_machine_kpis(df)
    for kpicol, machine in zip(st.columns(3), machine_groups):
        kpicol.title(machine)
        for period in ["late", "this", "next"]:
            render_kpi_card(kpi_df, "Machine Group", machine, period, kpicol)

    # weeks and y scale come from all machines so the axes don't move when filtering
    weekly, y_max = build_grouped_saw_chart_data(df, "Machine Group", machine_groups)
    machine_option = st.selectbox("Machine", ["All"] + machine_groups, key="statii_machine")

    # chart here
    cap_col, _ = st.columns([1, 5])
    capacity = capacity_input("flat_cutting", cap_col)
    y_max = max(y_max, capacity)
    if machine_option == "All":
        chart_weekly, chart_colours, chart_capacity = weekly, machine_colours, capacity
    else:
        chart_weekly = weekly[weekly["Machine Group"] == machine_option]
        chart_colours = {machine_option: machine_colours[machine_option]}
        # capacity is split evenly between machines; not bundled work has no machine to measure against
        chart_capacity = None if machine_option == FLAT_NOT_BUNDLED else int(capacity // 2)
        df = df[df["Machine Group"] == machine_option]
    render_stacked_weekly_bar_chart(
        chart_weekly, "Week Label", "Hours Plan", "Machine Group", chart_colours,
        capacity=chart_capacity, show_75_line=False,
        y_max=y_max, overdue_col="Overdue Hours",
    )

    # table
    filtered_df = weld_table_filters(df, extra_cols=["Machine Group"])
    st.dataframe(filtered_df, column_config={"Date Requested": st.column_config.DateColumn("Date Requested", format="DD/MM/YY")}, hide_index=True)
else:
    st.title("Overview - Bundled Data")
    df = load_data_sp()
    df = df[df["Type"]=="FLAT"]
    df = clean_flat_data(df)
    df["Site"] = "Ballymena"
    df = add_flat_machine_group(df)

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