import json

# Path to your main.json file
MAIN_JSON_PATH = 'C:/Users/Ndosi/Desktop/Ntando/Hub/static/main.json'

# Load the JSON data
with open(MAIN_JSON_PATH, 'r', encoding='utf-8') as file:
    data = json.load(file)

# Add "doc": "" to every news item in each company
for company in data.get("companies", []):
    news_list = company.get("latest_news", [])
    for news_item in news_list:
        if "doc" not in news_item:
            news_item["doc"] = ""

# Save the updated JSON data
with open(MAIN_JSON_PATH, 'w', encoding='utf-8') as file:
    json.dump(data, file, indent=2)

print("✅ Added 'doc' field to all latest_news items.")
