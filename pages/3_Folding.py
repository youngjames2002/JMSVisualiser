import streamlit as st
from data import *
from metrics import *
from ui_components import *

page_setup("Folding")

df = load_data_sp()
df = df[df["Folding Required?"]=="Yes"]

clean_df = clean_fold_data(df)
kpi_df = build_fold_kpis(clean_df)

# render KPIS here
kpicol1, kpicol2 = st.columns(2)
kpicol1.title("Kilrea")
render_weld_kpi(kpi_df, "Kilrea", "late", kpicol1)
render_weld_kpi(kpi_df, "Kilrea", "this", kpicol1)
render_weld_kpi(kpi_df, "Kilrea", "next", kpicol1)
kpicol2.title("Ballymena")
render_weld_kpi(kpi_df, "Ballymena", "late", kpicol2)
render_weld_kpi(kpi_df, "Ballymena", "this", kpicol2)
render_weld_kpi(kpi_df, "Ballymena", "next", kpicol2)

max_capacity = 80
capacity = 80

# site toggle
site_filter = st.toggle("Toggle Site")
if site_filter:
    site="Ballymena"
else:
    site="Kilrea"
st.markdown(f"""<h3>Currently showing: {site}<h3>""", unsafe_allow_html=True)

# chart here
weekly, y_max = build_fold_chart_data(clean_df, site)
y_max = max(y_max, max_capacity)
render_weekly_bar_chart(
    weekly, "Week Label", "Estimated Fold Time (Hours)",
    capacity=capacity, show_75_line=True,
    y_max=y_max, text_col="Hours", overdue_col="Overdue Hours",
)

# table
render_fold_table(clean_df, site)