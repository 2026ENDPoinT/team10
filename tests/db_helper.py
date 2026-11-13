"""테스트용 DB 설정.

기본은 임시 SQLite 파일을 쓴다. TEST_DATABASE_URL 환경변수를 주면 그 PostgreSQL 에서 테스트한다
(테이블을 비우므로 실제 운영 DB 주소를 넣으면 안 된다).
"""
import os
from pathlib import Path
from unittest.mock import patch

import database

TABLES = ('quizzes', 'assignments', 'chat_conversations', 'wrong_answers', 'courses', 'students')


def use_test_database(testcase, directory):
    url = os.getenv('TEST_DATABASE_URL', '')
    env = patch.dict(os.environ, {'DATABASE_URL': url})
    env.start()
    testcase.addCleanup(env.stop)
    previous = database.DB_NAME
    database.DB_NAME = str(Path(directory) / 'test.db')
    testcase.addCleanup(setattr, database, 'DB_NAME', previous)
    database.init_db()
    if url:
        conn = database.get_db_connection()
        try:
            with conn:
                conn.execute(f'TRUNCATE {", ".join(TABLES)} RESTART IDENTITY CASCADE')
        finally:
            conn.close()


def make_students(count):
    """과제 테스트처럼 세션에 owner 를 직접 넣는 경우를 위해 id 1..count 계정을 만든다."""
    return [database.create_student(f'1000000{n}', 'test!', f'Student {n}', '1')['id'] for n in range(1, count + 1)]
