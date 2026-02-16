import pandas as pd
def load_data(filepath):
    df = pd.read_excel(filepath)

    df["Earliest Process Date"] = pd.to_datetime(
        df["Earliest Process Date"],
        dayfirst=True,
        errors="coerce"
    )
    return df

def add_date_columns(df):
    today = pd.Timestamp.today().normalize()
    df["Days Late"] = (df["Earliest Process Date"] - today).dt.days
    df["Is Late"] = df["Days Late"] < 0
    return df


def split_by_urgency(df):
    df = df.sort_values(by="Earliest Process Date", ascending=True).reset_index(drop=True)
    late_df = df[df["Days Late"] < 0]
    week_df = df[(df["Days Late"] >= 0) & (df["Days Late"] <= 7)]
    future_df = df[df["Days Late"] > 7]
    return late_df, week_df, future_df

def apply_filters(df, late_only, incomplete_only, selected_customers, selected_machines, customers, machines):
    filtered_df = df.copy()

    # Apply late filter
    if late_only:
        filtered_df = filtered_df[filtered_df["Days Late"] < 0]

    # Apply customer filter
    if set(selected_customers) != set(customers):
        filtered_df = filtered_df[
           filtered_df["Customer"].isin(selected_customers)
        ]

    # Apply machine filter
    if set(selected_machines) != set(machines):
        filtered_df = filtered_df[
         filtered_df["Machine"].isin(selected_machines)
        ]

    # apply incomplete filter
    if incomplete_only:
        filtered_df = filtered_df[filtered_df["Completed?"] == "No"]

    return filtered_df