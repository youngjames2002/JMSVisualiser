# ui.py
import streamlit as st
import plotly.express as px
import pandas as pd

def render_cutting_pie_chart(flat_hours, tube_hours):
    pie_data = pd.DataFrame({
        "Type": ["FLAT", "TUBE"],
        "Hours": [flat_hours, tube_hours]
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
                text=f"<b>{flat_hours+tube_hours:.1f} hrs</b>",
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

    st.plotly_chart(fig, use_container_width=True)

def render_folding_hours(folding_hours):
    st.markdown("### Total Estimated Folding Hours")

    st.markdown(f"""
    <div style="
        background: white;
        padding: 30px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        color: black;
    ">
        <h1 style="margin:0;">{round(folding_hours, 1)}</h1>
        <p style="margin:0; color: grey;">hours</p>
    </div>
    """, unsafe_allow_html=True)


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

def render_at_a_glance(flat_hours, tube_hours, folding_hours):
    col1, col2 = st.columns([2,1])

    with col1:
        st.markdown("### Total Estimated Cutting Hours")
        render_cutting_pie_chart(flat_hours, tube_hours)

    with col2:
        render_folding_hours(folding_hours)

def render_cards_section():
    st.markdown("<h2>All Bundles</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.markdown("### 🔴 Late")
    col2.markdown("### 🟡 Due This Week")
    col3.markdown("### 🟢 Future")