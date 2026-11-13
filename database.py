import sqlite3

DB_NAME = "database.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            name TEXT NOT NULL,
            year TEXT NOT NULL,
            password TEXT NOT NULL,
            UNIQUE(student_id, password)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            semester TEXT NOT NULL,
            credit INTEGER NOT NULL,
            grade TEXT NOT NULL,
            point REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_student(student_id, password):
    conn = get_db_connection()
    student = conn.execute('SELECT * FROM students WHERE student_id = ? AND password = ?', (student_id, password)).fetchone()
    conn.close()
    return student

# 기존에 있으면 이름과 학년을 업데이트하고, 없으면 새로 등록하는 함수
def save_or_update_student(student_id, name, year, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    # 먼저 해당 학번+비번의 학생이 있는지 확인하고 정보 갱신 시도
    cursor.execute('UPDATE students SET name = ?, year = ? WHERE student_id = ? AND password = ?', (name, year, student_id, password))
    # 갱신된 행이 없다면(신규 계정인 경우) 새로 삽입
    if cursor.rowcount == 0:
        try:
            cursor.execute('INSERT INTO students (student_id, name, year, password) VALUES (?, ?, ?, ?)',
                           (student_id, name, year, password))
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()

def get_all_courses(student_id, password):
    conn = get_db_connection()
    courses = conn.execute('SELECT * FROM courses WHERE student_id = ? AND password = ? ORDER BY semester DESC, id DESC', (student_id, password)).fetchall()
    conn.close()
    return courses

def get_course_by_id(course_id):
    conn = get_db_connection()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    conn.close()
    return course

def add_course(student_id, password, name, semester, credit, grade, point):
    conn = get_db_connection()
    conn.execute('INSERT INTO courses (student_id, password, name, semester, credit, grade, point) VALUES (?, ?, ?, ?, ?, ?, ?)',
                 (student_id, password, name, semester, credit, grade, point))
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