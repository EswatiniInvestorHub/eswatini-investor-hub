#!/usr/bin/env python3
import argparse, json, sqlite3, uuid, re
from datetime import datetime

# ---------- Parsing helpers ----------
CURRENCY_RE = re.compile(r'^\s*([A-Za-z£$€]?)(?:\s*Z?L?)?\s*([\d\s,._-]+)\s*$', re.UNICODE)

def parse_currency(s):
    """Return (value_float, currency_code_or_symbol, original_str). Accepts 'E15.00', 'E369 602 010', '£2.75', '15.00'."""
    if s is None: return None, None, None
    if isinstance(s, (int, float)): return float(s), None, str(s)
    s = str(s).strip()
    m = CURRENCY_RE.match(s)
    if not m:
        return None, None, s
    symbol, num = m.groups()
    num = num.replace(',', '').replace(' ', '').replace('_', '')
    try:
        val = float(num)
    except ValueError:
        return None, symbol or None, s
    # Map symbol 'E' to SZL if you like, otherwise leave symbol
    currency = 'SZL' if symbol == 'E' else (symbol or None)
    return val, currency, s

DATE_FORMATS = [
    "%Y-%m-%d",
    "%d %B %Y",    # 10 April 2025
    "%d %b %Y",    # 10 Apr 2025
    "%d-%m-%Y",
    "%m/%d/%Y",
]

def to_iso_date(s):
    """Normalize date strings to YYYY-MM-DD; returns (iso, original)."""
    if not s:
        return None, None
    s = str(s).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date().isoformat(), s
        except Exception:
            pass
    # Already iso-like?
    if re.match(r'^\d{4}-\d{2}-\d{2}$', s):
        return s, s
    return None, s

def to_int_maybe(s):
    if s is None: return None
    if isinstance(s, (int, float)): return int(s)
    cleaned = re.sub(r'[^\d]', '', str(s))
    return int(cleaned) if cleaned.isdigit() else None

# ---------- DB setup ----------
DDL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS companies (
    id                    TEXT PRIMARY KEY,
    name                  TEXT,
    share_price_raw       TEXT,
    share_price_value     REAL,
    share_price_currency  TEXT,
    market_cap_raw        TEXT,
    market_cap_value      REAL,
    market_cap_currency   TEXT,
    stock_code            TEXT,
    listed_instruments    TEXT,
    website               TEXT,
    about                 TEXT,
    logo                  TEXT,
    ticker                TEXT,
    total_issued_shares_raw TEXT,
    total_issued_shares   INTEGER
);

