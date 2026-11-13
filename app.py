import math
import re
import os
import secrets
from pathlib import Path
from werkzeug.middleware.proxy_fix import ProxyFix   # import 부분에 추가

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session
from scipy.stats import norm

from database import init_db, get_all_courses, get_course_by_id, add_course, update_course, delete_course, save_or_update_student, get_student, update_student_password
from gpa_calculator import GRADE_POINTS, calculate_gpa
from study_ai import init_study_ai  # [추가] AI 튜터 모듈 임포트
from study_ai.generated_quiz import init_generated_quiz
from assignments import init_assignments
from localization import init_localization
from study_records import init_study_records


load_dotenv(Path(__file__).with_name('.env'), override=True)
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)   # 이 줄 추가
app.config['MAX_CONTENT_LENGTH'] = 128 * 1024
init_localization(app)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or secrets.token_hex(32)


init_db()
init_study_ai(app)  # [추가] AI 튜터 블루프린트 등록

COURSE_CREDITS = {
    "프로그래밍입문(1)": 3, "Introduction to Programming 1": 3,
    "컴퓨터공학개론": 3, "Introduction to Computer Engineering": 3,
    "프로그래밍입문(2)": 3, "Introduction to Programming 2": 3,
    "선형대수학": 3, "Linear Algebra": 3,
    "이산수학": 3, "객체지향프로그래밍언어": 3, "Object Oriented Programming Language": 3,
    "유닉스시스템": 3, "Unix System": 3, "확률및랜덤변수": 3, "Probability and Random Variables": 3,
    "자료구조": 3, "Data Structure": 3, "디지털논리및시스템": 3, "Digital Logic and Systems": 3,
    "오픈소스소프트웨어": 3, "Open Source Software": 3, "데이터베이스": 3, "Database": 3, "데이디베이스": 3,
    "알고리즘": 3, "일고리즘": 3, "웹프로그래밍": 3, "데이터통신": 3, "유닉스프로그래밍": 3, "인공지능개론": 3,
    "형식언어및오토마타": 3, "Formal Language and Automata Theory": 3, "컴퓨터네트워크": 3,
    "데이터분석": 3, "시스템프로그래밍": 3, "컴퓨터비전": 3, "운영체제": 3, "정보보호론": 3,
    "기계학습": 3, "Machine Learning": 3, "소프트웨어공학": 3, "Software Engineering": 3,
    "컴퓨터그래픽스": 3, "모바일프로그래밍": 3, "컴퓨터보안": 3, "컴퓨터시스템구조": 3,
    "고급웹프로그래밍": 3, "게임프로그래밍": 3,
    "캡스톤디자인(1)": 3, "강화학습": 3, "Reinforcement Learning": 3,
    "프로그래밍언어론": 3, "Programming Language Theory": 3, "현장실습(1)": 3,
    "자연어처리": 3, "임베디드소프트웨어": 3, "코업(1)": 6, "코업프로젝트(1)": 12,
    "사물인터넷": 3, "차세대암호알고리즘": 3,
    "캡스톤디자인(2)": 3, "현장실습(3)": 3, "블록체인": 3, "컴파일러구조": 3,
    "코업(2)": 6, "코업프로젝트(2)": 12, "고급소프트웨어공학": 3, "데이터마이닝": 3, "데이디마이닝": 3,
    "사이버보안": 3, "빅데이터처리": 3
}

