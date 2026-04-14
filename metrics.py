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
        plot_df["Date Promised"] = plot_df["Date Promised"] + pd.Timedelta(days=2)
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
    schedule["Load After Overflow"]=0.0

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
        return 148
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

def build_weld_kpis(df):
    df = df.copy()

    # Fix column names (optional but safer)
    df.columns = df.columns.str.strip()

    # Convert types
    df["Week Ending"] = pd.to_datetime(df["Week Ending"], dayfirst=True, errors="coerce")
    df["Hours Plan"] = pd.to_numeric(df["Hours Plan"], errors="coerce").fillna(0)

    # Get this Friday + next Friday
    today = pd.Timestamp.today().normalize()
    this_week = (today + pd.offsets.Week(weekday=4)).normalize()
    next_week = this_week + pd.Timedelta(days=7)

    # Aggregate
    kpi_df = (
        df[df["Week Ending"].isin([this_week, next_week])]
        .groupby(["Site", "Week Ending"])["Hours Plan"]
        .sum()
        .unstack(fill_value=0)
        .rename(columns={
            this_week: "This Week Hours",
            next_week: "Next Week Hours"
        })
        .reset_index()
    )

    # Ensure both columns exist (in case one week missing)
    for col in ["This Week Hours", "Next Week Hours"]:
        if col not in kpi_df:
            kpi_df[col] = 0

    kpi_df["This Week Hours"] = kpi_df["This Week Hours"].apply(format_hours)
    kpi_df["Next Week Hours"] = kpi_df["Next Week Hours"].apply(format_hours)

    return kpi_df

def build_machine_kpis(df):
    df = df.copy()

    # Fix column names (optional but safer)
    df.columns = df.columns.str.strip() 

    # Convert types
    df["Week Ending"] = pd.to_datetime(df["Week Ending"], dayfirst=True, errors="coerce")
    df["Hours Plan"] = pd.to_numeric(df["Hours Plan"], errors="coerce").fillna(0)

    # Get this Friday + next Friday
    today = pd.Timestamp.today().normalize()
    this_week = (today + pd.offsets.Week(weekday=4)).normalize()
    next_week = this_week + pd.Timedelta(days=7)

    # Aggregate
    kpi_df = (
        df[df["Week Ending"].isin([this_week, next_week])]
        .groupby(["Operation", "Week Ending"])["Hours Plan"]
        .sum()
        .unstack(fill_value=0)
        .rename(columns={
            this_week: "This Week Hours",
            next_week: "Next Week Hours"
        })
        .reset_index()
    )

    # Ensure both columns exist (in case one week missing)
    for col in ["This Week Hours", "Next Week Hours"]:
        if col not in kpi_df:
            kpi_df[col] = 0

    kpi_df["This Week Hours"] = kpi_df["This Week Hours"].apply(format_hours)
    kpi_df["Next Week Hours"] = kpi_df["Next Week Hours"].apply(format_hours)

    return kpi_df

def build_saw_kpis(df):
    df = df.copy()
    df.columns = df.columns.str.strip()

    df["Week Ending"] = pd.to_datetime(df["Week Ending"], dayfirst=True, errors="coerce")
    df["Hours Plan"] = pd.to_numeric(df["Hours Plan"], errors="coerce").fillna(0)

    today = pd.Timestamp.today().normalize()
    this_week = (today + pd.offsets.Week(weekday=4)).normalize()
    next_week = this_week + pd.Timedelta(days=7)

    grouped = (
        df[df["Week Ending"].isin([this_week, next_week])]
        .groupby("Week Ending")["Hours Plan"]
        .sum()
    )

    # Build KPI row manually
    kpi_df = pd.DataFrame({
        "This Week Hours": [grouped.get(this_week, 0)],
        "Next Week Hours": [grouped.get(next_week, 0)]
    })

    # Format
    kpi_df["This Week Hours"] = kpi_df["This Week Hours"].apply(format_hours)
    kpi_df["Next Week Hours"] = kpi_df["Next Week Hours"].apply(format_hours)

    return kpi_df

def build_flat_kpis(df):
    df = df.copy()

    # Fix column names (optional but safer)
    df.columns = df.columns.str.strip()

    # Convert types
    df["Week Ending"] = pd.to_datetime(df["Week Ending"], dayfirst=True, errors="coerce")
    df["Estimated Bundle Time (Hours)"] = pd.to_numeric(df["Estimated Bundle Time (Hours)"], errors="coerce").fillna(0)

    # Get this Friday + next Friday
    today = pd.Timestamp.today().normalize()
    this_week = (today + pd.offsets.Week(weekday=4)).normalize()
    next_week = this_week + pd.Timedelta(days=7)

    # Aggregate
    kpi_df = (
        df[df["Week Ending"].isin([this_week, next_week])]
        .groupby(["Site", "Week Ending"])["Estimated Bundle Time (Hours)"]
        .sum()
        .unstack(fill_value=0)
        .rename(columns={
            this_week: "This Week Hours",
            next_week: "Next Week Hours"
        })
        .reset_index()
    )

    # Ensure both columns exist (in case one week missing)
    for col in ["This Week Hours", "Next Week Hours"]:
        if col not in kpi_df:
            kpi_df[col] = 0

    kpi_df["This Week Hours"] = kpi_df["This Week Hours"].apply(format_hours)
    kpi_df["Next Week Hours"] = kpi_df["Next Week Hours"].apply(format_hours)

    return kpi_df

