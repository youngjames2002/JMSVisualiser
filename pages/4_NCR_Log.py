import streamlit as st
from data import *
from ui_components import *
from ncr_functions import *

import plotly.io as pio
pio.templates.default = "simple_white"

st.set_page_config(layout="wide")

#load css
load_css('stylesheet.css')

# title
tcol1, tcol2 = st.columns([1,4])
tcol2.title("NCR Log Overview")
render_logo(tcol1)

# load data from sheet
df = load_data_ncr_sp()
df = clean_ncr_data(df)

# date filter
col1, col2 = st.columns([1, 4])
with col1:
    date_filter = st.date_input("Showing Only Data after this date: ", value=datetime.datetime(2025,1,1))
date_filter = pd.to_datetime(date_filter)
df = df[df["Date"] >= date_filter]

# sales order metrics and chart
col1, col2 = st.columns(2)
col1.markdown("## Sales Orders Impact")
col2.markdown("## Impact Over Time")
so_df = load_so_sp()
render_sales_order_impact(df, so_df, date_filter, col1)
weekly = calculate_weekly_impact(df, so_df)
render_impact_chart(weekly,date_filter,col2)


# internal/external and completion status
col1, col2 = st.columns(2)
col1.markdown("## Internal vs External Count")
col2.markdown("## Completion Status")
render_internal_chart(df, col1)
render_progress_bars(df, col2)


# render overview dataframes
col1, col2, col3, col4 = st.columns(4)
col1.markdown(f"Count By Customer")
render_df(df, col1, "Customer Grouped")
col2.markdown(f"Count By Department")
render_df(df, col2, "Department")
col3.markdown(f"Count By Person Reporting")
render_df(df, col3, "Non Conformance Received/Recorded By")
col4.markdown(f"Count By Root Cause")
render_df(df, col4, "Root Cause")

st.markdown(f"## FULL NCR LOG SINCE {date_filter.strftime('%d %b %Y')}")
st.dataframe(df)

# refresh data
if st.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()
    df = load_data_ncr_sp()
    df = clean_ncr_data(df)
st.markdown("Note: It will take a few minutes after changes are made on sharepoint before they can register on the dashboard")

# ts debugs
debug = st.toggle("View Debug Data?", value=False)
if debug:
    render_debug_data(df, date_filter)
