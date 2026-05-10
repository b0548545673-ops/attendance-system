import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, date

app = Flask(__name__)
CORS(app)

# ================= DATABASE =================

import os

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

# ================= INIT DB =================

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id SERIAL PRIMARY KEY,
        name TEXT,
        salary FLOAT,
        salary_type TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id SERIAL PRIMARY KEY,
        employee_name TEXT,
        work_date TEXT,
        clock_in TEXT,
        clock_out TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ================= HOME =================

@app.route("/")
def home():
    return "השרת עובד ✔ מערכת נוכחות פעילה בענן"

# ================= EMPLOYEES =================

@app.route("/employees")
def employees():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM employees")
    rows = cur.fetchall()

    conn.close()
    return jsonify(rows)

# ================= ADD EMPLOYEE =================

@app.route("/add_employee", methods=["POST"])
def add_employee():

    data = request.json

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO employees (name, salary, salary_type)
        VALUES (%s, %s, %s)
    """, (data["name"], data["salary"], data["salary_type"]))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

# ================= CLOCK IN =================

@app.route("/clock_in", methods=["POST"])
def clock_in():

    name = data = request.json["name"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO attendance (employee_name, work_date, clock_in, clock_out)
        VALUES (%s, %s, %s, %s)
    """, (name, str(date.today()), now, ""))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

# ================= CLOCK OUT =================

@app.route("/clock_out", methods=["POST"])
def clock_out():

    name = request.json["name"]

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE attendance
        SET clock_out=%s
        WHERE employee_name=%s AND clock_out=''
    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), name))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

# ================= RUN =================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)