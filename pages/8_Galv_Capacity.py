import streamlit as st
from data import *
from ui_components import *
from metrics import *

page_setup("Galv Capacity")

data = statii_paint_data()
df = clean_galv_data(data)

daily_view = st.toggle("Toggle Weekly View vs Daily View (Next Month)", value=False)
weekly = build_paint_plot_data(daily_view, df)

render_galv_chart(weekly, weekly["Price"].max())
render_paint_table(weekly, df)