import sqlite3, hashlib

def init_db():
    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    # ตารางผู้ใช้
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    """)

    # ตารางนักเรียน
    c.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        birthdate TEXT,
        class TEXT,
        parent_name TEXT
    )
    """)

    # ตารางการเช็คชื่อ
    c.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        date TEXT DEFAULT (DATE('now')),
        FOREIGN KEY (student_id) REFERENCES students(id)
    )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

def seed_data():
    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    # เพิ่ม Admin เริ่มต้น
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", 
              ("admin", hashlib.sha256("1234".encode()).hexdigest(), "admin"))

    # เพิ่ม Teacher เริ่มต้น
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", 
              ("teacher1", hashlib.sha256("1234".encode()).hexdigest(), "teacher"))

    # เพิ่มนักเรียนตัวอย่าง
    students = [
        ("สมชาย ใจดี", "2015-05-10", "ป.1", "นายใจดี"),
        ("สมหญิง ขยัน", "2014-08-22", "ป.2", "นางขยัน"),
        ("อนันต์ ตั้งใจ", "2016-01-15", "อนุบาล", "นายตั้งใจ")
    ]
    for s in students:
        c.execute("INSERT OR IGNORE INTO students (name, birthdate, class, parent_name) VALUES (?, ?, ?, ?)", s)

    conn.commit()
    conn.close()
    print("✅ Seed data (users + students) inserted!")

if __name__ == "__main__":
    init_db()
    seed_data()
