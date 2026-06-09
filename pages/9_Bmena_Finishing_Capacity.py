import streamlit as st
import plotly.express as px
from data import *
from ui_components import *

page_setup("Ballymena Finishing Capacity")

if st.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()

data = statii_ballymena_finish_data()
df = clean_paint_data_from_api(data)
df = df[~df["Specification"].str.contains("no finish", case=False, na=False)]
df = df[~df["Specification"].str.contains("natural", case=False, na=False)]
df = df[~df["Specification"].str.contains("mill", case=False, na=False)]

weekly = build_paint_plot_data(day_week_toggle=False, df=df)

render_weekly_bar_chart(
    weekly, "Week Label", "Price",
    highlight_week=False, show_75_line=False,
    y_title="Finish Value (£)", x_title="Week Ending",
    text_format="currency",
)

render_paint_table(weekly, df)
render_bmena_finish_pie(df)