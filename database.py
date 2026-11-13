import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / 'data'
DATA_DIR.mkdir(exist_ok=True)
DB_NAME = str(DATA_DIR / 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # 테이블에 student_id(학번) 컬럼 추가
    conn.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            name TEXT NOT NULL,
            semester TEXT NOT NULL,
            credit INTEGER NOT NULL,
            grade TEXT NOT NULL,
            point REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# 특정 학번의 과목들만 조회
def get_all_courses(student_id):
    conn = get_db_connection()
    courses = conn.execute('SELECT * FROM courses WHERE student_id = ? ORDER BY semester DESC, id DESC', (student_id,)).fetchall()
    conn.close()
    return courses

def get_course_by_id(course_id):
    conn = get_db_connection()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    conn.close()
    return course

# 데이터 저장 시 student_id 함께 저장
def add_course(student_id, name, semester, credit, grade, point):
    conn = get_db_connection()
    conn.execute('INSERT INTO courses (student_id, name, semester, credit, grade, point) VALUES (?, ?, ?, ?, ?, ?)',
                 (student_id, name, semester, credit, grade, point))
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
