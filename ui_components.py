# ui.py
import streamlit as st
import plotly.express as px
import pandas as pd
from metrics import *
from data import *
import plotly.graph_objects as go
import datetime
from PIL import Image

def render_hours(flat_hours, tube_hours, folding_hours):
    st.markdown(f"""
    <div class="app-card black">
        <h1 style="margin:0;">FLAT: {int(flat_hours)} hours</h1>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div class="app-card black">
        <h1 style="margin:0;">FOLDING: {int(folding_hours)} hours</h1>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div class="app-card black">
        <h1 style="margin:0;">TUBE: {int(tube_hours)} hours</h1>
    </div>
    """, unsafe_allow_html=True)

def render_cards(dataframe, column):
    for _, row in dataframe.iterrows():

        bundle_name = row["Bundle/Job"]
        due_raw = row["Earliest Process Date"]
        bundle_type = row["Type"]
        bundle_status = row["Completed?"]
        fold_status = row["Folding Required?"]

        if pd.notnull(due_raw):
            due_date = due_raw.strftime("%d/%m/%Y")
        else:
            due_date = "No date"

        band_color = urgency_colour(bundle_status,due_raw)

        # checks if details side panel is showing
        is_selected = (st.session_state.selected_bundle == bundle_name)
        card_class = "bundle-card selected" if is_selected else "bundle-card"

        # Card container
        #if row["Completed?"] != "Yes":
        column.markdown(f"""
                <div class="{card_class}" style="border-left:8px solid {band_color};">
                    <div class="bundle-title">{bundle_name}</div>
                    <div class="bundle-date">Due Date: {due_date}</div>
                    <div class="bundle-date">Completion Status: {bundle_status}</div>
                    <div class="bundle-date">Folding Required? {fold_status}</div>
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
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
        """
        <div style="text-align: center;">
            <h3>Total Estimated Hours</h3>
        </div>
        """,
        unsafe_allow_html=True
        )
        render_hours(flat_cutting, tube_cutting, total_folding)

    with col2:
        st.markdown(
        """
        <div style="text-align: center;">
            <h3>Ratio of Late Jobs</h3>
        </div>
        """,
        unsafe_allow_html=True
        )
        render_late_status_ratio(late_df, week_df, future_df)

    with col3:
        st.markdown(
        """
        <div style="text-align: center;">
            <h3>Top Customers by Hours</h3>
        </div>
        """,
        unsafe_allow_html=True
        )
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
        showlegend=False,
        yaxis_title="Hours"
    )
    st.plotly_chart(fig, use_container_width=True)

def render_top_customers(df):
    top3 = (
        df.groupby("Customer Grouped")["Estimated Bundle Time (Hours)"]
        .sum()
        .sort_values(ascending=False)
        .head(3)
    )
    
    topcs = top3.index.tolist()
    topchs = top3.values.tolist()

    while len(topcs) < 3:
        topcs.append("-")

    while len(topchs) < 3:
        topchs.append("-")

    c1, c2, c3 = topcs[:3]
    c1h, c2h, c3h = topchs[:3]


    st.markdown(f"""
    <div class="app-card black">
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

def render_capacity_titles():
    col1, col2, col3 = st.columns(3)
    col1.markdown("## TUBE CUTTING")
    col2.markdown("## FLAT CUTTING")
    col3.markdown("## FOLDING")

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

    filter_col1, filter_col2, filter_col3, filter_col4, filter_col5, filter_col6 = st.columns(6)

    df["Customer"] = df["Customer"].fillna("No Customer Assigned")
    df["Machine"] = df["Machine"].fillna("No Machine Assigned")

    # Late toggle
    late_statuses = "Late", "Due This Week", "Due in Future"
    default_statuses = "Late", "Due This Week"
    with filter_col1:
        late_select = st.multiselect(
            "By Due Date", 
            options=late_statuses, 
            default=default_statuses,
            key="late_filter"
        )

    # Customer multi-select
    with filter_col2:
        customers = sorted(df["Customer"])
        selected_customers = st.multiselect(
            "By Customer(s)",
            options=customers,
            default=customers,
            key="customer_filter"
        )

    # Machine multi-select
    with filter_col3:
        machines = sorted(df["Machine"].dropna().unique())
        selected_machines = st.multiselect(
            "By Machine(s)",
            options=machines,
            default=machines,
            key="machine_filter"
        )

    # incomplete toggle
    with filter_col4:
        incomplete_only = st.toggle("Show Incomplete Bundles Only", value=True)
    
    # folding toggle
    with filter_col5:
        folding_required = st.toggle("Show only Bundles Requiring Folding?", value=False)

    # search for bundle title
    with filter_col6:
        bundle_search = st.text_input("Search by Bundle Name",
        placeholder="Type here...",
        key="bundle_search"                             
    )

    return late_select, incomplete_only, selected_customers, selected_machines, bundle_search, folding_required

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
            panel_html += f"<p><b>{field}</b><br>{value}</p>"
            panel_html += f"<p><b>Estimated Fold Time (Hours):</b><br>{selected_row.get('Estimated Fold Time (Hours)', '—')}</p>"
            panel_html += f"<p><b>Fold Site:</b><br>{selected_row.get('Fold Site', '—')}</p>"
        else:
            panel_html += f"<p><b>{field}</b><br>{value}</p>"

    panel_html += "</div>"

    st.markdown(panel_html, unsafe_allow_html=True)

def render_capacity(section_name, df, col):
    col.write(f"## {section_name}")

    max_hours, sevenfive_hours, needed_hours = capacity_data(section_name,df)

    # check if over capacity
    if needed_hours > max_hours:
        text_colour = 'red'
        bar_colour = 'red'
    elif needed_hours > sevenfive_hours:
        text_colour = 'orange'
        bar_colour = 'orange'
    else:
        bar_colour='green'
        text_colour='green'

    render_capacity_cards(col,text_colour,needed_hours,sevenfive_hours,max_hours)
    render_capacity_chart(needed_hours, sevenfive_hours,max_hours, bar_colour,col)
    
def render_capacity_cards(col,text_colour,needed_hours,sevenfive_hours,max_hours):
    col.markdown(f"""
    <div class="app-card {text_colour}">
        <h3>75% Capacity</h3>
        <h2 style="margin:0;">{int(needed_hours)}/{int(sevenfive_hours)} ({int(needed_hours/sevenfive_hours*100)}%)</h2>       
        <p style="margin:0; color: grey;">hours</p>
    </div>
    """, unsafe_allow_html=True)
    col.markdown(f"""
    <div class="app-card {text_colour}">
        <h3>MAX Capacity</h3>
        <h2 style="margin:0;">{int(needed_hours)}/{int(max_hours)} ({int(needed_hours/max_hours*100)}%)</h2>     
        <p style="margin:0; color: grey;">hours</p>
    </div>
    """, unsafe_allow_html=True)
    
def render_capacity_chart(needed_hours, sevenfive_hours,max_hours, bar_colour,col):
    fig = go.Figure()

    # Required hours bar
    fig.add_trace(go.Bar(
        x=["Demand"],
        y=[needed_hours],
        name="Required Hours",
        marker=dict(
            color=bar_colour,
            line=dict(width=0)
        ),
        width=0.5
    ))

    # 75% Capacity line
    fig.add_hline(
        y=sevenfive_hours,
        line=dict(color="black", width=7, dash="dash"),
        annotation_text="<b>75% Capacity</b>",
        annotation_position="top right",
        annotation_font_size=20,
        annotation_font=dict(size=12)
    )

    # Max Capacity line
    fig.add_hline(
        y=max_hours,
        line=dict(color="black", width=7),
        annotation_text="<b>MAX Capacity</b>",
        annotation_position="top right",
        annotation_font_size=20,
        annotation_font=dict(size=12)
    )

    fig.update_layout(
        height=350,
        margin=dict(l=40, r=40, t=30, b=40),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(
            title="Hours",
            gridcolor="rgba(0,0,0,0.05)",
            zeroline=False
        ),
        xaxis=dict(
            showgrid=False
        ),
        showlegend=False,
        font=dict(
            family="Segoe UI, sans-serif",
            size=13,
            color="#1a1a1a"
        )
    )

    col.plotly_chart(fig, use_container_width=True)

def render_bmena_finishing_cards():
    df = load_data_Bmena_sp()
    filtered_df = bmena_finishing_filters(df)
    # filtered_df = df # debug
    # st.dataframe(filtered_df) # debug
    st.markdown(f"Number Outstanding: {len(filtered_df)}")
    for _, row in filtered_df.iterrows():

        with st.container():
            def render_field(title, value):
                if pd.notna(value) and value != "":
                    # If it's a datetime or Timestamp → format it
                    if isinstance(value, (pd.Timestamp, datetime.date, datetime.datetime)):
                        value = value.strftime("%d/%m/%Y")

                    return f"<div style='margin-bottom:6px;'><strong>{title}:</strong> {value}</div>"
                return ""

            col1_html = "".join([
                render_field("Customer", row.get("Customer")),
                render_field("Combined", row.get("Combined")),
                render_field("Price", row.get("Price")),
                render_field("Finish Required Week Ending", row.get("Finish Required Week Ending")),
                render_field("Description", row.get("Description"))
            ])

            # Column 2
            col2_html = "".join([
                render_field("Line No", row.get("Line No.")),
                render_field("PO", row.get("PO")),
                render_field("Drawing No", row.get("Drawing No.")),
                render_field("Quantity Ordered", row.get("Quantity Ordered")),
                render_field("Specification", row.get("Specification")),
            ])

            # Column 3
            col3_html = "".join([
                render_field("Bundle", row.get("Bundle")),
                render_field("Tube Bundle", row.get("Tube Bundle")),
                render_field("Welder", row.get("Welder")),
                render_field("Date Sent to Finish", row.get("Date Sent to Finish")),
                render_field("Date Returned to JMS", row.get("Date Returned to JMS")),
                render_field("Delivery Qty Outstanding", row.get("Delivery Qty Outstanding")),
                render_field("Date Delivered", row.get("Date Delivered")),
            ])

            st.markdown(f"""
        <div class="app-card black" style="padding:20px;">
            <div style="display:flex; gap:40px; text-align:left">
                <div style="flex:1;">{col1_html}</div>
                <div style="flex:1;">{col2_html}</div>
                <div style="flex:1;">{col3_html}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_logo(col):
    logo = Image.open("assets/logo.jpg")
    col.image(logo, width=500)