CURRICULUM = {
    "1학년 1학기": ["컴퓨터공학개론", "Introduction to Computer Engineering", "프로그래밍입문(1)", "Introduction to Programming 1"],
    "1학년 2학기": ["선형대수학", "Linear Algebra", "프로그래밍입문(2)", "Introduction to Programming 2"],
    "2학년 1학기": ["이산수학", "객체지향프로그래밍언어", "Object Oriented Programming Language", "유닉스시스템", "Unix System", "확률및랜덤변수", "Probability and Random Variables", "자료구조", "Data Structure", "디지털논리및시스템", "Digital Logic and Systems"],
    "2학년 2학기": ["오픈소스소프트웨어", "Open Source Software", "데이터베이스", "Database", "알고리즘", "웹프로그래밍", "데이터통신", "유닉스프로그래밍", "인공지능개론"],
    "3학년 1학기": ["형식언어및오토마타", "Formal Language and Automata Theory", "컴퓨터네트워크", "데이터분석", "시스템프로그래밍", "컴퓨터비전", "운영체제", "정보보호론"],
    "3학년 2학기": ["기계학습", "Machine Learning", "소프트웨어공학", "Software Engineering", "컴퓨터그래픽스", "모바일프로그래밍", "컴퓨터보안", "컴퓨터시스템구조", "고급웹프로그래밍", "게임프로그래밍"],
    "4학년 1학기": ["캡스톤디자인(1)", "강화학습", "Reinforcement Learning", "프로그래밍언어론", "Programming Language Theory", "현장실습(1)", "자연어처리", "임베디드소프트웨어", "코업(1)", "코업프로젝트(1)", "사물인터넷", "차세대암호알고리즘"],
    "4학년 2학기": ["캡스톤디자인(2)", "현장실습(3)", "블록체인", "컴파일러구조", "코업(2)", "코업프로젝트(2)", "고급소프트웨어공학", "데이터마이닝", "사이버보안", "빅데이터처리"]
}

ALLOWED_SEMESTERS = ["여름학기", "1학기", "2학기", "겨울학기"]

# 비밀번호 규칙: 5~20자 + 특수문자(!@#$%^&*) 1개 이상 (templates/_password_rules.html 과 동일하게 유지)
PASSWORD_MIN_LENGTH = 5
PASSWORD_MAX_LENGTH = 20
PASSWORD_SPECIAL_CHARS = re.compile(r'[!@#$%^&*]')
PASSWORD_RULE_MESSAGE = '비밀번호는 5~20자이며 특수문자(!@#$%^&*)를 1개 이상 포함해야 합니다.'


TERM_ORDER = {'1학기': 1, '여름학기': 2, '2학기': 3, '겨울학기': 4}


def semester_sort_key(semester):
    """'2026년 1학기' -> (2026, 1). 형식이 다르면 맨 뒤로."""
    match = re.match(r'^(\d{4})년\s*(.+)$', semester or '')
    if not match:
        return (0, 0)
    return (int(match.group(1)), TERM_ORDER.get(match.group(2), 9))


def is_valid_password(password):
    return (PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH
            and PASSWORD_SPECIAL_CHARS.search(password) is not None)

init_generated_quiz(app, CURRICULUM)
init_assignments(app, CURRICULUM)
init_study_records(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    student_id = request.form.get('student_id', '').strip()
    name = request.form.get('name', '').strip()
    year = request.form.get('year', '').strip()
    password = request.form.get('password', '').strip()

    if not re.match(r'^[1-9][0-9]{7}$', student_id):
        flash('학번은 0으로 시작하지 않는 8자리 숫자여야 합니다.', 'error')
        return redirect(url_for('index'))

    if not name:
        flash('이름을 입력해주세요.', 'error')
        return redirect(url_for('index'))

    if not year:
        flash('학년을 선택해주세요.', 'error')
        return redirect(url_for('index'))

    # 새로 만드는 계정만 규칙 검사 (규칙 도입 전에 만든 기존 계정은 그대로 로그인 가능)
    if get_student(student_id, password) is None and not is_valid_password(password):
        flash(PASSWORD_RULE_MESSAGE, 'error')
        return redirect(url_for('index'))

    save_or_update_student(student_id, name, year, password)

    account = get_student(student_id, password)
    session.clear()
    session['assignment_owner'] = account['id']
    session['assignment_navigation'] = {'student_id': student_id, 'name': name, 'year': year}
    session['student_id'] = student_id
    session['password'] = password
    session['name'] = name
    session['year'] = year

    return redirect(url_for('scores'))

@app.route('/logout')
def logout():
    session.clear()
    flash('성공적으로 로그아웃되었습니다.', 'success')
    return redirect(url_for('index'))


@app.route('/scores', methods=['GET'])
def scores():
    if 'student_id' not in session or 'password' not in session:
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('index'))

    student_id = session['student_id']
    password = session['password']
    name = session.get('name', '')
    year = session.get('year', '')

    courses = get_all_courses(student_id, password)
    stats = calculate_gpa(courses)

    # 성적 등록 칸 아래 목록: 최근 학기부터, 같은 학기는 과목명 순
    registered_courses = sorted(courses, key=lambda c: c['name'])
    registered_courses.sort(key=lambda c: semester_sort_key(c['semester']), reverse=True)

    # 그래프: 학기별 평점 + 그 학기에 들은 과목 이름 (점에 마우스를 올리면 표시)
    chart_data = [
        {'semester': sem, 'gpa': data['gpa'], 'courses': sorted(c['name'] for c in data['courses'])}
        for sem, data in stats['semesters'].items()
    ]

    return render_template('scores.html', 
                           student_id=student_id, 
                           name=name, 
                           year=year, 
                           stats=stats, 
                           registered_courses=registered_courses,
                           chart_data=chart_data,
                           grades=GRADE_POINTS.keys(),
                           curriculum=CURRICULUM,
                           course_credits=COURSE_CREDITS,
                           allowed_semesters=ALLOWED_SEMESTERS)

