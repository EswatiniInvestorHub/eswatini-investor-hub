import json

# Path to your main.json
MAIN_JSON_PATH = 'C:/Users/Ndosi/Desktop/Ntando/Hub/static/main.json'

# Mapping from company ID to the update data (from your spreadsheet)
updates_by_id = {
    "company1": {
        "ticker": "NED",
        "stock_code": "SZ0005797904",
        "market_cap": "E369 602 010",
        "total_issued_shares": "24 640 134"
    },
    "company4": {
        "ticker": "RSC",
        "stock_code": "SZ0005797920",
        "market_cap": "E1 637 887 440",
        "total_issued_shares": "96 346 320"
    },
    "company9": {
        "ticker": "SEL",
        "stock_code": "SZE000331015",
        "market_cap": "E684 500 000",
        "total_issued_shares": "18 500 000"
    },
    "company2": {
        "ticker": "SWP",
        "stock_code": "SZ0005797946",
        "market_cap": "E186 000 000",
        "total_issued_shares": "23 250 000"
    },
    "company7": {
        "ticker": "GRYS",
        "stock_code": "SZE000331023",
        "market_cap": "E597 796 079",
        "total_issued_shares": "229 921 569"
    },
    "company3": {
        "ticker": "SBC",
        "stock_code": "SZE000331031",
        "market_cap": "E868 410 000",
        "total_issued_shares": "96 490 000"
    },
    "company6": {
        "ticker": "INALA",
        "stock_code": "SZE000331049",
        "market_cap": "E86 392 800",
        "total_issued_shares": "71 994 000"
    },
    "company5": {
        "ticker": "NPC",
        "stock_code": "SZE000331056",
        "market_cap": "E268 500 000",
        "total_issued_shares": "179 000 000"
    },
    "company8": {
        "ticker": "FNBE",
        "stock_code": "SZE000331064",
        "market_cap": "E1 972 390 000",
        "total_issued_shares": "133 000 000"
    }
}

# Load the existing main.json
with open(MAIN_JSON_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Update each company by id
for company in data.get("companies", []):
    cid = company.get("id")
    if cid in updates_by_id:
        company.update(updates_by_id[cid])

# Save changes
with open(MAIN_JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print("✅ Company updates applied using company IDs.")
