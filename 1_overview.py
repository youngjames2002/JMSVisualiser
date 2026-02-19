import streamlit as st
from data import *
from metrics import *
from ui_components import *

st.set_page_config(layout="wide")

#load css
load_css('stylesheet.css')

if "selected_bundle" not in st.session_state:
    st.session_state.selected_bundle = None

# title
st.title("Bundle Data Visualiser - Admin View")

# load data from sheet
df = load_data()

# at a glance placholder
at_a_glance_container = st.container()

# filter by lateness, customer and machine
st.divider()
late_only, incomplete_only, selected_customers, selected_machines = render_filter_section(df)
st.divider()
filtered_df = apply_filters(df, late_only, incomplete_only, selected_customers, selected_machines)

# render at a glance section
late_df, week_df, future_df = split_by_urgency(filtered_df)
with at_a_glance_container:
    render_at_a_glance(filtered_df,late_df, week_df, future_df)

# render cards section
render_cards_titles()
col1, col2, col3, col4 = st.columns(4)
render_cards(late_df, col1)
render_cards(week_df, col2)
render_cards(future_df, col3)
render_side_panel(filtered_df)

# bar chart of hours due by day
render_bar_chart(filtered_df, col4)
render_line_chart(filtered_df, col4)

# progress bar of complete hours
render_progress_bar(filtered_df, col4)