@app.route('/manage', methods=['GET'])
def manage():
    if 'student_id' not in session or 'password' not in session:
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('index'))

    student_id = session['student_id']
    password = session['password']
    name = session['name']
    year = session['year']

    selected_search_course = request.args.get('search_course', '').strip()
    search_result_semester = None
    searched = False

    courses = get_all_courses(student_id, password)

    if selected_search_course:
        searched = True
        for c in courses:
            if c['name'] == selected_search_course:
                search_result_semester = c['semester']
                break

    stats = calculate_gpa(courses)

    return render_template('manage.html',
                           student_id=student_id,
                           name=name,
                           year=year,
                           stats=stats,
                           curriculum=CURRICULUM,
                           selected_search_course=selected_search_course,
                           search_result_semester=search_result_semester,
                           searched=searched)

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if 'student_id' not in session or 'password' not in session:
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('index'))

    student_id = session['student_id']
    name = session['name']
    year = session['year']

    result = None

    if request.method == 'POST':
        try:
            def get_float(key, default):
                val = request.form.get(key)
                if val is None or str(val).strip() == '':
                    return default
                return float(val)

            def get_int(key, default):
                val = request.form.get(key)
                if val is None or str(val).strip() == '':
                    return default
                return int(val)

            total_students = get_int('total_students', 40)
            if total_students <= 0:
                flash('수강 인원은 0을 포함하지 않는 양수여야 합니다.', 'error')
                return redirect(url_for('predict'))

            max_score = get_float('max_score', 100)
            if max_score <= 0:
                flash('중간고사 최고 점수는 0보다 커야 합니다.', 'error')
                return redirect(url_for('predict'))

            my_mid = get_float('my_mid', 0)
            if not (0 <= my_mid <= max_score):
                flash(f'내 중간고사 점수는 0부터 {max_score} 사이의 숫자만 입력할 수 있습니다.', 'error')
                return redirect(url_for('predict'))

            mid_mean = get_float('mid_mean', 0)
            if not (0 <= mid_mean <= max_score):
                flash(f'중간고사 평균은 0부터 {max_score} 사이의 숫자만 입력할 수 있습니다.', 'error')
                return redirect(url_for('predict'))

            mid_std = get_float('mid_std', 10)
            if not (0 <= mid_std <= 100):
                flash('중간고사 표준편차는 0부터 100 사이의 숫자만 입력할 수 있습니다.', 'error')
                return redirect(url_for('predict'))
            if mid_std == 0: 
                mid_std = 1.0  
            
            mid_weight = get_float('mid_weight', 40)
            final_weight = get_float('final_weight', 40)

            if mid_weight + final_weight > 100:
                flash('중간 반영과 기말 반영의 합이 100을 초과합니다. 비율을 제대로 적어주세요.', 'error')
                return redirect(url_for('predict'))

            target_grade = request.form.get('target_grade', 'A+')

            cumulative_pcts = {
                'A+': 10.0,
                'A0': 30.0,
                'B+': 50.0,
                'B0': 70.0,
                'C+': 85.0,
                'C0': 100.0
            }

            target_pct = cumulative_pcts.get(target_grade, 30.0)
            target_ratio = target_pct / 100.0

            z_target = norm.ppf(1.0 - target_ratio)
            z_mid = (my_mid - mid_mean) / mid_std

            total_w = mid_weight + final_weight
            w_m = (mid_weight / total_w) if total_w > 0 else 0.5
            w_f = (final_weight / total_w) if total_w > 0 else 0.5

            combined_std_factor = math.sqrt(w_m**2 + w_f**2)
            if w_f > 0:
                z_final = ((z_target * combined_std_factor) - (w_m * z_mid)) / w_f
            else:
                z_final = 0.0

            required_final_score = mid_mean + (z_final * mid_std)
            # 0점 이하일 경우 0점으로 보정
            required_final_score = max(0.0, required_final_score)

            final_cdf = norm.cdf(z_final)
            required_final_rank_ratio = max(0.0, min(1.0, 1.0 - final_cdf))
            required_final_rank = max(1, min(total_students, math.ceil(total_students * required_final_rank_ratio)))

            result = {
                'total_students': total_students,
                'target_grade': target_grade,
                'target_pct': target_pct,
                'required_final_rank': required_final_rank,
                'required_final_score': round(required_final_score, 1),
                'required_final_ratio': round(required_final_rank_ratio * 100, 1)
            }
        except Exception as e:
            print("PREDICT ERROR:", e)
            flash(f'입력값을 올바르게 확인해주세요. (상세: {e})', 'error')

    return render_template('predict.html',
                           student_id=student_id,
                           name=name,
                           year=year,
                           result=result)

