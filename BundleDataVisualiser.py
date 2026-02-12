import streamlit as st
st.set_page_config(layout = "wide")
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css('stylesheet.css')        
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# pull data from staging sheet
stagingSheet = "C:\\Users\\james\\JMS Metaltec\\JMS Engineering Team - JMS Engineering Team SharePoint\\JMS Master Schedule\\testAutomation\\bundleStagingSheet.xlsx"
df = pd.read_excel(stagingSheet)

#convert to UK Date Format
df["Earliest Process Date"] = pd.to_datetime(
    df["Earliest Process Date"],
    dayfirst=True,
    errors="coerce"
)

# Title
st.title("Bundle Data Visualiser - Admin View")

# session state initialisation
if "selected_bundle" not in st.session_state:
    st.session_state.selected_bundle = None

# show important data at a glance
st.markdown("<h2>At a Glance</h2>", unsafe_allow_html=True)
# late only filter
today = pd.Timestamp.today().normalize()
late_only = st.toggle("Show Late Bundles Only")

df["Days Late"] = (df["Earliest Process Date"] - today).dt.days
df["Is Late"] = df["Days Late"] < 0
if late_only:
    df_filtered_late = df[df["Is Late"] == True]
else:
    df_filtered_late = df

tube_df = df_filtered_late[df_filtered_late["Type"] == 'TUBE']
flat_df = df_filtered_late[df_filtered_late["Type"] == 'FLAT']

# calculate total folding hours and total bundle hours, tube and flat
total_folding_hours = df_filtered_late["Estimated Fold Time (Hours)"].sum()
flat_cutting_hours = flat_df["Estimated Bundle Time (Hours)"].sum()
tube_cutting_hours = tube_df["Estimated Bundle Time (Hours)"].sum()

col1, col2 = st.columns([2,1])
#col1 at a glance (cutting hours)
col1.markdown("### Total Estimated Cutting Hours")
pie_data = pd.DataFrame({
    "Type": ["FLAT", "TUBE"],
    "Hours": [flat_cutting_hours, tube_cutting_hours]
})

pie_data = pie_data[pie_data["Hours"] > 0]

fig = px.pie(
    pie_data,
    names="Type",
    values="Hours",
    hole=0.65
)

# Show hours instead of %
fig.update_traces(
    texttemplate="%{label}<br>%{value:.1f} hrs",
    textposition="inside"
)

# Turn into semi-circle properly
fig.update_layout(
    showlegend=False,
    margin=dict(t=10, b=0, l=0, r=0),
)

fig.update_traces(rotation=180)

fig.update_layout(
    annotations=[
        dict(
            text=f"<b>{flat_cutting_hours+tube_cutting_hours:.1f} hrs</b>",
            x=0.5,
            y=0.25,   # Lower = smaller visual footprint
            font_size=16,
            showarrow=False
        )
    ]
)

fig.update_layout(
    height=350
)

col1.plotly_chart(fig, use_container_width=True)

#col2 at a glance (folding hours)
col2.markdown("### Total Estimated Folding Hours")

col2.markdown(f"""
<div style="
    background: white;
    padding: 30px;
    border-radius: 12px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    color: black;
">
    <h1 style="margin:0;">{round(total_folding_hours, 1)}</h1>
    <p style="margin:0; color: grey;">hours</p>
</div>
""", unsafe_allow_html=True)

# display all bundles in card format (title and due date) - colour coded relative to due date
# if you click a bundle it should enlarge and show the full data for it
st.markdown("<h2>All Bundles</h2>", unsafe_allow_html=True)
df_sorted_date = df.sort_values(by="Earliest Process Date", ascending=True).reset_index(drop=True)

#categorise bundles by late status
col1,col2,col3 = st.columns(3)
late_df = df_sorted_date[df_sorted_date["Days Late"] < 0]
week_df = df_sorted_date[(df_sorted_date["Days Late"] >= 0) & (df_sorted_date["Days Late"] <= 7)]
future_df = df_sorted_date[df_sorted_date["Days Late"] > 7]

