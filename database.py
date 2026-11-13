import json
import sqlite3
import time
from pathlib import Path

WRONG_ANSWER_LIMIT = 10   # 계정당 저장되는 틀린 문제 수
CONVERSATION_LIMIT = 3    # 계정당 저장되는 AI 대화 수


def update_student_password(student_id, old_password, new_password):
    """비밀번호 변경. 결과: 'ok' | 'same' | 'taken' | 'not_found'

    students 테이블의 기본키가 (student_id, password) 이므로, 같은 학번에서 이미 다른 성적 셋이
    사용 중인 비밀번호로 바꾸면 UNIQUE 제약 오류가 난다. 미리 확인하고 오류 대신 결과 코드로 알려준다.
    """
    if new_password == old_password:
        return 'same'

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        taken = cursor.execute(
            'SELECT 1 FROM students WHERE student_id = ? AND password = ?',
            (student_id, new_password)
        ).fetchone()
        if taken:
            return 'taken'

        # 학생 정보 테이블 비밀번호 수정
        cursor.execute('''
            UPDATE students
            SET password = ?
            WHERE student_id = ? AND password = ?
        ''', (new_password, student_id, old_password))
        if cursor.rowcount == 0:
            conn.rollback()
            return 'not_found'

        # 해당 학생이 등록한 과목·오답 노트·AI 대화의 비밀번호 연결 정보도 함께 수정
        for table in ('courses', 'wrong_answers', 'chat_conversations'):
            cursor.execute(f'''
                UPDATE {table}
                SET password = ?
                WHERE student_id = ? AND password = ?
            ''', (new_password, student_id, old_password))

        conn.commit()
        return 'ok'
    except sqlite3.IntegrityError:
        # 확인 직후 다른 요청이 같은 비밀번호를 만든 경우 등: 변경 내용 전체 취소
        conn.rollback()
        return 'taken'
    finally:
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
    # 퀴즈 오답 노트 (학번 + 비밀번호가 일치해야 조회 가능, 계정당 최대 WRONG_ANSWER_LIMIT 개)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wrong_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            password TEXT NOT NULL,
            subject TEXT NOT NULL,
            question TEXT NOT NULL,
            choices TEXT NOT NULL,
            answer INTEGER NOT NULL,
            selected_answer INTEGER,
            explanation TEXT NOT NULL,
            saved_at REAL NOT NULL
        )
    ''')
    # AI 대화 기록 (학번 + 비밀번호가 일치해야 조회 가능, 계정당 최대 CONVERSATION_LIMIT 개)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            password TEXT NOT NULL,
            title TEXT NOT NULL,
            messages TEXT NOT NULL,
            updated_at REAL NOT NULL
        )
    ''')
    # CREATE TABLE IF NOT EXISTS does not upgrade an existing table.
    columns = {row['name'] for row in conn.execute('PRAGMA table_info(courses)')}
    if 'password' not in columns:
        # Legacy rows have no known credential. Preserve them without assigning
        # them to an arbitrary account; NULL will not match a login password.
        conn.execute('ALTER TABLE courses ADD COLUMN password TEXT')
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

def get_student(student_id, password):
    # students 테이블에는 별도 id 컬럼이 없으므로 SQLite rowid를 id로 사용
    conn = get_db_connection()
    student = conn.execute(
        'SELECT rowid AS id, * FROM students WHERE student_id = ? AND password = ?',
        (student_id, password)
    ).fetchone()
    conn.close()
    return student

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


# ---------------------------------------------------------------------
# 퀴즈 오답 노트 (학번 + 비밀번호 단위)
# ---------------------------------------------------------------------
def _wrong_answer_view(row):
    return {
        'id': row['id'], 'subject': row['subject'], 'question': row['question'],
        'choices': json.loads(row['choices']), 'answer': row['answer'],
        'selected_answer': row['selected_answer'], 'explanation': row['explanation'],
        'saved_at': row['saved_at'],
    }


