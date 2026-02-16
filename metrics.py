import pandas as pd

def calculate_totals(df):
    tube_df = df[df["Type"] == "TUBE"]
    flat_df = df[df["Type"] == "FLAT"]

    total_folding = df["Estimated Fold Time (Hours)"].sum()
    flat_cutting = flat_df["Estimated Bundle Time (Hours)"].sum()
    tube_cutting = tube_df["Estimated Bundle Time (Hours)"].sum()

    return total_folding, flat_cutting, tube_cutting

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