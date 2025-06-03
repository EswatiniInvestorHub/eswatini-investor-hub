import pandas as pd
import json

# Path to your CSV and JSON files
csv_file_path = "c:/Users/Ndosi/Desktop/Ntando/New/Hub/static/SharePrices_Sorted.csv"
json_file_path = "c:/Users/Ndosi/Desktop/Ntando/New/Hub/static/main.json"

# Load the CSV file
share_prices_df = pd.read_csv(csv_file_path)

# Load the JSON file
with open(json_file_path, 'r') as json_file:
    companies_data = json.load(json_file)

# Mapping between CSV columns and JSON company IDs
company_mapping = {
    "Nedbank Eswatini": "company1",
    "Royal Swazi Sugar": "company4",
    "SWD Empowerment Limited": "company9",
    "SWAPROP": "company2",
    "Greystone": "company7",
    "SBC Limited": "company3",
    "Inala Capital Limited": "company6",
    "NPC Limited": "company5",
    "FNB Limited": "company8"
}

# Generate price history for a company
def generate_price_history(data, company_column):
    price_history = []
    for _, row in data.iterrows():
        price_history.append({
            "date": row["Date"],
            "price": row[company_column]
        })
    return price_history

# Update each company's price history in the JSON
for company in companies_data["companies"]:
    company_id = company["id"]
    # Find the matching column name in the CSV for the company ID
    csv_column = next((col for col, id_ in company_mapping.items() if id_ == company_id), None)
    if csv_column and csv_column in share_prices_df.columns:
        price_history = generate_price_history(share_prices_df, csv_column)
        company["price_history"] = {
            "open": f"E{price_history[0]['price']:.2f}",
            "close": f"E{price_history[-1]['price']:.2f}",
            "data": price_history
        }

# Save the updated JSON file
with open(json_file_path, 'w') as json_file:
    json.dump(companies_data, json_file, indent=4)

print("Price history updated successfully.")
