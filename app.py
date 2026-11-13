import re
import os
import secrets
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session
from study_ai import init_study_ai
from database import init_db, get_all_courses, get_course_by_id, add_course, update_course, delete_course
from gpa_calculator import GRADE_POINTS, calculate_gpa

# This local app uses its own settings even when VS Code inherits older values.
load_dotenv(Path(__file__).with_name('.env'), override=True)
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or secrets.token_hex(32)
app.config.update(AI_MODE=os.getenv('AI_MODE', 'groq'), STUDY_BACK_ENDPOINT='scores',
                  MAX_CONTENT_LENGTH=128 * 1024)
init_study_ai(app)


@app.before_request
def remember_study_navigation():
    # Local navigation only. Student identity is never added to AI requests.
    if request.endpoint in ('scores', 'quiz'):
        student_id = request.args.get('student_id', '')
        if re.fullmatch(r'[1-9][0-9]{7}', student_id):
            session['study_navigation'] = {'student_id': student_id,
                'name': request.args.get('name', '')[:100], 'year': request.args.get('year', '')[:10]}

init_db()

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

from study_ai.generated_quiz import init_generated_quiz
init_generated_quiz(app, CURRICULUM)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scores')
def scores():
    student_id = request.args.get('student_id', '').strip()
    name = request.args.get('name', '').strip()
    year = request.args.get('year', '').strip()

    if not re.match(r'^[1-9][0-9]{7}$', student_id):
        flash('학번은 0으로 시작하지 않는 8자리 숫자여야 합니다.', 'error')
        return redirect(url_for('index'))

    courses = get_all_courses(student_id)
    stats = calculate_gpa(courses)

    return render_template('scores.html', 
                           student_id=student_id, 
                           name=name, 
                           year=year, 
                           stats=stats, 
                           grades=GRADE_POINTS.keys(),
                           curriculum=CURRICULUM,
                           course_credits=COURSE_CREDITS,
                           allowed_semesters=ALLOWED_SEMESTERS)

@app.route('/quiz')
def quiz():
    # 학습 퀴즈 페이지 (학생 정보 유지)
    student_id = request.args.get('student_id', '')
    name = request.args.get('name', '')
    year = request.args.get('year', '')

    return render_template('quiz.html',
                           student_id=student_id,
                           name=name,
                           year=year,
                           curriculum=CURRICULUM) 

@app.route('/add', methods=['POST'])
def add():
    student_id = request.form.get('student_id', '')
    name_val = request.form.get('name', '')
    year = request.form.get('year', '')

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

    # 이미 등록된 과목인지 전체 기간 내에서 중복 검사 (등록된 연도/학기 함께 표시)
    existing_courses = get_all_courses(student_id)
    for c in existing_courses:
        if c['name'] == course_name:
            flash(f"이미 등록된 과목입니다: '{course_name}' ({c['semester']})", 'error')
            return redirect(url_for('scores', student_id=student_id, name=name_val, year=year))

    if grade not in GRADE_POINTS:
        flash('올바른 성적 등급을 선택해주세요.', 'error')
        return redirect(url_for('scores', student_id=student_id, name=name_val, year=year))

    credit = COURSE_CREDITS[course_name]
    point = GRADE_POINTS[grade]
    
    add_course(student_id, course_name, semester, credit, grade, point)
    flash('과목이 성공적으로 등록되었습니다.', 'success')
    return redirect(url_for('scores', student_id=student_id, name=name_val, year=year))

@app.route('/edit/<int:course_id>', methods=['GET', 'POST'])
def edit(course_id):
    course = get_course_by_id(course_id)
    if not course:
        flash('존재하지 않는 과목입니다.', 'error')
        return redirect(url_for('index'))

    student_id = request.args.get('student_id', '') or request.form.get('student_id', '')
    name = request.args.get('name', '') or request.form.get('name', '')
    year = request.args.get('year', '') or request.form.get('year', '')

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

        # 수정 시 자기 자신을 제외하고 이미 등록된 동일 과목이 있는지 전체 기간 내에서 검사
        existing_courses = get_all_courses(student_id)
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
        return redirect(url_for('scores', student_id=student_id, name=name, year=year))

    return render_template('edit.html', course=course, grades=GRADE_POINTS.keys(), student_id=student_id, name=name, year=year, curriculum=CURRICULUM, course_credits=COURSE_CREDITS, allowed_semesters=ALLOWED_SEMESTERS, curr_year=curr_year, curr_term=curr_term)

@app.route('/delete/<int:course_id>', methods=['POST'])
def delete(course_id):
    student_id = request.form.get('student_id', '')
    name = request.form.get('name', '')
    year = request.form.get('year', '')

    delete_course(course_id)
    flash('과목이 삭제되었습니다.', 'success')
    return redirect(url_for('scores', student_id=student_id, name=name, year=year))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.getenv('PORT', '5002')), debug=False)
