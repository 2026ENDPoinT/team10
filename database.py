#데이터베이스 연결 및 관리
import sqlite3

DB_NAME = "database.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            semester TEXT NOT NULL,
            credit INTEGER NOT NULL,
            grade TEXT NOT NULL,
            point REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_all_courses():
    conn = get_db_connection()
    courses = conn.execute('SELECT * FROM courses ORDER BY semester DESC, id DESC').fetchall()
    conn.close()
    return courses

def get_course_by_id(course_id):
    conn = get_db_connection()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    conn.close()
    return course

def add_course(name, semester, credit, grade, point):
    conn = get_db_connection()
    conn.execute('INSERT INTO courses (name, semester, credit, grade, point) VALUES (?, ?, ?, ?, ?)',
                 (name, semester, credit, grade, point))
    conn.commit()
    conn.close()

def update_course(course_id, name, semester, credit, grade, point):
    conn = get_db_connection()
    conn.execute('''
        UPDATE courses SET name = ?, semester = ?, credit = ?, grade = ?, point = ?
        WHERE id = ?
    ''', (name, semester, credit, grade, point, course_id))
    conn.commit()
    conn.close()

def delete_course(course_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM courses WHERE id = ?', (course_id,))
    conn.commit()
    conn.close()