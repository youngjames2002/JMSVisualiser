import streamlit as st
from data import *
from metrics import *
from ui_components import *

import plotly.io as pio
pio.templates.default = "simple_white"

from login import require_auth
require_auth()

st.set_page_config(layout="wide")

#load css
load_css('stylesheet.css')

# load data from sheet
# !!!! CHANGE THIS WHEN SWITCHING MACHINES !!!!
df = load_data_sp()

#title
tcol1, tcol2 = st.columns([1,4])
tcol2.title("Bundles Capacity Overview")
render_logo(tcol1)

# folding, flat and tube cutting need shown as
# just hours/total possible
# visualise this as progress bars and colour coded
# show as a ratio for both 75% and MAX
# replicate filters most likely?

#filters
late_only, incomplete_only, selected_customers, selected_machines, bundle_search,folding_required = render_filter_section(df)
filtered_df = apply_filters(df, late_only, incomplete_only, selected_customers, selected_machines, bundle_search,folding_required)

#column titles
col1, col2, col3 = st.columns(3)
render_capacity("Tube Cutting", filtered_df, col1)
render_capacity("Flat Cutting", filtered_df, col2)
render_capacity("Folding", filtered_df, col3)

# refresh data
if st.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()
    df = load_data_sp()
st.markdown("Note: It will take a few minutes after changes are made on sharepoint before they can register on the dashboard")