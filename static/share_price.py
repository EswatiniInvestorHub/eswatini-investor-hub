import json

filepath = 'C:/Users/Ndosi/Desktop/Ntando/New/Hub/static/main.json'

with open(filepath, 'r', encoding='utf-8') as f:
    data = json.load(f)

for company in data.get('companies', []):
    try:
        price_history = company.get('price_history', {})
        price_data = price_history.get('data', [])
        latest_close = None

        if price_data and price_data[-1].get('close'):
            latest_close = price_data[-1]['close']
        elif price_history.get('close'):
            latest_close = price_history['close']

        if latest_close:
            company['share_price'] = latest_close
            print(f"✅ {company['name']}: share_price updated to {latest_close}")
        else:
            print(f"⚠️ {company['name']}: No close value found.")
    except Exception as e:
        print(f"❌ Error processing {company.get('name', 'unknown')}: {e}")

with open(filepath, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print("✅ All share_price fields updated.")
