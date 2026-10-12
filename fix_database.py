
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "scamshield.db")
connection = sqlite3.connect(db_path)
cursor = connection.cursor()

for table in ["scam_accounts", "payment_checks", "scam_reports"]:
    print("\nTABLE:", table)
    cursor.execute('PRAGMA table_info("' + table + '")')
    rows = cursor.fetchall()

    if not rows:
        print("No columns found")
    else:
        for row in rows:
            print("Column:", row[1], "| Type:", row[2])

connection.close()
input("\nPress Enter to close...")
