
import os
import sqlite3
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "scamshield-demo-secret-key"

DB_PATH = os.path.join(app.root_path, "scamshield.db")


def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    """Create missing tables and add synthetic demo identifiers."""
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scam_accounts (
            identifier TEXT UNIQUE NOT NULL,
            note TEXT,
            reason TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receiver TEXT NOT NULL,
            amount REAL NOT NULL,
            method TEXT NOT NULL,
            result TEXT NOT NULL,
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scam_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identifier TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT DEFAULT 'Unverified',
            reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO scam_accounts (identifier, note, reason)
        VALUES (?, ?, ?)
    """, (
        "scamdemo@upi",
        "Synthetic demo record",
        "Demo suspicious identifier"
    ))

    cursor.execute("""
        INSERT OR IGNORE INTO scam_accounts (identifier, note, reason)
        VALUES (?, ?, ?)
    """, (
        "fraudtest@upi",
        "Synthetic demo record",
        "Demo fraud-test identifier"
    ))

    connection.commit()
    connection.close()


@app.route("/", methods=["GET", "POST"])
def home():
    result = None

    if request.method == "POST":
        receiver = request.form.get("receiver", "").strip().lower()
        amount_text = request.form.get("amount", "").strip()
        method = request.form.get(
            "payment_method",
            request.form.get("method", "UPI")
        ).strip()

        if not receiver or not amount_text:
            result = {
                "risk": "Invalid Input",
                "message": "Please enter the receiver ID and amount."
            }
        else:
            try:
                amount = float(amount_text)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                result = {
                    "risk": "Invalid Input",
                    "message": "Enter a valid amount greater than zero."
                }
            else:
                connection = get_db()
                cursor = connection.cursor()

                cursor.execute(
                    "SELECT identifier FROM scam_accounts WHERE lower(identifier) = ?",
                    (receiver,)
                )
                known_account = cursor.fetchone()

                if known_account:
                    risk = "High Risk"
                    message = (
                        "This identifier matches a synthetic demo entry. "
                        "This result is not proof of actual fraud."
                    )
                elif amount >= 25000:
                    risk = "Warning"
                    message = (
                        "This is a high-value transaction. Verify the "
                        "receiver independently before paying."
                    )
                else:
                    risk = "Low Risk"
                    message = (
                        "No matching demo identifier was found. "
                        "This does not guarantee the payment is safe."
                    )

                cursor.execute("""
                    INSERT INTO payment_checks
                    (receiver, amount, method, result, checked_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    receiver,
                    amount,
                    method,
                    f"{risk}: {message}",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                connection.commit()
                connection.close()

                result = {
                    "risk": risk,
                    "message": message,
                    "receiver": receiver,
                    "amount": amount,
                    "payment_method": method
                }

    return render_template("index.html", result=result)


@app.route("/analysis")
def analysis():
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, receiver, amount, method, result, checked_at
        FROM payment_checks
        ORDER BY id DESC
        LIMIT 100
    """)
    checks = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM payment_checks")
    total_checks = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM payment_checks
        WHERE lower(result) LIKE '%high risk%'
    """)
    high_risk_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM payment_checks
        WHERE lower(result) LIKE '%warning%'
    """)
    warning_count = cursor.fetchone()[0]

    connection.close()

    return render_template(
        "analysis.html",
        checks=checks,
        total_checks=total_checks,
        high_risk_count=high_risk_count,
        warning_count=warning_count
    )

@app.route("/dataset")
def dataset():
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT identifier, note, reason
        FROM scam_accounts
        ORDER BY identifier
    """)
    accounts = cursor.fetchall()

    cursor.execute("""
        SELECT id, identifier, reason, status, reported_at
        FROM scam_reports
        ORDER BY id DESC
    """)
    reports = cursor.fetchall()

    connection.close()

    return render_template(
        "dataset.html",
        accounts=accounts,
        reports=reports
    )



@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        reason = request.form.get("reason", "").strip()

        if not identifier or not reason:
            flash("Please enter the identifier and reason.")
            return redirect(url_for("report"))

        connection = get_db()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO scam_reports (identifier, reason, status, reported_at)
            VALUES (?, ?, ?, ?)
        """, (
            identifier,
            reason,
            "Unverified",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        connection.commit()
        connection.close()

        flash("Your report has been saved for review.")
        return redirect(url_for("report"))

    return render_template("report.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/health")
def health():
    return {"status": "ok", "application": "ScamShield"}


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
