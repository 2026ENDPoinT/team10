from datetime import datetime
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from app import app
from db_helper import use_test_database
from assignments import notice, label, connection


class AssignmentTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.old = dict(app.config)
        use_test_database(self, self.folder.name)
        app.config.update(TESTING=True)
        self.client = app.test_client()
        response = self.client.post('/login', data={'student_id':'12345678','name':'Test','year':'1','password':'test!'})
        self.assertEqual(response.status_code,302)
        self.assertEqual(self.client.get('/assignments/').status_code,200)
        with self.client.session_transaction() as session:
            self.token = session['assignment_csrf']

    def tearDown(self):
        app.config.clear()
        app.config.update(self.old)
        self.folder.cleanup()

    def create(self, title='과제', deadline='2026-11-15T18:00', priority=2):
        return self.client.post('/assignments/save', data={'csrf_token':self.token,
            'subject':'선형대수학','title':title,'deadline':deadline,'priority':priority})

    def test_crud_completion_restore_and_isolation(self):
        self.assertEqual(self.create().status_code,302)
        self.assertIn('과제', self.client.get('/assignments/').get_data(as_text=True))
        other = app.test_client()
        other.post('/login', data={'student_id':'12345678','name':'Other','year':'1','password':'other!'})
        other.get('/assignments/')
        with other.session_transaction() as s:
            token = s['assignment_csrf']
        for action in ['complete','delete','restore']:
            self.assertEqual(other.post('/assignments/1/'+action, data={'csrf_token':token}).status_code,404)
        self.assertEqual(self.client.post('/assignments/1/complete',data={}).status_code,400)
        for action, expected in [('complete',1),('restore',0)]:
            self.client.post('/assignments/1/'+action,data={'csrf_token':self.token})
            with app.app_context():
                c=connection()
                self.assertEqual(c.execute('SELECT completed FROM assignments').fetchone()['completed'],expected)
                c.close()
        self.client.post('/assignments/1/save', data={'csrf_token':self.token,'subject':'선형대수학',
            'title':'수정된 과제','deadline':'2026-11-16T12:00','priority':3})
        self.assertIn('수정된 과제',self.client.get('/assignments/').get_data(as_text=True))
        self.client.post('/assignments/1/delete',data={'csrf_token':self.token})
        self.assertNotIn('수정된 과제',self.client.get('/assignments/').get_data(as_text=True))

    def test_order_notice_and_dates(self):
        self.create('낮은중요도','2026-11-15T18:00',1)
        self.create('높은중요도','2026-11-15T18:00',3)
        self.create('오늘과제','2026-11-13T18:00')
        self.create('지난과제','2026-11-13T08:00')
        self.create('사일후','2026-11-17T18:00')
        with patch('assignments.now_kst',return_value=datetime(2026,11,13,12)):
            page=self.client.get('/assignments/').get_data(as_text=True)
            self.assertLess(page.index('높은중요도'),page.index('낮은중요도'))
            self.assertIn('오늘 마감인 과제가 1개, 3일 이내 마감인 과제가 2개',page)
            self.assertEqual(label('2026-11-13T18:00'),'오늘 마감')
            self.assertEqual(label('2026-11-14T00:00'),'D-1')
            self.client.post('/assignments/3/complete',data={'csrf_token':self.token})
            scores=self.client.get('/scores?student_id=12345678&name=Test&year=1')
            self.assertEqual(scores.status_code,200)
            self.assertIn('오늘 마감인 과제가 0개',scores.get_data(as_text=True))

    def test_separate_date_fields_and_leap_day(self):
        data = {'csrf_token':self.token, 'subject':'선형대수학', 'title':'윤년 과제',
                'priority':'2', 'deadline_year':'2028', 'deadline_month':'2',
                'deadline_day':'29', 'deadline_time':'00:05'}
        self.client.post('/assignments/save', data=data)
        with app.app_context():
            c = connection()
            self.assertEqual(c.execute('SELECT deadline FROM assignments').fetchone()['deadline'], '2028-02-29T00:05')
            c.close()
        page = self.client.get('/assignments/').get_data(as_text=True)
        self.assertIn('name="deadline_year"', page)
        self.assertIn('type="hidden" name="deadline_year"', page)
        self.assertIn('type="time" name="deadline_time"', page)
        self.assertNotIn('name="deadline_hour"', page)
        self.assertIn('value="29" selected', page)
        data['deadline_year'] = '2027'
        self.client.post('/assignments/1/save', data=data)
        with app.app_context():
            c = connection()
            self.assertEqual(c.execute('SELECT deadline FROM assignments').fetchone()['deadline'], '2028-02-29T00:05')
            c.close()

    def test_login_required_and_validation(self):
        self.assertEqual(app.test_client().get('/assignments/').status_code,302)
        self.create('invalid','bad date')
        with app.app_context():
            c=connection()
            self.assertEqual(c.execute('SELECT COUNT(*) AS n FROM assignments').fetchone()['n'],0)
            c.close()
