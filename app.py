
from flask import Flask, render_template, request
import sqlite3
import os

app = Flask(__name__)

DB_PATH = os.path.join(app.root_path, "scamshield.db")


# Connect to the SQLite database
def get_db():
    return sqlite3.connect(DB_PATH)


# Create database tables
def init_db():
    with get_db() as conn:

        # Table for demonstration scam identifiers
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scam_accounts (
                identifier TEXT PRIMARY KEY,
                note TEXT NOT NULL
            )
        """)

        # Add synthetic demo identifiers
        conn.executemany("""
            INSERT OR IGNORE INTO scam_accounts
            (identifier, note)
            VALUES (?, ?)
        """, [
            (
                "scamdemo@upi",
                "Synthetic test record - not a real report"
            ),
            (
                "fraudtest@upi",
                "Synthetic test record - not a real report"
            )
        ])

        # Table for saving payment checks
        conn.execute("""
            CREATE TABLE IF NOT EXISTS payment_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receiver TEXT NOT NULL,
                amount REAL NOT NULL,
                method TEXT NOT NULL,
                result TEXT NOT NULL,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


# Home page and payment checking
@app.route("/", methods=["GET", "POST"])
def home():
    result = None

    if request.method == "POST":

        receiver = request.form.get(
            "receiver", ""
        ).strip().lower()

        method = request.form.get(
            "method", "UPI"
        ).strip()

        amount_text = request.form.get(
            "amount", ""
        ).strip()

        # Validate input
        try:
            amount = float(amount_text)

            if not receiver or amount <= 0:
                raise ValueError

        except ValueError:
            result = {
                "level": "error",
                "title": "Invalid input",
                "message": (
                    "Enter a receiver ID and a valid "
                    "positive amount."
                )
            }

            return render_template(
                "index.html",
                result=result
            )

        # Check receiver against demo database
        with get_db() as conn:
            match = conn.execute(
                """
                SELECT note
                FROM scam_accounts
                WHERE identifier = ?
                """,
                (receiver,)
            ).fetchone()

        # Rule 1: Known synthetic demo identifier
        if match:
            result = {
                "level": "danger",
                "title": "DEMO FLAGGED IDENTIFIER",
                "message": (
                    "This identifier matches a synthetic "
                    "test record in our local database. "
                    "Do not proceed in this demonstration. "
                    "This is not a real scam report."
                )
            }

        # Rule 2: High amount review
        elif amount >= 25000:
            result = {
                "level": "warning",
                "title": "Please verify the payment",
                "message": (
                    "This amount meets our demonstration "
                    "review threshold. Amount alone does "
                    "not prove fraud. Verify the receiver "
                    "independently before paying."
                )
            }

        # Rule 3: No demo match
        else:
            result = {
                "level": "safe",
                "title": "No known demo match found",
                "message": (
                    "No matching identifier was found in "
                    "our sample database. This does not "
                    "mean the receiver is safe."
                )
            }

        # Add payment information to displayed result
        result["receiver"] = receiver
        result["amount"] = f"₹{amount:,.2f}"
        result["method"] = method

        # Save the payment check in SQLite
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO payment_checks
                (receiver, amount, method, result)
                VALUES (?, ?, ?, ?)
                """,
                (
                    receiver,
                    amount,
                    method,
                    result["title"]
                )
            )

    return render_template(
        "index.html",
        result=result
    )


# Analysis dashboard

@app.route("/analysis")
def analysis():
    with get_db() as conn:
        total_records = conn.execute(
            "SELECT COUNT(*) FROM scam_accounts"
        ).fetchone()[0]

        total_checks = conn.execute(
            "SELECT COUNT(*) FROM payment_checks"
        ).fetchone()[0]

        recent_checks = conn.execute("""
            SELECT receiver, amount, method, result, checked_at
            FROM payment_checks
            ORDER BY id DESC
            LIMIT 10
        """).fetchall()

    return render_template(
        "analysis.html",
        total_records=total_records,
        total_checks=total_checks,
        recent_checks=recent_checks
    )



# Demo dataset page
@app.route("/dataset")
def dataset():
    with get_db() as conn:
        records = conn.execute(
            """
            SELECT identifier, note
            FROM scam_accounts
            """
        ).fetchall()

    return render_template(
        "dataset.html",
        records=records
    )


# About page
@app.route("/about")
def about():
    return render_template("about.html")


# Start application
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
