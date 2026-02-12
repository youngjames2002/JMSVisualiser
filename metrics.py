def calculate_totals(df):
    tube_df = df[df["Type"] == "TUBE"]
    flat_df = df[df["Type"] == "FLAT"]

    total_folding = df["Estimated Fold Time (Hours)"].sum()
    flat_cutting = flat_df["Estimated Bundle Time (Hours)"].sum()
    tube_cutting = tube_df["Estimated Bundle Time (Hours)"].sum()

    return total_folding, flat_cutting, tube_cutting