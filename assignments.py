"""Korean-time assignment tracker, isolated from grade storage."""
import hmac
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for

bp = Blueprint('assignments', __name__, url_prefix='/assignments')
KST = timezone(timedelta(hours=9))


def now_kst():
    return datetime.now(KST).replace(tzinfo=None)


def connection():
    conn = sqlite3.connect(current_app.config['ASSIGNMENTS_DB'])
    conn.row_factory = sqlite3.Row
    conn.execute('''CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY, owner INTEGER NOT NULL, subject TEXT NOT NULL,
        title TEXT NOT NULL, deadline TEXT NOT NULL,
        priority INTEGER NOT NULL CHECK(priority BETWEEN 1 AND 3),
        completed INTEGER NOT NULL DEFAULT 0 CHECK(completed IN (0,1)))''')
    conn.commit()
    return conn


def token():
    return session.setdefault('assignment_csrf', secrets.token_urlsafe(32))


def label(value):
    deadline = datetime.fromisoformat(value)
    now = now_kst()
    days = (deadline.date() - now.date()).days
    if days == 0:
        return '오늘 마감 · 시간 지남' if deadline < now else '오늘 마감'
    return f'D-{days}' if days > 0 else f'마감 {abs(days)}일 지남'


def notice():
    owner = session.get('assignment_owner')
    result = {'today': 0, 'soon': 0, 'overdue': 0}
    if not owner:
        return result
    conn = connection()
    try:
        rows = conn.execute('SELECT deadline FROM assignments WHERE owner=? AND completed=0', (owner,)).fetchall()
    finally:
        conn.close()
    now = now_kst()
    for row in rows:
        deadline = datetime.fromisoformat(row['deadline'])
        days = (deadline.date() - now.date()).days
        if deadline < now:
            result['overdue'] += 1
        elif days == 0:
            result['today'] += 1
        elif 1 <= days <= 3:
            result['soon'] += 1
    return result


def init_assignments(app, curriculum):
    folder = Path(app.root_path) / 'data'
    folder.mkdir(exist_ok=True)
    app.config.setdefault('ASSIGNMENTS_DB', str(folder / 'assignments.db'))
    app.config['ASSIGNMENT_SUBJECTS'] = list(dict.fromkeys(c for courses in curriculum.values() for c in courses))
    app.register_blueprint(bp)
    app.jinja_env.globals.update(assignment_csrf=token, assignment_notice=notice, deadline_label=label)


@bp.before_request
def protect():
    if not session.get('assignment_owner'):
        flash('과제 관리를 사용하려면 다시 로그인해 주세요.', 'error')
        return redirect(url_for('index'))
    if request.method == 'POST':
        expected = session.get('assignment_csrf', '')
        if not expected or not hmac.compare_digest(expected, request.form.get('csrf_token', '')):
            abort(400, description='요청이 만료되었습니다. 새로고침해 주세요.')


@bp.get('/')
def index():
    conn = connection()
    try:
        rows = conn.execute('SELECT * FROM assignments WHERE owner=? ORDER BY deadline, priority DESC, id',
                            (session['assignment_owner'],)).fetchall()
    finally:
        conn.close()
    return render_template('assignments.html', pending=[r for r in rows if not r['completed']],
        completed=[r for r in rows if r['completed']], subjects=current_app.config['ASSIGNMENT_SUBJECTS'],
        current_year=now_kst().year,
        **session.get('assignment_navigation', {}))


@bp.post('/save')
@bp.post('/<int:item_id>/save')
def save(item_id=None):
    subject = request.form.get('subject', '')
    title = request.form.get('title', '').strip()
    try:
        if 'deadline_year' in request.form:
            date_parts = [int(request.form.get('deadline_' + part, ''))
                          for part in ('year', 'month', 'day')]
            if 'deadline_time' in request.form:
                clock = datetime.strptime(request.form['deadline_time'], '%H:%M')
                deadline = datetime(*date_parts, clock.hour, clock.minute)
            else:
                deadline = datetime(*date_parts, int(request.form.get('deadline_hour', '')),
                                    int(request.form.get('deadline_minute', '')))
        else:
            deadline = datetime.strptime(request.form.get('deadline', ''), '%Y-%m-%dT%H:%M')
        priority = int(request.form.get('priority', ''))
        if subject not in current_app.config['ASSIGNMENT_SUBJECTS'] or not 1 <= len(title) <= 150 or priority not in (1,2,3):
            raise ValueError()
    except ValueError:
        flash('과목, 과제명(150자 이내), 마감 일시, 중요도를 확인해 주세요.', 'error')
        return redirect(url_for('.index'))
    values = (subject, title, deadline.isoformat(timespec='minutes'), priority)
    conn = connection()
    try:
        with conn:
            if item_id is None:
                conn.execute('INSERT INTO assignments(subject,title,deadline,priority,owner) VALUES(?,?,?,?,?)',
                             (*values, session['assignment_owner']))
            else:
                result = conn.execute('UPDATE assignments SET subject=?,title=?,deadline=?,priority=? WHERE id=? AND owner=?',
                                      (*values, item_id, session['assignment_owner']))
                if not result.rowcount:
                    abort(404)
    finally:
        conn.close()
    flash('과제를 저장했습니다.', 'success')
    return redirect(url_for('.index'))


@bp.post('/<int:item_id>/<action>')
def change(item_id, action):
    if action not in ('complete', 'restore', 'delete'):
        abort(404)
    conn = connection()
    try:
        with conn:
            if action == 'delete':
                result = conn.execute('DELETE FROM assignments WHERE id=? AND owner=?', (item_id,session['assignment_owner']))
            else:
                result = conn.execute('UPDATE assignments SET completed=? WHERE id=? AND owner=?',
                                      (int(action == 'complete'),item_id,session['assignment_owner']))
            if not result.rowcount:
                abort(404)
    finally:
        conn.close()
    return redirect(url_for('.index'))
