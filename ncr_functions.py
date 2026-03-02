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
    cols_to_tidy = ["Customer", "Department", "Non Conformance Received/Recorded By"]
    for col in cols_to_tidy:
        df[col] = (
            df[col].astype(str).str.strip().str.replace(r"\s+", " ", regex=True).str.title()
        )
    return df

def render_basic_counts(df, date_filter):
    # output raw counts of numbers
    # total number of ncrs
    date_filter = pd.to_datetime(date_filter)
    after_2025 = df[df["Date"] >= date_filter]
    st.markdown(f"NCRs from {date_filter}: {len(after_2025.index)}")

    # number by department
    list_and_df("Department", after_2025)
    # number by customer
    list_and_df("Customer", after_2025)
    # number by person recording ncr
    list_and_df("Non Conformance Received/Recorded By", after_2025)
    # number that are internal
    # number that are external
    # number per standardised root cause
    list_and_df("Root Cause", after_2025)
    # number per suggested corrective action completed
    # number returned to customer
    # number of reports done

def list_and_df(column, df):
    unique_list = df[column].dropna().unique().tolist()
    st.markdown(f"Unique {column} List: {unique_list}")
    unique_df = (
        df[column].value_counts().reset_index()
    )
    unique_df.columns = [column, "count"]
    unique_df["percentage of all"] = (
        (unique_df["count"] / len(df.index)) *100
    )
    st.dataframe(unique_df)    