"""모든 데이터 저장을 담당하는 모듈.

- 환경변수 DATABASE_URL 이 있으면 PostgreSQL(배포 환경, Render)에 연결한다.
- 없으면 data/database.db SQLite 파일을 사용한다(로컬 개발·테스트용).

SQL 은 두 DB 에서 같이 동작하도록 '?' 자리표시자로 작성하고, PostgreSQL 에서는 '%s' 로 바꿔 실행한다.
비밀번호는 해시로만 저장하며, 다른 테이블은 학생을 students.id(user_id)로 참조한다.
"""
import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path

WRONG_ANSWER_LIMIT = 10   # 계정당 저장되는 틀린 문제 수
CONVERSATION_LIMIT = 3    # 계정당 저장되는 AI 대화 수
QUIZ_LIFETIME_SECONDS = 86400

# 로컬 SQLite 파일 위치 (테스트에서 임시 파일로 바꿔 쓸 수 있다)
DB_NAME = str(Path(__file__).resolve().parent / 'data' / 'database.db')


def database_url():
    return os.getenv('DATABASE_URL', '').strip()


def using_postgres():
    return bool(database_url())


def _dict_row(cursor, row):
    return {column[0]: value for column, value in zip(cursor.description, row)}


class Connection:
    """sqlite3 / psycopg 연결을 같은 방식으로 쓰기 위한 얇은 래퍼.

    with conn: 블록은 트랜잭션(성공 시 commit, 오류 시 rollback)이며 연결을 닫지 않는다.
    """

    def __init__(self, raw, postgres):
        self.raw = raw
        self.postgres = postgres

    def execute(self, sql, params=()):
        if self.postgres:
            sql = sql.replace('?', '%s')
        cursor = self.raw.cursor()
        cursor.execute(sql, params)
        return cursor

    def begin_write(self):
        """읽은 뒤 고쳐 쓰는 작업 전에 호출. SQLite 는 쓰기 잠금을 먼저 잡는다.
        PostgreSQL 에서는 SELECT 뒤에 for_update 를 붙여 해당 행을 잠근다."""
        if not self.postgres:
            self.raw.execute('BEGIN IMMEDIATE')

    @property
    def for_update(self):
        return ' FOR UPDATE' if self.postgres else ''

    def commit(self):
        self.raw.commit()

    def rollback(self):
        self.raw.rollback()

    def close(self):
        self.raw.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.raw.commit()
        else:
            self.raw.rollback()
        return False


def get_db_connection():
    url = database_url()
    if url:
        import psycopg  # 배포 환경에서만 필요하므로 여기서 불러온다
        from psycopg.rows import dict_row
        return Connection(psycopg.connect(url, row_factory=dict_row), postgres=True)
    Path(DB_NAME).parent.mkdir(parents=True, exist_ok=True)
    raw = sqlite3.connect(DB_NAME, timeout=10)
    raw.row_factory = _dict_row
    raw.execute('PRAGMA foreign_keys = ON')
    return Connection(raw, postgres=False)


# ---------------------------------------------------------------------
# 스키마
# ---------------------------------------------------------------------
SCHEMA = [
    '''CREATE TABLE IF NOT EXISTS students (
        id {pk},
        student_id TEXT NOT NULL,
        password_key TEXT NOT NULL,
        name TEXT NOT NULL,
        year TEXT NOT NULL,
        UNIQUE (student_id, password_key)
    )''',
    '''CREATE TABLE IF NOT EXISTS courses (
        id {pk},
        user_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        semester TEXT NOT NULL,
        credit INTEGER NOT NULL,
        grade TEXT NOT NULL,
        point DOUBLE PRECISION NOT NULL
    )''',
    # 퀴즈 오답 노트 (계정당 최대 WRONG_ANSWER_LIMIT 개)
    '''CREATE TABLE IF NOT EXISTS wrong_answers (
        id {pk},
        user_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
        subject TEXT NOT NULL,
        question TEXT NOT NULL,
        choices TEXT NOT NULL,
        answer INTEGER NOT NULL,
        selected_answer INTEGER,
        explanation TEXT NOT NULL,
        saved_at DOUBLE PRECISION NOT NULL
    )''',
    # AI 대화 기록 (계정당 최대 CONVERSATION_LIMIT 개)
    '''CREATE TABLE IF NOT EXISTS chat_conversations (
        id {pk},
        user_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        messages TEXT NOT NULL,
        updated_at DOUBLE PRECISION NOT NULL
    )''',
    # 과제 (owner = students.id)
    '''CREATE TABLE IF NOT EXISTS assignments (
        id {pk},
        owner INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
        subject TEXT NOT NULL,
        title TEXT NOT NULL,
        deadline TEXT NOT NULL,
        priority INTEGER NOT NULL CHECK (priority BETWEEN 1 AND 3),
        completed INTEGER NOT NULL DEFAULT 0 CHECK (completed IN (0, 1)),
        estimated_minutes INTEGER NOT NULL DEFAULT 0,
        checklist TEXT NOT NULL DEFAULT '[]'
    )''',
    # AI 생성 퀴즈의 정답·해설 (브라우저 세션 단위, 24시간 후 삭제)
    '''CREATE TABLE IF NOT EXISTS quizzes (
        id TEXT PRIMARY KEY,
        owner TEXT NOT NULL,
        created DOUBLE PRECISION NOT NULL,
        subject TEXT NOT NULL,
        questions TEXT NOT NULL
    )''',
    'CREATE INDEX IF NOT EXISTS courses_user ON courses (user_id)',
    'CREATE INDEX IF NOT EXISTS wrong_answers_user ON wrong_answers (user_id)',
    'CREATE INDEX IF NOT EXISTS chat_conversations_user ON chat_conversations (user_id)',
    'CREATE INDEX IF NOT EXISTS assignments_owner ON assignments (owner)',
    'CREATE INDEX IF NOT EXISTS quizzes_owner ON quizzes (owner, created)',
]

