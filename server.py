import os
import psycopg2
from flask import Flask, request, jsonify, render_template, session, send_file
from datetime import datetime, date, timedelta
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)
app.secret_key = "final-secure-key"

DATABASE_URL = os.environ.get("DATABASE_URL")

# ================= DB =================

def db():
    if not DATABASE_URL:
        raise Exception("DATABASE_URL missing")
    return psycopg2.connect(DATABASE_URL)

# ================= INIT SAFE =================

def init_db():
    c = db()
    cur = c.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE,
        salary FLOAT,
        type TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id SERIAL PRIMARY KEY,
        name TEXT,
        day TEXT,
        in_time TEXT,
        out_time TEXT
    )
    """)

    c.commit()
    c.close()

init_db()

# ================= USERS =================

USERS = {
    "בנצי": {"pass": "259165", "role": "admin"},
    "כללי": {"pass": "112233", "role": "worker"}
}

# ================= UI =================

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/admin")
def admin():
    return render_template("admin.html")

# ================= LOGIN =================

@app.route("/login", methods=["POST"])
def login():
    d = request.json
    u = d.get("user")
    p = d.get("pass")

    if u in USERS and USERS[u]["pass"] == p:
        session["user"] = u
        session["role"] = USERS[u]["role"]
        return jsonify({"ok": True, "role": session["role"]})

    return jsonify({"ok": False})

# ================= EMPLOYEES =================

@app.route("/employees")
def employees():
    c = db()
    cur = c.cursor()

    cur.execute("SELECT id, name, salary, type FROM employees")
    rows = cur.fetchall()

    c.close()

    return jsonify([
        {"id": r[0], "name": r[1], "salary": r[2], "type": r[3]}
        for r in rows
    ])

# ================= ADD =================

@app.route("/add", methods=["POST"])
def add():
    if session.get("role") != "admin":
        return jsonify({"error": "no permission"}), 403

    d = request.json

    c = db()
    cur = c.cursor()

    cur.execute("""
    INSERT INTO employees(name,salary,type)
    VALUES(%s,%s,%s)
    ON CONFLICT (name) DO UPDATE SET salary=EXCLUDED.salary, type=EXCLUDED.type
    """, (d["name"], float(d["salary"]), d["type"]))

    c.commit()
    c.close()

    return jsonify({"ok": True})

# ================= DELETE =================

@app.route("/delete", methods=["POST"])
def delete():
    if session.get("role") != "admin":
        return jsonify({"error": "no permission"}), 403

    name = request.json.get("name","").strip()

    c = db()
    cur = c.cursor()

    cur.execute("DELETE FROM employees WHERE LOWER(name)=LOWER(%s)", (name,))
    cur.execute("DELETE FROM attendance WHERE LOWER(name)=LOWER(%s)", (name,))

    c.commit()
    c.close()

    return jsonify({"ok": True})

# ================= CLOCK =================

@app.route("/in", methods=["POST"])
def clock_in():
    name = request.json["name"]

    c = db()
    cur = c.cursor()

    cur.execute("""
    INSERT INTO attendance(name,day,in_time,out_time)
    VALUES(%s,%s,%s,'')
    """, (name, str(date.today()), datetime.now().isoformat()))

    c.commit()
    c.close()

    return jsonify({"ok": True})

@app.route("/out", methods=["POST"])
def clock_out():
    name = request.json["name"]

    c = db()
    cur = c.cursor()

    cur.execute("""
    UPDATE attendance
    SET out_time=%s
    WHERE name=%s AND out_time=''
    """, (datetime.now().isoformat(), name))

    c.commit()
    c.close()

    return jsonify({"ok": True})

# ================= SALARY SAFE =================

def calc_salary():
    week = (date.today() - timedelta(days=7)).isoformat()

    c = db()
    cur = c.cursor()

    cur.execute("SELECT name, salary, type FROM employees")
    emps = cur.fetchall()

    result = []
    total = 0

    for name, rate, typ in emps:

        cur.execute("""
        SELECT in_time, out_time FROM attendance
        WHERE name=%s AND day>= %s
        """, (name, week))

        rows = cur.fetchall()

        hours = 0
        days = 0

        for r in rows:
            if r and r[0] and r[1]:
                try:
                    t1 = datetime.fromisoformat(r[0])
                    t2 = datetime.fromisoformat(r[1])
                    hours += (t2 - t1).seconds / 3600
                    days += 1
                except:
                    continue

        salary = days*rate if typ == "יומי" else hours*rate
        total += salary

        result.append({
            "name": name,
            "days": days,
            "hours": round(hours,2),
            "salary": round(salary,2)
        })

    c.close()

    return {"data": result, "total": total}

@app.route("/salary")
def salary():
    return jsonify(calc_salary())

# ================= PDF SAFE =================

@app.route("/pdf")
def pdf():
    data = calc_salary()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)

    y = 800
    p.drawString(100, y, "Salary Report")
    y -= 30

    for e in data["data"]:
        p.drawString(100, y,
            f"{e['name']} | days:{e['days']} | hours:{e['hours']} | ₪{e['salary']}"
        )
        y -= 20

    y -= 20
    p.drawString(100, y, f"TOTAL: ₪{data['total']}")

    p.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="report.pdf")

# ================= RUN =================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)