CREATE TABLE IF NOT EXISTS news (
    id           TEXT PRIMARY KEY,
    company_id   TEXT NOT NULL,
    title        TEXT,
    date_raw     TEXT,
    date_iso     TEXT,
    content      TEXT,
    link         TEXT,
    doc          TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
    id           TEXT PRIMARY KEY,
    company_id   TEXT NOT NULL,
    title        TEXT,
    date_raw     TEXT,
    date_iso     TEXT,
    link         TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS price_history (
    company_id   TEXT NOT NULL,
    date_raw     TEXT,
    date_iso     TEXT,
    price        REAL,
    PRIMARY KEY (company_id, date_iso),
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- Optional: store summary open/close if present
CREATE TABLE IF NOT EXISTS price_summary (
    company_id   TEXT PRIMARY KEY,
    open_raw     TEXT,
    open_value   REAL,
    close_raw    TEXT,
    close_value  REAL,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);
CREATE INDEX IF NOT EXISTS idx_companies_ticker ON companies(ticker);
CREATE INDEX IF NOT EXISTS idx_news_company_date ON news(company_id, date_iso DESC);
CREATE INDEX IF NOT EXISTS idx_price_company_date ON price_history(company_id, date_iso DESC);
"""

UPSERT_COMPANY = """
INSERT INTO companies (
    id, name,
    share_price_raw, share_price_value, share_price_currency,
    market_cap_raw, market_cap_value, market_cap_currency,
    stock_code, listed_instruments, website, about, logo, ticker,
    total_issued_shares_raw, total_issued_shares
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
    name=excluded.name,
    share_price_raw=excluded.share_price_raw,
    share_price_value=excluded.share_price_value,
    share_price_currency=excluded.share_price_currency,
    market_cap_raw=excluded.market_cap_raw,
    market_cap_value=excluded.market_cap_value,
    market_cap_currency=excluded.market_cap_currency,
    stock_code=excluded.stock_code,
    listed_instruments=excluded.listed_instruments,
    website=excluded.website,
    about=excluded.about,
    logo=excluded.logo,
    ticker=excluded.ticker,
    total_issued_shares_raw=excluded.total_issued_shares_raw,
    total_issued_shares=excluded.total_issued_shares;
"""

UPSERT_NEWS = """
INSERT INTO news (id, company_id, title, date_raw, date_iso, content, link, doc)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
    company_id=excluded.company_id,
    title=excluded.title,
    date_raw=excluded.date_raw,
    date_iso=excluded.date_iso,
    content=excluded.content,
    link=excluded.link,
    doc=excluded.doc;
"""

UPSERT_EVENT = """
INSERT INTO events (id, company_id, title, date_raw, date_iso, link)
VALUES (?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
    company_id=excluded.company_id,
    title=excluded.title,
    date_raw=excluded.date_raw,
    date_iso=excluded.date_iso,
    link=excluded.link;
"""

UPSERT_PRICE = """
INSERT INTO price_history (company_id, date_raw, date_iso, price)
VALUES (?, ?, ?, ?)
ON CONFLICT(company_id, date_iso) DO UPDATE SET
    date_raw=excluded.date_raw,
    price=excluded.price;
"""

UPSERT_PRICE_SUMMARY = """
INSERT INTO price_summary (company_id, open_raw, open_value, close_raw, close_value)
VALUES (?, ?, ?, ?, ?)
ON CONFLICT(company_id) DO UPDATE SET
    open_raw=excluded.open_raw,
    open_value=excluded.open_value,
    close_raw=excluded.close_raw,
    close_value=excluded.close_value;
"""

def ensure_id(value):
    return value if value else str(uuid.uuid4())

# ---------- Conversion ----------
def convert(json_path, sqlite_path):
    with open(json_path, "r", encoding="utf-8") as f:
        root = json.load(f)

    companies = root.get("companies", [])
    conn = sqlite3.connect(sqlite_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()
    cur.executescript(DDL)

    n_comp = n_news = n_events = n_prices = 0

    for c in companies:
        cid = c.get("id") or str(uuid.uuid4())

        sp_val, sp_cur, sp_raw = parse_currency(c.get("share_price"))
        mc_val, mc_cur, mc_raw = parse_currency(c.get("market_cap"))
        total_shares_raw = c.get("total_issued_shares")
        total_shares = to_int_maybe(total_shares_raw)

        cur.execute(UPSERT_COMPANY, (
            cid, c.get("name"),
            sp_raw, sp_val, sp_cur,
            mc_raw, mc_val, mc_cur,
            c.get("stock_code"),
            c.get("listed_instruments"),
            c.get("website"),
            c.get("about"),
            c.get("logo"),
            c.get("ticker"),
            total_shares_raw, total_shares
        ))
        n_comp += 1

        # News
        for nw in c.get("latest_news", []) or []:
            nid = ensure_id(nw.get("id"))
            date_iso, date_raw = to_iso_date(nw.get("date"))
            cur.execute(UPSERT_NEWS, (
                nid, cid, nw.get("title"),
                date_raw, date_iso, nw.get("content"),
                nw.get("link"), nw.get("doc")
            ))
            n_news += 1

        # Events
        for ev in c.get("events", []) or []:
            evid = ensure_id(ev.get("id"))
            date_iso, date_raw = to_iso_date(ev.get("date"))
            cur.execute(UPSERT_EVENT, (
                evid, cid, ev.get("title"),
                date_raw, date_iso, ev.get("link")
            ))
            n_events += 1

        # Price history
        ph = c.get("price_history") or {}
        # Optional open/close
        if "open" in ph or "close" in ph:
            open_val, _, open_raw = parse_currency(ph.get("open"))
            close_val, _, close_raw = parse_currency(ph.get("close"))
            cur.execute(UPSERT_PRICE_SUMMARY, (cid, open_raw, open_val, close_raw, close_val))

        # Dense series
        for row in ph.get("data", []) or []:
            d_iso, d_raw = to_iso_date(row.get("date"))
            price = row.get("price")
            if d_iso and price is not None:
                cur.execute(UPSERT_PRICE, (cid, d_raw, d_iso, float(price)))
                n_prices += 1

    conn.commit()
    conn.close()
    print(f"✅ Done. Companies: {n_comp}, News: {n_news}, Events: {n_events}, Prices: {n_prices}")
    print(f"➡️  SQLite file written to: {sqlite_path}")

# ---------- CLI ----------
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Convert main.json to main.db (SQLite)")
    ap.add_argument("json_path", help="Path to main.json")
    ap.add_argument("sqlite_path", nargs="?", default="main.db", help="Output SQLite path (default: main.db)")
    args = ap.parse_args()
    convert(args.json_path, args.sqlite_path)