# 학생을 참조하는 테이블. 계정 구조가 바뀌면 함께 legacy_* 로 보관한다.
ACCOUNT_TABLES = ('students', 'courses', 'wrong_answers', 'chat_conversations', 'assignments')
ACCOUNT_INDEXES = ('courses_user', 'wrong_answers_user', 'chat_conversations_user', 'assignments_owner')


def _table_columns(conn, table):
    if conn.postgres:
        rows = conn.execute('SELECT column_name AS name FROM information_schema.columns '
                            'WHERE table_schema = current_schema() AND table_name = ?', (table,)).fetchall()
    else:
        rows = conn.execute(f'PRAGMA table_info({table})').fetchall()
    return {row['name'] for row in rows}


def _retire_old_account_tables(conn):
    """예전 계정 구조(평문 비밀번호, 또는 학번당 계정 하나)의 테이블은 지우지 않고 legacy_* 로 이름만 바꾼다."""
    columns = _table_columns(conn, 'students')
    if not columns or 'password_key' in columns:
        return
    suffix = str(int(time.time()))
    for index in ACCOUNT_INDEXES:
        conn.execute(f'DROP INDEX IF EXISTS {index}')
    for table in ACCOUNT_TABLES:
        if _table_columns(conn, table):
            conn.execute(f'ALTER TABLE {table} RENAME TO legacy_{table}_{suffix}')
    print(f'[database] 예전 계정 구조의 테이블을 legacy_*_{suffix} 로 보관했습니다. 새 구조로 다시 만듭니다.')


def init_db():
    _password_pepper()  # 배포 환경에서 PASSWORD_PEPPER 가 빠졌으면 시작할 때 바로 알린다
    conn = get_db_connection()
    try:
        with conn:
            if conn.postgres:
                # 여러 서버 프로세스가 동시에 테이블을 만들지 않도록 잠금
                conn.execute('SELECT pg_advisory_xact_lock(1010)')
                pk = 'SERIAL PRIMARY KEY'
            else:
                pk = 'INTEGER PRIMARY KEY AUTOINCREMENT'
            _retire_old_account_tables(conn)
            for statement in SCHEMA:
                conn.execute(statement.format(pk=pk))
    finally:
        conn.close()

# ---------------------------------------------------------------------
# 계정: (학번, 비밀번호) 조합마다 별도의 계정
# ---------------------------------------------------------------------
def _password_pepper():
    pepper = os.getenv('PASSWORD_PEPPER', '').strip()
    if pepper:
        return pepper
    if using_postgres():
        raise RuntimeError('PASSWORD_PEPPER 환경변수가 필요합니다. Render의 Environment에 긴 임의 문자열로 추가하세요.')
    return 'local-development-only'  # 로컬 SQLite 개발용


def _password_key(student_id, password):
    """같은 학번·비밀번호면 항상 같은 값이 나오는 키. 평문 비밀번호 대신 이 값을 저장하고 계정을 찾는다.
    서버 비밀값(PASSWORD_PEPPER)이 없으면 DB만으로는 비밀번호를 알아낼 수 없다."""
    salt = f'{_password_pepper()}:{student_id}'.encode()
    return hashlib.scrypt(password.encode(), salt=salt, n=2 ** 14, r=8, p=1, dklen=32).hex()


def _is_unique_violation(exc):
    return isinstance(exc, sqlite3.IntegrityError) or getattr(exc, 'sqlstate', None) == '23505'


