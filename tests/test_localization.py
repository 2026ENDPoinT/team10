from pathlib import Path
import tempfile
import unittest
from app import app
from db_helper import use_test_database


class LocalizationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.old_config = dict(app.config)
        use_test_database(self, self.directory.name)
        app.config.update(TESTING=True)
        self.client = app.test_client()
        self.client.post('/login', data={'student_id':'12345678','name':'과제명', 'year':'1','password':'test!'})

    def tearDown(self):
        app.config.clear()
        app.config.update(self.old_config)
        self.directory.cleanup()

    def test_all_pages_and_language_roundtrip(self):
        pages = {'/':'Sign in', '/scores':'Grade summary', '/manage':'Find and manage courses',
                 '/predict':'Forecast settings', '/quiz?student_id=12345678&name=Test&year=1':'Quiz settings',
                 '/assignments/':'New assignment', '/ai/':'What shall we study today?'}
        self.client.set_cookie('ui_language','en')
        for url, expected in pages.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code,200)
                html = response.get_data(as_text=True)
                self.assertIn('lang="en"',html)
                self.assertIn(expected,html)
                self.assertIn('switchSiteLanguage()',html)
        self.client.set_cookie('ui_language','ko')
        html=self.client.get('/assignments/').get_data(as_text=True)
        self.assertIn('새 과제 등록',html)
        self.assertIn('lang="ko"',html)

    def test_values_names_and_error_translation(self):
        self.client.set_cookie('ui_language','en')
        html=self.client.get('/assignments/').get_data(as_text=True)
        self.assertIn('value="선형대수학"',html)
        self.assertIn('Linear Algebra',html)
        self.assertIn('과제명',html)  # Student name is not translated.
        response=self.client.post('/ai/api/quiz/generate', json={'subject':'invalid','count':1})
        self.assertEqual(response.status_code,400)
        self.assertEqual(response.json['error'],'Select a course from the curriculum.')
        html=self.client.get('/ai/').get_data(as_text=True)
        self.assertIn('value="en" selected',html)

    def test_unknown_cookie_falls_back_to_korean(self):
        self.client.set_cookie('ui_language','invalid')
        self.assertIn('lang="ko"',self.client.get('/').get_data(as_text=True))
