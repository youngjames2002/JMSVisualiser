import streamlit as st
from data import *
from ui_components import *

st.set_page_config(layout="wide")

#load css
load_css('stylesheet.css')

# load data from sheet
# !!!! CHANGE THIS WHEN SWITCHING MACHINES !!!!
df = load_data_Bmena_sp()

#title
tcol1, tcol2 = st.columns([1,4])
tcol2.title("Ballymena Unaccounted Finishing Jobs")
render_logo(tcol1)

#display cards
st.markdown("Showing all records with due date this week or before, with no value for delivery date, supplier or comments")
render_bmena_finishing_cards(df)

# refresh data
if st.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()
    df = load_data_Bmena_sp()
st.markdown("Note: It will take a few minutes after changes are made on sharepoint before they can register on the dashboard")