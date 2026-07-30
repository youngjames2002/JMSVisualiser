import streamlit as st
from data import *
from metrics import *
from ui_components import *

page_setup("Total Order Value By Month")
st.markdown("_Displays All Sales Orders present on Statii and their Value, grouped by Month on SO Date Promised_")

all_so = load_so_statii()

last_year = pd.Timestamp.now() - pd.DateOffset(years=1)
filter_date = st.date_input(label="Showing all orders since",value=last_year)
st.markdown("_(Defaults to past 12 months)_")
value_by_month = build_order_value_by_month(all_so, filter_date)

average = value_by_month["value"].mean()

render_weekly_bar_chart(
    value_by_month, "month_label", "value",
    color="bar_color", highlight_week=False, show_75_line=False,
    y_title="Value (£)", x_title="Month",
    text_format="currency", hover_suffix="", capacity=average, capacity_label="Average"
)
