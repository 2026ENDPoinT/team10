import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch
from app import app
from assignments import connection, planning_context


class PlanningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old = dict(app.config)
        app.config.update(TESTING=True, ASSIGNMENTS_DB=str(Path(self.temp.name)/'tasks.db'))
        self.clock = patch('assignments.now_kst',return_value=datetime(2026,11,14,12))
        self.clock.start()
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session.update(assignment_owner=1,assignment_csrf='test',
                assignment_navigation={'student_id':'12345678','name':'Test','year':'1'},
                student_id='12345678',name='Test',year='1',password='test!')

    def tearDown(self):
        self.clock.stop()
        app.config.clear()
        app.config.update(self.old)
        self.temp.cleanup()

    def save(self, **changes):
        data={'csrf_token':'test','subject':'웹프로그래밍','title':'보고서','deadline':'2026-11-15T18:00',
              'priority':'2','estimated_hours':'2','estimated_minutes':'10',
              'checklist':'자료 조사\n목차 작성\n본문 작성\n검토 후 제출'}
        data.update(changes)
        return self.client.post('/assignments/save',data=data)

    def row(self):
        with app.app_context():
            conn=connection()
            row=conn.execute('SELECT * FROM assignments WHERE id=1').fetchone()
            conn.close()
            return row

    def test_checklist_progress_submission_and_chat(self):
        self.assertEqual(self.save().status_code,302)
        self.assertEqual(self.row()['estimated_minutes'],130)
        for index in (0,1):
            self.assertEqual(self.client.post(f'/assignments/1/check/{index}',data={'csrf_token':'test','done':'1'}).status_code,302)
        html=self.client.get('/assignments/').get_data(as_text=True)
        self.assertIn('50%',html)
        self.assertIn('AI랑 계획하기',html)
        self.assertEqual(self.row()['completed'],0)
        response=self.client.get('/ai/?assignment_id=1')
        self.assertEqual(response.status_code,200)
        self.assertIn('assignment-plan-context',response.get_data(as_text=True))
        for index in (2,3):
            self.client.post(f'/assignments/1/check/{index}',data={'csrf_token':'test','done':'1'})
        self.assertEqual(self.row()['completed'],0)
        self.client.post('/assignments/1/complete',data={'csrf_token':'test'})
        self.assertEqual(self.row()['completed'],1)
        self.client.post('/assignments/1/check/0',data={'csrf_token':'test','done':'0'})
        self.assertFalse(json.loads(self.row()['checklist'])[0]['done'])

    def test_ownership_csrf_and_validation(self):
        self.save()
        self.assertEqual(self.client.post('/assignments/1/check/0',data={'done':'1'}).status_code,400)
        self.assertEqual(self.client.post('/assignments/1/check/99',data={'csrf_token':'test','done':'1'}).status_code,404)
        other=app.test_client()
        with other.session_transaction() as session:
            session.update(assignment_owner=2,assignment_csrf='other')
        self.assertEqual(other.get('/ai/?assignment_id=1').status_code,404)
        self.assertEqual(other.post('/assignments/1/check/0',data={'csrf_token':'other','done':'1'}).status_code,404)
        self.save(checklist='duplicate\nduplicate')
        self.save(estimated_hours='-1')
        with app.app_context():
            conn=connection()
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM assignments').fetchone()[0],1)
            conn.close()

    def test_legacy_migration_and_repeated_initialization(self):
        conn=sqlite3.connect(app.config['ASSIGNMENTS_DB'])
        conn.execute('CREATE TABLE assignments(id INTEGER PRIMARY KEY,owner INTEGER,subject TEXT,title TEXT,deadline TEXT,priority INTEGER,completed INTEGER)')
        conn.execute("INSERT INTO assignments VALUES(1,1,'Course','Original','2026-11-15T18:00',2,0)")
        conn.commit()
        conn.close()
        self.assertEqual(self.row()['title'],'Original')
        self.assertEqual(self.row()['estimated_minutes'],0)
        self.assertEqual(json.loads(self.row()['checklist']),[])
