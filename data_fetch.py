'''import requests
import pandas as pd
from bs4 import BeautifulSoup

# URL of the Hockey Reference standings page
url = "https://www.hockey-reference.com/leagues/NHL_2024_standings.html"

# Send a GET request to fetch the HTML content
response = requests.get(url)
response.raise_for_status()  # Check for HTTP request errors

# Parse the HTML with BeautifulSoup
soup = BeautifulSoup(response.content, "html.parser")

# Find the table that contains the "Team vs Team" records
# Look for the correct table ID or class name (this might need adjustments)
team_vs_team_table = soup.find("table", id="team_vs_team")

if team_vs_team_table:
    # Convert the "Team vs Team" table to a DataFrame using pandas
    df = pd.read_html(str(team_vs_team_table))[0]

    # Save the DataFrame to a CSV file
    csv_file = "team_vs_team_record.csv"
    df.to_csv(csv_file, index=False)

    print(f"Data has been saved to {csv_file}")
else:
    print("The 'Team vs Team' table was not found on the page. Check the table ID or structure.")
'''
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
