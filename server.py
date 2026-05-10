from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime, date

app = Flask(__name__)
CORS(app)

# ================= DB =================

conn = sqlite3.connect("cloud.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    salary REAL,
    salary_type TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_name TEXT,
    work_date TEXT,
    clock_in TEXT,
    clock_out TEXT
)
""")

conn.commit()

# ================= ROUTES =================

@app.route("/")
def home():
    return "השרת עובד ✔ מערכת נוכחות פעילה"


@app.route("/add_employee", methods=["POST"])
def add_employee():

    data = request.json

    cursor.execute("""
        INSERT INTO employees (name, salary, salary_type)
        VALUES (?, ?, ?)
    """, (data["name"], data["salary"], data["salary_type"]))

    conn.commit()
    return jsonify({"status": "ok"})


@app.route("/employees")
def employees():

    rows = cursor.execute("SELECT * FROM employees").fetchall()
    return jsonify(rows)


@app.route("/clock_in", methods=["POST"])
def clock_in():

    data = request.json
    name = data["name"]
    today = str(date.today())

    exists = cursor.execute("""
        SELECT * FROM attendance
        WHERE employee_name=? AND work_date=?
    """, (name, today)).fetchone()

    if exists:
        return jsonify({"status": "already"})

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO attendance (employee_name, work_date, clock_in, clock_out)
        VALUES (?, ?, ?, ?)
    """, (name, today, now, ""))

    conn.commit()
    return jsonify({"status": "ok"})


@app.route("/clock_out", methods=["POST"])
def clock_out():

    data = request.json
    name = data["name"]
    today = str(date.today())

    row = cursor.execute("""
        SELECT id FROM attendance
        WHERE employee_name=? AND work_date=? AND clock_out=''
    """, (name, today)).fetchone()

    if not row:
        return jsonify({"status": "no_entry"})

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE attendance
        SET clock_out=?
        WHERE id=?
    """, (now, row[0]))

    conn.commit()
    return jsonify({"status": "ok"})


# ================= RUN =================

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)