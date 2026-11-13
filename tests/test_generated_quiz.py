import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from app import app, CURRICULUM


class GeneratedQuizTests(unittest.TestCase):
    def setUp(self):
        self.previous = dict(app.config)
        self.directory = tempfile.TemporaryDirectory()
        app.config.update(TESTING=True, AI_MODE='groq', GROQ_API_KEY='test',
                          AI_QUIZ_DB=str(Path(self.directory.name) / 'quizzes.db'))
        self.client = app.test_client()
        self.question = {'question': '행렬 A가 2×3일 때 전치행렬의 크기는?',
                         'choices': ['2×3', '3×2', '2×2', '3×3'], 'answer': 1,
                         'explanation': '전치행렬은 행과 열을 바꾸므로 3×2입니다.'}

    def tearDown(self):
        app.config.clear()
        app.config.update(self.previous)
        self.directory.cleanup()

    def generate(self, questions=None):
        with patch('study_ai.generated_quiz.request_groq', return_value={'choices': [{'message': {
                'content': json.dumps({'questions': [self.question] if questions is None else questions})}}],
                'usage': {'total_tokens': 500}}) as provider:
            response = self.client.post('/ai/api/quiz/generate', json={'subject': '선형대수학', 'count': 1})
        return response, provider

    def test_curriculum_generation_grading_and_session_ownership(self):
        self.assertEqual(app.config['QUIZ_SUBJECTS'], {c for courses in CURRICULUM.values() for c in courses})
        result, provider = self.generate()
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.json['questions']), 1)
        self.assertNotIn('answer', result.json['questions'][0])
        self.assertNotIn('explanation', result.json['questions'][0])
        self.assertIn('선형대수학', provider.call_args.args[0]['messages'][1]['content'])
        quiz_id = result.json['quiz_id']
        with patch('study_ai.generated_quiz.request_groq') as provider:
            for answer, score in [(1,1), (0,0), (None,0)]:
                graded = self.client.post('/ai/api/quiz/grade', json={'quiz_id': quiz_id, 'answers': [answer], 'answer': 0})
                self.assertEqual(graded.status_code, 200)
                self.assertEqual(graded.json['correct'], score)
                self.assertEqual(graded.json['questions'][0]['explanation'], self.question['explanation'])
            provider.assert_not_called()
        other = app.test_client().post('/ai/api/quiz/grade', json={'quiz_id': quiz_id, 'answers': [1]})
        self.assertEqual(other.status_code, 404)
        self.assertEqual(self.client.post('/ai/api/quiz/grade', json={'quiz_id': quiz_id, 'answers': [True]}).status_code, 400)
        self.assertEqual(self.client.post('/ai/api/quiz/generate', json={'subject':'선형대수학','count':1}).status_code,429)

    def test_invalid_requests_never_call_provider(self):
        with patch('study_ai.generated_quiz.request_groq') as provider:
            for data in [{'subject':'fake', 'count':1}, {'subject':'선형대수학', 'count':6},
                         {'subject':'선형대수학', 'count':True}, {'subject':'선형대수학', 'count':1, 'topic':'x'*201}]:
                self.assertEqual(self.client.post('/ai/api/quiz/generate', json=data).status_code,400)
            self.assertEqual(self.client.post('/ai/api/quiz/generate', json={}, headers={'Origin':'https://other.test'}).status_code,403)
            provider.assert_not_called()

    def test_malformed_model_output_rejected(self):
        for questions in [[], [self.question, self.question], [{**self.question,'answer':4}],
                          [{**self.question,'choices':['same']*4}], [{**self.question,'explanation':''}]]:
            result, _ = self.generate(questions)
            self.assertEqual(result.status_code,502)