def build_fold_kpis(df):
    df = df.copy()

    # Fix column names (optional but safer)
    df.columns = df.columns.str.strip()

    # Convert types
    df["Week Ending"] = pd.to_datetime(df["Week Ending"], dayfirst=True, errors="coerce")
    df["Estimated Fold Time (Hours)"] = pd.to_numeric(df["Estimated Fold Time (Hours)"], errors="coerce").fillna(0)

    # Get this Friday + next Friday
    today = pd.Timestamp.today().normalize()
    this_week = (today + pd.offsets.Week(weekday=4)).normalize()
    next_week = this_week + pd.Timedelta(days=7)

    # Aggregate
    kpi_df = (
        df[df["Week Ending"].isin([this_week, next_week])]
        .groupby(["Site", "Week Ending"])["Estimated Fold Time (Hours)"]
        .sum()
        .unstack(fill_value=0)
        .rename(columns={
            this_week: "This Week Hours",
            next_week: "Next Week Hours"
        })
        .reset_index()
    )

    # Ensure both columns exist (in case one week missing)
    for col in ["This Week Hours", "Next Week Hours"]:
        if col not in kpi_df:
            kpi_df[col] = 0

    kpi_df["This Week Hours"] = kpi_df["This Week Hours"].apply(format_hours)
    kpi_df["Next Week Hours"] = kpi_df["Next Week Hours"].apply(format_hours)

    return kpi_df


def build_tube_kpis(df):
    df = df.copy()
    df.columns = df.columns.str.strip()

    df["Week Ending"] = pd.to_datetime(df["Week Ending"], dayfirst=True, errors="coerce")
    df["Estimated Bundle Time (Hours)"] = pd.to_numeric(df["Estimated Bundle Time (Hours)"], errors="coerce").fillna(0)

    today = pd.Timestamp.today().normalize()
    this_week = (today + pd.offsets.Week(weekday=4)).normalize()
    next_week = this_week + pd.Timedelta(days=7)

    grouped = (
        df[df["Week Ending"].isin([this_week, next_week])]
        .groupby("Week Ending")["Estimated Bundle Time (Hours)"]
        .sum()
    )

    # Build KPI row manually
    kpi_df = pd.DataFrame({
        "This Week Hours": [grouped.get(this_week, 0)],
        "Next Week Hours": [grouped.get(next_week, 0)]
    })

    # Format
    kpi_df["This Week Hours"] = kpi_df["This Week Hours"].apply(format_hours)
    kpi_df["Next Week Hours"] = kpi_df["Next Week Hours"].apply(format_hours)

    return kpi_df

def format_hours(hours):
    h = int(hours)
    m = int(round((hours - h) * 60))
    return f"{h}h {m}m"

def build_weld_chart_data(df, site):
    df = df.copy()

    # get global max for fixed graph scale
    full_weekly = (
        df.groupby("Week Ending")["Hours Plan"]
        .sum()
        .reset_index()
    )
    y_max = full_weekly["Hours Plan"].max() if not full_weekly.empty else 0

    # filter to only appropriate site
    df = df[df["Site"] == site]

    # Clean columns
    df.columns = df.columns.str.strip()

    # Convert types
    df["Week Ending"] = pd.to_datetime(df["Week Ending"], dayfirst=True, errors="coerce")
    df["Hours Plan"] = pd.to_numeric(df["Hours Plan"], errors="coerce").fillna(0)

    # Aggregate to weekly level
    weekly = (
        df.groupby("Week Ending")["Hours Plan"]
        .sum()
        .reset_index()
        .sort_values("Week Ending")
    )

    # Format label for display
    weekly["Week Label"] = weekly["Week Ending"].dt.strftime("%d %b")

    return weekly, y_max

