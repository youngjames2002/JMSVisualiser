# ui.py
import streamlit as st
import plotly.express as px
import pandas as pd
from metrics import *
from data import *
import plotly.graph_objects as go

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
    folding_capacity = 30 #random number

    st.markdown("### Total Estimated Folding Hours")
    if folding_hours > folding_capacity:
        text_colour = 'red'
    else:
        text_colour = 'black'

    st.markdown(f"""
    <div style="
        background: white;
        padding: 30px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        color: {text_colour};
    ">
        <h1 style="margin:0;">{round(folding_hours, 1)}/{round(folding_capacity,1)}</h1>
        <p style="margin:0; color: grey;">hours</p>
    </div>
    """, unsafe_allow_html=True)


def render_cards(dataframe, column):
    for _, row in dataframe.iterrows():

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

        # checks if details side panel is showing
        is_selected = (st.session_state.selected_bundle == bundle_name)
        card_class = "bundle-card selected" if is_selected else "bundle-card"

        # Card container
        if row["Completed?"] != "Yes":
            column.markdown(f"""
                <div class="{card_class}" style="border-left:8px solid {band_color};">
                    <div class="bundle-title">{bundle_name}</div>
                    <div class="bundle-date">Due Date: {due_date}</div>
                    <div class="bundle-type">{bundle_type}</div>
                </div>
            """, unsafe_allow_html=True)

            # Click button
            button_label = "Close Details" if is_selected else "View Details"

            if column.button(button_label, key=f"btn_{bundle_name}"):
                if is_selected:
                    # If already open → close it
                    st.session_state.selected_bundle = None
                else:
                    # Otherwise open it
                    st.session_state.selected_bundle = bundle_name
                st.rerun()       

