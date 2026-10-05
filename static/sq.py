import sqlite3
import os

# Build absolute path to static/main.db
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # path to static/
DB_PATH = os.path.join(BASE_DIR, "main.db")

print("Using DB:", DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("PRAGMA table_info(price_history);")
print(cur.fetchall())
