import streamlit as st
from data import *
from metrics import *
from ui_components import *

page_setup("Total Order Value By Month")

all_so = load_so_statii()

last_year = pd.Timestamp.now() - pd.DateOffset(years=1)
filter_date = st.date_input(label="Showing all orders since",value=last_year)
st.markdown("_(Defaults to past 12 months)_")

st.subheader("Expected Value")
st.markdown("_Displays All Sales Orders present on Statii and their Value, grouped by Month on SO Date Promised_")

value_by_month_promised = build_order_value_by_month(all_so, filter_date, date_column="date_promised")

render_weekly_bar_chart(
    value_by_month_promised, "month_label", "value",
    color="bar_color", highlight_week=False, show_75_line=False,
    y_title="Value (£)", x_title="Month",
    text_format="currency", hover_suffix=""
)

st.subheader("Actual Delivered Value")
st.markdown("_Displays All Sales Orders present on Statii and their Value, grouped by Month on SO Date Completed, fitlering out incomplete jobs_")

value_by_month_completed = build_order_value_by_month(all_so, filter_date, date_column="date_completed")
value_by_month_completed = align_value_by_month(value_by_month_completed, value_by_month_promised)

render_weekly_bar_chart(
    value_by_month_completed, "month_label", "value",
    color="bar_color", highlight_week=False, show_75_line=False,
    y_title="Value (£)", x_title="Month",
    text_format="currency", hover_suffix=""
)

st.subheader("Actual vs Expected (Difference)")
st.markdown("_Green: Actual Delivered exceeded Expected. Red: Actual Delivered fell short of Expected. Hatched: no Actual Delivered value yet._")

value_by_month_diff = build_value_diff_by_month(value_by_month_promised, value_by_month_completed)

render_weekly_bar_chart(
    value_by_month_diff, "month_label", "value",
    color="bar_color", highlight_week=False, show_75_line=False,
    y_title="Value (£)", x_title="Month",
    text_format="currency", hover_suffix="",
    pattern_col="no_actual_data"
)
