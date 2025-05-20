from flask import Flask, jsonify, render_template, request, redirect, url_for
import json
import os
import pandas as pd
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename


app = Flask(__name__)

MAIN_JSON_PATH = 'C:/Users/Ndosi/Desktop/Ntando/Hub/static/main.json'
BONDS_JSON_PATH = 'C:/Users/Ndosi/Desktop/Ntando/Hub/static/Bonds.json'

def load_data():
    with open(MAIN_JSON_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(MAIN_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def load_bonds():
    if os.path.exists(BONDS_JSON_PATH):
        with open(BONDS_JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_bonds(bonds):
    with open(BONDS_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(bonds, f, indent=2)

@app.route('/')
def index():
    # Load Bonds
    try:
        with open(os.path.join(app.static_folder, 'Bonds.json'), 'r', encoding='utf-8') as f:
            bonds = json.load(f)
        print("✅ Bonds loaded.")
    except Exception as e:
        print(f"❌ Bonds load error: {e}")
        bonds = []

    # Load Companies
    try:
        with open(os.path.join(app.static_folder, 'main.json'), 'r', encoding='utf-8') as f:
            main_data = json.load(f)
        companies = main_data.get('companies', [])
        print(f"✅ Companies loaded: {len(companies)}")
    except Exception as e:
        print(f"❌ Companies load error: {e}")
        companies = []

    # Load Documents
    try:
        with open(os.path.join(app.static_folder, 'documents.json'), 'r', encoding='utf-8') as f:
            documents = json.load(f)
        print(f"✅ Documents loaded: {len(documents)}")
    except Exception as e:
        print(f"❌ Documents load error: {e}")
        documents = []

    # Render homepage with all data
    return render_template(
        'index.html',
        companies=companies,
        bonds=bonds,
        documents=documents
    )


@app.route('/update_price', methods=['POST'])
def update_price():
    company_id = request.form['company_id']
    new_price = float(request.form['price'])
    today = datetime.now().strftime('%Y-%m-%d')

    data = load_data()
    for company in data['companies']:
        if company['id'] == company_id:
            company['share_price'] = f"E{new_price:.2f}"
            company['price_history']['close'] = f"E{new_price:.2f}"
            company['price_history']['open'] = f"E{new_price:.2f}"
            company['price_history']['data'].insert(0, {
                "date": today,
                "price": new_price
            })
            break

    save_data(data)
    return redirect(url_for('admin'))

@app.route('/add_news', methods=['POST'])
def add_news():
    company_id = request.form['company_id']
    title = request.form['title']
    content = request.form['content']
    link = request.form['link']
    today = datetime.now().strftime('%-d %B %Y')
    news_id = str(uuid.uuid4())

    data = load_data()
    for company in data['companies']:
        if company['id'] == company_id:
            company.setdefault('latest_news', []).insert(0, {
                "id": news_id,
                "title": title,
                "date": today,
                "content": content,
                "link": link
            })
            break

    save_data(data)
    return redirect(url_for('admin'))

@app.route('/add_bond', methods=['POST'])
def add_bond():
    company_id = request.form['company_id']
    name = request.form['name']
    value = request.form['value']
    maturity = request.form['maturity']
    bond_id = str(uuid.uuid4())

    data = load_data()
    for company in data['companies']:
        if company['id'] == company_id:
            if 'bonds' not in company:
                company['bonds'] = []
            company['bonds'].append({
                "id": bond_id,
                "name": name,
                "value": value,
                "maturity": maturity
            })
            break

    save_data(data)
    return redirect(url_for('admin'))

@app.route('/delete_news', methods=['POST'])
def delete_news():
    news_id = request.form['news_id']
    data = load_data()
    for company in data['companies']:
        if 'latest_news' in company:
            company['latest_news'] = [n for n in company['latest_news'] if n.get('id') != news_id]
    save_data(data)
    return redirect(url_for('admin'))

@app.route('/delete_user', methods=['POST'])
def delete_user():
    user_id = request.form['user_id']
    data = load_data()
    data['users'] = [u for u in data['users'] if u.get('id') != user_id]
    save_data(data)
    return redirect(url_for('admin'))

@app.route('/add_user', methods=['POST'])
def add_user():
    user_id = str(uuid.uuid4())
    name = request.form['name']
    email = request.form['email']

    data = load_data()
    data.setdefault('users', []).append({
        "id": user_id,
        "name": name,
        "email": email
    })
    save_data(data)
    return redirect(url_for('admin'))

@app.route('/admin/bonds/add', methods=['POST'])
def add_external_bond():
    bonds = load_bonds()
    new_bond = {
        "id": str(uuid.uuid4()),
        "name": request.form['name'],
        "rate": request.form['rate'],
        "auction_date": request.form['auction_date']
    }
    bonds.append(new_bond)
    save_bonds(bonds)
    return redirect(url_for('admin'))


@app.route('/admin/bonds/delete', methods=['POST'])
def delete_external_bond():
    bond_id = request.form['bond_id']
    bonds = load_bonds()
    bonds = [b for b in bonds if b.get('id') != bond_id]
    save_bonds(bonds)
    return redirect(url_for('admin'))




@app.route('/api/equities', methods=['GET'])
def get_equities():
    data = load_json_data('main.json')
    equities = []

    for company in data.get('companies', []):
        name = company.get('name', 'Unknown')
        share_price = company.get('share_price', 'N/A')

        # Clean price string if it starts with "E" and convert to float
        try:
            clean_price = float(str(share_price).replace("E", "").strip())
        except:
            clean_price = None

        # Get price history for % change calculation
        price_data = company.get('price_history', {}).get('data', [])

        if len(price_data) >= 2:
            try:
                latest = float(price_data[0].get('price'))
                previous = float(price_data[1].get('price'))
                if previous != 0:
                    change = ((latest - previous) / previous) * 100
                    formatted_change = f"{change:+.2f}%"
                else:
                    formatted_change = "0%"
            except:
                formatted_change = "0%"
        else:
            formatted_change = "0%"

        equities.append({
            "issuer": name,
            "price": f"E{clean_price:.2f}" if clean_price is not None else share_price,
            "change": formatted_change
        })

    return jsonify(equities)






# Function to load data from JSON files in the static folder
def load_json_data(filename):
    filepath = os.path.join(app.static_folder, filename)
    with open(filepath, 'r') as f:
        return json.load(f)

# Routes for serving HTML pages
@app.route('/admin')
def admin():
    # --- Load Bonds ---
    try:
        with open(os.path.join(app.static_folder, 'Bonds.json'), 'r', encoding='utf-8') as f:
            bonds = json.load(f)
        print("✅ Bonds loaded.")
    except Exception as e:
        print(f"❌ Bonds load error: {e}")
        bonds = []

    # --- Load Companies and Users from main.json ---
    try:
        with open(os.path.join(app.static_folder, 'main.json'), 'r', encoding='utf-8') as f:
            main_data = json.load(f)
        companies = main_data.get('companies', [])
        users = main_data.get('users', [])
        print(f"✅ Companies loaded: {len(companies)}")
        print(f"✅ Users loaded: {len(users)}")
    except Exception as e:
        print(f"❌ main.json load error: {e}")
        companies, users = [], []

    # --- Load Documents ---
    try:
        doc_path = os.path.join(app.static_folder, 'documents.json')
        with open(doc_path, 'r', encoding='utf-8') as f:
            documents = json.load(f)
        print(f"✅ Documents loaded: {len(documents)}")
    except Exception as e:
        print(f"❌ Documents load error: {e}")
        documents = []

    # --- Render Admin Page ---
    return render_template(
        'admin.html',
        companies=companies,
        users=users,
        bonds=bonds,
        documents=documents
    )














@app.route('/news')
def news():
    return render_template('News.html')

@app.route('/education')
def education():
    return render_template('Education.html')

@app.route('/invest')
def invest():
    return render_template('Invest.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/faq')
def faq():
    return render_template('FAQ.html')

@app.route('/investments')
def investments():
    return render_template('Investments.html')

@app.route('/equities')
def equities():
    try:
        with open(os.path.join(app.static_folder, 'main.json'), 'r', encoding='utf-8') as f:
            data = json.load(f)
        companies = data.get('companies', [])
    except Exception as e:
        print("❌ Failed to load main.json:", e)
        companies = []

    return render_template('Eq.html', companies=companies)


@app.route('/bonds')
def bonds():
    json_path = os.path.join(app.root_path, 'static', 'Bonds.json')
    with open(json_path) as f:
        bond_data = json.load(f)
    return render_template('Bonds.html', bonds=bond_data)

@app.route('/funds')
def funds():
    return render_template('Funds.html')

@app.route('/estate')
def estate():
    return render_template('Estate.html')

@app.route('/about')
def about():
    return render_template('About.html')

@app.route('/contact')
def contact():
    return render_template('Contact.html')







@app.route('/api/news', methods=['GET'])
def get_news():
    data = load_json_data('news.json')
    return jsonify(data)

@app.route('/api/documents', methods=['GET'])
def get_documents():
    filepath = os.path.join(app.static_folder, 'documents.json')
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# New API Route for main.json
@app.route('/api/company/<company_id>', methods=['GET'])
def get_company(company_id):
    try:
        data = load_json_data('main.json')
        company = next((item for item in data['companies'] if item['id'] == company_id), None)
        if company:
            return jsonify(company)
        else:
            return jsonify({"error": "Company not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# New API Route for CSV Data
@app.route('/api/share_prices', methods=['GET'])
def get_share_prices():
    try:
        csv_file_path = os.path.join(app.static_folder, 'Share Prices_Sorted.csv')
        df = pd.read_csv(csv_file_path)
        data = df.to_dict(orient='records')
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/upload_document', methods=['POST'])
def upload_document():
    file = request.files['file']
    description = request.form['description']
    release_date = request.form['release_date']

    if file:
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(app.static_folder, 'documents')
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)

        file_link = f'/static/documents/{filename}'

        # Update documents.json
        doc_path = os.path.join(app.static_folder, 'documents.json')
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                docs = json.load(f)
        except:
            docs = []

        docs.insert(0, {
            "description": description,
            "release_date": release_date,
            "file_link": file_link
        })

        with open(doc_path, 'w', encoding='utf-8') as f:
            json.dump(docs, f, indent=2)

    return redirect(url_for('admin'))



@app.route('/delete_document', methods=['POST'])
def delete_document():
    file_link = request.form['file_link']  # e.g. "/static/documents/report.pdf"

    # ✅ Load and update documents.json
    json_path = os.path.join(app.static_folder, 'documents.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            docs = json.load(f)

        # Filter out the document to delete
        updated_docs = [doc for doc in docs if doc.get('file_link') != file_link]

        # Save the updated list
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(updated_docs, f, indent=2)

        print(f"✅ Deleted entry from documents.json: {file_link}")
    except Exception as e:
        print(f"❌ Error updating documents.json: {e}")

    return redirect(url_for('admin'))






# Search Route
@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('query', '').lower()
    
    equities = load_json_data('equities.json')
    news = load_json_data('news.json')
    documents = load_json_data('documents.json')
    main_data = load_json_data('main.json')['companies']  # Adjusting to new structure
    
    def search_in_data(data, query):
        return [item for item in data if query in json.dumps(item).lower()]
    
    equities_results = search_in_data(equities, query)
    news_results = search_in_data(news, query)
    documents_results = search_in_data(documents, query)
    main_results = search_in_data(main_data, query)
    
    results = {
        "equities": equities_results,
        "news": news_results,
        "documents": documents_results,
        "main": main_results
    }
    
    if not any(results.values()):
        return jsonify({"message": "not available"})
    
    return jsonify(results)

# Run the application
if __name__ == '__main__':
    app.run(debug=True)