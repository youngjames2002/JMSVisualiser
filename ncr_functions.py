import streamlit as st
import plotly.express as px
import pandas as pd

def clean_ncr_data(df):
    # clean data massively
    # filter nulls
    df = df[df['Description'].isna() == False]
    return df

def render_basic_counts(df):
    # output raw counts of numbers
    # total number of ncrs
    after_2025 = df[df["Date"] >= "2025-01-01"]
    st.markdown(f"NCRs from start of 2025: {len(after_2025.index)}")

    # number by department
    unique_departments = after_2025["Department"].dropna().unique().tolist()
    st.markdown(f"Unique Department List: {unique_departments}")

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
    # number by customer
    unique_customers = after_2025["Customer"].dropna().unique().tolist()
    st.markdown(f"Unique Customer List: {unique_customers}")
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
    # number by person recording ncr
    # number that are internal
    # number that are external
    # number per standardised root cause
    # number per suggested corrective action completed
    # number returned to customer
    # number of reports done
