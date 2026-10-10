
import sqlite3

conn = sqlite3.connect("scamshield.db")
cursor = conn.cursor()

# Table 1: Demo scam identifiers
cursor.execute("""
CREATE TABLE IF NOT EXISTS scam_accounts (
    identifier TEXT PRIMARY KEY,
    note TEXT NOT NULL
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO scam_accounts (identifier, note)
VALUES (?, ?)
""", [
    ("scamdemo@upi", "Synthetic test record - not a real report"),
    ("fraudtest@upi", "Synthetic test record - not a real report")
])

# Table 2: Payment checks
cursor.execute("""
CREATE TABLE IF NOT EXISTS payment_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receiver TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount > 0),
    method TEXT NOT NULL,
    result TEXT NOT NULL,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Table 3: Scam reports
cursor.execute("""
CREATE TABLE IF NOT EXISTS scam_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identifier TEXT NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Unverified',
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

print("Database and tables created successfully!")

cursor.execute("""
SELECT name FROM sqlite_master
WHERE type = 'table'
ORDER BY name
""")

print("Tables:", cursor.fetchall())

conn.close()