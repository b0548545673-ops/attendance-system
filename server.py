import os
import psycopg2
from flask import Flask, request, jsonify, render_template, session, redirect, send_file
from datetime import datetime, date, timedelta
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)
app.secret_key = "secure-key"

DATABASE_URL = os.environ.get("DATABASE_URL")

def db():
    return psycopg2.connect(DATABASE_URL)

# ================= INIT =================

def init_db():
    c = db()
    cur = c.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS employees(
        id SERIAL PRIMARY KEY,
        name TEXT,
        salary FLOAT,
        type TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS attendance(
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
    "admin": {"pass": "259165", "role": "admin"},
    "worker": {"pass": "112233", "role": "worker"}
}

# ================= LOGIN =================

@app.route("/")
def login_page():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    d = request.json
    u = d["user"]
    p = d["pass"]

    if u in USERS and USERS[u]["pass"] == p:
        session["user"] = u
        session["role"] = USERS[u]["role"]
        return jsonify({"ok": True, "role": session["role"]})

    return jsonify({"ok": False})

# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    return render_template("dashboard.html", user=session["user"], role=session["role"])

# ================= ADMIN =================

@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return "אין הרשאה"

    return render_template("admin.html")

# ================= EMPLOYEES =================

@app.route("/employees")
def employees():
    c = db()
    cur = c.cursor()

    cur.execute("SELECT * FROM employees")
    data = cur.fetchall()

    c.close()
    return jsonify(data)

@app.route("/add", methods=["POST"])
def add():
    if session.get("role") != "admin":
        return "no"

    d = request.json
    c = db()
    cur = c.cursor()

    cur.execute("""
    INSERT INTO employees(name,salary,type)
    VALUES(%s,%s,%s)
    """, (d["name"], d["salary"], d["type"]))

    c.commit()
    c.close()

    return jsonify({"ok": True})

@app.route("/delete", methods=["POST"])
def delete():
    if session.get("role") != "admin":
        return "no"

    name = request.json["name"]

    c = db()
    cur = c.cursor()

    cur.execute("DELETE FROM employees WHERE name=%s", (name,))
    cur.execute("DELETE FROM attendance WHERE name=%s", (name,))

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

# ================= SALARY =================

@app.route("/salary")
def salary():

    week = (date.today() - timedelta(days=7)).isoformat()

    c = db()
    cur = c.cursor()

    cur.execute("SELECT * FROM employees")
    emps = cur.fetchall()

    result = []
    total = 0

    for e in emps:
        name, rate, typ = e[1], e[2], e[3]

        cur.execute("""
        SELECT in_time,out_time FROM attendance
        WHERE name=%s AND day>= %s
        """, (name, week))

        rows = cur.fetchall()

        hours = 0
        days = 0

        for r in rows:
            if r[0] and r[1]:
                t1 = datetime.fromisoformat(r[0])
                t2 = datetime.fromisoformat(r[1])
                hours += (t2 - t1).seconds / 3600
                days += 1

        salary = days*rate if typ=="יומי" else hours*rate
        total += salary

        result.append({
            "name": name,
            "days": days,
            "hours": round(hours,2),
            "salary": round(salary,2)
        })

    c.close()

    return jsonify({"data": result, "total": total})

# ================= PDF =================

@app.route("/pdf")
def pdf():

    data = salary().json

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)

    y = 800
    p.drawString(100,y,"דוח שכר שבועי")
    y -= 30

    for e in data["data"]:
        p.drawString(100,y,f"{e['name']} | ימים:{e['days']} | ₪{e['salary']}")
        y -= 20

    y -= 20
    p.drawString(100,y,f"סהכ: {data['total']} ₪")

    p.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="salary.pdf")

# ================= RUN =================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)