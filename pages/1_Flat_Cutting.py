import streamlit as st
from data import *
from metrics import *
from ui_components import *

page_setup("Flat Cutting")

df = load_data_sp()
df = df[df["Type"]=="FLAT"]

clean_df = clean_flat_data(df)
 # strip Site = all flat is Bmena
clean_df = clean_df.drop(["Site"], axis=1)
kpi_df = build_tube_kpis(clean_df)

# KPIS HERE
st.title("Overview")
render_saw_bundle_kpi(kpi_df, "late")
render_saw_bundle_kpi(kpi_df, "this")
render_saw_bundle_kpi(kpi_df, "next")


# chart here
weekly = build_tube_chart_data(clean_df)
capacity=capacity_hours("Flat Cutting")
y_max = max(capacity, weekly["Estimated Bundle Time (Hours)"].max())
render_flat_chart(weekly, capacity, y_max)

# table
render_tube_table(clean_df)