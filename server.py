import psycopg2
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime, date
import os

app = Flask(__name__)
CORS(app)

# ================= DATABASE =================

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

# ================= USERS =================

users = {
    "admin": {"password": "1234", "role": "admin"},
    "worker": {"password": "1111", "role": "worker"}
}

# ================= HOME =================

@app.route("/")
def home():
    return render_template("index.html")

# ================= LOGIN =================

@app.route("/login", methods=["POST"])
def login():
    data = request.json

    username = data["username"]
    password = data["password"]

    if username in users and users[username]["password"] == password:
        return jsonify({
            "status": "ok",
            "role": users[username]["role"]
        })

    return jsonify({"status": "fail"})

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
    data = request.json
    name = data["name"]

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

# ================= SALARY ALL =================

@app.route("/salary_all")
def salary_all():

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM employees")
    employees = cur.fetchall()

    result = []

    for e in employees:
        name = e[1]
        rate = e[2]
        type_ = e[3]

        cur.execute("""
            SELECT clock_in, clock_out FROM attendance
            WHERE employee_name=%s
        """, (name,))

        records = cur.fetchall()

        hours = 0
        days = 0

        for r in records:
            if r[0] and r[1]:
                t1 = datetime.strptime(r[0], "%Y-%m-%d %H:%M:%S")
                t2 = datetime.strptime(r[1], "%Y-%m-%d %H:%M:%S")

                hours += (t2 - t1).total_seconds() / 3600
                days += 1

        if type_ == "יומי":
            salary = days * rate
        else:
            salary = hours * rate

        result.append({
            "name": name,
            "hours": round(hours, 2),
            "days": days,
            "salary": round(salary, 2)
        })

    conn.close()
    return jsonify(result)

# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():

    today = str(date.today())

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*) FROM attendance
        WHERE work_date=%s AND clock_out=''
    """, (today,))
    active = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM employees")
    total = cur.fetchone()[0]

    conn.close()

    return jsonify({
        "active": active,
        "total_employees": total
    })

# ================= RUN =================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)