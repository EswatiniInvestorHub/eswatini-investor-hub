from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from datetime import timedelta, datetime
import sqlite3
import os
import uuid
import json
from functools import wraps
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

# IMPORTANT:
# Put a strong SECRET_KEY, ADMIN_USERNAME and ADMIN_PASSWORD
# in Render Environment Variables for production.
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")
app.permanent_session_lifetime = timedelta(minutes=20)

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "securepassword123")

# Keep the database outside the static/ folder.
# On Render, set DB_PATH to a persistent-disk path if you use
# a persistent disk. Locally, this defaults to instance/main.db.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_DB_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(DEFAULT_DB_DIR, exist_ok=True)

DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(DEFAULT_DB_DIR, "main.db")
)

# Uploaded documents/bond files are stored under static/uploads locally.
UPLOAD_ROOT = os.path.join(BASE_DIR, "static", "uploads")
DOCUMENT_UPLOAD_DIR = os.path.join(UPLOAD_ROOT, "documents")
BOND_UPLOAD_DIR = os.path.join(UPLOAD_ROOT, "bonds")
os.makedirs(DOCUMENT_UPLOAD_DIR, exist_ok=True)
os.makedirs(BOND_UPLOAD_DIR, exist_ok=True)


# ============================================================
# DATABASE HELPERS
# ============================================================

def get_db_connection():
    """Open a SQLite connection with dictionary-like rows."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def table_exists(conn, table_name):
    """Return True if a table exists."""
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    ).fetchone()
    return row is not None


def column_exists(conn, table_name, column_name):
    """Return True if a column exists in a table."""
    if not table_exists(conn, table_name):
        return False

    columns = conn.execute(
        f'PRAGMA table_info("{table_name}")'
    ).fetchall()

    return any(column["name"] == column_name for column in columns)


def ensure_database():
    """
    Create the database tables if they do not exist.

    This does NOT delete or overwrite existing data.
    It is safe to run when the converted main.db already exists.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            share_price REAL,
            market_cap INTEGER,
            stock_code TEXT,
            listed_instruments TEXT,
            website TEXT,
            about TEXT,
            logo TEXT,
            ticker TEXT,
            total_issued_shares INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id TEXT NOT NULL,
            date TEXT NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id TEXT PRIMARY KEY,
            company_id TEXT,
            title TEXT NOT NULL,
            date TEXT,
            date_iso TEXT,
            content TEXT,
            link TEXT,
            doc TEXT,
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            company_id TEXT,
            title TEXT NOT NULL,
            date TEXT,
            date_iso TEXT,
            link TEXT,
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bonds (
            id TEXT PRIMARY KEY,
            company_id TEXT,
            name TEXT,
            value REAL,
            interest_rate REAL,
            maturity_date TEXT,
            description TEXT,
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TEXT
        )
    """)

    # External bonds used by the existing Bonds.html page.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS external_bonds (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            programme TEXT,
            rate TEXT,
            maturity_date TEXT,
            payment_frequency TEXT,
            email TEXT,
            phone TEXT,
            logos TEXT,
            pdf TEXT,
            link TEXT,
            auction_date TEXT
        )
    """)

    # Documents used by the existing Admin panel.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            release_date TEXT,
            file_link TEXT NOT NULL
        )
    """)

    # Questions submitted through the FAQ page.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            question TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Indexes make common dashboard/company queries faster.
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_price_history_company_date
        ON price_history(company_id, date)
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_news_company_date
        ON news(company_id, date_iso)
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_company_date
        ON events(company_id, date_iso)
    """)

    conn.commit()
    conn.close()


# Create tables when the app starts.
ensure_database()


def ensure_external_bonds_schema():
    """Add required columns to an existing external_bonds table."""
    conn = get_db_connection()

    if table_exists(conn, "external_bonds") and not column_exists(
        conn, "external_bonds", "auction_date"
    ):
        conn.execute(
            "ALTER TABLE external_bonds ADD COLUMN auction_date TEXT"
        )
        conn.commit()

    conn.close()


