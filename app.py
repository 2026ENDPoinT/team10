#Flask 서버 및 기능 처리
from flask import Flask, render_template, request, redirect, url_for, flash
from database import init_db, get_all_courses, get_course_by_id, add_course, update_course, delete_course
from gpa_calculator import GRADE_POINTS, calculate_gpa

app = Flask(__name__)
app.secret_key = 'super_secret_key'

init_db()

@app.route('/')
def index():
    # 조건 1: 학번, 이름, 학년 입력 메인 페이지
    return render_template('index.html')

@app.route('/scores')
def scores():
    # 성적 입력 및 조회 페이지 (학생 정보 유지)
    student_id = request.args.get('student_id', '')
    name = request.args.get('name', '')
    year = request.args.get('year', '')

    courses = get_all_courses()
    stats = calculate_gpa(courses)

    return render_template('scores.html', 
                           student_id=student_id, 
                           name=name, 
                           year=year, 
                           stats=stats, 
                           grades=GRADE_POINTS.keys())

@app.route('/quiz')
def quiz():
    # 학습 퀴즈 페이지 (학생 정보 유지)
    student_id = request.args.get('student_id', '')
    name = request.args.get('name', '')
    year = request.args.get('year', '')

    return render_template('quiz.html',
                           student_id=student_id,
                           name=name,
                           year=year)

@app.route('/add', methods=['POST'])
def add():
    student_id = request.form.get('student_id', '')
    name_val = request.form.get('name', '')
    year = request.form.get('year', '')

    name = request.form.get('name_input', '').strip()
    semester = request.form.get('semester', '').strip()
    credit_str = request.form.get('credit', '').strip()
    grade = request.form.get('grade', '').strip()

    # 예외 처리 1: 과목명 또는 수강 학기 미입력
    if not name or not semester:
        flash('과목명과 수강 학기를 모두 입력해주세요.', 'error')
        return redirect(url_for('scores', student_id=student_id, name=name_val, year=year))

    # 예외 처리 2: 학점 수가 숫자가 아니거나 0 이하인 경우
    try:
        credit = int(credit_str)
        if ((credit <= 0) or (credit > 7)):
            raise ValueError
    except ValueError:
        flash('올바른 학점 수를 입력해주세요.', 'error')
        return redirect(url_for('scores', student_id=student_id, name=name_val, year=year))

    # 예외 처리 3: 지원하지 않는 성적 등급
    if grade not in GRADE_POINTS:
        flash('올바른 성적 등급을 선택해주세요.', 'error')
        return redirect(url_for('scores', student_id=student_id, name=name_val, year=year))

    point = GRADE_POINTS[grade]
    add_course(name, semester, credit, grade, point)
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

    if request.method == 'POST':
        c_name = request.form.get('name', '').strip()
        semester = request.form.get('semester', '').strip()
        credit_str = request.form.get('credit', '').strip()
        grade = request.form.get('grade', '').strip()

        if not c_name or not semester:
            flash('과목명과 수강 학기를 모두 입력해주세요.', 'error')
            return redirect(url_for('edit', course_id=course_id, student_id=student_id, name=name, year=year))

        try:
            credit = int(credit_str)
            if (credit <= 0)&(credit >=7):
                raise ValueError
        except ValueError:
            flash('학점 수는 0보다 큰 정수로 입력해주세요.', 'error')
            return redirect(url_for('edit', course_id=course_id, student_id=student_id, name=name, year=year))

        if grade not in GRADE_POINTS:
            flash('올바른 성적 등급을 선택해주세요.', 'error')
            return redirect(url_for('edit', course_id=course_id, student_id=student_id, name=name, year=year))

        point = GRADE_POINTS[grade]
        update_course(course_id, c_name, semester, credit, grade, point)
        flash('과목 정보가 수정되었습니다.', 'success')
        return redirect(url_for('scores', student_id=student_id, name=name, year=year))

    return render_template('edit.html', course=course, grades=GRADE_POINTS.keys(), student_id=student_id, name=name, year=year)

@app.route('/delete/<int:course_id>', methods=['POST'])
def delete(course_id):
    student_id = request.form.get('student_id', '')
    name = request.form.get('name', '')
    year = request.form.get('year', '')

    delete_course(course_id)
    flash('과목이 삭제되었습니다.', 'success')
    return redirect(url_for('scores', student_id=student_id, name=name, year=year))

if __name__ == '__main__':
    app.run(debug=True)
