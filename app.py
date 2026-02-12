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
filepath = "C:\\Users\\james\\JMS Metaltec\\JMS Engineering Team - JMS Engineering Team SharePoint\\JMS Master Schedule\\testAutomation\\bundleStagingSheet.xlsx"
df = load_data(filepath)
df = add_date_columns(df)

# sort by late status
late_df, week_df, future_df = split_by_urgency(df)

# calculate cut/fold hours for at a glance
total_folding, flat_cutting, tube_cutting = calculate_totals(df)

# render at a glance section
st.markdown("<h2>At a Glance</h2>", unsafe_allow_html=True)
late_only = st.toggle("Show Late Bundles Only")
if late_only:
    metrics_df = df[df["Is Late"] == True]
else:
    metrics_df = df
total_folding, flat_cutting, tube_cutting = calculate_totals(metrics_df)
render_at_a_glance(flat_cutting, tube_cutting, total_folding)

# render cards section
render_cards_section()
col1, col2, col3 = st.columns(3)
render_cards(late_df, col1)
render_cards(week_df, col2)
render_cards(future_df, col3)