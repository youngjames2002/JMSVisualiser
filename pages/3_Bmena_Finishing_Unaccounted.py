import streamlit as st
from data import *
from ui_components import *

st.set_page_config(layout="wide")

#load css
load_css('stylesheet.css')

#title
tcol1, tcol2 = st.columns([1,4])
tcol2.title("Ballymena Unaccounted Finishing Jobs")
render_logo(tcol1)

#display cards
st.markdown("Showing all records with due date this week or before, with no value for delivery date, supplier or comments")
render_bmena_finishing_cards