def render_at_a_glance(df,late_df, week_df, future_df):
    total_folding, flat_cutting, tube_cutting = calculate_totals(df)
    st.markdown("<h2>At a Glance</h2>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("### Total Estimated Cutting Hours")
        render_cutting_pie_chart(flat_cutting, tube_cutting)

    with col2:
        render_folding_hours(total_folding)

    with col3:
        st.markdown("### Ratio of Late Jobs")
        render_late_status_ratio(late_df, week_df, future_df)

    with col4:
        st.markdown("### Top Customers by Hours")
        render_top_customers(df)

def render_late_status_ratio(late_df, week_df, future_df):
    late_hours = late_df["Estimated Bundle Time (Hours)"].sum()
    week_hours = week_df["Estimated Bundle Time (Hours)"].sum()
    future_hours = future_df["Estimated Bundle Time (Hours)"].sum()

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=["Late", "This Week", "Future"],
        y=[late_hours, week_hours, future_hours],
        marker_color=["#d62728", "#ffbf00", "#2ca02c"]  # red, yellow, green
    ))

    fig.update_layout(
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

def render_top_customers(df):
    top3 = (
        df.groupby("Customer")["Estimated Bundle Time (Hours)"]
        .sum()
        .sort_values(ascending=False)
        .head(3)
    )
    
    c1, c2, c3 = top3.index
    c1h, c2h, c3h = top3.values


    st.markdown(f"""
    <div style="
        background: white;
        padding: 30px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        color: black;
    ">
        <h3 style="margin:0;">1. {c1} - {c1h} hours</h3>
        <h3 style="margin:0;">2. {c2} - {c2h} hours</h3>
        <h3 style="margin:0;">3. {c3} - {c3h} hours</h3>
    </div>
    """, unsafe_allow_html=True)
        
def render_cards_titles():
    st.markdown("<h2>All Bundles</h2>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown("### 🔴 Late")
    col2.markdown("### 🟡 Due This Week")
    col3.markdown("### 🟢 Future")
    col4.markdown('### Charts')

def render_bar_chart(df, column):
    melted = bar_chart_hours_by_date(df)

    fig = px.bar(
        melted,
        x="Display Date",
        y="Hours",
        color="Colour Group",      # controls red vs normal
        pattern_shape="Type",      # visually splits Cutting/Folding
        barmode="stack"
    )

    # Force colours
    fig.update_traces(marker_line_width=0)

    fig.update_layout(
        title="Total Hours by Date (Cutting + Folding)",
        xaxis_title="Date",
        yaxis_title="Total Hours",
        height=500
    )

    fig.update_layout(
        coloraxis_showscale=False
    )

    fig.update_traces(
        marker=dict(
            color=None
        )
    )

    # Manual color mapping
    fig.for_each_trace(
        lambda trace: trace.update(
            marker_color="red" if "Late" in trace.name else "#2E86C1"
        )
    )

    column.plotly_chart(fig, use_container_width=True)

def render_line_chart(df, column):
    melted = bar_chart_hours_by_date(df)
    daily_totals = sum_hours_by_date(melted)
    
    # Create month selector (sorted chronologically)
    available_months = sorted(daily_totals["YearMonth"].unique())

    #default to show current month
    current_month = pd.Timestamp.today().to_period("M")

    if current_month in available_months:
        default_index = available_months.index(current_month)
    else:
        default_index = len(available_months) - 1  # fallback to latest available month

    selected_month = column.selectbox(
        "Select Month",
        available_months,
        format_func=lambda x: x.strftime("%B %Y"),
        index=default_index
    )
    monthly_data = cumulative_data_line_chart(daily_totals, selected_month)

    # Plot
    fig = px.line(
        monthly_data,
        x="Display Date",
        y="Cumulative Hours",
        markers=True
    )

    fig.update_layout(
        title=f"Cumulative Hours - {selected_month.strftime('%B %Y')}",
        xaxis_title="Date",
        yaxis_title="Cumulative Hours",
        height=500
    )

    fig.update_yaxes(range=[0, monthly_data["Cumulative Hours"].max() * 1.05])
    column.plotly_chart(fig, use_container_width=True)
    

def render_filter_section(df):
    st.markdown("## Filters")

    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

    df["Customer"] = df["Customer"].fillna("No Customer Assigned")
    df["Machine"] = df["Machine"].fillna("No Machine Assigned")

    # Late toggle
    with filter_col1:
        late_only = st.toggle("Show Late Bundles Only")

    # Customer multi-select
    with filter_col2:
        customers = sorted(df["Customer"].dropna().unique())
        selected_customers = st.multiselect(
            "Select Customer(s)",
            options=customers,
            default=customers,
            key="customer_filter"
        )

    # Machine multi-select
    with filter_col3:
        machines = sorted(df["Machine"].dropna().unique())
        selected_machines = st.multiselect(
            "Select Machine(s)",
            options=machines,
            default=machines,
            key="machine_filter"
        )

    # incomplete toggle
    with filter_col4:
        incomplete_only = st.toggle("Show Incomplete Bundles Only", value=True)

    filtered_df = apply_filters(df, late_only, incomplete_only, selected_customers, selected_machines, customers, machines)

    return filtered_df

def render_progress_bar(df, column):
    total = len(df)
    completed = (df["Completed?"] == "Yes").sum()
    progress = completed / total if total > 0 else 0
    column.progress(progress,"Progress Bar Task Completion: "+ str(completed)+ "/"+ str(total)+ ", "+ str(round(progress*100,2))+ "%")

def render_side_panel(df):
    selected_bundle = st.session_state.get("selected_bundle")

    if selected_bundle is None:
        return

    # Find row using Bundle/Job
    selected_rows = df[df["Bundle/Job"] == selected_bundle]

    if selected_rows.empty:
        return  # In case filters removed it

    selected_row = selected_rows.iloc[0]

    st.markdown("""
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
        </style>
    """, unsafe_allow_html=True)

    panel_html = """
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

    panel_html += "</div>"

    st.markdown(panel_html, unsafe_allow_html=True)