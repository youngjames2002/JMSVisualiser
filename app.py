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
late_only, selected_customers, selected_machines, customers, machines = render_filter_section(df)
filtered_df = apply_filters(df, late_only, selected_customers, selected_machines, customers, machines)

# calculate cut/fold hours for at a glance
total_folding, flat_cutting, tube_cutting = calculate_totals(filtered_df)

# render at a glance section
st.markdown("<h2>At a Glance</h2>", unsafe_allow_html=True)
# late_only = st.toggle("Show Late Bundles Only")
if late_only:
    metrics_df = filtered_df[filtered_df["Is Late"] == True]
else:
    metrics_df = filtered_df
total_folding, flat_cutting, tube_cutting = calculate_totals(metrics_df)
render_at_a_glance(flat_cutting, tube_cutting, total_folding)

# render cards section
render_cards_section()
col1, col2, col3 = st.columns(3)
late_df, week_df, future_df = split_by_urgency(filtered_df)
render_cards(late_df, col1)
render_cards(week_df, col2)
render_cards(future_df, col3)

# bar chart of hours due by day
render_bar_chart(filtered_df)
