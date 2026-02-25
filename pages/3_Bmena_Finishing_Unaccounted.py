import streamlit as st
from data import *
from ui_components import *

st.set_page_config(layout="wide")

#load css
load_css('stylesheet.css')

# load data from sheet
# !!!! CHANGE THIS WHEN SWITCHING MACHINES !!!!
df = load_data_Bmena_local()

#title
st.title("Ballymena Unaccounted Finishing Jobs")

#display cards
render_bmena_finishing_cards(df)