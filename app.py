from flask import Flask, jsonify, render_template, request, redirect, url_for
import json
import os
import pandas as pd
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import timedelta


app = Flask(__name__)
app.secret_key = 'Investor'  # Replace with a real secret key
app.permanent_session_lifetime = timedelta(minutes=20)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "securepassword123"


MAIN_JSON_PATH = os.path.join(app.static_folder, 'main.json')
BONDS_JSON_PATH = os.path.join(app.static_folder, 'Bonds.json')

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
    link = request.form.get('link', '')
    raw_date = request.form['date']

    try:
        formatted_date = datetime.strptime(raw_date, "%Y-%m-%d").strftime('%d %B %Y')
    except ValueError:
        return "Invalid date format. Use the date picker.", 400

    news_id = str(uuid.uuid4())

    data = load_data()
    for company in data['companies']:
        if company['id'] == company_id:
            company.setdefault('latest_news', []).insert(0, {
                "id": news_id,
                "title": title,
                "date": formatted_date,
                "content": content,
                "link": link,
                "doc": ""  # ✅ Add this line
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
    company_id = request.form['company_id']
    news_id = request.form['news_id']

    data = load_data()

    for company in data['companies']:
        if company['id'] == company_id:
            news_list = company.get('latest_news', [])
            company['latest_news'] = [n for n in news_list if n.get('id') != news_id]
            save_data(data)
            flash('News deleted successfully.')
            break

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

from flask import request, redirect, url_for
from werkzeug.utils import secure_filename
import uuid, os

@app.route('/admin/bonds/add', methods=['POST'])
def add_external_bond():
    bonds = load_bonds()
    bond_id = str(uuid.uuid4())

    # Get form data
    name = request.form['name']
    programme = request.form['programme']
    rate = request.form['rate']
    maturity_date = request.form['maturity_date']
    payment_frequency = request.form['payment_frequency']
    email = request.form['email']
    phone = request.form.get('phone', '')
    link = request.form.get('link', '')

    # Upload logo(s)
    logos = []
    logo_files = request.files.getlist('logos')
    logo_path = os.path.join(app.static_folder, 'images', 'bonds')
    os.makedirs(logo_path, exist_ok=True)

    for logo_file in logo_files:
        if logo_file and logo_file.filename:
            filename = secure_filename(f"{bond_id}_{logo_file.filename}")
            filepath = os.path.join(logo_path, filename)
            logo_file.save(filepath)
            logos.append(f"images/bonds/{filename}")

    # Upload PDF
    pdf_file = request.files['pdf']
    pdf_filename = secure_filename(f"{bond_id}_{pdf_file.filename}")
    pdf_dir = os.path.join(app.static_folder, 'pdfs')
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.join(pdf_dir, pdf_filename)
    pdf_file.save(pdf_path)

    # Create bond record
    new_bond = {
        "id": bond_id,
        "name": name,
        "programme": programme,
        "rate": rate,
        "maturity_date": maturity_date,
        "payment_frequency": payment_frequency,
        "email": email,
        "phone": phone,
        "logos": logos,
        "pdf": f"pdfs/{pdf_filename}"
    }

    if link:
        new_bond["link"] = link

    bonds.append(new_bond)
    save_bonds(bonds)

    return redirect(url_for('admin'))


@app.route('/admin/bonds/delete', methods=['POST'])
def delete_external_bond():
    bond_id = request.form['bond_id']
    bonds = load_bonds()
    updated_bonds = []

    for bond in bonds:
        if bond.get('id') == bond_id:
            # Delete logo files
            for logo in bond.get('logos', []):
                try:
                    os.remove(os.path.join(app.static_folder, logo))
                except Exception as e:
                    print(f"Failed to delete logo: {e}")

            # Delete PDF file
            try:
                os.remove(os.path.join(app.static_folder, bond['pdf']))
            except Exception as e:
                print(f"Failed to delete PDF: {e}")
        else:
            updated_bonds.append(bond)

    save_bonds(updated_bonds)
    return redirect(url_for('admin'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Simple authentication (replace with your own logic)
        if username == 'admin' and password == 'Investor@Hub2025':
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash('Invalid credentials', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


from flask import request, redirect, url_for, flash
from datetime import datetime
import json, os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@app.route('/submit_question', methods=['POST'])
def submit_question():
    name = request.form['name']
    email = request.form['email']
    question = request.form['question']
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    entry = {
        "timestamp": timestamp,
        "name": name,
        "email": email,
        "question": question
    }

    # Save to a local JSON file
    path = os.path.join(app.static_folder, 'questions.json')
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = []

        data.append(entry)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        send_question_email(name, email, question)  # 🔔 Send email alert

        flash("✅ Thank you! Your question has been submitted.")
    except Exception as e:
        flash(f"❌ Error saving your question: {e}")

    return redirect(url_for('faq'))


def send_question_email(name, sender_email, question):
    # Email configuration
    smtp_user = "mntandoyenkhosi@gmail.com"
    smtp_pass = "bjnl wnrf ovca krdj"  # Gmail App Password

    receiver_email = "mntandoyenkhosi@gmail.com"
    subject = f"New FAQ Question from {name}"

    # Compose email
    message = MIMEMultipart()
    message["From"] = smtp_user
    message["To"] = receiver_email
    message["Subject"] = subject

    body = f"""
    A new question was submitted via the FAQ form:

    Name: {name}
    Email: {sender_email}

    Question:
    {question}
    """

    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, receiver_email, message.as_string())
        server.quit()
        print("✅ Question email sent successfully.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


from dateutil.relativedelta import relativedelta

@app.route('/api/equities', methods=['GET'])
def get_equities():
    data = load_json_data('main.json')
    equities = []

    for company in data.get('companies', []):
        name = company.get('name', 'Unknown')
        share_price = company.get('share_price', 'N/A')

        try:
            clean_price = float(str(share_price).replace("E", "").strip())
        except:
            clean_price = None

        price_data = company.get('price_history', {}).get('data', [])
        formatted_change = "0%"

        if len(price_data) >= 2:
            try:
                # Sort data by date ascending
                sorted_data = sorted(price_data, key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'))

                # Convert dates to datetime for comparison
                for entry in sorted_data:
                    entry['date_obj'] = datetime.strptime(entry['date'], '%Y-%m-%d')

                latest_entry = sorted_data[-1]
                latest_date = latest_entry['date_obj']
                latest_price = float(latest_entry['price'])

                # Target date is one month before
                target_month = latest_date - relativedelta(months=1)

                # Find the closest earlier date in the same month as target
                previous_entry = None
                for entry in reversed(sorted_data[:-1]):
                    entry_month = entry['date_obj'].month
                    entry_year = entry['date_obj'].year

                    if entry_year == target_month.year and entry_month == target_month.month:
                        previous_entry = entry
                        break

                if previous_entry:
                    previous_price = float(previous_entry['price'])
                    if previous_price != 0:
                        change = ((latest_price - previous_price) / previous_price) * 100
                        formatted_change = f"{change:+.2f}%"
                else:
                    formatted_change = "0%"
            except Exception as e:
                print(f"❌ Error processing {name}: {e}")
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
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
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



@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))




@app.route('/news')
def news():
    return render_template('News.html')

@app.route('/edit_news/<company_id>/<news_id>', methods=['GET'])
def edit_news(company_id, news_id):
    data = load_data()
    company = next((c for c in data['companies'] if c['id'] == company_id), None)
    if not company:
        return "Company not found", 404

    news_item = next((n for n in company.get("latest_news", []) if n["id"] == news_id), None)
    if not news_item:
        return "News item not found", 404

    # Convert existing '05 June 2024' to '2024-06-05'
    try:
        formatted_input_date = datetime.strptime(news_item["date"], "%d %B %Y").strftime('%Y-%m-%d')
    except ValueError:
        formatted_input_date = ""

    return render_template(
        "edit_news.html",
        company_id=company_id,
        news=news_item,
        formatted_input_date=formatted_input_date
    )




@app.route('/api/bonds')
def api_bonds():
    try:
        bonds = load_bonds()
        return jsonify(bonds)
    except Exception as e:
        print(f"❌ Error loading bonds: {e}")
        return jsonify({'error': 'Failed to load bonds'}), 500



@app.route('/education')
def education():
    return render_template('Education.html')

@app.route('/admin/edit_news', methods=['GET'])
def edit_news_form():
    company_id = request.args.get('company_id')
    news_id = request.args.get('news_id')
    data = load_data()

    for company in data['companies']:
        if company['id'] == company_id:
            for news in company.get('latest_news', []):
                if news['id'] == news_id:
                    return render_template('edit_news.html', news=news, company_id=company_id)

    return "News item not found", 404




@app.route('/update_news', methods=['POST'])
def update_news():
    company_id = request.form['company_id']
    news_id = request.form['news_id']
    title = request.form['title']
    content = request.form['content']
    link = request.form.get('link', '')
    remove_doc = request.form.get('remove_doc')
    doc_file = request.files.get('doc_file')

    # Keep the existing formatted date
    date = request.form['date']
    try:
        formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime('%d %B %Y')
    except ValueError:
        formatted_date = date  # fallback to existing format

    new_doc_path = ''
    if doc_file and doc_file.filename.endswith('.pdf'):
        filename = f"{uuid.uuid4()}.pdf"
        save_path = os.path.join(app.static_folder, 'documents', filename)
        doc_file.save(save_path)
        new_doc_path = f"documents/{filename}"

    data = load_data()
    for company in data['companies']:
        if company['id'] == company_id:
            for news in company.get("latest_news", []):
                if news['id'] == news_id:
                    news['title'] = title
                    news['date'] = formatted_date
                    news['content'] = content
                    news['link'] = link
                    if remove_doc:
                        news['doc'] = ''
                    elif new_doc_path:
                        news['doc'] = new_doc_path
                    break

    save_data(data)
    return redirect(url_for('admin'))






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
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            bonds = json.load(f)
        print(f"✅ Loaded {len(bonds)} bonds.")
    except Exception as e:
        print(f"❌ Failed to load Bonds.json: {e}")
        bonds = []

    return render_template('Bonds.html', bonds=bonds)


@app.route('/funds')
def funds():
    return render_template('Funds.html')

@app.route('/estate')
def estate():
    return render_template('Estate.html')

@app.route('/company/<company_id>')
def company_detail(company_id):
    data = load_data()
    company = next((c for c in data['companies'] if c['id'] == company_id), None)
    if not company:
        return "Company not found", 404

    current_date = datetime.now().strftime('%d %B %Y')
    return render_template('company_detail.html', company=company, current_date=current_date)



@app.route('/admin/company/<company_id>', methods=['GET', 'POST'])
def edit_company(company_id):
    data = load_data()

    company = next((c for c in data['companies'] if c['id'] == company_id), None)
    if not company:
        return "Company not found", 404

    if request.method == 'POST':
        # Update About
        company['about'] = request.form.get('about', '')

        # Update Events
        event_titles = request.form.getlist('event_title')
        event_dates = request.form.getlist('event_date')
        event_links = request.form.getlist('event_link')

        company['events'] = []
        for title, date, link in zip(event_titles, event_dates, event_links):
            if title.strip():  # Avoid blank rows
                company['events'].append({
                    'title': title,
                    'date': date,
                    'link': link
                })

        save_data(data)
        return redirect(url_for('edit_company', company_id=company_id))

    return render_template('admin_edit_company.html', company=company)





@app.route('/about')
def about():
    return render_template('About.html')

from collections import OrderedDict

@app.route('/update_share_price', methods=['POST'])
def update_share_price():
    company_id = request.form['company_id']
    new_price = request.form['new_price']

    data = load_data()
    today = datetime.now().strftime('%Y-%m-%d')

    for i, company in enumerate(data['companies']):
        if company['id'] == company_id:
            # Update share price
            company['share_price'] = f"E{new_price}"

            # Update price history
            history = company.setdefault("price_history", {}).setdefault("data", [])
            history.append({"date": today, "price": float(new_price)})

            # Reorder keys to ensure share_price is last
            reordered = OrderedDict()
            for key in company:
                if key != "share_price":
                    reordered[key] = company[key]
            reordered["share_price"] = company["share_price"]
            data['companies'][i] = reordered
            break

    save_data(data)
    return redirect(url_for('admin'))


@app.route('/contact')
def contact():
    return render_template('Contact.html')







@app.route('/api/news', methods=['GET'])
def get_news():
    data = load_data()  # ✅ This should load main.json
    news_items = []

    for company in data.get("companies", []):
        for news in company.get("latest_news", []):
            news_items.append(news)

    # ✅ Sort by most recent date
    news_items.sort(key=lambda x: datetime.strptime(x["date"], "%d %B %Y"), reverse=True)

    return jsonify(news_items)

@app.route('/api/admin_news', methods=['GET'])
def get_admin_news():
    data = load_data()
    admin_news_items = []

    for company in data.get("companies", []):
        company_id = company.get("id")
        for news in company.get("latest_news", []):
            item = news.copy()
            item["company_id"] = company_id
            admin_news_items.append(item)

    # Sort by most recent date
    admin_news_items.sort(key=lambda x: datetime.strptime(x["date"], "%d %B %Y"), reverse=True)
    return jsonify(admin_news_items)



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


# Run the application
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)