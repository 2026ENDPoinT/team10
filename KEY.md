1. Flask 백엔드 (app.py) 및 전역 상수
상수 및 설정

app: Flask 앱 인스턴스

COURSE_CREDITS: 과목명과 학점이 매핑된 딕셔너리 (예: "프로그래밍입문(1)": 3)

CURRICULUM: 학년/학기별 개설 과목 목록 딕셔너리 (예: "1학년 1학기": [...])

ALLOWED_SEMESTERS: 허용된 학기 목록 리스트 (["여름학기", "1학기", "2학기", "겨울학기"])

라우트 함수 내 주요 변수 및 요청 파서

student_id: 학번 (문자열, 8자리 정규식 검증)

name, name_val, c_name, course_name: 학생 이름 또는 과목명

year: 학년 (1~4)

sel_year, curr_year: 수강 연도 (예: "2026")

sel_sem, curr_term, semester: 수강 학기 (예: "1학기", 형식: "2026년 1학기")

grade: 성적 등급 (예: "A+", "B0" 등)

credit: 과목 학점 (정수)

point: 성적 평점 (실수, 예: 4.5)

stats: 전체 및 학기별 성적 통계 딕셔너리 (overall_gpa, total_credits, semesters 포함)

courses, existing_courses: 과목 데이터 리스트

2. 데이터베이스 (database.py 및 테이블 스키마)
상수 및 연결

DB_NAME: 데이터베이스 파일명 ("database.db")

conn: SQLite 커넥션 객체

courses 테이블 컬럼명 (데이터 추가/수정/조회 시 정확히 일치해야 함)

id: 기본키, 자동 증가 정수 (INTEGER PRIMARY KEY AUTOINCREMENT)

student_id: 학번 (TEXT NOT NULL)

name: 과목명 (TEXT NOT NULL)

semester: 수강 학기 (TEXT NOT NULL, 예: "2026년 1학기")

credit: 학점 (INTEGER NOT NULL)

grade: 등급 (TEXT NOT NULL, 예: "A0")

point: 평점 (REAL NOT NULL, 예: 4.0)

3. 성적 계산 모듈 (gpa_calculator.py)
상수 및 변수

GRADE_POINTS: 등급별 평점 맵핑 딕셔너리 ('A+': 4.5, 'A0': 4.0, ..., 'F': 0.0)

calculate_gpa(courses) 함수의 내부 및 반환 변수

total_credits: 전체 누적 학점 합계

total_grade_points: (학점 × 평점) 총합

semester_data: 학기별 상세 데이터를 누적하는 딕셔너리

overall_gpa: 전체 누적 평점 평균 (소수점 둘째 자리 반올림)

formatted_semesters: 반환 딕셔너리의 semesters 키에 들어가는 학기별 정리 데이터 (gpa, credits, courses 포함)

4. HTML 폼 입력 (name 속성) 및 템플릿 변수
팀원들이 데이터를 전송(POST / GET)하거나 템플릿에서 출력할 때 사용하는 이름들입니다.

메인 페이지 (index.html) 입력 필드

student_id: 학번 입력 (<input name="student_id">)

name: 이름 입력 (<input name="name">)

year: 학년 선택 (<select name="year">)

성적 등록 및 수정 폼 (scores.html, edit.html) 입력 필드

name_input: 과목명 선택 드롭다운 (<select name="name_input">)

semester_year: 수강 연도 선택 (<select name="semester_year">)

semester_term: 수강 학기 선택 (<select name="semester_term">)

credit: 학점 필드 (<input name="credit">, 자동 입력 및 readonly)

grade: 성적 등급 선택 (<select name="grade">)

Jinja2 템플릿 출력 변수 (scores.html, edit.html에서 사용)

{{ student_id }}, {{ name }}, {{ year }}

{{ stats.overall_gpa }}, {{ stats.total_credits }}

{{ stats.semesters }} (반복문 내에서 semester, data.gpa, data.credits, data.courses 접근)

{{ course.id }}, {{ course.name }}, {{ course.credit }}, {{ course.grade }}, {{ course.point }}

{{ curriculum }} (course_credits[c]와 함께 과목 및 학점 렌더링에 사용)

{{ allowed_semesters }}

{{ grades }}
