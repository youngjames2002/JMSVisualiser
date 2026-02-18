import streamlit as st
from data import *
from metrics import *
from ui_components import *

st.set_page_config(layout="wide")

#load css
load_css('stylesheet.css')

# load data from sheet
# !!!! CHANGE THIS WHEN SWITCHING MACHINES !!!!
df = load_data()

#title
st.title("Capacity Overview")

# folding, flat and tube cutting need shown as
# just hours/total possible
# visualise this as progress bars and colour coded
# show as a ratio for both 75% and MAX
# replicate filters most likely?

#filters
late_only, incomplete_only, selected_customers, selected_machines = render_filter_section(df)
filtered_df = apply_filters(df, late_only, incomplete_only, selected_customers, selected_machines)

#column titles
col1, col2, col3 = st.columns(3)
render_capacity("Tube Cutting", filtered_df, col1)
render_capacity("Flat Cutting", filtered_df, col2)
render_capacity("Folding", filtered_df, col3)