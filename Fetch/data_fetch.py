import pandas as pd

# Load the merged table
merged_table = pd.read_csv("merged_table.csv")  # Replace with the actual file path

# Sort the table by the 'Rk_y' column in ascending order
merged_table = merged_table.sort_values(by="Rk_y", ascending=True)

# Define the desired column order for head-to-head columns
head_to_head_columns = [
    "ANA", "ARI", "BOS", "BUF", "CAR", "CBJ", "CGY", "CHI", "COL", "DAL", "DET", "EDM", 
    "FLA", "LAK", "MIN", "MTL", "NJD", "NSH", "NYI", "NYR", "OTT", "PHI", "PIT", "SEA", 
    "SJS", "STL", "TBL", "TOR", "VAN", "VEG", "WPG", "WSH"
]

# Rearrange the head-to-head columns to the specified order
column_order = (
    [col for col in merged_table.columns if col not in head_to_head_columns] + head_to_head_columns
)
merged_table = merged_table[column_order]

# Save the updated table to a new CSV file
sorted_csv_file = "sorted_merged_table.csv"
merged_table.to_csv(sorted_csv_file, index=False)

print(f"Sorted and rearranged table has been saved to {sorted_csv_file}")
