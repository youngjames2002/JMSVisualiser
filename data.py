import pandas as pd
import streamlit as st
from openpyxl import load_workbook
from pathlib import Path

def load_data():
    ## CHANGE THIS ON DIFFERENT MACHINES
    filepath = r"C:\Users\james\OneDrive - JMS Metaltec\JMS Engineering Team - JMS Engineering Team SharePoint\JMS Master Schedule\testAutomation\bundleStagingSheet.xlsx"
    df = pd.read_excel(filepath)

    df["Earliest Process Date"] = pd.to_datetime(
        df["Earliest Process Date"],
        dayfirst=True,
        errors="coerce"
    )
    df = add_date_columns(df)
    df = apply_company_grouping(df)
    return df

def load_data_Bmena():
    ## CHANGE THIS ON DIFFERENT MACHINES
    src_file = src_file = Path.cwd() / r"C:\Users\james\OneDrive - JMS Metaltec\JMS Engineering Team - JMS Engineering Team SharePoint\Paint Schedule\Bmena Finishing Schedule.xlsm"
    wb = load_workbook(filename=src_file, data_only=True)
    sheet = wb["Schedule"]
    lookup_table = sheet.tables["Table1"]
    data = sheet[lookup_table.ref]
    rows_list=[]

    for row in data:
        cols=[]
        for col in row:
            cols.append(col.value)
        rows_list.append(cols)

    df = pd.DataFrame(data=rows_list[1:], index=None, columns=rows_list[0])

    return df

def apply_company_grouping(df):
    df = df.copy()

    df["Customer Grouped"] = df["Customer"].str.upper().str.strip()

    COMPANY_KEYWORDS = [
        "BAMFORD",
        "CDE",
        "TOBERMORE",
        "FARLOW",
        "SANDVIK",
        "CROSSLAND"
    ]

    for keyword in COMPANY_KEYWORDS:
        df.loc[
            df["Customer Grouped"].str.contains(keyword, na=False),
            "Customer Grouped"
        ] = keyword

    return df

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def add_date_columns(df):
    today = pd.Timestamp.today().normalize()
    df["Days Late"] = (df["Earliest Process Date"] - today).dt.days
    df["Is Late"] = df["Days Late"] < 0
    return df


def split_by_urgency(df):
    df = df.sort_values(by="Earliest Process Date", ascending=True).reset_index(drop=True)
    late_df = df[df["Days Late"] < 0]
    week_df = df[(df["Days Late"] >= 0) & (df["Days Late"] <= 7)]
    future_df = df[df["Days Late"] > 7]
    return late_df, week_df, future_df

def apply_filters(df, late_select, incomplete_only, selected_customers, selected_machines, bundle_search):
    filtered_df = df.copy()

    # Late filter
    late_mask = df["Days Late"] < 0
    week_mask = (df["Days Late"] >= 0) & (df["Days Late"] <= 7)
    future_mask = df["Days Late"] > 7

    status_mask = False

    if "Late" in late_select:
        status_mask = status_mask | late_mask

    if "Due This Week" in late_select:
        status_mask = status_mask | week_mask

    if "Due in Future" in late_select:
        status_mask = status_mask | future_mask

    filtered_df = filtered_df[status_mask]

    # Customer filter
    filtered_df = filtered_df[
        filtered_df["Customer"].isin(selected_customers)
    ]

    # Machine filter
    filtered_df = filtered_df[
        filtered_df["Machine"].isin(selected_machines)
    ]

    # Incomplete filter
    if incomplete_only:
        filtered_df = filtered_df[
            filtered_df["Completed?"] == "No"
        ]

    # bundle search
    if bundle_search:
        filtered_df = filtered_df[
            filtered_df["Bundle/Job"]
            .astype(str)
            .str.contains(bundle_search, case=False, na=False)
    ]

    return filtered_df

def bmena_finishing_filters(df):
    # date filter
    # get today
    today = pd.Timestamp.today().normalize()

    # Ensure datetime
    df["Finish Required Week Ending"] = pd.to_datetime(
        df["Finish Required Week Ending"], errors="coerce"
    )

    # Find the nearest date AFTER today
    future_dates = df.loc[
        df["Finish Required Week Ending"] > today,
        "Finish Required Week Ending"
    ]
    if not future_dates.empty:
        cutoff_date = future_dates.min()
    else:
        # If no future dates exist, use max date in column
        cutoff_date = df["Finish Required Week Ending"].max()

    # Filter rows with date <= cutoff
    filtered_df = df[
        df["Finish Required Week Ending"] <= cutoff_date
    ]  

    # blank filters
    # only records with date delivered AND supplier AND comments blanked
    filtered_df = filtered_df[filtered_df["Date Delivered"].isna()]
    filtered_df = filtered_df[filtered_df["Supplier"].isna()]
    filtered_df = filtered_df[filtered_df["Comments"].isna()]

    return filtered_df
# This is hardcoded for now but could change to be read from somewhere
# if needed and would be changing often
def capacity_hours(section_name):
    if section_name == "Tube Cutting":
        return 28
    elif section_name == "Flat Cutting":
        return 152
    elif section_name == "Folding":
        return 190
    else:
        return 0
    

    
