import json
import unittest
from unittest.mock import patch
import httpx
from app import app


class GeminiTests(unittest.TestCase):
    def setUp(self):
        self.previous = dict(app.config)
        app.config.update(TESTING=True, AI_MODE='gemini', GEMINI_API_KEY='test-key',
                          GEMINI_MODEL='gemini-3.5-flash-lite', YOUTUBE_API_KEY='')
        self.client = app.test_client()

    def tearDown(self):
        app.config.clear()
        app.config.update(self.previous)

    def reply(self, data, status=200):
        return httpx.Response(status, json=data, request=httpx.Request('POST', 'https://generativelanguage.googleapis.com'))

    def test_history_schema_and_korean_reply(self):
        data = {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': json.dumps({
            'reply': '함께 공부해 볼까요?', 'study_topic': '파이썬', 'video_query': ''})}]}}]}
        with patch('study_ai.gemini.httpx.post', return_value=self.reply(data)) as post:
            response = self.client.post('/ai/api/chat', json={'message': '연습 문제 주세요',
                'history': [{'role': 'user', 'content': '안녕'}, {'role': 'assistant', 'content': '안녕하세요'}]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['reply'], '함께 공부해 볼까요?')
        args = post.call_args.kwargs
        self.assertEqual(args['headers']['x-goog-api-key'], 'test-key')
        self.assertEqual(args['json']['contents'][1]['role'], 'model')
        self.assertIn('한국어', args['json']['systemInstruction']['parts'][0]['text'])
        self.assertEqual(args['json']['generationConfig']['responseFormat']['text']['mimeType'], 'APPLICATION_JSON')
        self.assertNotIn('test-key', response.get_data(as_text=True))

    def test_missing_key_and_provider_banner(self):
        app.config['GEMINI_API_KEY'] = ''
        self.assertFalse(self.client.get('/ai/api/health').json['configured'])
        self.assertIn(b'GEMINI_API_KEY', self.client.get('/ai/').data)
        self.assertEqual(self.client.post('/ai/api/chat', json={'message': '안녕'}).status_code, 503)

    def test_provider_failures(self):
        for code, expected in [(400,503),(403,503),(404,503),(429,429),(500,502)]:
            with self.subTest(code=code), patch('study_ai.gemini.httpx.post', return_value=self.reply({'error': 'secret'}, code)):
                result = self.client.post('/ai/api/chat', json={'message': '안녕'})
                self.assertEqual(result.status_code, expected)
                self.assertNotIn('secret', result.json['error'])

    def test_blocked_incomplete_and_malformed_replies(self):
        for data in ({}, {'candidates': [{'finishReason': 'MAX_TOKENS'}]},
                     {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text':'bad JSON'}]}}]}):
            with patch('study_ai.gemini.httpx.post', return_value=self.reply(data)):
                self.assertEqual(self.client.post('/ai/api/chat', json={'message': '안녕'}).status_code, 502)

    def test_timeout(self):
        with patch('study_ai.gemini.httpx.post', side_effect=httpx.ReadTimeout('private detail')):
            self.assertEqual(self.client.post('/ai/api/chat', json={'message': '안녕'}).status_code, 504)
