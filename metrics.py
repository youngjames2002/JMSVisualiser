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

    return summary