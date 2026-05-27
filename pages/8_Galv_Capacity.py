import streamlit as st
from data import *
from ui_components import *
from metrics import *

page_setup("Galv Capacity")

if st.button("Refresh Statii Data"):
    statii_galv_data.clear()
    st.rerun()

data = statii_galv_data()
df = clean_galv_data(data)

daily_view = st.toggle("Toggle Weekly View vs Daily View (Next Month)", value=False)
weekly = build_paint_plot_data(daily_view, df)

render_weekly_bar_chart(
    weekly, "Week Label", "Price",
    color="green", highlight_week=False,
    y_max=weekly["Price"].max(),
    y_title="Value (£)", x_title="Day" if daily_view else "Week Ending",
    text_format="currency",
)
if not daily_view:
    render_paint_table(weekly, df)