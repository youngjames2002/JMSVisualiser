import streamlit as st
from data import *
from metrics import *
from ui_components import *

page_setup("Flat Cutting")

capacity=capacity_hours("Flat Cutting")

statii_toggle = st.toggle("Toggle Statii Data and Bundled Data")
if statii_toggle:
    if st.button("Refresh Statii Data"):
        statii_bundle_jobs.clear()
        st.rerun()
    st.title("Overview - Statii Data")
    df = statii_bundle_jobs("Laser - Flat")
    df = clean_statii_bundle_data(df)
    df["Site"] = "Ballymena"

    # build and render kpis
    kpi_df = build_saw_kpis(df)
    render_saw_bundle_kpi(kpi_df, "late")
    render_saw_bundle_kpi(kpi_df, "this")
    render_saw_bundle_kpi(kpi_df, "next")

    # build and render chart
    weekly, y_max = build_saw_chart_data(df)
    render_weekly_bar_chart(
        weekly, "Week Label", "Hours Plan",
        capacity=capacity, show_75_line=True,
        y_max=y_max, text_col="Hours", overdue_col="Overdue Hours",
    )

    # table
    filtered_df = weld_table_filters(df)
    st.dataframe(filtered_df, column_config={"Date Requested": st.column_config.DateColumn("Date Requested", format="DD/MM/YY")})
else:
    st.title("Overview - Bundled Data")
    df = load_data_sp()
    df = df[df["Type"]=="FLAT"]
    df = clean_flat_data(df)
    df["Site"] = "Ballymena"
    kpi_df = build_tube_kpis(df)
    weekly, y_max = build_tube_chart_data(df)


    # KPIS HERE
    render_saw_bundle_kpi(kpi_df, "late")
    render_saw_bundle_kpi(kpi_df, "this")
    render_saw_bundle_kpi(kpi_df, "next")

    # chart here

    render_weekly_bar_chart(
        weekly, "Week Label", "Estimated Bundle Time (Hours)",
        capacity=capacity, show_75_line=True,
        y_max=y_max, text_col="Hours", overdue_col="Overdue Hours",
    )

    # table
    render_tube_table(df)