def _public_student(row):
    return {'id': row['id'], 'student_id': row['student_id'], 'name': row['name'], 'year': row['year']}


def get_student(student_id, password):
    """학번 + 비밀번호 조합의 계정. 없으면 None."""
    conn = get_db_connection()
    try:
        row = conn.execute('SELECT * FROM students WHERE student_id = ? AND password_key = ?',
                           (student_id, _password_key(student_id, password))).fetchone()
    finally:
        conn.close()
    return _public_student(row) if row else None


def create_student(student_id, password, name, year):
    """새 계정을 만든다. 같은 (학번, 비밀번호) 계정이 이미 있으면 None."""
    conn = get_db_connection()
    try:
        with conn:
            row = conn.execute('''
                INSERT INTO students (student_id, password_key, name, year) VALUES (?, ?, ?, ?)
                ON CONFLICT (student_id, password_key) DO NOTHING
                RETURNING id
            ''', (student_id, _password_key(student_id, password), name, year)).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return {'id': row['id'], 'student_id': student_id, 'name': name, 'year': year}


def update_student_profile(user_id, name, year):
    conn = get_db_connection()
    try:
        with conn:
            conn.execute('UPDATE students SET name = ?, year = ? WHERE id = ?', (name, year, user_id))
    finally:
        conn.close()


def update_student_password(user_id, student_id, new_password):
    """비밀번호 변경. 결과: 'ok' | 'same' | 'taken' | 'not_found'

    같은 학번의 다른 계정이 이미 쓰는 비밀번호로는 바꿀 수 없다('taken').
    성적·오답·대화·과제는 user_id 로 연결되어 있으므로 그대로 유지된다.
    """
    new_key = _password_key(student_id, new_password)
    conn = get_db_connection()
    try:
        with conn:
            row = conn.execute('SELECT password_key FROM students WHERE id = ? AND student_id = ?',
                               (user_id, student_id)).fetchone()
            if row is None:
                return 'not_found'
            if row['password_key'] == new_key:
                return 'same'
            if conn.execute('SELECT 1 FROM students WHERE student_id = ? AND password_key = ?',
                            (student_id, new_key)).fetchone():
                return 'taken'
            conn.execute('UPDATE students SET password_key = ? WHERE id = ?', (new_key, user_id))
        return 'ok'
    except Exception as exc:
        if _is_unique_violation(exc):  # 확인 직후 다른 요청이 같은 비밀번호 계정을 만든 경우
            return 'taken'
        raise
    finally:
        conn.close()

# ---------------------------------------------------------------------
# 성적(과목)
# ---------------------------------------------------------------------
def get_all_courses(user_id):
    conn = get_db_connection()
    try:
        return conn.execute('SELECT * FROM courses WHERE user_id = ? ORDER BY id', (user_id,)).fetchall()
    finally:
        conn.close()


def get_course(course_id, user_id):
    """내 과목이면 반환, 없거나 남의 과목이면 None."""
    conn = get_db_connection()
    try:
        return conn.execute('SELECT * FROM courses WHERE id = ? AND user_id = ?', (course_id, user_id)).fetchone()
    finally:
        conn.close()


def add_course(user_id, name, semester, credit, grade, point):
    conn = get_db_connection()
    try:
        with conn:
            conn.execute('''
                INSERT INTO courses (user_id, name, semester, credit, grade, point)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, name, semester, credit, grade, point))
    finally:
        conn.close()


def update_course(course_id, user_id, name, semester, credit, grade, point):
    conn = get_db_connection()
    try:
        with conn:
            return conn.execute('''
                UPDATE courses SET name = ?, semester = ?, credit = ?, grade = ?, point = ?
                WHERE id = ? AND user_id = ?
            ''', (name, semester, credit, grade, point, course_id, user_id)).rowcount > 0
    finally:
        conn.close()


def delete_course(course_id, user_id):
    conn = get_db_connection()
    try:
        with conn:
            return conn.execute('DELETE FROM courses WHERE id = ? AND user_id = ?',
                                (course_id, user_id)).rowcount > 0
    finally:
        conn.close()


# ---------------------------------------------------------------------
# 퀴즈 오답 노트
# ---------------------------------------------------------------------
def _wrong_answer_view(row):
    return {
        'id': row['id'], 'subject': row['subject'], 'question': row['question'],
        'choices': json.loads(row['choices']), 'answer': row['answer'],
        'selected_answer': row['selected_answer'], 'explanation': row['explanation'],
        'saved_at': row['saved_at'],
    }


def save_wrong_answers(user_id, subject, questions):
    """틀린 문제 저장. 같은 문제는 새로 덮어쓰고, 최근 WRONG_ANSWER_LIMIT 개만 남긴다."""
    if not questions:
        return
    conn = get_db_connection()
    try:
        with conn:
            now = time.time()
            for offset, q in enumerate(questions):
                conn.execute('DELETE FROM wrong_answers WHERE user_id = ? AND question = ?',
                             (user_id, q['question']))
                conn.execute('''
                    INSERT INTO wrong_answers
                        (user_id, subject, question, choices, answer, selected_answer, explanation, saved_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, subject, q['question'], json.dumps(q['choices'], ensure_ascii=False),
                      q['answer'], q.get('selected_answer'), q['explanation'], now + offset * 1e-6))
            conn.execute('''
                DELETE FROM wrong_answers
                WHERE user_id = ? AND id NOT IN (
                    SELECT id FROM wrong_answers WHERE user_id = ?
                    ORDER BY saved_at DESC, id DESC LIMIT ?)
            ''', (user_id, user_id, WRONG_ANSWER_LIMIT))
    finally:
        conn.close()


