import sqlite3

def update_student_password(student_id, old_password, new_password):
    conn = get_db_connection()
    cursor = conn.cursor()
    # 학생 정보 테이블 비밀번호 수정
    cursor.execute('''
        UPDATE students 
        SET password = ? 
        WHERE student_id = ? AND password = ?
    ''', (new_password, student_id, old_password))
    
    # 해당 학생이 등록한 과목들의 비밀번호 연결 정보도 함께 수정
    cursor.execute('''
        UPDATE courses 
        SET password = ? 
        WHERE student_id = ? AND password = ?
    ''', (new_password, student_id, old_password))
    
    conn.commit()
    conn.close()
    
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # 학생 및 과목 정보를 관리하는 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT,
            password TEXT,
            name TEXT,
            year TEXT,
            PRIMARY KEY (student_id, password)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            password TEXT,
            name TEXT NOT NULL,
            semester TEXT NOT NULL,
            credit INTEGER NOT NULL,
            grade TEXT NOT NULL,
            point REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_or_update_student(student_id, name, year, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO students (student_id, password, name, year)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(student_id, password) 
        DO UPDATE SET name=excluded.name, year=excluded.year
    ''', (student_id, password, name, year))
    conn.commit()
    conn.close()

def get_all_courses(student_id, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM courses 
        WHERE student_id = ? AND password = ?
    ''', (student_id, password))
    courses = cursor.fetchall()
    conn.close()
    return courses

def get_course_by_id(course_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM courses WHERE id = ?', (course_id,))
    course = cursor.fetchone()
    conn.close()
    return course

def add_course(student_id, password, name, semester, credit, grade, point):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO courses (student_id, password, name, semester, credit, grade, point)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (student_id, password, name, semester, credit, grade, point))
    conn.commit()
    conn.close()

def update_course(course_id, name, semester, credit, grade, point):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE courses
        SET name = ?, semester = ?, credit = ?, grade = ?, point = ?
        WHERE id = ?
    ''', (name, semester, credit, grade, point, course_id))
    conn.commit()
    conn.close()

def delete_course(course_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM courses WHERE id = ?', (course_id,))
    conn.commit()
    conn.close()