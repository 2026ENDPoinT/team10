# team10
ENDPoinT 해커톤 2026 Team 10

---
*구현과제*

**주제: 성적 관리 소프트웨어 구현**

성적을 관리하는 핵심 기능을 구현하고, 필요에 따라 개인 학습·강의 관련 보조 기능을 추가할 수 있습니다.

필수 구현 범위와 세부 안내는 운영진 공지를 확인해 주세요.

---

**파일 예시**

```
team10/
│
├── app.py                    # Flask 서버 실행 및 페이지 라우팅
├── database.py               # 데이터베이스 연결 및 관리
├── requirements.txt          # 프로젝트에 필요한 Python 라이브러리
├── README.md                 # 프로젝트 소개 및 실행 방법
├── Plan.md                   # 프로젝트 목표 및 개발 계획
├── STRUCTURE.md              # 전체 파일 구조 및 역할 설명
│
├── docs/                     # 개발 관련 문서
│   ├── Backend.md            # 백엔드 개발 규칙 및 구조
│   ├── Frontend.md           # 프론트엔드 개발 규칙 및 구조
│   ├── Database.md           # 데이터베이스 설계
│   └── API.md                # 프론트엔드와 백엔드 간 통신 규칙
│
├── templates/                # HTML 페이지
│   ├── index.html            # 메인 페이지
│   ├── scores.html           # 성적 입력 및 조회
│   ├── recommendations.html  # 강의 추천 페이지
│   ├── quiz.html             # 학습 퀴즈 페이지
│   ├── game.html             # 미니게임 페이지
│   └── ai_solver.html        # AI 문제 풀이 페이지
│
├── static/                   # CSS, JavaScript, 이미지
│   ├── css/
│   │   └── style.css         # 공통 스타일
│   │
│   ├── js/
│   │   ├── main.js           # 공통 JavaScript
│   │   ├── quiz.js           # 퀴즈 기능
│   │   └── game.js           # 미니게임 기능
│   │
│   └── img/                  # 이미지 및 아이콘
│
├── services/                 # 주요 기능별 처리 로직
│   ├── recommendation.py     # 강의 추천 알고리즘
│   └── ai_solver.py          # AI 문제 풀이 처리
│
└── data/                     # 데이터 저장
    └── scores.db             # SQLite 데이터베이스 (자동 생성)
```

---
| 이름 | 역할 |
|---|---|
| 권민준 | 미정 |
| 김준호 | 미정 |
| 조셉 커리지 | 미정 |