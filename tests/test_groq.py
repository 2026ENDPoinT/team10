import json
from pathlib import Path
import unittest
from unittest.mock import patch

import httpx
from app import app


class GroqTests(unittest.TestCase):
    def setUp(self):
        self.previous = dict(app.config)
        app.config.update(TESTING=True, AI_MODE='groq', GROQ_API_KEY='private-test-key',
                          GROQ_MODEL='openai/gpt-oss-120b', YOUTUBE_API_KEY='')
        self.client = app.test_client()

    def tearDown(self):
        app.config.clear()
        app.config.update(self.previous)

    def response(self, data, status=200):
        return httpx.Response(status, json=data, request=httpx.Request('POST', 'https://api.groq.com'))

    def test_korean_quiz_history_and_video_handoff(self):
        context = json.loads((Path(__file__).parent / 'quiz_context.json').read_text(encoding='utf-8'))
        data = {'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps({
            'reply': '입력과 출력을 함께 복습해 봅시다.', 'study_topic': '파이썬 입출력',
            'video_query': '파이썬 입출력 기초 강의'})}}]}
        with patch('study_ai.groq.httpx.post', return_value=self.response(data)) as post:
            result = self.client.post('/ai/api/chat', json={'message': '강의를 추천해 줘',
                'quiz_context': context, 'history': [{'role': 'assistant', 'content': '함께 공부해요'}]})
        self.assertEqual(result.status_code, 200)
        self.assertIn('복습', result.json['reply'])
        self.assertIn('youtube.com/results?', result.json['videos']['search_url'])
        body = post.call_args.kwargs['json']
        self.assertEqual(body['model'], 'openai/gpt-oss-120b')
        self.assertIn('한국어', body['messages'][0]['content'])
        self.assertIn(context['questions'][0]['question'], body['messages'][1]['content'])
        self.assertEqual(body['messages'][-2]['role'], 'assistant')
        self.assertTrue(body['response_format']['json_schema']['strict'])
        self.assertNotIn('private-test-key', result.get_data(as_text=True))
        self.assertIn('Groq', self.client.get('/ai/').get_data(as_text=True))

    def test_missing_key(self):
        app.config['GROQ_API_KEY'] = ''
        self.assertFalse(self.client.get('/ai/api/health').json['configured'])
        self.assertIn(b'GROQ_API_KEY', self.client.get('/ai/').data)
        with patch('study_ai.groq.httpx.post') as post:
            self.assertEqual(self.client.post('/ai/api/chat', json={'message': '안녕'}).status_code, 503)
            post.assert_not_called()

    def test_errors_do_not_expose_provider_details(self):
        for code, expected in [(400,503),(401,503),(403,503),(404,503),(429,429),(500,502)]:
            with self.subTest(code=code), patch('study_ai.groq.httpx.post', return_value=self.response({'error':'private-test-key'}, code)):
                result = self.client.post('/ai/api/chat', json={'message': '안녕'})
                self.assertEqual(result.status_code, expected)
                self.assertNotIn('private-test-key', result.json['error'])

    def test_incomplete_and_malformed(self):
        for data in ({}, {'choices': []}, {'choices': [{'finish_reason':'length'}]},
                     {'choices': [{'finish_reason':'stop','message':{'content':'bad JSON'}}]}):
            with self.subTest(data=data), patch('study_ai.groq.httpx.post', return_value=self.response(data)):
                self.assertEqual(self.client.post('/ai/api/chat', json={'message':'안녕'}).status_code, 502)

    def test_timeout(self):
        with patch('study_ai.groq.httpx.post', side_effect=httpx.ReadTimeout('private-test-key')):
            result = self.client.post('/ai/api/chat', json={'message':'안녕'})
        self.assertEqual(result.status_code, 504)
        self.assertNotIn('private-test-key', result.json['error'])
