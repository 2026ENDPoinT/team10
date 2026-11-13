"""Offline tests against the actual copied team application and its isolated DB."""
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import app as project
import database
from db_helper import use_test_database


class IntegratedAppTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.original_db = database.DB_NAME
        use_test_database(self, self.directory.name)
        self.old_config = dict(project.app.config)
        project.app.config.update(TESTING=True, SECRET_KEY='test-only-key', AI_MODE='openai',
                                  OPENAI_API_KEY='', YOUTUBE_API_KEY='')
        self.client = project.app.test_client()
        self.student = {'student_id': '12345678', 'name': 'Test Student', 'year': '1'}

    def tearDown(self):
        project.app.config.clear()
        project.app.config.update(self.old_config)
        self.directory.cleanup()

    def test_original_pages_and_integrated_links(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        scores = self.client.get('/scores', query_string=self.student)
        self.assertEqual(scores.status_code, 200)
        self.assertIn(b'/ai/', scores.data)
        quiz = self.client.get('/quiz', query_string=self.student)
        self.assertEqual(quiz.status_code, 200)
        self.assertIn(b'/ai/static/quiz-bridge.js', quiz.data)
        self.assertIn(b'id="quiz-ai-review-btn"', quiz.data)
        self.assertLess(quiz.data.index(b'/ai/static/quiz-bridge.js'), quiz.data.index(b'/static/js/quiz.js'))
        self.assertNotIn(b'/*quiz', quiz.data)

    def test_quiz_to_tutor_return_navigation(self):
        self.client.get('/quiz', query_string=self.student)
        tutor = self.client.get('/ai/')
        self.assertEqual(tutor.status_code, 200)
        self.assertNotIn('성적 관리로 돌아가기'.encode(), tutor.data)  # 돌아가기 버튼은 삭제됨 (아일랜드로 이동)
        self.assertIn(b'OPENAI_API_KEY', tutor.data)

    def test_no_key_never_returns_fake_answer(self):
        response = self.client.post('/ai/api/chat', json={'message': 'Explain division.'})
        self.assertEqual(response.status_code, 503)
        self.assertIn('OPENAI_API_KEY', response.json['error'])
        self.assertNotIn('reply', response.json)
        self.assertFalse(self.client.get('/ai/api/health').json['configured'])

    def test_tutor_uses_actual_quiz_contract_without_touching_grades(self):
        user_id = database.create_student('12345678', 'test!', 'Test Student', '1')['id']
        database.add_course(user_id, '프로그래밍입문(1)', '2026년 1학기', 3, 'A', 4.0)
        before = database.get_all_courses(user_id)
        self.client.get('/quiz', query_string=self.student)
        project.app.config['OPENAI_API_KEY'] = 'test-only-not-real'
        context = json.loads((Path(__file__).parent / 'quiz_context.json').read_text(encoding='utf-8'))
        with patch('study_ai.service.OpenAI') as ai:
            call = ai.return_value.__enter__.return_value.responses.create
            call.return_value = SimpleNamespace(status='completed', output_text=json.dumps({
                'reply': 'print() displays a value; input() reads text.',
                'study_topic': 'Python input and output', 'video_query': 'Python input print beginner lesson'}))
            response = self.client.post('/ai/api/chat', json={
                'message': 'Help me with this mistake and find a video.', 'quiz_context': context,
                'mode': 'videos', 'preferences': {'language': 'en', 'level': 'beginner'}})
        self.assertEqual(response.status_code, 200)
        self.assertIn('youtube.com/results?', response.json['videos']['search_url'])
        request_data = json.dumps(call.call_args.kwargs, ensure_ascii=False)
        self.assertIn(context['questions'][0]['question'], request_data)
        self.assertNotIn('12345678', request_data)
        self.assertNotIn('Test Student', request_data)
        self.assertEqual(before, database.get_all_courses(user_id))

    def test_database_default_belongs_to_copy(self):
        expected = Path(project.__file__).resolve().parent / 'data' / 'database.db'
        self.assertEqual(Path(self.original_db), expected)


if __name__ == '__main__':
    unittest.main()