def build_machine_chart_data(df, operation=None):
    df = df.copy()

    # Clean columns early
    df.columns = df.columns.str.strip()
    df["Operation"] = df["Operation"].astype(str).str.strip()

    # get global max for fixed graph scale
    full_weekly = (
        df.groupby("Week Ending")["Hours Plan"]
        .sum()
        .reset_index()
    )
    y_max = full_weekly["Hours Plan"].max() if not full_weekly.empty else 0

    # -----------------------------
    # Handle filtering properly
    # -----------------------------
    if operation is not None:
        # If empty list → return empty df
        if isinstance(operation, list) and len(operation) == 0:
            return pd.DataFrame(columns=["Week Ending", "Hours Plan", "Week Label"]), 0

        # If single string → convert to list
        if isinstance(operation, str):
            operation = [operation]

        df = df[df["Operation"].isin(operation)]

    # -----------------------------
    # Convert types
    # -----------------------------
    df["Week Ending"] = pd.to_datetime(df["Week Ending"], dayfirst=True, errors="coerce")
    df["Hours Plan"] = pd.to_numeric(df["Hours Plan"], errors="coerce").fillna(0)

    # -----------------------------
    # Handle empty AFTER filter
    # -----------------------------
    if df.empty:
        return pd.DataFrame(columns=["Week Ending", "Hours Plan", "Week Label"])

    # -----------------------------
    # Aggregate
    # -----------------------------
    weekly = (
        df.groupby("Week Ending")["Hours Plan"]
        .sum()
        .reset_index()
        .sort_values("Week Ending")
    )

    weekly["Week Label"] = weekly["Week Ending"].dt.strftime("%d %b")

    return weekly, y_max

def build_saw_chart_data(df):
    df = df.copy()

    # Clean columns
    df.columns = df.columns.str.strip()

    # Convert types
    df["Week Ending"] = pd.to_datetime(df["Week Ending"], dayfirst=True, errors="coerce")
    df["Hours Plan"] = pd.to_numeric(df["Hours Plan"], errors="coerce").fillna(0)

    # Aggregate to weekly level
    weekly = (
        df.groupby("Week Ending")["Hours Plan"]
        .sum()
        .reset_index()
        .sort_values("Week Ending")
    )

    # Format label for display
    weekly["Week Label"] = weekly["Week Ending"].dt.strftime("%d %b")

    return weekly

def build_tube_chart_data(df):
    df = df.copy()

    # Clean columns
    df.columns = df.columns.str.strip()

    # Convert types
    df["Week Ending"] = pd.to_datetime(df["Week Ending"], dayfirst=True, errors="coerce")
    df["Estimated Bundle Time (Hours)"] = pd.to_numeric(df["Estimated Bundle Time (Hours)"], errors="coerce").fillna(0)

    # Aggregate to weekly level
    weekly = (
        df.groupby("Week Ending")["Estimated Bundle Time (Hours)"]
        .sum()
        .reset_index()
        .sort_values("Week Ending")
    )

    # Format label for display
    weekly["Week Label"] = weekly["Week Ending"].dt.strftime("%d %b")
    weekly["Hours"] = weekly["Estimated Bundle Time (Hours)"].apply(format_hours)

    return weekly

def build_flat_chart_data(df, site):
    df = df.copy()

    # get global max for fixed graph scale
    full_weekly = (
        df.groupby("Week Ending")["Estimated Bundle Time (Hours)"]
        .sum()
        .reset_index()
    )
    y_max = full_weekly["Estimated Bundle Time (Hours)"].max() if not full_weekly.empty else 0

    # filter to only appropriate site
    df = df[df["Site"] == site]

    # Clean columns
    df.columns = df.columns.str.strip()

    # Convert types
    df["Week Ending"] = pd.to_datetime(df["Week Ending"], dayfirst=True, errors="coerce")
    df["Estimated Bundle Time (Hours)"] = pd.to_numeric(df["Estimated Bundle Time (Hours)"], errors="coerce").fillna(0)

    # Aggregate to weekly level
    weekly = (
        df.groupby("Week Ending")["Estimated Bundle Time (Hours)"]
        .sum()
        .reset_index()
        .sort_values("Week Ending")
    )

    # Format label for display
    weekly["Week Label"] = weekly["Week Ending"].dt.strftime("%d %b")
    weekly["Hours"] = weekly["Estimated Bundle Time (Hours)"].apply(format_hours)

    return weekly, y_max

def build_fold_chart_data(df, site):
    df = df.copy()

    # get global max for fixed graph scale
    full_weekly = (
        df.groupby("Week Ending")["Estimated Fold Time (Hours)"]
        .sum()
        .reset_index()
    )
    y_max = full_weekly["Estimated Fold Time (Hours)"].max() if not full_weekly.empty else 0

    # filter to only appropriate site
    df = df[df["Site"] == site]

    # Clean columns
    df.columns = df.columns.str.strip()

    # Convert types
    df["Week Ending"] = pd.to_datetime(df["Week Ending"], dayfirst=True, errors="coerce")
    df["Estimated Fold Time (Hours)"] = pd.to_numeric(df["Estimated Fold Time (Hours)"], errors="coerce").fillna(0)

    # Aggregate to weekly level
    weekly = (
        df.groupby("Week Ending")["Estimated Fold Time (Hours)"]
        .sum()
        .reset_index()
        .sort_values("Week Ending")
    )

    # Format label for display
    weekly["Week Label"] = weekly["Week Ending"].dt.strftime("%d %b")
    weekly["Hours"] = weekly["Estimated Fold Time (Hours)"].apply(format_hours)

    return weekly, y_max
    

