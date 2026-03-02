import streamlit as st
import plotly.express as px
import pandas as pd
from data import *

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

    # log as internal (replacing null), "No Official NCR" (replacing n/a) or the customer NCR for "Customer NCR No column"
    df["Customer NCR No."] = (
        df["Customer NCR No."].replace("N/A", "No Official NCR No.").fillna("Internal")
    )

    # sort companies being reported differently
    df = apply_company_grouping(df)
    return df

def render_debug_data(df, date_filter):
    st.markdown("### DEBUGGING ZONE")
    # output raw counts of numbers
    # total number of ncrs
    date_filter = pd.to_datetime(date_filter)
    date_filtered_df = df[df["Date"] >= date_filter]
    st.dataframe(date_filtered_df)
    st.markdown(f"NCRs from {date_filter}: {len(date_filtered_df.index)}")

    # number by department
    list_and_df("Department", date_filtered_df)
    # number by customer
    list_and_df("Customer", date_filtered_df)
    # number by person recording ncr
    list_and_df("Non Conformance Received/Recorded By", date_filtered_df)
    # number that are internal
    st.markdown(f"No. of Internal NCRS: {(date_filtered_df["Customer NCR No."] == "Internal").sum()}")
    # number that are external
    st.markdown(f"No. of External NCRS: {(date_filtered_df["Customer NCR No."] != "Internal").sum()}")
    # number per standardised root cause
    list_and_df("Root Cause", date_filtered_df)
    # number per suggested corrective action completed
    SCA_completed = len(date_filtered_df) - (date_filtered_df["Suggested Corrective Action Implemented"] == "Yes").sum()
    SCA_percent = round((SCA_completed/len(date_filtered_df))*100,2)
    st.markdown(f"Number of NCRS with suggested corrective action completed: {SCA_completed} ({SCA_percent}%)")
    # number returned to customer
    RTC_completed = len(date_filtered_df) - (date_filtered_df["Returned to Customer"]=="Yes").sum()
    RTC_percent = round((RTC_completed/len(date_filtered_df))*100,2)
    st.markdown(f"Number of NCRS returned to customer: {RTC_completed} ({RTC_percent}%)")
    # number of reports done
    report_done = len(date_filtered_df) - (date_filtered_df["Report Done"]=="Yes").sum()
    report_percent = round((report_done/len(date_filtered_df))*100,2)
    st.markdown(f"Number of NCRS with report completed: {report_done} ({report_percent}%)")

def list_and_df(column, df):
    unique_list = df[column].dropna().unique().tolist()
    st.markdown(f"Unique {column} List: {unique_list}")
    unique_df = (
        df[column].value_counts().reset_index()
    )
    unique_df.columns = [column, "count"]
    unique_df[f"% of total"] = (
        (unique_df["count"] / len(df.index)) *100
    )
    st.dataframe(unique_df) 

def render_df(df, col, header):
    col.markdown(f"Count By {header}")
    unique_df = (
        df[header].value_counts().reset_index()
    )
    unique_df.columns = [header, "count"]
    unique_df[f"% of total"] = (
        round(((unique_df["count"] / len(df.index)) *100), 2)
    )
    col.dataframe(unique_df, hide_index=True) 

def render_progress_bars(df, col):
    # Suggested Corrective Action
    SCA_completed = len(df) - (df["Suggested Corrective Action Implemented"] == "Yes").sum()
    SCA_percent = round((SCA_completed/len(df)),2)
    col.progress(float(SCA_percent), f"Number of NCRS with suggested corrective action completed: {SCA_completed} ({SCA_percent*100}%)")
    # Returned to Customer
    RTC_completed = len(df) - (df["Returned to Customer"] == "Yes").sum()
    RTC_percent = round((RTC_completed/len(df)),2)
    col.progress(float(RTC_percent), f"Number of NCRS returned to customer: {RTC_completed} ({RTC_percent*100}%)")
    # Report Done
    report_done = len(df) - (df["Report Done"] == "Yes").sum()
    report_percent = round((report_done/len(df)),2)
    col.progress(float(report_percent), f"Number of NCRS with report completed: {int(report_done)} ({report_percent*100:.1f}%)")

def render_internal_chart(df, col):
    counts = df["Customer NCR No."].value_counts()

    internal = counts.get("Internal", 0)
    external = counts.sum() - internal

    col.metric("Internal NCRs", internal)
    col.metric("External NCRs", external)

    pie_data = pd.DataFrame({
        "Type": ["Internal", "External"],
        "Count": [internal, external]
    })


    # Pie chart for proportion
    fig = px.pie(
        pie_data, names="Type", values="Count", hole=0.4, color="Type",
        color_discrete_map={"Internal": "#2ecc71", "External": "#3498db"}
    )
    col.plotly_chart(fig, use_container_width=False)

def render_sales_order_chart(df, date_filter, col):
    # read in all sales orders since date that is filtered from statii
    # done reading from a hardcoded CSV file, will upgrade to be an API call when we get that functionality from statii
    # have to do a dump out and save to NCR Log/ALL SALES ORDERS.csv on sharepoint
    so_df = load_so_sp()
    # filter so_df by date filter
    date_filter = pd.to_datetime(date_filter)
    so_df["Date Created"] = pd.to_datetime(so_df["Date Created"])
    so_df = so_df[so_df["Date Created"] >= date_filter]
    # st.dataframe(so_df) # debug

    num_so = len(so_df)
    num_ncr = len(df)

    # visualise data
    col.metric(f"Number of NCRs since {date_filter}:", num_ncr)
    col.metric(f"Number of SOs since {date_filter}:", num_so)

    pie_data = pd.DataFrame({
        "Type": ["NCRs", "SOs"],
        "Count": [num_ncr, num_so]
    })


    # Pie chart for proportion
    fig = px.pie(
        pie_data, names="Type", values="Count", hole=0.4, color="Type",
        color_discrete_map={"NCRs": "#2ecc71", "SOs": "#3498db"}
    )
    col.plotly_chart(fig, use_container_width=False)