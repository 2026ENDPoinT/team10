"""퀴즈 오답 노트(최대 10개)와 AI 대화 기록(최대 3개) 저장 테스트. 실제 database.db 는 건드리지 않는다."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database
from app import app
from db_helper import use_test_database


class StudyRecordTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.previous = dict(app.config)
        use_test_database(self, self.directory.name)
        app.config.update(TESTING=True, AI_MODE='groq', GROQ_API_KEY='test')
        self.client = self.login('26101150', 'mine!')
        self.user_id = database.get_student('26101150', 'mine!')['id']

    def tearDown(self):
        app.config.clear()
        app.config.update(self.previous)
        self.directory.cleanup()

    def login(self, student_id, password):
        client = app.test_client()
        client.post('/login', data={'student_id': student_id, 'name': 'T', 'year': '1', 'password': password})
        return client

    @staticmethod
    def question(n):
        return {'question': f'문제 {n}', 'choices': ['a', 'b', 'c', 'd'], 'answer': 1, 'explanation': f'해설 {n}'}

    def take_quiz(self, client, questions, answers):
        reply = {'choices': [{'message': {'content': json.dumps({'questions': questions})}}], 'usage': {}}
        with patch('study_ai.generated_quiz.request_groq', return_value=reply):
            quiz = client.post('/ai/api/quiz/generate',
                               json={'subject': '선형대수학', 'count': len(questions), 'topic': '행렬'})
        self.assertEqual(quiz.status_code, 200, quiz.json)
        return client.post('/ai/api/quiz/grade', json={'quiz_id': quiz.json['quiz_id'], 'answers': answers})

    # ---------------- 오답 노트 ----------------
    def test_grading_saves_only_wrong_answers_for_the_account(self):
        graded = self.take_quiz(self.client, [self.question(1), self.question(2), self.question(3)], [1, 0, None])
        self.assertTrue(graded.json['wrong_answers_saved'])
        items = self.client.get('/api/wrong-answers').json['items']
        self.assertEqual([i['question'] for i in items], ['문제 3', '문제 2'])   # 최근 것부터, 맞힌 문제는 제외
        self.assertEqual(items[0]['selected_answer'], None)
        self.assertEqual(items[1]['explanation'], '해설 2')
        self.assertEqual(items[1]['subject'], '선형대수학')

        # 같은 학번이라도 비밀번호가 다르면 다른 계정이므로 보이지 않음
        self.assertEqual(self.login('26101150', 'other!').get('/api/wrong-answers').json['items'], [])
        self.assertEqual(self.login('26101151', 'mine!').get('/api/wrong-answers').json['items'], [])
        # 로그인하지 않으면 조회 불가
        self.assertEqual(app.test_client().get('/api/wrong-answers').status_code, 401)

    def test_wrong_answers_keep_latest_ten_without_duplicates(self):
        for n in range(12):
            database.save_wrong_answers(self.user_id, '선형대수학', [{**self.question(n), 'selected_answer': 0}])
        database.save_wrong_answers(self.user_id, '선형대수학', [{**self.question(5), 'selected_answer': 2}])
        items = self.client.get('/api/wrong-answers').json['items']
        self.assertEqual(len(items), 10)
        self.assertEqual(items[0]['question'], '문제 5')            # 다시 틀린 문제는 최신으로 갱신
        self.assertEqual(items[0]['selected_answer'], 2)
        self.assertEqual(sum(i['question'] == '문제 5' for i in items), 1)
        self.assertNotIn('문제 0', [i['question'] for i in items])  # 가장 오래된 문제부터 삭제
        self.assertNotIn('문제 1', [i['question'] for i in items])

    def test_delete_wrong_answer_is_owner_only_and_same_origin(self):
        self.take_quiz(self.client, [self.question(1)], [0])
        item_id = self.client.get('/api/wrong-answers').json['items'][0]['id']
        other = self.login('26101150', 'other!')
        self.assertEqual(other.post(f'/api/wrong-answers/{item_id}/delete', json={}).status_code, 404)
        self.assertEqual(self.client.post(f'/api/wrong-answers/{item_id}/delete', json={},
                                          headers={'Origin': 'https://evil.test'}).status_code, 403)
        deleted = self.client.post(f'/api/wrong-answers/{item_id}/delete', json={})
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(deleted.json['items'], [])

    def test_logged_out_quiz_is_graded_but_not_saved(self):
        graded = self.take_quiz(app.test_client(), [self.question(1)], [0])
        self.assertFalse(graded.json['wrong_answers_saved'])

    # ---------------- AI 대화 기록 ----------------
    def chat(self, text):
        return [{'role': 'user', 'content': text}, {'role': 'assistant', 'content': '답변: ' + text}]

    def test_conversations_update_in_place_and_keep_latest_three(self):
        first = self.client.post('/api/conversations', json={'id': None, 'messages': self.chat('첫 질문')})
        self.assertEqual(first.status_code, 200)
        first_id = first.json['id']
        updated = self.client.post('/api/conversations',
                                   json={'id': first_id, 'messages': self.chat('첫 질문') + self.chat('추가 질문')})
        self.assertEqual(updated.json['id'], first_id)
        self.assertEqual(len(updated.json['items']), 1)
        self.assertEqual(len(updated.json['items'][0]['messages']), 4)
        self.assertEqual(updated.json['items'][0]['title'], '첫 질문')

        for text in ['둘', '셋', '넷']:
            result = self.client.post('/api/conversations', json={'messages': self.chat(text)})
        titles = [i['title'] for i in result.json['items']]
        self.assertEqual(titles, ['넷', '셋', '둘'])        # 최근 3개만, 가장 오래된 '첫 질문' 삭제
        # 삭제된 대화 번호로 저장하면 새 대화로 저장
        again = self.client.post('/api/conversations', json={'id': first_id, 'messages': self.chat('다시')})
        self.assertNotEqual(again.json['id'], first_id)

    def test_conversations_are_private_validated_and_deletable(self):
        saved = self.client.post('/api/conversations', json={'messages': self.chat('비밀')}).json['id']
        other = self.login('26101150', 'other!')
        self.assertEqual(other.get('/api/conversations').json['items'], [])
        # 다른 계정이 남의 대화 번호로 저장해도 덮어쓰지 못함
        hijack = other.post('/api/conversations', json={'id': saved, 'messages': self.chat('덮어쓰기')})
        self.assertNotEqual(hijack.json['id'], saved)
        self.assertEqual(self.client.get('/api/conversations').json['items'][0]['messages'][0]['content'], '비밀')
        self.assertEqual(other.post(f'/api/conversations/{saved}/delete', json={}).status_code, 404)

        for bad in [{'messages': []}, {'messages': [{'role': 'system', 'content': 'x'}]},
                    {'messages': [{'role': 'user', 'content': '   '}]}, {'id': '1', 'messages': self.chat('x')},
                    {'messages': [{'role': 'user', 'content': 'x' * 12001}]}]:
            self.assertEqual(self.client.post('/api/conversations', json=bad).status_code, 400, bad)
        self.assertEqual(app.test_client().post('/api/conversations', json={'messages': self.chat('x')}).status_code, 401)
        self.assertEqual(self.client.post('/api/conversations', json={'messages': self.chat('x')},
                                          headers={'Origin': 'https://evil.test'}).status_code, 403)
        # 막힌 요청(로그인 없음·다른 사이트)은 아무것도 저장하지 않았으므로 삭제 후 목록은 비어 있음
        self.assertEqual(self.client.post(f'/api/conversations/{saved}/delete', json={}).json['items'], [])

    def test_password_change_keeps_saved_records(self):
        self.take_quiz(self.client, [self.question(1)], [0])
        self.client.post('/api/conversations', json={'messages': self.chat('기록')})
        self.client.post('/change-password', data={'new_password': 'newpw!'})
        self.assertEqual(len(self.client.get('/api/wrong-answers').json['items']), 1)
        self.assertEqual(len(self.client.get('/api/conversations').json['items']), 1)
        # 새 비밀번호로 로그인하면 같은 기록이 보이고, 예전 비밀번호는 이제 다른(빈) 계정이다
        self.assertEqual(len(self.login('26101150', 'newpw!').get('/api/conversations').json['items']), 1)
        self.assertEqual(self.login('26101150', 'mine!').get('/api/conversations').json['items'], [])

    def test_password_change_rejects_password_of_another_grade_set(self):
        self.login('26101150', 'other!')
        changed = self.client.post('/change-password', data={'new_password': 'other!'}, follow_redirects=True)
        self.assertIn('같은 학번에서 이미 사용 중인 비밀번호입니다.', changed.get_data(as_text=True))
        self.assertEqual(database.get_student('26101150', 'mine!')['id'], self.user_id)

    # ---------------- 로그인 ----------------
    def test_same_student_id_with_different_passwords_are_separate_accounts(self):
        first = app.test_client()
        response = first.post('/login', data={'student_id': '22222222', 'name': 'A', 'year': '1', 'password': '!!!!!'},
                              follow_redirects=True)
        self.assertIn('새 성적 셋이 만들어졌습니다.', response.get_data(as_text=True))
        first.post('/add', data={'name_input': '선형대수학', 'semester_year': '2026', 'semester_term': '1학기', 'grade': 'A+'})
        second = app.test_client()
        second.post('/login', data={'student_id': '22222222', 'name': 'B', 'year': '1', 'password': '@@@@@'})
        first_id = database.get_student('22222222', '!!!!!')['id']
        second_id = database.get_student('22222222', '@@@@@')['id']
        self.assertNotEqual(first_id, second_id)
        self.assertEqual([c['name'] for c in database.get_all_courses(first_id)], ['선형대수학'])
        self.assertEqual(database.get_all_courses(second_id), [])
        again = app.test_client()
        response = again.post('/login', data={'student_id': '22222222', 'name': 'A', 'year': '1', 'password': '!!!!!'},
                              follow_redirects=True)
        self.assertNotIn('새 성적 셋이 만들어졌습니다.', response.get_data(as_text=True))
        with again.session_transaction() as session:
            self.assertEqual(session['user_id'], first_id)
        # 새 조합은 비밀번호 규칙을 지켜야 만들어진다
        weak = app.test_client().post('/login', data={'student_id': '22222222', 'name': 'C', 'year': '1', 'password': 'abc'})
        self.assertEqual(weak.headers['Location'], '/')
        with self.client.session_transaction() as session:
            self.assertNotIn('password', session)

    def test_pages_show_saved_sections(self):
        for url, marker in [('/quiz', 'id="wrong-notes"'), ('/ai/', 'id="saved-chats"')]:
            html = self.client.get(url).get_data(as_text=True)
            self.assertIn(marker, html)
            self.assertIn('data-logged-in="true"', html)
            self.assertIn('data-logged-in="false"', app.test_client().get(url).get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
