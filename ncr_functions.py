import streamlit as st
import plotly.express as px
import pandas as pd
from data import *
from datetime import timedelta

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

    # Create week column
    df["Week"] = df["Date"].dt.to_period("W").dt.start_time
    return df

def render_debug_data(df, date_filter):
    st.markdown("### DEBUGGING ZONE")
    # output raw counts of numbers
    # total number of ncrs
    date_filter = pd.to_datetime(date_filter)
    date_filtered_df = df[df["Date"] >= date_filter]
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
    col.progress(float(SCA_percent), f"NCRS with suggested corrective action completed: {SCA_completed} ({SCA_percent*100}%)")
    # Returned to Customer
    RTC_completed = len(df) - (df["Returned to Customer"] == "Yes").sum()
    RTC_percent = round((RTC_completed/len(df)),2)
    col.progress(float(RTC_percent), f"NCRS returned to customer: {RTC_completed} ({RTC_percent*100}%)")
    # Report Done
    report_done = len(df) - (df["Report Done"] == "Yes").sum()
    report_percent = round((report_done/len(df)),2)
    col.progress(float(report_percent), f"NCRS with report completed: {int(report_done)} ({report_percent*100:.1f}%)")

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

def render_sales_order_impact(df, so_df, date_filter, col):
    # read in all sales orders since date that is filtered from statii
    # done reading from a hardcoded CSV file, will upgrade to be an API call when we get that functionality from statii
    # have to do a dump out and save to NCR Log/ALL SALES ORDERS.csv on sharepoint
    # filter so_df by date filter
    date_filter = pd.to_datetime(date_filter)
    so_df["Date Required"] = pd.to_datetime(so_df["Date Required"], format="%d/%m/%y")
    so_df = so_df[so_df["Date Required"] >= date_filter]
    # st.dataframe(so_df) # debug

    # make sure SO list is unqiue
    so_df["S.O. No."].dropna().unique()
    sos_affected = (
        df["Original sales Order"].dropna().astype(str).str.strip()
    )
    sos_affected = sos_affected[~sos_affected.str.upper().isin(["N/A", "NA", "NONE", ""])]
    sos_affected = sos_affected.unique()

    num_so = len(so_df)
    num_ncr = len(df)
    num_affected = len(sos_affected)

    date_display = date_filter.strftime('%d %b %Y')

    # visualise data
    col.metric(f"Total Number of NCRs since {date_display}:", num_ncr)
    col.metric(f"Number of NCRS with SO attached:", num_affected)
    col.metric(f"Total Number of SOs since {date_display}:", num_so)
    col.metric(f"Affected SOs %:", round(((num_affected/num_so)*100),2))

    # weekly comparison
    today = pd.Timestamp.today()
    this_week_start = today - pd.Timedelta(days=today.weekday())  # floor to Monday
    last_week_start = this_week_start - pd.Timedelta(weeks=1)

    this_week = len(df[df["Week"] == this_week_start.normalize()])
    last_week = len(df[df["Week"] == last_week_start.normalize()])
    delta = this_week - last_week

    col.metric(
        "NCRs Logged This Week",
        this_week,
        delta=f"{delta:+d} vs last week ({last_week})",
        delta_color="inverse"
    )

def calculate_weekly_impact(df, so_df):
    df["Date"] = pd.to_datetime(df["Date"])
    so_df["Date Required"] = pd.to_datetime(so_df["Date Required"])

    # Create week column
    so_df["Week"] = so_df["Date Required"].dt.to_period("W").dt.start_time

    # Weekly total SOs
    weekly_so = so_df.groupby("Week")["S.O. No."].nunique().reset_index(name="Total SOs")

    # Weekly affected SOs
    affected = df[df["Original sales Order"].notna()]
    weekly_affected = affected.groupby("Week")["Original sales Order"].nunique().reset_index(name="Affected SOs")

    # Merge
    weekly = weekly_so.merge(weekly_affected, on="Week", how="left").fillna(0)

    # Calculate %
    weekly["Affected %"] = (weekly["Affected SOs"] / weekly["Total SOs"]) * 100

    return weekly

def render_impact_chart(weekly, date_filter, col):
    weekly = weekly[weekly["Week"] >= date_filter]
    # filter to only show chart up to latest NCR
    last_week_with_value = weekly.loc[weekly["Affected %"] > 0, "Week"].max()
    if pd.isna(last_week_with_value):
        col.write("No affected SOs to display.")
        return
    max_show_week = last_week_with_value + timedelta(weeks=2)
    weekly_filtered = weekly[weekly["Week"] <= max_show_week]

    fig = px.line(
        weekly_filtered,
        x="Week",
        y="Affected %",
        markers=True
    )

    fig.update_traces(
        line=dict(color="red", width=3),
        marker=dict(size=8, color="red")
    )

    fig.update_layout(
        yaxis_title="Affected SO %",
        xaxis_title="Week",
    )

    col.plotly_chart(fig, use_container_width=True)