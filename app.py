import streamlit as st
from data import *
from metrics import *
from ui_components import *

st.set_page_config(layout="wide")

#load css
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css('stylesheet.css')

if "selected_bundle" not in st.session_state:
    st.session_state.selected_bundle = None

# title
st.title("Bundle Data Visualiser - Admin View")

# load data from sheet
# !!!! CHANGE THIS WHEN SWITCHING MACHINES !!!!
filepath = "C:\\Users\\james\\JMS Metaltec\\JMS Engineering Team - JMS Engineering Team SharePoint\\JMS Master Schedule\\testAutomation\\bundleStagingSheet.xlsx"
df = load_data(filepath)
df = add_date_columns(df)

# filter by lateness, customer and machine
# tidy this into better functions and add filter for complete or not (in same manner as late filter)
filtered_df = render_filter_section(df)

# render at a glance section
render_at_a_glance(filtered_df)

# render cards section
render_cards_titles()
col1, col2, col3, col4 = st.columns(4)
late_df, week_df, future_df = split_by_urgency(filtered_df)
render_cards(late_df, col1)
render_cards(week_df, col2)
render_cards(future_df, col3)
render_side_panel(df)

# bar chart of hours due by day
render_bar_chart(filtered_df, col4)
render_line_chart(filtered_df, col4)

# progress bar of complete hours
render_progress_bar(filtered_df, col4)