def weld_table_filters(df):
    # filter by week ending
    weeks_dt = sorted(
        pd.to_datetime(df["Week Ending"], dayfirst=True).dropna().unique()
    )

    weeks = [d.strftime("%d/%m/%Y") for d in weeks_dt]

    # Get this week's Friday
    today = pd.Timestamp.today().normalize()
    this_week = (today + pd.offsets.Week(weekday=4)).strftime("%d/%m/%Y")

    # Set default (only if it exists in list)
    default_week = [this_week] if this_week in weeks else []

    selected_weeks = st.multiselect(
        "Filter By Week(s)",
        options=weeks,
        default=default_week,
        key="week_filter"
    )

    filtered_df = df[df["Week Ending"].isin(selected_weeks)]
    
    # strip back some unesscary fields and reorder
    filtered_df["Date Requested"] = pd.to_datetime(filtered_df["Date Requested"], errors="coerce").dt.strftime("%d/%m/%y")
    filtered_df = filtered_df.drop(columns=["Operation", "Customer Grouped"], errors="ignore")
    filtered_df = filtered_df[
        [
            "S.O. No.",
            "Number",
            "Customer",
            "Hours Plan",
            "Time Planned",
            "Date Requested",
            "Week Ending",
            "Site"
        ]
    ]
    filtered_df = filtered_df.sort_values("Hours Plan", ascending=False)
    
    return filtered_df

def machine_table_filters(df):
     # filter by week ending
    weeks_dt = sorted(
        pd.to_datetime(df["Week Ending"], dayfirst=True).dropna().unique()
    )

    weeks = [d.strftime("%d/%m/%Y") for d in weeks_dt]

    # Get this week's Friday
    today = pd.Timestamp.today().normalize()
    this_week = (today + pd.offsets.Week(weekday=4)).strftime("%d/%m/%Y")

    # Set default (only if it exists in list)
    default_week = [this_week] if this_week in weeks else []

    selected_weeks = st.multiselect(
        "Filter By Week(s)",
        options=weeks,
        default=default_week,
        key="week_filter"
    )

    df = df[df["Week Ending"].isin(selected_weeks)]
    df = df.drop(columns=["Site", "Customer Grouped", "Hours Plan"], errors="ignore")
    return df

def flat_table_filters(df, site):
    df = df.copy()
    # filter by site
    if site == "Ballymena":
        df = df[df["Machine"] == "Regius"]
    elif site == "Kilrea":
        df = df[df["Machine"] == "Ensis"]

    # strip columns and reorder
    df = df.drop(columns=["Completed?", "Customer Grouped", "Site"])
    df = df[[
        "Bundle/Job",
        "Hours",
        "Customer", 
        "Earliest Process Date",
        "Week Ending",
        "Sales Orders Included in Bundle",
        "Folding Required?",
        "Earliest Fold Date",
        "Estimated Fold Time (Hours)",
        "Fold Site",
        "Welding Required?",
        "Finishing Required?",
        "Type",
        "Machine"
    ]]

    # sort by num hours
    df = df.sort_values("Hours", ascending=False)
    return df

def fold_table_filters(df, site):
    df = df.copy()
    # site filter
    df = df[df["Site"] == site]
    #strip columns and reorder
    df = df.drop(columns=["Completed?", "Customer Grouped", "Machine", "Estimated Bundle Time (Hours)", "Earliest Process Date", "Type", "Estimated Fold Time (Hours)", "Folding Required?"])
    df = df[[
        "Bundle/Job",
        "Hours",
        "Customer",
        "Earliest Fold Date",
        "Week Ending",
        "Site",
        "Sales Orders Included in Bundle",
        "Welding Required?",
        "Finishing Required?"
    ]]
    #sort by num hours
    df = df.sort_values("Hours", ascending=False)
    return df

def tube_table_filters(df):
    df=df.copy()
    # strip columns and reorder
    df = df.drop(columns=["Completed?", "Customer Grouped", "Folding Required?", "Earliest Fold Date", "Estimated Fold Time (Hours)", "Fold Site", "Welding Required?", "Finishing Required?"])
    df = df[[
        "Bundle/Job",
        "Hours",
        "Customer", 
        "Earliest Process Date",
        "Week Ending",
        "Sales Orders Included in Bundle",
        "Type",
        "Machine"
    ]]

    # sort by num hours
    df = df.sort_values("Hours", ascending=False)
    return df