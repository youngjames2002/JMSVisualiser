import streamlit as st
import plotly.express as px
import pandas as pd

def clean_ncr_data(df):
    # clean data massively

    # parse dates
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Date Complete"] = pd.to_datetime(df["Date Complete"], errors="coerce")

    # Standardise Y/N columns
    yn_cols = ["Returned to Customer", "Report Done"]
    for col in yn_cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .str.upper()
                .replace({"Y": "Yes", "N": "No"})
            )

    # completion flag for suggeastive action implemented
    df["Suggested Corrective Action Implemented"] = df["Date Complete"].notna().map(
        {True: "Yes", False: "No"}
    )
    # fill missing data with 'Data Unknown' for str columns
    for col in ['Non Conformance Received/Recorded By', 'Description', 'Department', 'Root Cause']:
        df[col] = df[col].fillna("Data Unknown")

    # tidy input (strip trailing spaces and standardise capitilasition)
    cols_to_tidy = ["Customer", "Department"]
    for col in cols_to_tidy:
        df[col] = (
            df[col].astype(str).str.strip().str.replace(r"\s+", " ", regex=True).str.title()
        )
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
    root_causes = after_2025["Root Cause"].dropna().unique().tolist()
    st.markdown(f"Root Causes List: {root_causes}")
    root_causes_df = (
        after_2025["Root Cause"]
        .value_counts()
        .reset_index()
    )

    root_causes_df.columns = ["Root Cause", "count"]
    root_causes_df = root_causes_df[root_causes_df["count"] >= 2]
    root_causes_df["percentage of all"] = (
        (root_causes_df["count"] / len(after_2025.index)) *100
    )
    st.dataframe(root_causes_df)
    # number per suggested corrective action completed
    # number returned to customer
    # number of reports done