@app.route('/quiz')
def quiz():

    student_id = session.get('student_id', '')
    name = session.get('name', '')
    year = session.get('year', '')

    return render_template('quiz.html',
                           student_id=student_id,
                           name=name,
                           year=year,
                           curriculum=CURRICULUM) 

@app.route('/change-password', methods=['POST'])
def change_password():
    if 'student_id' not in session or 'password' not in session:
        return redirect(url_for('index'))
    
    student_id = session['student_id']
    old_password = session['password']
    new_password = request.form.get('new_password', '').strip()

    if not is_valid_password(new_password):
        flash(PASSWORD_RULE_MESSAGE, 'error')
        return redirect(request.referrer or url_for('scores'))

    result = update_student_password(student_id, old_password, new_password)
    if result == 'same':
        flash('현재 비밀번호와 다른 비밀번호를 입력해주세요.', 'error')
        return redirect(request.referrer or url_for('scores'))
    if result == 'taken':
        flash('같은 학번에서 이미 사용 중인 비밀번호입니다. 다른 비밀번호를 입력해주세요.', 'error')
        return redirect(request.referrer or url_for('scores'))
    if result == 'not_found':
        session.clear()
        flash('계정 정보를 찾을 수 없습니다. 다시 로그인해주세요.', 'error')
        return redirect(url_for('index'))

    session['password'] = new_password
    flash('비밀번호가 성공적으로 변경되었습니다.', 'success')
    
    return redirect(request.referrer or url_for('scores'))

