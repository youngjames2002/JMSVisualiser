import streamlit as st
from data import *
from metrics import *
from ui_components import *

import plotly.io as pio
pio.templates.default = "simple_white"

st.set_page_config(layout="wide")

#load css
load_css('stylesheet.css')

if "selected_bundle" not in st.session_state:
    st.session_state.selected_bundle = None

# title
tcol1, tcol2 = st.columns([1,4])
tcol2.title("Bundles Overview")
render_logo(tcol1)

# load data from sheet
df = load_data_sp()

# at a glance placholder
at_a_glance_container = st.container()

# filter by lateness, customer and machine
st.divider()
late_only, incomplete_only, selected_customers, selected_machines, bundle_search, folding_required = render_filter_section(df)
st.divider()
filtered_df = apply_filters(df, late_only, incomplete_only, selected_customers, selected_machines, bundle_search, folding_required)

# render at a glance section
late_df, week_df, future_df = split_by_urgency(filtered_df)
with at_a_glance_container:
    render_at_a_glance(filtered_df,late_df, week_df, future_df)

# render cards section
render_cards_titles()
col1, col2, col3, col4 = st.columns(4)
render_cards(late_df, col1, key_prefix="late")
render_cards(week_df, col2, key_prefix="week")
render_cards(future_df, col3, key_prefix="future")
render_side_panel(filtered_df)

# bar chart of hours due by day
melted = bar_chart_hours_by_date(df)
render_bar_chart(melted, col4)
render_line_chart(melted, col4)

# progress bar of complete hours
render_progress_bar(filtered_df, col4)

# refresh data
if st.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()
    df = load_data_sp()
st.markdown("Note: It will take a few minutes after changes are made on sharepoint before they can register on the dashboard")