def save_wrong_answers(student_id, password, subject, questions):
    """틀린 문제 저장. 같은 문제는 새로 덮어쓰고, 최근 WRONG_ANSWER_LIMIT 개만 남긴다."""
    if not questions:
        return
    conn = get_db_connection()
    try:
        with conn:
            now = time.time()
            for offset, q in enumerate(questions):
                conn.execute(
                    'DELETE FROM wrong_answers WHERE student_id = ? AND password = ? AND question = ?',
                    (student_id, password, q['question']))
                conn.execute('''
                    INSERT INTO wrong_answers
                        (student_id, password, subject, question, choices, answer, selected_answer, explanation, saved_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (student_id, password, subject, q['question'], json.dumps(q['choices'], ensure_ascii=False),
                      q['answer'], q.get('selected_answer'), q['explanation'], now + offset * 1e-6))
            conn.execute('''
                DELETE FROM wrong_answers
                WHERE student_id = ? AND password = ? AND id NOT IN (
                    SELECT id FROM wrong_answers WHERE student_id = ? AND password = ?
                    ORDER BY saved_at DESC, id DESC LIMIT ?)
            ''', (student_id, password, student_id, password, WRONG_ANSWER_LIMIT))
    finally:
        conn.close()


def get_wrong_answers(student_id, password):
    conn = get_db_connection()
    try:
        rows = conn.execute('''
            SELECT * FROM wrong_answers WHERE student_id = ? AND password = ?
            ORDER BY saved_at DESC, id DESC LIMIT ?
        ''', (student_id, password, WRONG_ANSWER_LIMIT)).fetchall()
    finally:
        conn.close()
    return [_wrong_answer_view(row) for row in rows]


def delete_wrong_answer(item_id, student_id, password):
    conn = get_db_connection()
    try:
        with conn:
            cursor = conn.execute('DELETE FROM wrong_answers WHERE id = ? AND student_id = ? AND password = ?',
                                  (item_id, student_id, password))
        return cursor.rowcount > 0
    finally:
        conn.close()


# ---------------------------------------------------------------------
# AI 대화 기록 (학번 + 비밀번호 단위)
# ---------------------------------------------------------------------
def _conversation_view(row):
    return {'id': row['id'], 'title': row['title'], 'messages': json.loads(row['messages']),
            'updated_at': row['updated_at']}


def save_conversation(student_id, password, conversation_id, title, messages):
    """대화 저장(내 대화면 갱신, 아니면 새로 저장). 최근 CONVERSATION_LIMIT 개만 남기고 대화 id 를 돌려준다."""
    conn = get_db_connection()
    try:
        with conn:
            now = time.time()
            payload = json.dumps(messages, ensure_ascii=False)
            updated = 0
            if conversation_id is not None:
                updated = conn.execute('''
                    UPDATE chat_conversations SET title = ?, messages = ?, updated_at = ?
                    WHERE id = ? AND student_id = ? AND password = ?
                ''', (title, payload, now, conversation_id, student_id, password)).rowcount
            if not updated:
                conversation_id = conn.execute('''
                    INSERT INTO chat_conversations (student_id, password, title, messages, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (student_id, password, title, payload, now)).lastrowid
            conn.execute('''
                DELETE FROM chat_conversations
                WHERE student_id = ? AND password = ? AND id NOT IN (
                    SELECT id FROM chat_conversations WHERE student_id = ? AND password = ?
                    ORDER BY updated_at DESC, id DESC LIMIT ?)
            ''', (student_id, password, student_id, password, CONVERSATION_LIMIT))
        return conversation_id
    finally:
        conn.close()


def get_conversations(student_id, password):
    conn = get_db_connection()
    try:
        rows = conn.execute('''
            SELECT * FROM chat_conversations WHERE student_id = ? AND password = ?
            ORDER BY updated_at DESC, id DESC LIMIT ?
        ''', (student_id, password, CONVERSATION_LIMIT)).fetchall()
    finally:
        conn.close()
    return [_conversation_view(row) for row in rows]


def delete_conversation(conversation_id, student_id, password):
    conn = get_db_connection()
    try:
        with conn:
            cursor = conn.execute('DELETE FROM chat_conversations WHERE id = ? AND student_id = ? AND password = ?',
                                  (conversation_id, student_id, password))
        return cursor.rowcount > 0
    finally:
        conn.close()