@app.route('/add', methods=['POST'])
def add():
    if 'student_id' not in session or 'password' not in session:
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('index'))

    student_id = session['student_id']
    password = session['password']
    name_val = session.get('name', '')
    year = session.get('year', '')

    course_name = request.form.get('name_input', '').strip()
    sel_year = request.form.get('semester_year', '').strip()
    sel_sem = request.form.get('semester_term', '').strip()
    grade = request.form.get('grade', '').strip()

    if not course_name or course_name not in COURSE_CREDITS:
        flash('올바른 과목을 선택해주세요.', 'error')
        return redirect(url_for('scores', student_id=student_id, name=name_val, year=year))

    if not sel_year or not sel_sem or sel_sem not in ALLOWED_SEMESTERS:
        flash('수강 연도와 올바른 학기를 선택해주세요.', 'error')
        return redirect(url_for('scores', student_id=student_id, name=name_val, year=year))

    semester = f"{sel_year}년 {sel_sem}"

    existing_courses = get_all_courses(student_id, password)
    for c in existing_courses:
        if c['name'] == course_name:
            flash(f"이미 등록된 과목입니다: '{course_name}' ({c['semester']})", 'error')
            return redirect(url_for('scores', student_id=student_id, name=name_val, year=year))

    if grade not in GRADE_POINTS:
        flash('올바른 성적 등급을 선택해주세요.', 'error')
        return redirect(url_for('scores', student_id=student_id, name=name_val, year=year))

    credit = COURSE_CREDITS[course_name]
    point = GRADE_POINTS[grade]
    
    add_course(student_id, password, course_name, semester, credit, grade, point)
    flash('과목이 성공적으로 등록되었습니다.', 'success')
    return redirect(url_for('scores', student_id=student_id, name=name_val, year=year))

@app.route('/edit/<int:course_id>', methods=['GET', 'POST'])
def edit(course_id):
    if 'student_id' not in session:
        return redirect(url_for('index'))

    student_id = session['student_id']
    name = session.get('name', '')
    year = session.get('year', '')

    course = get_course_by_id(course_id)
    if not course or course['student_id'] != student_id or course['password'] != session['password']:
        flash('존재하지 않거나 권한이 없는 과목입니다.', 'error')
        return redirect(url_for('manage'))


    curr_year = "2026"
    curr_term = "1학기"
    if course and ' ' in course['semester']:
        parts = course['semester'].split(' ')
        curr_year = parts[0].replace('년', '')
        curr_term = parts[1]

    if request.method == 'POST':
        c_name = request.form.get('name_input', '').strip()
        sel_year = request.form.get('semester_year', '').strip()
        sel_sem = request.form.get('semester_term', '').strip()
        grade = request.form.get('grade', '').strip()

        if not c_name or c_name not in COURSE_CREDITS:
            flash('올바른 과목을 선택해주세요.', 'error')
            return redirect(url_for('edit', course_id=course_id, student_id=student_id, name=name, year=year))

        if not sel_year or not sel_sem or sel_sem not in ALLOWED_SEMESTERS:
            flash('수강 연도와 올바른 학기를 선택해주세요.', 'error')
            return redirect(url_for('edit', course_id=course_id, student_id=student_id, name=name, year=year))

        semester = f"{sel_year}년 {sel_sem}"
    
        existing_courses = get_all_courses(student_id, session['password'])
        for c in existing_courses:
            if c['id'] != course_id and c['name'] == c_name:
                flash(f"이미 등록된 과목입니다: '{c_name}' ({c['semester']})", 'error')
                return redirect(url_for('edit', course_id=course_id, student_id=student_id, name=name, year=year))

        if grade not in GRADE_POINTS:
            flash('올바른 성적 등급을 선택해주세요.', 'error')
            return redirect(url_for('edit', course_id=course_id, student_id=student_id, name=name, year=year))

        credit = COURSE_CREDITS[c_name]
        point = GRADE_POINTS[grade]
        
        update_course(course_id, c_name, semester, credit, grade, point)
        flash('과목 정보가 수정되었습니다.', 'success')

        return redirect(url_for('manage'))

    return render_template('edit.html', course=course, grades=GRADE_POINTS.keys(), student_id=student_id, name=name, year=year, curriculum=CURRICULUM, course_credits=COURSE_CREDITS, allowed_semesters=ALLOWED_SEMESTERS, curr_year=curr_year, curr_term=curr_term)

@app.route('/delete/<int:course_id>', methods=['POST'])
def delete(course_id):
    if 'student_id' not in session:
        return redirect(url_for('index'))

    course = get_course_by_id(course_id)
    if course and course['student_id'] == session['student_id'] and course['password'] == session['password']:
        delete_course(course_id)
        flash('과목이 삭제되었습니다.', 'success')
    
    return redirect(url_for('manage'))

if __name__ == '__main__':
    app.run(debug=True)