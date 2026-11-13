from datetime import datetime
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from flask import Flask
from assignments import init_assignments, connection


class DeadlineTests(unittest.TestCase):
    def test_past_dates_times_and_update_preserve_existing_data(self):
        with tempfile.TemporaryDirectory() as folder:
            app = Flask(__name__)
            app.config.update(TESTING=True, SECRET_KEY='test', ASSIGNMENTS_DB=str(Path(folder)/'tasks.db'))
            init_assignments(app, {'semester':['Course']})
            client = app.test_client()
            with client.session_transaction() as session:
                session['assignment_owner'] = 1
                session['assignment_csrf'] = 'test-token'

            def save(date, path='/assignments/save'):
                return client.post(path, data={'subject':'Course', 'title':'Task', 'priority':2,
                    'deadline':date, 'csrf_token':'test-token'})

            with patch('assignments.now_kst', return_value=datetime(2026,11,14,12,52,30)):
                for value in ['2026-11-13T23:59', '2026-11-14T12:51', '2026-11-14T12:52']:
                    self.assertEqual(save(value).status_code,302)
                    with client.session_transaction() as session:
                        self.assertIn(('error','이미 지난 시간을 입력할 수 없습니다.'), session['_flashes'])
                with app.app_context():
                    c=connection()
                    self.assertEqual(c.execute('SELECT COUNT(*) FROM assignments').fetchone()[0],0)
                    c.close()
                save('2026-11-14T12:53')
                save('2026-11-13T10:00', '/assignments/1/save')
                with app.app_context():
                    c=connection()
                    self.assertEqual(c.execute('SELECT deadline FROM assignments').fetchone()[0],'2026-11-14T12:53')
                    c.close()
                response=client.post('/assignments/save',data={'subject':'Course','title':'Parts','priority':2,
                    'csrf_token':'test-token','deadline_year':2026,'deadline_month':11,
                    'deadline_day':13,'deadline_time':'23:59'})
                self.assertEqual(response.status_code,302)
                with app.app_context():
                    c=connection()
                    self.assertEqual(c.execute('SELECT COUNT(*) FROM assignments').fetchone()[0],1)
                    c.close()
