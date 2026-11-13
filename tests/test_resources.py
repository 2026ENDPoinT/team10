import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import httpx

from study_ai.resources import find_video_lessons


class VideoTests(unittest.TestCase):
    def setUp(self):
        self.config = {'AI_MODE': 'openai', 'YOUTUBE_API_KEY': 'test-key-not-real'}
        self.preferences = {'language': 'ko', 'level': 'beginner', 'video_duration': 'medium'}

    def response(self, data, status=200):
        return httpx.Response(status, json=data, request=httpx.Request('GET', 'https://www.googleapis.com/youtube/v3/search'))

    def test_empty_query_does_not_search(self):
        with patch('study_ai.resources.httpx.get') as get:
            self.assertEqual(find_video_lessons('', self.preferences, self.config)['items'], [])
        get.assert_not_called()

    def test_no_key_is_honest_search_link(self):
        with patch('study_ai.resources.httpx.get') as get:
            result = find_video_lessons('파이썬 // 기초', self.preferences, {'AI_MODE': 'openai', 'YOUTUBE_API_KEY': ''})
        get.assert_not_called()
        self.assertEqual(result['items'], [])
        self.assertEqual(parse_qs(urlsplit(result['search_url']).query)['search_query'], ['파이썬 // 기초'])

    def test_youtube_metadata_and_preferences(self):
        data = {'items': [{'id': {'videoId': 'AbCdEf12345'}, 'snippet': {'title': 'Python &amp; division', 'channelTitle': 'Example teacher'}}]}
        with patch('study_ai.resources.httpx.get', return_value=self.response(data)) as get:
            result = find_video_lessons('파이썬 정수 나눗셈', self.preferences, self.config)
        self.assertEqual(result['items'][0]['title'], 'Python & division')
        self.assertEqual(result['items'][0]['url'], 'https://www.youtube.com/watch?v=AbCdEf12345')
        self.assertEqual(get.call_args.kwargs['params']['relevanceLanguage'], 'ko')
        self.assertEqual(get.call_args.kwargs['params']['videoDuration'], 'medium')
        self.assertEqual(get.call_args.kwargs['params']['type'], 'video')
        self.assertNotIn('test-key-not-real', str(result))

    def test_invalid_ids_cannot_become_links(self):
        data = {'items': [None, {'id': {'videoId': 'https://evil.example'}, 'snippet': {'title': 'Bad', 'channelTitle': 'Bad'}}]}
        with patch('study_ai.resources.httpx.get', return_value=self.response(data)):
            result = find_video_lessons('Python', self.preferences, self.config)
        self.assertEqual(result['items'], [])
        self.assertIn('No matching videos', result['notice'])

    def test_quota_or_http_failure_preserves_fallback_without_key_leak(self):
        with patch('study_ai.resources.httpx.get', return_value=self.response({'error': 'secret details'}, 403)):
            result = find_video_lessons('Python', self.preferences, self.config)
        self.assertEqual(result['items'], [])
        self.assertIn('temporarily unavailable', result['notice'])
        self.assertNotIn('secret details', str(result))
        self.assertNotIn('test-key-not-real', str(result))

    def test_invalid_provider_response_does_not_break_chat(self):
        for data in ([], {'items': None}):
            with self.subTest(data=data), patch('study_ai.resources.httpx.get', return_value=self.response(data)):
                result = find_video_lessons('Python', self.preferences, self.config)
                self.assertIn('temporarily unavailable', result['notice'])