def render_cards(dataframe, column):

    for i in range(len(dataframe)):
        row = dataframe.iloc[i]

        bundle_id = f"{row.name}"
        bundle_name = row["Bundle/Job"]
        due_raw = row["Earliest Process Date"]
        days_diff = row["Days Late"]
        bundle_type = row["Type"]

        if pd.notnull(due_raw):
            due_date = due_raw.strftime("%d/%m/%Y")
        else:
            due_date = "No date"
            days_diff = None

        # Colour logic
        if days_diff is None:
            band_color = "#cccccc"
        elif days_diff < -7:
            band_color = "#8B0000"
        elif days_diff < 0:
            band_color = "#FF0000"
        elif days_diff == 0:
            band_color = "#ff9999"
        elif days_diff <= 7:
            band_color = "#FFD700"
        else:
            band_color = "#28a745"

        # Card container
        column.markdown(f"""
            <div class="bundle-card" style="border-left: 8px solid {band_color};">
                <div class="bundle-title">{bundle_name}</div>
                <div class="bundle-date">Due Date: {due_date}</div>
                <div class="bundle-type">{bundle_type}</div>
            </div>
        """, unsafe_allow_html=True)

        # Click button
        button_label = ("Close Details"
            if st.session_state.selected_bundle == row.name
            else "View Details"
        )
        if column.button(button_label, key=f"btn_{bundle_id}"):
            if st.session_state.selected_bundle == row.name:
                # If already open → close it
                st.session_state.selected_bundle = None
            else:
                # Otherwise open it
                st.session_state.selected_bundle = row.name
            st.rerun()

col1.markdown("### 🔴 Late")
col2.markdown("### 🟡 Due This Week")
col3.markdown("### 🟢 Future")
render_cards(late_df, col1)
render_cards(week_df, col2)
render_cards(future_df, col3)

# =========================
# Slide-in Side Panel
# =========================

if st.session_state.selected_bundle is not None:

    selected_row = df.loc[st.session_state.selected_bundle]

    st.markdown(
        """
        <style>
        .side-panel {
            position: fixed;
            top: 0;
            right: 0;
            width: 420px;
            height: 100vh;
            background-color: white;
            box-shadow: -6px 0 20px rgba(0,0,0,0.15);
            padding: 30px;
            overflow-y: auto;
            z-index: 9999;
            color: black;
        }
        .close-btn {
            background-color: #f44336;
            color: white;
            padding: 6px 12px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 14px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    panel_html = f"""
    <div class="side-panel">
    <br>
        <h3>Bundle Details</h3>
    """

    list_details_shown = [
    "Bundle/Job",
    "Customer",
    "Date Added",
    "Type",
    "Earliest Process Date",
    "Estimated Bundle Time (Hours)",
    "Welding Required?",
    "Sales Orders Included in Bundle",
    "Machine",
    "Finishing Required?",
    "Assign to:",
    "Folding Required?"
]
    for field in list_details_shown:
        value = selected_row.get(field, "—")

        if field == "Folding Required?" and str(value).lower() == "yes":
            panel_html += f"<p><b>{field}:</b><br>{value}</p>"
            panel_html += f"<p><b>Estimated Fold Time (Hours):</b><br>{selected_row.get('Estimated Fold Time (Hours)', '—')}</p>"
            panel_html += f"<p><b>Fold Site:</b><br>{selected_row.get('Fold Site', '—')}</p>"
        else:
            panel_html += f"<p><b>{field}:</b><br>{value}</p>"
        

    st.markdown(panel_html, unsafe_allow_html=True)
    panel_html += "</div>"

    # Close button (must be outside raw HTML to work)
    if st.button("Close Panel"):
        st.session_state.selected_bundle = None
        st.rerun()

# be able to filter bundles being viewed by type, fold needed, time, etc all data

# be able to make bunle cards show more or less info

#debug
st.write(df.columns.tolist())

