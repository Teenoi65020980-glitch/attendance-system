from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3, hashlib, io, base64
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "secret_key"

# ------------------ ฟังก์ชันช่วย ------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db():
    conn = sqlite3.connect("attendance.db")
    return conn

# ------------------ หน้าแรก ------------------
@app.route("/")
def index():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM students")
    students = c.fetchall()
    conn.close()
    return render_template("index.html", students=students)

# ------------------ Login ------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = hash_password(request.form["password"])

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = user[1]
            session["role"] = user[3]
            return redirect("/")
        else:
            return "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"
    return render_template("login.html")

# ------------------ Logout ------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ------------------ Register ------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = hash_password(request.form["password"])
        role = request.form["role"]

        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                  (username, password, role))
        conn.commit()
        conn.close()
        return redirect("/login")
    return render_template("register.html")

# ------------------ เพิ่มเด็กใหม่ ------------------
@app.route("/add_student", methods=["POST"])
def add_student():
    if session.get("role") != "teacher":
        return "ไม่มีสิทธิ์เข้าถึง"
    name = request.form["name"]
    birthdate = request.form["birthdate"]
    class_name = request.form["class"]
    parent_name = request.form["parent_name"]

    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO students (name, birthdate, class, parent_name) VALUES (?, ?, ?, ?)",
              (name, birthdate, class_name, parent_name))
    conn.commit()
    conn.close()
    return redirect("/")

# ------------------ เช็คชื่อ ------------------
@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():
    if session.get("role") != "teacher":
        return "ไม่มีสิทธิ์เข้าถึง"
    student_id = request.form["student_id"]
    status = request.form["status"]

    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO attendance (student_id, status) VALUES (?, ?)", (student_id, status))
    conn.commit()
    conn.close()
    return redirect("/")

# ------------------ Dashboard ------------------
@app.route("/dashboard")
def dashboard():
    if session.get("role") != "admin":
        return "ไม่มีสิทธิ์เข้าถึง"

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT status, COUNT(*) FROM attendance GROUP BY status")
    stats = c.fetchall()
    conn.close()

    # สร้างกราฟ
    labels = [s[0] for s in stats]
    values = [s[1] for s in stats]
    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct="%1.1f%%")
    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()

    return render_template("dashboard.html", stats=stats, graph_url=graph_url)

# ------------------ Export Excel ------------------
@app.route("/export_excel")
def export_excel():
    if session.get("role") != "admin":
        return "ไม่มีสิทธิ์เข้าถึง"

    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM attendance", conn)
    conn.close()

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Attendance")
    output.seek(0)

    return send_file(output, download_name="attendance.xlsx", as_attachment=True)

# ------------------ Export PDF ------------------
@app.route("/export_pdf")
def export_pdf():
    if session.get("role") != "admin":
        return "ไม่มีสิทธิ์เข้าถึง"

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM attendance")
    data = c.fetchall()
    conn.close()

    output = io.BytesIO()
    p = canvas.Canvas(output, pagesize=letter)
    p.drawString(100, 750, "รายงานการเช็คชื่อ")
    y = 700
    for row in data:
        p.drawString(100, y, str(row))
        y -= 20
    p.save()
    output.seek(0)

    return send_file(output, download_name="attendance.pdf", as_attachment=True)

# ------------------ User Management ------------------
@app.route("/users")
def users():
    if session.get("role") != "admin":
        return "ไม่มีสิทธิ์เข้าถึง"

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, username, role FROM users")
    users = c.fetchall()
    conn.close()
    return render_template("users.html", users=users)

@app.route("/update_role/<int:user_id>", methods=["POST"])
def update_role(user_id):
    if session.get("role") != "admin":
        return "ไม่มีสิทธิ์เข้าถึง"
    new_role = request.form["role"]

    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET role=? WHERE id=?", (new_role, user_id))
    conn.commit()
    conn.close()
    return redirect("/users")

@app.route("/delete_user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    if session.get("role") != "admin":
        return "ไม่มีสิทธิ์เข้าถึง"

    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return redirect("/users")

# ------------------ Init DB ------------------
@app.route("/init")
def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        birthdate TEXT,
        class TEXT,
        parent_name TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        status TEXT,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )
    """)

    conn.commit()
    conn.close()
    return "Database initialized!"

# ------------------ Run ------------------
if __name__ == "__main__":
    app.run(debug=True)