def get_wrong_answers(user_id):
    conn = get_db_connection()
    try:
        rows = conn.execute('''
            SELECT * FROM wrong_answers WHERE user_id = ?
            ORDER BY saved_at DESC, id DESC LIMIT ?
        ''', (user_id, WRONG_ANSWER_LIMIT)).fetchall()
    finally:
        conn.close()
    return [_wrong_answer_view(row) for row in rows]


def delete_wrong_answer(item_id, user_id):
    conn = get_db_connection()
    try:
        with conn:
            return conn.execute('DELETE FROM wrong_answers WHERE id = ? AND user_id = ?',
                                (item_id, user_id)).rowcount > 0
    finally:
        conn.close()


# ---------------------------------------------------------------------
# AI 대화 기록
# ---------------------------------------------------------------------
def _conversation_view(row):
    return {'id': row['id'], 'title': row['title'], 'messages': json.loads(row['messages']),
            'updated_at': row['updated_at']}


def save_conversation(user_id, conversation_id, title, messages):
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
                    WHERE id = ? AND user_id = ?
                ''', (title, payload, now, conversation_id, user_id)).rowcount
            if not updated:
                conversation_id = conn.execute('''
                    INSERT INTO chat_conversations (user_id, title, messages, updated_at)
                    VALUES (?, ?, ?, ?) RETURNING id
                ''', (user_id, title, payload, now)).fetchone()['id']
            conn.execute('''
                DELETE FROM chat_conversations
                WHERE user_id = ? AND id NOT IN (
                    SELECT id FROM chat_conversations WHERE user_id = ?
                    ORDER BY updated_at DESC, id DESC LIMIT ?)
            ''', (user_id, user_id, CONVERSATION_LIMIT))
        return conversation_id
    finally:
        conn.close()


def get_conversations(user_id):
    conn = get_db_connection()
    try:
        rows = conn.execute('''
            SELECT * FROM chat_conversations WHERE user_id = ?
            ORDER BY updated_at DESC, id DESC LIMIT ?
        ''', (user_id, CONVERSATION_LIMIT)).fetchall()
    finally:
        conn.close()
    return [_conversation_view(row) for row in rows]


def delete_conversation(conversation_id, user_id):
    conn = get_db_connection()
    try:
        with conn:
            return conn.execute('DELETE FROM chat_conversations WHERE id = ? AND user_id = ?',
                                (conversation_id, user_id)).rowcount > 0
    finally:
        conn.close()


# ---------------------------------------------------------------------
# AI 생성 퀴즈 (브라우저 세션 단위)
# ---------------------------------------------------------------------
def _purge_old_quizzes(conn):
    conn.execute('DELETE FROM quizzes WHERE created < ?', (time.time() - QUIZ_LIFETIME_SECONDS,))


def latest_quiz_time(owner):
    conn = get_db_connection()
    try:
        row = conn.execute('SELECT created FROM quizzes WHERE owner = ? ORDER BY created DESC LIMIT 1',
                           (owner,)).fetchone()
    finally:
        conn.close()
    return row['created'] if row else None


def save_quiz(quiz_id, owner, subject, questions):
    conn = get_db_connection()
    try:
        with conn:
            _purge_old_quizzes(conn)
            conn.execute('INSERT INTO quizzes (id, owner, created, subject, questions) VALUES (?, ?, ?, ?, ?)',
                         (quiz_id, owner, time.time(), subject, json.dumps(questions, ensure_ascii=False)))
    finally:
        conn.close()


def get_quiz(quiz_id, owner):
    conn = get_db_connection()
    try:
        return conn.execute('SELECT * FROM quizzes WHERE id = ? AND owner = ? AND created >= ?',
                            (quiz_id, owner, time.time() - QUIZ_LIFETIME_SECONDS)).fetchone()
    finally:
        conn.close()
