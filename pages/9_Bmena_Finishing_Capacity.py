import streamlit as st
import plotly.express as px
from data import *
from ui_components import *

page_setup("Ballymena Finishing Capacity")

if st.button("Refresh Statii Data"):
    statii_ballymena_finish_data.clear()
    st.rerun()

data = statii_ballymena_finish_data()
df = clean_paint_data_from_api(data)
df = df[~df["Specification"].str.contains("no finish", case=False, na=False)]

weekly = build_paint_plot_data(day_week_toggle=False, df=df)

render_weekly_bar_chart(
    weekly, "Week Label", "Price",
    highlight_week=False, show_75_line=False,
    y_title="Finish Value (£)", x_title="Week Ending",
    text_format="currency",
)

render_paint_table(weekly, df)

st.markdown("## Finish Type Breakdown")

def _finish_category(spec):
    s = str(spec).lower()
    if "e-coat" in s or "ecoat" in s or "e coat" in s:
        return "E-coat"
    if "protx" in s:
        return "ProtX"
    if "tjc" in s:
        return "TJC"
    if "galv" in s or "galvanised" in s:
        return "Galvanised"
    return "Other"

df["Finish Type"] = df["Specification"].apply(_finish_category)
pie_data = df.groupby("Finish Type", as_index=False)["Price"].sum()
named = pie_data[pie_data["Finish Type"] != "Other"].sort_values("Price", ascending=False)
other = pie_data[pie_data["Finish Type"] == "Other"]
pie_data = pd.concat([named, other], ignore_index=True)

fig = px.pie(pie_data, names="Finish Type", values="Price")
fig.update_traces(textinfo="label+percent", hovertemplate="%{label}<br>£%{value:,.0f}<extra></extra>",
                  sort=False)
st.plotly_chart(fig, use_container_width=True)