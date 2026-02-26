import pandas as pd
import streamlit as st
from openpyxl import load_workbook
from pathlib import Path
from io import BytesIO
import msal
import requests

def load_data_local():
    ## CHANGE THIS ON DIFFERENT MACHINES
    filepath = r"C:\Users\james\OneDrive - JMS Metaltec\JMS Engineering Team - JMS Engineering Team SharePoint\JMS Master Schedule\testAutomation\bundleStagingSheet.xlsx"
    df = pd.read_excel(filepath)

    df["Earliest Process Date"] = pd.to_datetime(
        df["Earliest Process Date"],
        dayfirst=True,
        errors="coerce"
    )
    df = apply_company_grouping(df)
    return df

def load_data_Bmena_local():
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

def load_data_ncr_local():
    src_file = src_file = Path.cwd() / r"C:\Users\james\OneDrive - JMS Metaltec\JMS Engineering Team - JMS Engineering Team SharePoint\NCR Log\NCR Log.xlsm"
    wb = load_workbook(filename=src_file, data_only=True)
    sheet = wb["1 - Non-Conformance Log"]
    lookup_table = sheet.tables["Table1"]
    data = sheet[lookup_table.ref]
    rows_list=[]

    for row in data:
        cols=[]
        for col in row:
            cols.append(col.value)
        rows_list.append(cols)

    df = pd.DataFrame(data=rows_list[1:], index=None, columns=rows_list[0])

    # fix dates
    df["Date"] = pd.to_datetime(
        df["Date"],
        dayfirst=True,
        errors="coerce"
    )

    return df

def download_excel_from_sharepoint(site_name: str, file_path:str) -> BytesIO:
    # download from sharepoint and return bytesIO object

    TENANT_ID = st.secrets["TENANT_ID"]
    CLIENT_ID = st.secrets["CLIENT_ID"]
    CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
    SHAREPOINT_SITE = st.secrets["SHAREPOINT_SITE"]

    AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
    SCOPE = ["https://graph.microsoft.com/.default"]

    app = msal.ConfidentialClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )  
    # debug st.json(token)  # should contain "access_token" if successful

    token = app.acquire_token_for_client(scopes=SCOPE)
    if "access_token" not in token:
        st.error("Authentication failed")
        return None

    headers = {"Authorization": f"Bearer {token['access_token']}"} 

    # Get SharePoint site ID
    site_url = f"https://graph.microsoft.com/v1.0/sites/{SHAREPOINT_SITE}:/sites/{site_name}"
    site_response = requests.get(site_url, headers=headers)
    site_response.raise_for_status()
    site_id = site_response.json()["id"]

    # debug
    drives_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
    drives_response = requests.get(drives_url, headers=headers)
    st.write(drives_response.json())

    # Download the file
    file_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root:/{file_path}:/content"
    file_response = requests.get(file_url, headers=headers)
    file_response.raise_for_status()

    return BytesIO(file_response.content)
@st.cache_data(show_spinner=True)
def load_data_sp():
    bytes_io = download_excel_from_sharepoint(
        site_name="JMSEngineeringTeam",
        file_path="Shared Documents/JMS Engineering Team SharePoint/JMS Master Schedule/testAutomation/bundleStagingSheet.xlsx"
    )
    if bytes_io is None:
        return pd.DataFrame()  # return empty DataFrame if download failed

    df = pd.read_excel(bytes_io)

    # Example processing (replace with your real functions)
    df["Earliest Process Date"] = pd.to_datetime(
        df["Earliest Process Date"],
        dayfirst=True,
        errors="coerce"
    )
    df = apply_company_grouping(df)
    return df

@st.cache_data(show_spinner=True)
def load_data_Bmena_sp():
    bytes_io = download_excel_from_sharepoint(
        site_name="JMSEngineeringTeam",
        file_path="Shared Documents/JMS Engineering Team SharePoint/Paint Schedule/Bmena Finishing Schedule.xlsm"
    )
    if bytes_io is None:
        return pd.DataFrame()  # return empty DataFrame if download failed

    wb = load_workbook(filename=bytes_io, data_only=True)
    sheet = wb["Schedule"]
    lookup_table = sheet.tables["Table1"]
    data = sheet[lookup_table.ref]

    # Convert table to DataFrame
    rows_list = [[cell.value for cell in row] for row in data]
    df = pd.DataFrame(rows_list[1:], columns=rows_list[0])
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


def split_by_urgency(df):
    today = pd.Timestamp.today().normalize()
    df = df.sort_values(by="Earliest Process Date", ascending=True).reset_index(drop=True)

    df["Week"] = df["Earliest Process Date"].dt.to_period("W")
    current_week = today.to_period("W")

    late_df = df[df["Earliest Process Date"] < today]
    week_df = df[
        (df["Week"] == current_week) &
        (df["Earliest Process Date"] >= today)         
    ]
    future_df = df[df["Week"] > current_week]
    return late_df, week_df, future_df

def apply_filters(df, late_select, incomplete_only, selected_customers, selected_machines, bundle_search):
    filtered_df = df.copy()

    # Late Filter -- Calendar Week
    today = pd.Timestamp.today().normalize()
    current_week = today.to_period("W")

    due_dates = filtered_df["Earliest Process Date"]
    due_weeks = due_dates.dt.to_period("W")

    # Status masks (calendar-based)
    late_mask = due_dates < today
    week_mask = (due_weeks == current_week) & (due_dates >= today)
    future_mask = due_weeks > current_week

    status_mask = False

    if "Late" in late_select:
        status_mask |= late_mask

    if "Due This Week" in late_select:
        status_mask |= week_mask

    if "Due in Future" in late_select:
        status_mask |= future_mask

    if late_select:
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
    

    
