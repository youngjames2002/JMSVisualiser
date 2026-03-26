import pandas as pd
from data import *

def calculate_totals(df):
    tube_df = df[df["Type"] == "TUBE"]
    flat_df = df[df["Type"] == "FLAT"]

    total_folding = df["Estimated Fold Time (Hours)"].sum()
    flat_cutting = flat_df["Estimated Bundle Time (Hours)"].sum()
    tube_cutting = tube_df["Estimated Bundle Time (Hours)"].sum()

    return total_folding, flat_cutting, tube_cutting

def capacity_needed_hours(df, section_name):
    total_folding, flat_cutting, tube_cutting = calculate_totals(df)
    if section_name == "Tube Cutting":
        return tube_cutting
    elif section_name == "Flat Cutting":
        return flat_cutting
    elif section_name == "Folding":
        return total_folding
    else:
        return 0

def bar_chart_hours_by_date(df):
    today = pd.Timestamp.today().normalize()

    df = df.copy()

    # Create Late flag
    df["Is Late"] = df["Earliest Process Date"] < today

    # Group by actual date
    summary = (
        df
        .groupby(["Earliest Process Date", "Is Late"])
        .agg({
            "Estimated Bundle Time (Hours)": "sum",
            "Estimated Fold Time (Hours)": "sum"
        })
        .reset_index()
    )

    # Melt to stacked format
    melted = summary.melt(
        id_vars=["Earliest Process Date", "Is Late"],
        value_vars=[
            "Estimated Bundle Time (Hours)",
            "Estimated Fold Time (Hours)"
        ],
        var_name="Type",
        value_name="Hours"
    )

    # Clean labels
    melted["Type"] = melted["Type"].replace({
        "Estimated Bundle Time (Hours)": "Cutting",
        "Estimated Fold Time (Hours)": "Folding"
    })

    # Create colour grouping
    melted["Colour Group"] = melted["Is Late"].apply(
        lambda x: "Late" if x else "On Time"
    )

    melted["Display Date"] = melted["Earliest Process Date"].dt.strftime("%d/%m/%Y")

    return melted

def cumulative_data_line_chart(daily_totals, selected_month):
     # Filter to selected month
    monthly_data = (
        daily_totals[daily_totals["YearMonth"] == selected_month]
        .copy()
        .sort_values("Display Date")
    )

    # Insert a zero row at month start if it doesn't exist
    month_start = selected_month.to_timestamp()
    if month_start not in monthly_data["Display Date"].values:
        monthly_data = pd.concat([
            pd.DataFrame({
                "Display Date": [month_start],
                "Hours": [0]
            }),
            monthly_data
        ]).sort_values("Display Date")

    # Monthly cumulative
    monthly_data["Cumulative Hours"] = monthly_data["Hours"].cumsum()

    return monthly_data    
    
def sum_hours_by_date(melted):
    # Parse UK format dates
    melted["Display Date"] = pd.to_datetime(
        melted["Display Date"],
        format="%d/%m/%Y"
    )

    # Sum total hours per date
    daily_totals = (
        melted
        .groupby("Display Date", as_index=False)["Hours"]
        .sum()
        .sort_values("Display Date")
    )

    # Add Year-Month period
    daily_totals["YearMonth"] = daily_totals["Display Date"].dt.to_period("M")

    return daily_totals

def capacity_data(section_name,df):
    # check if we're showing multiple weeks
    if df.empty:
        weeks_covered = 1
    else:
        today = pd.Timestamp.today().normalize()

        # Calculate week index relative to today
        week_index = ((df["Earliest Process Date"] - today).dt.days // 7)

        max_week = week_index.max()

        # Ensure minimum of 1 week
        weeks_covered = max(max_week + 1, 1)
    
    # get capacity hours
    max_hours = capacity_hours(section_name)*weeks_covered
    sevenfive_hours = int(max_hours*.75) 

    # get needed hours
    needed_hours = capacity_needed_hours(df, section_name)

    return max_hours, sevenfive_hours, needed_hours

def urgency_colour(completed, due_date):
    today = pd.Timestamp.today().normalize()
    current_week = today.to_period("W")
    due_week = due_date.to_period("W")
    if completed == "Yes":
        return "grey"
    elif due_date == today:
        return "#FF69B4"  # pink -> today
    elif due_date < today:
        return "#FF0000"  # red → overdue (past date)
    elif due_week == current_week:
        return "#FFD700"  # yellow → due this week
    elif due_week == current_week + 1:
        return "#90EE90"  # light green → next week
    else:
        return "#006400"  # dark green → future
    
def build_paint_plot_data(day_week_toggle, df):
    if day_week_toggle:
        next_month = pd.Timestamp.today() + pd.Timedelta(days=30)
        plot_df = df[df["Date Promised"] <= next_month].copy()
        plot_df["Date Promised"] = plot_df["Date Promised"] - pd.Timedelta(days=2)
        plot_df["Plot Group"] = plot_df["Date Promised"].dt.strftime("%d %b")
        group_col = "Date Promised"
    else:
        plot_df = df.copy()
        plot_df["Plot Group"] = plot_df["Week Label"]
        group_col = "Week Due"

    # render graph
    weekly = plot_df.groupby(group_col)["Price"].sum().sort_index().reset_index()
    weekly["Week Label"] = weekly[group_col].apply(
        lambda x: x.strftime("%d %b") if hasattr(x, "strftime") else x
    )
    weekly["colour"] = "green"

    return weekly

def calculate_paint_overflow(weekly, capacity, new_job_value):
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


    return next_week_available

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