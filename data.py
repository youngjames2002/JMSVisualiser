import pandas as pd
import streamlit as st
def load_data():
    filepath = "C:\\Users\\james\\JMS Metaltec\\JMS Engineering Team - JMS Engineering Team SharePoint\\JMS Master Schedule\\testAutomation\\bundleStagingSheet.xlsx"
    df = pd.read_excel(filepath)

    df["Earliest Process Date"] = pd.to_datetime(
        df["Earliest Process Date"],
        dayfirst=True,
        errors="coerce"
    )
    df = add_date_columns(df)
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

def apply_filters(df, late_select, incomplete_only, selected_customers, selected_machines):
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

    return filtered_df

# This is hardcoded for now but could change to be read from somewhere
# if needed and will be changing often
def capacity_hours(section_name):
    if section_name == "Tube Cutting":
        return 28
    elif section_name == "Flat Cutting":
        return 152
    elif section_name == "Folding":
        return 190
    else:
        return 0