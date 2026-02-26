import streamlit as st
from data import *
from ui_components import *
from ncr_functions import *

import plotly.io as pio
pio.templates.default = "simple_white"

st.set_page_config(layout="wide")

#load css
load_css('stylesheet.css')

# title
tcol1, tcol2 = st.columns([1,4])
tcol2.title("NCR Log Overview")
render_logo(tcol1)

# load data from sheet
df = load_data_ncr_local()
df = clean_ncr_data(df)

st.dataframe(df)

# recorded by

# Customer NCR nos - n/a means none, blank means internal
# currently n/a switch to "No Official NCR"
# start logging internal ones as "Internal"

# standardised by description

# add columns for quantity, part numner, Assembly as well? - ask eric

# multiple ways to be complete
# either by sending it back or by the corrective action being implemented
# report done
# show which ones are outstanding and number of outstanding by each type

# for getting percentages - relate one defect to one sales order - if one part of a sales order is defect the whole thing
# percentage is % of Sales orders present in NCR log / total sales orders sent out - in a given time frame

# total internal ncrs is just a number


# PLAN for this
# clean data
# present basic info
# read data from statii
# use that as comparison to create percentage charts and graphs and more advanced details.