def seed_legacy_bonds():
    """Restore the three public bonds without overwriting existing records."""
    conn = get_db_connection()

    legacy_bonds = [
        (
            "legacy-npc100", "Nkonyeni Precast", "NPC 100",
            "Prime Plus 1.5%", "05 April 2034", "Annual",
            "transfersecretary@sng.gt.com", "+26824057000",
            __import__("json").dumps([
                "https://eswatini-investor-hub-2.onrender.com/static/images/logo/npc1.jpg"
            ]),
            "https://eswatini-investor-hub-2.onrender.com/static/documents/npc100.pdf",
            "", "05 April 2024"
        ),
        (
            "legacy-npc102", "Nkonyeni Precast", "NPC 102",
            "Prime Plus 1%", "02 January 2030", "Annual",
            "transfersecretary@sng.gt.com", "+26824057000",
            __import__("json").dumps([
                "https://eswatini-investor-hub-2.onrender.com/static/images/logo/npc1.jpg"
            ]),
            "https://eswatini-investor-hub-2.onrender.com/static/documents/npc102.pdf",
            "", ""
        ),
        (
            "legacy-government", "Government Bond", "SGIFB008",
            "11.5%", "30 May 2032", "Semi Annual",
            "cbe_domestic_market@centralbank.org.sz", "",
            __import__("json").dumps([
                "https://eswatini-investor-hub-2.onrender.com/static/images/logo/gov.jpg",
                "https://eswatini-investor-hub-2.onrender.com/static/images/logo/ebc.jpg"
            ]),
            "https://eswatini-investor-hub-2.onrender.com/static/documents/government_bond.pdf",
            "https://lnkd.in/", ""
        ),
    ]

    conn.executemany(
        """
        INSERT OR IGNORE INTO external_bonds
        (
            id, name, programme, rate, maturity_date,
            payment_frequency, email, phone, logos, pdf, link, auction_date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        legacy_bonds
    )

    conn.commit()
    conn.close()


ensure_external_bonds_schema()
seed_legacy_bonds()


# ============================================================
# FORMATTING / DATA HELPERS
# ============================================================

def format_currency(value, decimals=2):
    """Format a numeric value as Eswatini Lilangeni."""
    if value is None:
        return "N/A"

    try:
        value = float(value)
        return f"E{value:,.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)


def parse_money(value):
    """
    Convert values such as:
      E15.00
      E369 602 010
      15.00
    into numeric values.
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return value

    cleaned = str(value).strip()
    cleaned = cleaned.replace("E", "").replace("e", "")
    cleaned = cleaned.replace(",", "").replace(" ", "")

    if not cleaned:
        return None

    try:
        number = float(cleaned)

        # Return integers as integers where appropriate.
        if number.is_integer():
            return int(number)

        return number
    except ValueError:
        return None


def normalize_date(date_value):
    """
    Convert common date inputs to YYYY-MM-DD.
    Returns None when no valid date can be parsed.
    """
    if not date_value:
        return None

    date_value = str(date_value).strip()

    formats = [
        "%Y-%m-%d",
        "%d %B %Y",
        "%d %b %Y",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass

    return None


def display_date(date_iso):
    """Convert YYYY-MM-DD to a readable date."""
    if not date_iso:
        return ""

    try:
        return datetime.strptime(
            str(date_iso), "%Y-%m-%d"
        ).strftime("%d %B %Y")
    except ValueError:
        return str(date_iso)


def company_share_price(company):
    """Return a numeric company share price."""
    return parse_money(company.get("share_price"))


def calculate_price_change(conn, company_id):
    """
    Calculate the latest price change using the two latest
    historical observations.

    Returns:
        change_value, change_percent
    """
    rows = conn.execute("""
        SELECT price
        FROM price_history
        WHERE company_id = ?
        ORDER BY date DESC, id DESC
        LIMIT 2
    """, (company_id,)).fetchall()

    if len(rows) < 2:
        return 0.0, 0.0

    latest = float(rows[0]["price"])
    previous = float(rows[1]["price"])

    change = latest - previous

    if previous == 0:
        percent = 0.0
    else:
        percent = (change / previous) * 100

    return change, percent


# ============================================================
# DATA LOADING
# ============================================================

def load_data():
    """
    Load the complete public/admin dataset in the same general
    structure that the old JSON application expected.

    This makes migration easier because existing templates can
    continue using:
        company["price_history"]["data"]
        company["latest_news"]
        company["events"]
        company["bonds"]
    """
    conn = get_db_connection()

    company_rows = conn.execute("""
        SELECT *
        FROM companies
        ORDER BY name ASC
    """).fetchall()

    companies = []

    for row in company_rows:
        company = dict(row)

        # Current price
        company["share_price_value"] = company_share_price(company)

        # Price change
        change_value, change_percent = calculate_price_change(
            conn, company["id"]
        )

        company["price_change"] = change_value
        company["price_change_percent"] = change_percent

        # Keep formatted display price available.
        if company["share_price_value"] is not None:
            company["share_price_display"] = format_currency(
                company["share_price_value"]
            )
        else:
            company["share_price_display"] = "N/A"

        # Price history
        price_rows = conn.execute("""
            SELECT id, date, price
            FROM price_history
            WHERE company_id = ?
            ORDER BY date DESC, id DESC
        """, (company["id"],)).fetchall()

        company["price_history"] = {
            "data": [
                {
                    "date": ph["date"],
                    "price": float(ph["price"])
                }
                for ph in price_rows
            ]
        }

        # News
        news_rows = conn.execute("""
            SELECT id, company_id, title, date, date_iso,
                   content, link, doc
            FROM news
            WHERE company_id = ?
            ORDER BY
                CASE WHEN date_iso IS NULL OR date_iso = '' THEN 1 ELSE 0 END,
                date_iso DESC,
                id DESC
        """, (company["id"],)).fetchall()

        company["latest_news"] = []

        for n in news_rows:
            item = dict(n)

            if not item.get("date") and item.get("date_iso"):
                item["date"] = display_date(item["date_iso"])

            company["latest_news"].append(item)

        # Events
        event_rows = conn.execute("""
            SELECT id, company_id, title, date, date_iso, link
            FROM events
            WHERE company_id = ?
            ORDER BY
                CASE WHEN date_iso IS NULL OR date_iso = '' THEN 1 ELSE 0 END,
                date_iso DESC,
                id DESC
        """, (company["id"],)).fetchall()

        company["events"] = [dict(e) for e in event_rows]

        # Bonds
        bond_rows = conn.execute("""
            SELECT id, company_id, name, value,
                   interest_rate, maturity_date, description
            FROM bonds
            WHERE company_id = ?
            ORDER BY maturity_date ASC, name ASC
        """, (company["id"],)).fetchall()

        company["bonds"] = [dict(b) for b in bond_rows]

        companies.append(company)

    user_rows = conn.execute("""
        SELECT *
        FROM users
        ORDER BY created_at DESC, name ASC
    """).fetchall()

    users = [dict(u) for u in user_rows]

    # All bonds/events are also returned separately for templates
    # that expect top-level collections.
    bond_rows = conn.execute("""
        SELECT *
        FROM bonds
        ORDER BY name ASC
    """).fetchall()

    bonds = [dict(b) for b in bond_rows]

    event_rows = conn.execute("""
        SELECT *
        FROM events
        ORDER BY
            CASE WHEN date_iso IS NULL OR date_iso = '' THEN 1 ELSE 0 END,
            date_iso DESC
    """).fetchall()

    events = [dict(e) for e in event_rows]

    news_rows = conn.execute("""
        SELECT *
        FROM news
        ORDER BY
            CASE WHEN date_iso IS NULL OR date_iso = '' THEN 1 ELSE 0 END,
            date_iso DESC
    """).fetchall()

    all_news = [dict(n) for n in news_rows]

    external_bond_rows = conn.execute("""
        SELECT *
        FROM external_bonds
        ORDER BY name ASC
    """).fetchall()
    external_bonds = []
    for row in external_bond_rows:
        item = dict(row)
        item["logos"] = json.loads(item.get("logos") or "[]")
        external_bonds.append(item)

    document_rows = conn.execute("""
        SELECT *
        FROM documents
        ORDER BY release_date DESC, id DESC
    """).fetchall()
    documents = [dict(row) for row in document_rows]

    conn.close()

    return {
        "companies": companies,
        "users": users,
        # "bonds" remains the company-bond collection from the converted DB.
        "bonds": bonds,
        "external_bonds": external_bonds,
        "documents": documents,
        "events": events,
        "news": all_news,
    }


def get_company(company_id):
    """Return one company or None."""
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM companies WHERE id = ?",
        (company_id,)
    ).fetchone()
    conn.close()

    return dict(row) if row else None


# ============================================================
# ADMIN AUTHENTICATION
# ============================================================

def admin_required(view_function):
    """Protect an admin route."""
    @wraps(view_function)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("login"))
        return view_function(*args, **kwargs)

    return wrapped


