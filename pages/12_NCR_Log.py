import streamlit as st
from data import load_css
from ncr_functions import *

st.set_page_config(layout="wide", page_title="NCR Log Dashboard", page_icon="📋")


def inject_styles():
    load_css("stylesheet.css")
    st.markdown("""
    <style>
    .stApp { background-color: #f0f4fb; }
    .main .block-container { padding-top: 1.5rem; max-width: 1400px; }
    #MainMenu, footer, header { visibility: hidden; }
    .stButton > button {
        background-color: #2c7be5; color: white; border: none;
        border-radius: 8px; padding: 10px 26px; font-weight: 600; font-size: 14px;
    }
    .stButton > button:hover { background-color: #1a5fc1; color: white; }
    label, [data-testid="stWidgetLabel"] p {
        font-size: 13px !important; font-weight: 600 !important; color: #112444 !important;
    }
    [data-testid="stDataEditor"] { border-radius: 10px; overflow: hidden; box-shadow: 0 1px 6px rgba(17,36,68,0.09); }
    [data-testid="stCaptionContainer"] p, .stCaption p { color: #4a5568 !important; }
    [data-testid="stProgressLabel"], .stProgress p, [data-testid="stProgressBar"] + p { color: #112444 !important; }
    div[data-testid="stText"] p { color: #112444 !important; }
    </style>
    """, unsafe_allow_html=True)


def main():
    inject_styles()

    if st.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    date_filter = render_date_filter()

    conn = get_connection()
    df   = load_ncr_data(conn)
    df = df[(df["date"] >= date_filter) | (df["date"].isna())]

    render_page_header(date_filter)

    names, customers, departments, delegated = get_filter_options(df)

    render_kpi_section(df)
    render_breakdown_section(df, customers, departments)
    render_so_and_weekly(df, date_filter)
    render_completion_stats(df)
    render_ncr_table(df, conn, names, customers, departments, delegated)

    conn.close()


main()
