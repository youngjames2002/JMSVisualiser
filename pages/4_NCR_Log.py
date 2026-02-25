import streamlit as st
from data import *
from metrics import *
from ui_components import *

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
#filter nulls
df = df[df['Description'].isna() == False]

st.dataframe(df)

# display basic info
# no of ncrs in this table
no_ncrs = len(df.index)
st.markdown(f"NCRs listed in table: {no_ncrs}")
# no of ncrs since 2025
after_2025 = df[df["Date"] >= "2025-01-01"]
st.markdown(f"NCRs from start of 2025: {len(after_2025.index)}")

# basic counts off what we have so far
# list of unique customers
unique_customers = after_2025["Customer"].dropna().unique().tolist()
st.markdown(f"Unique Customer List: {unique_customers}")
# number by customer
customer_counts_df = (
    after_2025["Customer"]
    .value_counts()
    .reset_index()
)

customer_counts_df.columns = ["Customer", "count"]
customer_counts_df["percentage"] = (
    (customer_counts_df["count"] / len(after_2025.index)) *100
)
st.dataframe(customer_counts_df)
# list of unique departments
unique_departments = after_2025["Department"].dropna().unique().tolist()
st.markdown(f"Unique Department List: {unique_departments}")
# number by department
department_count_df = (
    after_2025["Department"]
    .value_counts()
    .reset_index()
)

department_count_df.columns = ["Department", "count"]
department_count_df["percentage"] = (
    (department_count_df["count"] / len(after_2025.index)) *100
)
st.dataframe(department_count_df)

