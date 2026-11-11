# 4.5 만점 기준 성적 등급별 평점 맵핑
GRADE_POINTS = {
    'A+': 4.5, 'A0': 4.0,
    'B+': 3.5, 'B0': 3.0,
    'C+': 2.5, 'C0': 2.0,
    'D+': 1.5, 'D0': 1.0,
    'F': 0.0
}

def calculate_gpa(courses):
    """
    수강 과목 리스트를 받아 학기별/전체 평점평균과 학점 수를 계산하는 함수
    """
    total_credits = 0
    total_grade_points = 0.0
    
    # 학기별 데이터를 저장할 딕셔너리
    semester_data = {}

    for course in courses:
        credit = course['credit']
        point = course['point']
        semester = course['semester']

        # 전체 누적 평점 및 학점 계산을 위한 누적
        total_credits += credit
        total_grade_points += (credit * point)

        # 학기별 학점 및 평점 계산을 위한 데이터 분류
        if semester not in semester_data:
            semester_data[semester] = {
                'credits': 0,
                'grade_points': 0.0,
                'courses': []
            }
        semester_data[semester]['credits'] += credit
        semester_data[semester]['grade_points'] += (credit * point)
        semester_data[semester]['courses'].append(course)

    # 전체 누적 평점 평균 계산 (소수점 둘째 자리까지 반올림)
    overall_gpa = round(total_grade_points / total_credits, 2) if total_credits > 0 else 0.0

    # 학기별 평점 평균 계산
    formatted_semesters = {}
    for sem, data in semester_data.items():
        sem_gpa = round(data['grade_points'] / data['credits'], 2) if data['credits'] > 0 else 0.0
        formatted_semesters[sem] = {
            'gpa': sem_gpa,
            'credits': data['credits'],  # 학기별 등록 학점 수
            'courses': data['courses']
        }

    return {
        'overall_gpa': overall_gpa,       # 전체 누적 평점 평균
        'total_credits': total_credits,   # 전체 등록 학점 수
        'semesters': formatted_semesters  # 학기별 상세 정보 (평점, 학점, 과목 목록)
    }