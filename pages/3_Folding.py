import streamlit as st
from data import *
from metrics import *
from ui_components import *

page_setup("Folding")

max_capacity = 80
capacity = 80

statii_toggle = st.toggle("Toggle Bundled Data and Statii Data")
if statii_toggle:
    if st.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    st.title("Overview - Statii Data")
    df = statii_bundle_jobs("Brake Press")
    df = clean_statii_bundle_data(df)

    # build and render kpis
    kpi_df = build_weld_kpis(df)
    kpicol1, kpicol2 = st.columns(2)
    kpicol1.title("Kilrea")
    render_weld_kpi(kpi_df, "Kilrea", "late", kpicol1)
    render_weld_kpi(kpi_df, "Kilrea", "this", kpicol1)
    render_weld_kpi(kpi_df, "Kilrea", "next", kpicol1)
    kpicol2.title("Ballymena")
    render_weld_kpi(kpi_df, "Ballymena", "late", kpicol2)
    render_weld_kpi(kpi_df, "Ballymena", "this", kpicol2)
    render_weld_kpi(kpi_df, "Ballymena", "next", kpicol2)

    site_option = st.selectbox("Site", ["Kilrea", "Ballymena", "Both Sites"], key="statii_site")
    if site_option == "Both Sites":
        site = None
        capacity = max_capacity * 2
    else:
        site = site_option
        capacity = max_capacity
    st.markdown(f"""<h3>Currently showing: {site_option}<h3>""", unsafe_allow_html=True)

    # build and render chart
    if site is not None:
        df = df[df["Site"] == site]
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

    site_option = st.selectbox("Site", ["Kilrea", "Ballymena", "Both Sites"], key="bundle_site")
    if site_option == "Both Sites":
        site = None
        capacity = max_capacity * 2
    else:
        site = site_option
        capacity = max_capacity
    st.markdown(f"""<h3>Currently showing: {site_option}<h3>""", unsafe_allow_html=True)

    # chart here
    weekly, y_max = build_fold_chart_data(clean_df, site)
    y_max = max(y_max, max_capacity)
    render_weekly_bar_chart(
        weekly, "Week Label", "Estimated Fold Time (Hours)",
        capacity=capacity, show_75_line=True,
        y_max=y_max, text_col="Hours", overdue_col="Overdue Hours",
    )

    # table
    render_fold_table(clean_df, site)