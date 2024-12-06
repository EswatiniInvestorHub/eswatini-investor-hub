from flask import Flask, jsonify, render_template, request
import json
import os
import pandas as pd

app = Flask(__name__)

# Function to load data from JSON files in the static folder
def load_json_data(filename):
    filepath = os.path.join(app.static_folder, filename)
    with open(filepath, 'r') as f:
        return json.load(f)

# Routes for serving HTML pages
@app.route('/')
def index():
    return render_template('index.html')

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
    return render_template('Eq.html')

@app.route('/bonds')
def bonds():
    return render_template('Bonds.html')

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

# API Routes for JSON Data
@app.route('/api/equities', methods=['GET'])
def get_equities():
    data = load_json_data('equities.json')
    return jsonify(data)

@app.route('/api/news', methods=['GET'])
def get_news():
    data = load_json_data('news.json')
    return jsonify(data)

@app.route('/api/documents', methods=['GET'])
def get_documents():
    data = load_json_data('documents.json')
    return jsonify(data)

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