# ============================================================
# PUBLIC HOME
# ============================================================

@app.route("/")
def index():
    data = load_data()

    return render_template(
        "index.html",
        companies=data["companies"],
        bonds=data["external_bonds"],
        events=data["events"],
        news=data["news"],
        documents=data["documents"]
    )


# ============================================================
# ADMIN
# ============================================================

@app.route("/admin")
@admin_required
def admin():
    data = load_data()

    return render_template(
        "admin.html",
        companies=data["companies"],
        users=data["users"],
        bonds=data["external_bonds"],
        events=data["events"],
        news=data["news"],
        documents=data["documents"]
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.permanent = True
            session["admin_logged_in"] = True
            flash("Logged in successfully.", "success")
            return redirect(url_for("admin"))

        flash("Invalid credentials.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


# ============================================================
# COMPANY PRICE MANAGEMENT
# ============================================================

@app.route("/update_price", methods=["POST"])
@admin_required
def update_price():
    company_id = request.form.get("company_id", "").strip()
    price_raw = request.form.get("price", "").strip()
    date_raw = request.form.get("date", "").strip()

    if not company_id or not price_raw:
        flash("Company and price are required.", "error")
        return redirect(url_for("admin"))

    price = parse_money(price_raw)

    if price is None or price < 0:
        flash("Please enter a valid price.", "error")
        return redirect(url_for("admin"))

    date_iso = normalize_date(date_raw) if date_raw else datetime.now().strftime(
        "%Y-%m-%d"
    )

    if not date_iso:
        flash("Invalid date.", "error")
        return redirect(url_for("admin"))

    conn = get_db_connection()

    company = conn.execute(
        "SELECT id FROM companies WHERE id = ?",
        (company_id,)
    ).fetchone()

    if not company:
        conn.close()
        flash("Company not found.", "error")
        return redirect(url_for("admin"))

    # Update current price.
    conn.execute("""
        UPDATE companies
        SET share_price = ?
        WHERE id = ?
    """, (price, company_id))

    # If a record already exists for that company/date, update it.
    existing = conn.execute("""
        SELECT id
        FROM price_history
        WHERE company_id = ? AND date = ?
        LIMIT 1
    """, (company_id, date_iso)).fetchone()

    if existing:
        conn.execute("""
            UPDATE price_history
            SET price = ?
            WHERE id = ?
        """, (price, existing["id"]))
    else:
        conn.execute("""
            INSERT INTO price_history (company_id, date, price)
            VALUES (?, ?, ?)
        """, (company_id, date_iso, price))

    conn.commit()
    conn.close()

    flash(
        f"Share price updated successfully to {format_currency(price)}.",
        "success"
    )

    return redirect(url_for("admin"))


# ============================================================
# NEWS MANAGEMENT
# ============================================================

@app.route("/add_news", methods=["POST"])
@admin_required
def add_news():
    company_id = request.form.get("company_id", "").strip()
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    link = request.form.get("link", "").strip()
    raw_date = request.form.get("date", "").strip()
    doc = request.form.get("doc", "").strip()

    if not company_id or not title or not content:
        flash("Company, title and content are required.", "error")
        return redirect(url_for("admin"))

    date_iso = normalize_date(raw_date)

    if raw_date and not date_iso:
        flash("Invalid news date.", "error")
        return redirect(url_for("admin"))

    if not date_iso:
        date_iso = datetime.now().strftime("%Y-%m-%d")

    formatted_date = display_date(date_iso)
    news_id = str(uuid.uuid4())

    conn = get_db_connection()

    company = conn.execute(
        "SELECT id FROM companies WHERE id = ?",
        (company_id,)
    ).fetchone()

    if not company:
        conn.close()
        flash("Company not found.", "error")
        return redirect(url_for("admin"))

    conn.execute("""
        INSERT INTO news
            (id, company_id, title, date, date_iso, content, link, doc)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        news_id,
        company_id,
        title,
        formatted_date,
        date_iso,
        content,
        link,
        doc
    ))

    conn.commit()
    conn.close()

    flash("News added successfully.", "success")
    return redirect(url_for("admin"))


@app.route("/delete_news", methods=["POST"])
@admin_required
def delete_news():
    news_id = request.form.get("news_id", "").strip()

    if not news_id:
        flash("News ID is required.", "error")
        return redirect(url_for("admin"))

    conn = get_db_connection()

    cursor = conn.execute(
        "DELETE FROM news WHERE id = ?",
        (news_id,)
    )

    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    if deleted:
        flash("News deleted successfully.", "success")
    else:
        flash("News item not found.", "error")

    return redirect(url_for("admin"))


# ============================================================
# USER MANAGEMENT
# ============================================================

@app.route("/add_user", methods=["POST"])
@admin_required
def add_user():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()

    if not name or not email:
        flash("Name and email are required.", "error")
        return redirect(url_for("admin"))

    user_id = str(uuid.uuid4())
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO users (id, name, email, created_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, name, email, created_at))

    conn.commit()
    conn.close()

    flash("User added successfully.", "success")
    return redirect(url_for("admin"))


@app.route("/delete_user", methods=["POST"])
@admin_required
def delete_user():
    user_id = request.form.get("user_id", "").strip()

    if not user_id:
        flash("User ID is required.", "error")
        return redirect(url_for("admin"))

    conn = get_db_connection()

    cursor = conn.execute(
        "DELETE FROM users WHERE id = ?",
        (user_id,)
    )

    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    if deleted:
        flash("User deleted successfully.", "success")
    else:
        flash("User not found.", "error")

    return redirect(url_for("admin"))


# ============================================================
# OPTIONAL COMPANY DETAIL ROUTE
# ============================================================

@app.route("/company/<company_id>")
def company_detail(company_id):
    conn = get_db_connection()

    company_row = conn.execute("""
        SELECT *
        FROM companies
        WHERE id = ?
    """, (company_id,)).fetchone()

    if not company_row:
        conn.close()
        return "Company not found", 404

    company = dict(company_row)

    price_rows = conn.execute("""
        SELECT date, price
        FROM price_history
        WHERE company_id = ?
        ORDER BY date DESC, id DESC
    """, (company_id,)).fetchall()

    company["price_history"] = {
        "data": [
            {"date": row["date"], "price": float(row["price"])}
            for row in price_rows
        ]
    }

    news_rows = conn.execute("""
        SELECT *
        FROM news
        WHERE company_id = ?
        ORDER BY date_iso DESC, id DESC
    """, (company_id,)).fetchall()

    company["latest_news"] = [dict(row) for row in news_rows]

    event_rows = conn.execute("""
        SELECT *
        FROM events
        WHERE company_id = ?
        ORDER BY date_iso DESC, id DESC
    """, (company_id,)).fetchall()

    company["events"] = [dict(row) for row in event_rows]

    bond_rows = conn.execute("""
        SELECT *
        FROM bonds
        WHERE company_id = ?
        ORDER BY maturity_date ASC
    """, (company_id,)).fetchall()

    company["bonds"] = [dict(row) for row in bond_rows]

    change_value, change_percent = calculate_price_change(
        conn, company_id
    )

    company["price_change"] = change_value
    company["price_change_percent"] = change_percent
    company["share_price_value"] = company_share_price(company)
    company["share_price_display"] = (
        format_currency(company["share_price_value"])
        if company["share_price_value"] is not None
        else "N/A"
    )

    conn.close()

    # This route expects company.html. If you don't have that template
    # yet, create it later. Existing pages are unaffected.
    return render_template("company_detail.html", company=company)



# ============================================================
# EQUITIES / BONDS PAGES
# ============================================================

@app.route("/equities")
def equities():
    """Render the existing equities dashboard."""
    data = load_data()
    return render_template("Eq.html", companies=data["companies"])


@app.route("/bonds")
def bonds():
    """Render the existing external-bonds dashboard."""
    data = load_data()
    return render_template("Bonds.html", bonds=data["external_bonds"])


# ============================================================
# COMPANY EDITING
# ============================================================

@app.route("/edit_company/<company_id>", methods=["GET", "POST"])
@admin_required
def edit_company(company_id):
    conn = get_db_connection()

    company_row = conn.execute(
        "SELECT * FROM companies WHERE id = ?",
        (company_id,)
    ).fetchone()

    if not company_row:
        conn.close()
        flash("Company not found.", "error")
        return redirect(url_for("admin"))

    if request.method == "POST":
        about = request.form.get("about", "").strip()

        conn.execute(
            "UPDATE companies SET about = ? WHERE id = ?",
            (about, company_id)
        )

        # The existing form submits repeated event_title/event_date/event_link
        # fields. Rebuild the company's events from those submitted values.
        titles = request.form.getlist("event_title")
        dates = request.form.getlist("event_date")
        links = request.form.getlist("event_link")

        conn.execute("DELETE FROM events WHERE company_id = ?", (company_id,))

        for title, date_value, link in zip(titles, dates, links):
            title = title.strip()
            date_value = date_value.strip()
            link = link.strip()

            if not title:
                continue

            date_iso = normalize_date(date_value) if date_value else ""
            display_value = (
                display_date(date_iso) if date_iso else date_value
            )

            conn.execute("""
                INSERT INTO events
                    (company_id, title, date, date_iso, link)
                VALUES (?, ?, ?, ?, ?)
            """, (
                company_id,
                title,
                display_value,
                date_iso,
                link
            ))

        conn.commit()
        conn.close()

        flash("Company information and events updated successfully.", "success")
        return redirect(url_for("admin"))

    company = dict(company_row)
    event_rows = conn.execute("""
        SELECT *
        FROM events
        WHERE company_id = ?
        ORDER BY
            CASE WHEN date_iso IS NULL OR date_iso = '' THEN 1 ELSE 0 END,
            date_iso ASC,
            id ASC
    """, (company_id,)).fetchall()
    company["events"] = [dict(row) for row in event_rows]

    conn.close()

    return render_template("admin_edit_company.html", company=company)


# ============================================================
# NEWS EDITING
# ============================================================

@app.route("/edit_news/<company_id>/<news_id>", methods=["GET"])
@admin_required
def edit_news(company_id, news_id):
    conn = get_db_connection()

    row = conn.execute("""
        SELECT *
        FROM news
        WHERE id = ? AND company_id = ?
    """, (news_id, company_id)).fetchone()

    conn.close()

    if not row:
        flash("News item not found.", "error")
        return redirect(url_for("admin"))

    news_item = dict(row)
    formatted_input_date = (
        news_item.get("date_iso")
        or normalize_date(news_item.get("date"))
        or ""
    )

    return render_template(
        "edit_news.html",
        news=news_item,
        company_id=company_id,
        formatted_input_date=formatted_input_date
    )


@app.route("/update_news", methods=["POST"])
@admin_required
def update_news():
    company_id = request.form.get("company_id", "").strip()
    news_id = request.form.get("news_id", "").strip()
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    link = request.form.get("link", "").strip()
    raw_date = request.form.get("date", "").strip()
    remove_doc = request.form.get("remove_doc") == "1"

    if not company_id or not news_id or not title or not content:
        flash("Company, news ID, title and content are required.", "error")
        return redirect(url_for("admin"))

    date_iso = normalize_date(raw_date)
    if raw_date and not date_iso:
        flash("Invalid news date.", "error")
        return redirect(url_for("admin"))

    if not date_iso:
        date_iso = datetime.now().strftime("%Y-%m-%d")

    conn = get_db_connection()
    old = conn.execute(
        "SELECT doc FROM news WHERE id = ? AND company_id = ?",
        (news_id, company_id)
    ).fetchone()

    if not old:
        conn.close()
        flash("News item not found.", "error")
        return redirect(url_for("admin"))

    old_doc = old["doc"] or ""
    new_doc = "" if remove_doc else old_doc

    doc_file = request.files.get("doc_file")
    if doc_file and doc_file.filename:
        filename = secure_filename(doc_file.filename)
        if not filename.lower().endswith(".pdf"):
            conn.close()
            flash("News document must be a PDF.", "error")
            return redirect(url_for("admin"))

        unique_name = f"{uuid.uuid4().hex}_{filename}"
        save_path = os.path.join(DOCUMENT_UPLOAD_DIR, unique_name)
        doc_file.save(save_path)
        new_doc = os.path.join(
            "uploads", "documents", unique_name
        ).replace("\\", "/")

    conn.execute("""
        UPDATE news
        SET title = ?, date = ?, date_iso = ?, content = ?, link = ?, doc = ?
        WHERE id = ? AND company_id = ?
    """, (
        title,
        display_date(date_iso),
        date_iso,
        content,
        link,
        new_doc,
        news_id,
        company_id
    ))

    conn.commit()
    conn.close()

    flash("News item updated successfully.", "success")
    return redirect(url_for("admin"))


# ============================================================
# ADMIN NEWS API
# ============================================================

@app.route("/api/admin_news", methods=["GET"])
@admin_required
def api_admin_news():
    conn = get_db_connection()

    rows = conn.execute("""
        SELECT *
        FROM news
        ORDER BY
            CASE WHEN date_iso IS NULL OR date_iso = '' THEN 1 ELSE 0 END,
            date_iso DESC,
            id DESC
    """).fetchall()

    result = [dict(row) for row in rows]
    conn.close()
    return jsonify(result)


# ============================================================
# EXTERNAL BOND MANAGEMENT
# ============================================================

@app.route("/add_external_bond", methods=["POST"])
@admin_required
def add_external_bond():
    name = request.form.get("name", "").strip()
    programme = request.form.get("programme", "").strip()
    rate = request.form.get("rate", "").strip()
    maturity_date = request.form.get("maturity_date", "").strip()
    payment_frequency = request.form.get("payment_frequency", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    link = request.form.get("link", "").strip()

    if not all([name, programme, rate, maturity_date,
                payment_frequency, email]):
        flash("Please complete all required bond fields.", "error")
        return redirect(url_for("admin"))

    pdf_file = request.files.get("pdf")
    if not pdf_file or not pdf_file.filename:
        flash("A PDF file is required.", "error")
        return redirect(url_for("admin"))

    pdf_filename = secure_filename(pdf_file.filename)
    if not pdf_filename.lower().endswith(".pdf"):
        flash("Bond details file must be a PDF.", "error")
        return redirect(url_for("admin"))

    bond_id = str(uuid.uuid4())
    unique_pdf = f"{bond_id}_{pdf_filename}"
    pdf_file.save(os.path.join(BOND_UPLOAD_DIR, unique_pdf))

    logos = []
    for logo_file in request.files.getlist("logos"):
        if not logo_file or not logo_file.filename:
            continue

        logo_filename = secure_filename(logo_file.filename)
        ext = os.path.splitext(logo_filename)[1].lower()
        if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}:
            continue

        unique_logo = f"{uuid.uuid4().hex}_{logo_filename}"
        logo_file.save(os.path.join(BOND_UPLOAD_DIR, unique_logo))
        logos.append(os.path.join(
            "uploads", "bonds", unique_logo
        ).replace("\\", "/"))

        if len(logos) >= 2:
            break

    pdf_relative = os.path.join(
        "uploads", "bonds", unique_pdf
    ).replace("\\", "/")

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO external_bonds
            (id, name, programme, rate, maturity_date,
             payment_frequency, email, phone, logos, pdf, link)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        bond_id, name, programme, rate, maturity_date,
        payment_frequency, email, phone, json.dumps(logos),
        pdf_relative, link
    ))
    conn.commit()
    conn.close()

    flash("Bond added successfully.", "success")
    return redirect(url_for("admin"))


@app.route("/delete_external_bond", methods=["POST"])
@admin_required
def delete_external_bond():
    bond_id = request.form.get("bond_id", "").strip()

    conn = get_db_connection()
    row = conn.execute(
        "SELECT pdf, logos FROM external_bonds WHERE id = ?",
        (bond_id,)
    ).fetchone()

    if not row:
        conn.close()
        flash("Bond not found.", "error")
        return redirect(url_for("admin"))

    files_to_delete = [row["pdf"] or ""]
    try:
        files_to_delete.extend(json.loads(row["logos"] or "[]"))
    except json.JSONDecodeError:
        pass

    conn.execute("DELETE FROM external_bonds WHERE id = ?", (bond_id,))
    conn.commit()
    conn.close()

    for relative in files_to_delete:
        if not relative:
            continue
        absolute = os.path.join(BASE_DIR, "static", relative)
        if os.path.isfile(absolute):
            try:
                os.remove(absolute)
            except OSError:
                pass

    flash("Bond deleted successfully.", "success")
    return redirect(url_for("admin"))


# ============================================================
# DOCUMENT MANAGEMENT
# ============================================================

@app.route("/upload_document", methods=["POST"])
@admin_required
def upload_document():
    description = request.form.get("description", "").strip()
    release_date = request.form.get("release_date", "").strip()
    uploaded = request.files.get("file")

    if not description or not release_date or not uploaded or not uploaded.filename:
        flash("Description, release date and PDF are required.", "error")
        return redirect(url_for("admin"))

    date_iso = normalize_date(release_date)
    if not date_iso:
        flash("Invalid release date.", "error")
        return redirect(url_for("admin"))

    filename = secure_filename(uploaded.filename)
    if not filename.lower().endswith(".pdf"):
        flash("Only PDF documents are allowed.", "error")
        return redirect(url_for("admin"))

    unique_name = f"{uuid.uuid4().hex}_{filename}"
    uploaded.save(os.path.join(DOCUMENT_UPLOAD_DIR, unique_name))

    relative = os.path.join(
        "uploads", "documents", unique_name
    ).replace("\\", "/")

    doc_id = str(uuid.uuid4())
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO documents
            (id, description, release_date, file_link)
        VALUES (?, ?, ?, ?)
    """, (doc_id, description, date_iso, relative))
    conn.commit()
    conn.close()

    flash("Document uploaded successfully.", "success")
    return redirect(url_for("admin"))


@app.route("/delete_document", methods=["POST"])
@admin_required
def delete_document():
    file_link = request.form.get("file_link", "").strip()

    conn = get_db_connection()
    row = conn.execute(
        "SELECT id, file_link FROM documents WHERE file_link = ?",
        (file_link,)
    ).fetchone()

    if not row:
        conn.close()
        flash("Document not found.", "error")
        return redirect(url_for("admin"))

    conn.execute("DELETE FROM documents WHERE id = ?", (row["id"],))
    conn.commit()
    conn.close()

    absolute = os.path.join(BASE_DIR, "static", file_link)
    if os.path.isfile(absolute):
        try:
            os.remove(absolute)
        except OSError:
            pass

    flash("Document deleted successfully.", "success")
    return redirect(url_for("admin"))


# ============================================================
# FAQ QUESTION SUBMISSION
# ============================================================

@app.route("/submit_question", methods=["POST"])
def submit_question():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    question = request.form.get("question", "").strip()

    if not name or not email or not question:
        flash("Please complete all fields.", "error")
        return redirect(url_for("faq"))

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO questions (id, name, email, question, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        name,
        email,
        question,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

    flash("Your question has been submitted successfully.", "success")
    return redirect(url_for("faq"))


# ============================================================
# PUBLIC STATIC / INFORMATION PAGES
# ============================================================

@app.route("/news")
def news():
    # Pass real database news where possible.
    data = load_data()
    return render_template(
        "News.html",
        news=data["news"],
        companies=data["companies"]
    )


@app.route("/education")
def education():
    return render_template("Education.html")


@app.route("/invest")
def invest():
    return render_template("Invest.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/faq")
def faq():
    return render_template("FAQ.html")


@app.route("/investments")
def investments():
    data = load_data()

    return render_template(
        "Investments.html",
        companies=data["companies"],
        bonds=data["bonds"]
    )


@app.route("/funds")
def funds():
    return render_template("Funds.html")


@app.route("/estate")
def estate():
    return render_template("Estate.html")


@app.route("/about")
def about():
    return render_template("About.html")


@app.route("/contact")
def contact():
    return render_template("Contact.html")


# ============================================================
# API
# ============================================================

@app.route("/api/equities", methods=["GET"])
def get_equities():
    conn = get_db_connection()

    rows = conn.execute("""
        SELECT *
        FROM companies
        ORDER BY name ASC
    """).fetchall()

    equities = []

    for row in rows:
        company = dict(row)

        change_value, change_percent = calculate_price_change(
            conn, company["id"]
        )

        price = parse_money(company.get("share_price"))

        equities.append({
            "id": company["id"],
            "issuer": company["name"],
            "name": company["name"],
            "ticker": company.get("ticker"),
            "stock_code": company.get("stock_code"),
            "price": price,
            "price_display": (
                format_currency(price)
                if price is not None else "N/A"
            ),
            # Keep "change" as a percentage string because the existing
            # Eq.html JavaScript calls .replace("%", "") on it.
            "change": f"{change_percent:+.2f}%",
            "change_display": f"{change_percent:+.2f}%",
            "change_value": round(change_value, 4),
            "market_cap": company.get("market_cap"),
            "market_cap_display": (
                format_currency(company["market_cap"], 0)
                if company.get("market_cap") is not None
                else "N/A"
            )
        })

    conn.close()
    return jsonify(equities)


@app.route("/api/bonds", methods=["GET"])
def get_bonds():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT *
        FROM external_bonds
        ORDER BY name ASC
    """).fetchall()

    result = []
    for row in rows:
        item = dict(row)
        try:
            item["logos"] = json.loads(item.get("logos") or "[]")
        except json.JSONDecodeError:
            item["logos"] = []
        result.append(item)

    conn.close()
    return jsonify(result)


@app.route("/api/news", methods=["GET"])
def get_news():
    conn = get_db_connection()

    rows = conn.execute("""
        SELECT
            n.*,
            c.name AS company_name,
            c.ticker AS company_ticker
        FROM news n
        LEFT JOIN companies c ON c.id = n.company_id
        ORDER BY
            CASE WHEN n.date_iso IS NULL OR n.date_iso = '' THEN 1 ELSE 0 END,
            n.date_iso DESC,
            n.id DESC
    """).fetchall()

    news_items = [dict(row) for row in rows]

    conn.close()
    return jsonify(news_items)


@app.route("/api/users", methods=["GET"])
@admin_required
def get_users():
    conn = get_db_connection()

    rows = conn.execute("""
        SELECT *
        FROM users
        ORDER BY created_at DESC, name ASC
    """).fetchall()

    users = [dict(row) for row in rows]

    conn.close()
    return jsonify(users)


@app.route("/api/companies/<company_id>", methods=["GET"])
def api_company(company_id):
    conn = get_db_connection()

    company_row = conn.execute("""
        SELECT *
        FROM companies
        WHERE id = ?
    """, (company_id,)).fetchone()

    if not company_row:
        conn.close()
        return jsonify({"error": "Company not found"}), 404

    company = dict(company_row)

    price_rows = conn.execute("""
        SELECT date, price
        FROM price_history
        WHERE company_id = ?
        ORDER BY date ASC, id ASC
    """, (company_id,)).fetchall()

    news_rows = conn.execute("""
        SELECT *
        FROM news
        WHERE company_id = ?
        ORDER BY date_iso DESC, id DESC
    """, (company_id,)).fetchall()

    event_rows = conn.execute("""
        SELECT *
        FROM events
        WHERE company_id = ?
        ORDER BY date_iso DESC, id DESC
    """, (company_id,)).fetchall()

    bond_rows = conn.execute("""
        SELECT *
        FROM bonds
        WHERE company_id = ?
        ORDER BY maturity_date ASC
    """, (company_id,)).fetchall()

    change_value, change_percent = calculate_price_change(
        conn, company_id
    )

    result = {
        "company": company,
        "price_history": [
            {
                "date": row["date"],
                "price": float(row["price"])
            }
            for row in price_rows
        ],
        "news": [dict(row) for row in news_rows],
        "events": [dict(row) for row in event_rows],
        "bonds": [dict(row) for row in bond_rows],
        "change": round(change_value, 4),
        "change_percent": round(change_percent, 4)
    }

    conn.close()
    return jsonify(result)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():
    """Simple endpoint useful for deployment checks."""
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1").fetchone()
        conn.close()

        return jsonify({
            "status": "ok",
            "database": "connected"
        })
    except Exception as exc:
        return jsonify({
            "status": "error",
            "database": "unavailable",
            "error": str(exc)
        }), 500


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(error):
    return "<h1>404 - Page Not Found</h1><p>The requested page does not exist.</p>", 404


@app.errorhandler(500)
def internal_server_error(error):
    return "<h1>500 - Internal Server Error</h1><p>The application encountered an error.</p>", 500


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=os.environ.get("FLASK_DEBUG", "0") == "1"
    )
