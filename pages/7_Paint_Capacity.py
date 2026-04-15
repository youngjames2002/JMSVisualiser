import streamlit as st
from data import *
from ui_components import *

st.set_page_config(layout="wide")

page_setup("Paint Capacity")

CAPACITY = 35000
CLOSE_CALL = 30000

st.markdown("""
Go to Sales Order Lines in Statii and export the report **'Paint Capacity'**  
It should show the columns Line No, Customer, Specification, Price and Date Promised. Ensure that ALL rows are shown and not limited to 100.  
Download that and then click 'open'. This should open a spreadsheet. Select All and copy, then paste that into the box below
""")
raw_data = st.text_area("Paste Statii Dump here")
st.markdown("Hit Ctrl+Enter to generate Capacity Graphs")

if not raw_data:
    st.stop()

df = parse_paint_data(raw_data)
df = clean_paint_data(df)

daily_view = st.toggle("Toggle Weekly View vs Daily View (Next Month)", value=False)
capacity = CAPACITY / 4 if daily_view else CAPACITY
close_call = CLOSE_CALL / 4 if daily_view else CLOSE_CALL

weekly = build_paint_plot_data(daily_view, df)
weekly.loc[weekly["Price"] >= close_call, "colour"] = "orange"
weekly.loc[weekly["Price"] > capacity, "colour"] = "red"

render_paint_chart(weekly, "Day" if daily_view else "Week Ending", capacity)

if not daily_view:
    render_paint_next_week(weekly, capacity)
    render_paint_table(weekly, df)