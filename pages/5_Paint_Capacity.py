import streamlit as st
from data import *
from ui_components import *
from io import StringIO
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# load css
load_css('stylesheet.css')

# title
tcol1, tcol2 = st.columns([1,4])
tcol2.title("Paint Capacity")
render_logo(tcol1)

# SET CAPACITY
capacity = 35000
close_call = 30000

# take input
st.markdown("""
Go to Sales Order Lines in Statii and export the report **'Paint Capacity'**  
It should show the columns Line No, Customer, Specification, Price and Date Promised  
Download that and then click 'open'. This should open a spreadsheet. Select All and copy, then paste that into the box below
""")
raw_data = st.text_area("Paste Statii Dump here")
st.markdown("Hit Ctrl+Enter to generate Capacity Graphs")

# st.markdown(raw_data)
if raw_data:
    # read data to df
    try: 
        df = pd.read_csv(
            StringIO(raw_data), sep="\t", engine="python", quotechar='"', skip_blank_lines=True
        )
    except Exception as e:
        st.error(f"Cannot read data - ensure data is input from statii correctly - {e}")
        st.stop()

    # clean data
    # filter to remove customers who dont get painted
    df = df[~df["Customer"].str.contains("Bamford|Wright|Cunningham", case=False, na=False)]
    # filter for specifications that are paint
    df = df[df["Specification"].str.contains(r"\bRAL\b|\bprime\b|\bpaint\b", case=False, na=False)]

    # add week column and sort by that
    df["Date Promised"] = pd.to_datetime(
        df["Date Promised"], dayfirst=True, errors="coerce"
    )
    df = df.dropna(subset=["Date Promised"])
    df["Date Promised"] = df["Date Promised"] - pd.Timedelta(days=2)   # paint date is 2 days before so date
    df["Week Due"] = df["Date Promised"].dt.to_period("W-FRI").apply(lambda r: r.end_time)
    current_week = pd.Timestamp.today().to_period("W-FRI").end_time
    df = df[df["Week Due"] >= current_week]
    df["Week Label"] = df["Week Due"].dt.strftime("%d %b")
    df = df.sort_values("Week Due", ascending=True)

    day_week_toggle = st.toggle("Toggle Weekly View vs Daily View (Next Month)", value="False")
    if day_week_toggle:
        next_month = pd.Timestamp.today() + pd.Timedelta(days=30)
        plot_df = df[df["Date Promised"] <= next_month].copy()
        plot_df["Plot Group"] = plot_df["Date Promised"].dt.strftime("%d %b")
        group_col = "Date Promised"
        label_col = "Plot Group"
        capacity = capacity/4
        xlabel = "Day"
    else:
        plot_df = df.copy()
        plot_df["Plot Group"] = plot_df["Week Label"]
        group_col = "Week Due"
        label_col = "Plot Group" 
        xlabel = "Week Ending"   

    # render graph
    weekly = plot_df.groupby(group_col)["Price"].sum().sort_index().reset_index()
    weekly["Week Label"] = weekly[group_col].apply(
        lambda x: x.strftime("%d %b") if hasattr(x, "strftime") else x
    )
    weekly["colour"] = "green"
    weekly.loc[weekly["Price"] >= close_call, "colour"] = "orange"
    weekly.loc[weekly["Price"] > capacity, "colour"] = "red"
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=weekly["Week Label"],
        y=weekly["Price"],
        marker=dict(
            color=weekly["colour"],
            line=dict(width=0)
        ),
        name="Paint Capacity Over Time",
        text=weekly["Price"],
        texttemplate="£%{text:,.0f}",
        textposition="outside"
    ))

    fig.add_hline(
        y=capacity,
        line=dict(color="red", width=4, dash="dash"),
        annotation_text=f"<b>Capacity £{capacity:,.0f}</b>",
        annotation_position="top right"
    )

    fig.update_layout(
        height=500,
        margin=dict(l=40, r=40, t=30, b=40),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",

        yaxis=dict(
            title="Paint Value (£)",
            gridcolor="rgba(0,0,0,0.05)",
            zeroline=False
        ),

        xaxis=dict(
            title=xlabel,
            showgrid=False
        ),

        showlegend=False,

        font=dict(
            family="Segoe UI, sans-serif",
            size=13,
            color="#1a1a1a"
        )
    )

    st.plotly_chart(fig, use_container_width=True)


    # render next available time
    st.markdown("## Next Available Week")
    new_job_value = st.number_input(
        "Enter Paint Value (£)",
        min_value=0,
        max_value=capacity,
        step=500,
        value=500
    )
    schedule = weekly.copy()
    overflow=0
    schedule["Load After Overflow"]=0

    for i in range(len(schedule)):
        load=schedule.loc[i,'Price'] + overflow

        if load > capacity:
            overflow=load-capacity
            schedule.loc[i, "Load After Overflow"] = capacity
        else:
            schedule.loc[i, "Load After Overflow"] = load
            overflow=0

    next_week_available = None
    for i in range(len(schedule)):
        if schedule.loc[i, "Load After Overflow"] + new_job_value <= capacity:
            next_week_available = schedule.loc[i, "Week Due"]
            break
    if next_week_available is None:
        # start from last known week
        future_week = schedule["Week Due"].iloc[-1]
        overflow_load = overflow  # leftover from last week

        while True:
            future_week += pd.Timedelta(days=7)
            if overflow_load + new_job_value <= capacity:
                next_week_available = future_week
                break
            overflow_load = max(0, overflow_load - capacity)

    if next_week_available:
        st.success(f"Next Available Week Ending: {next_week_available.strftime('%d %b %Y')}")

    # render table of orders due week by week
    st.markdown("## View Lines by Week")
    weeks = sorted(weekly["Week Due"].unique())
    week_labels = {w: pd.to_datetime(w).strftime("%d %b") for w in weeks}
    selected_weeks = st.multiselect(
        "Filter By Week Due",
        options=weeks,
        default=weeks[0],
        format_func=lambda x: week_labels[x],
        key="week_filter"
    )
    df_ts_week = df[df["Week Due"].isin(selected_weeks)]
    st.dataframe(df_ts_week.drop(columns=df_ts_week.columns[-2])) 