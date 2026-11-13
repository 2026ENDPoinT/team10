# team10 · 대학생 성적·학습 관리 프로그램

ENDPoinT 해커톤 2026 Team 10

**주제: 성적 관리 소프트웨어 구현.** 성적 관리를 중심으로 기말고사 목표 예측, AI 퀴즈, AI 학습 파트너, 과제 관리 같은 학습 보조 기능을 더한 Flask 웹 애플리케이션입니다. 모든 화면은 한국어/영어 전환을 지원합니다.

---

## 주요 기능

| 화면 | 주소 | 기능 |
|---|---|---|
| 첫 화면 · 로그인 | `/` | 기능 소개와 로그인. 학번 + 비밀번호 조합마다 독립된 성적 데이터가 관리됩니다. |
| 성적 | `/scores` | 과목·수강 연도·학기·등급을 등록하면 학점이 자동 입력됩니다. 전체 평점(4.5 만점), 총 학점, 등록한 과목 목록을 보여 주고, 학기별 평점 추이 그래프를 그립니다. 그래프의 점에 마우스를 올리면 그 학기의 과목이 표시됩니다. |
| 관리 | `/manage` | 과목을 검색해 수강 학기를 확인하고, 학기별 과목을 수정·삭제합니다. 같은 과목은 중복 등록되지 않습니다. |
| 예측 | `/predict` | 수강 인원, 중간고사 점수·평균·표준편차, 반영 비율, 목표 등급을 입력하면 정규분포를 바탕으로 기말고사에서 필요한 점수와 석차를 계산합니다. |
| 퀴즈 | `/quiz` | 과목과 학습 주제(필수)를 입력하면 AI가 객관식 1~5문제를 만듭니다. 서버에서 채점한 뒤 해설을 보여 줍니다. 틀린 문제는 **저장된 오답**(최대 10개)에 자동 저장되고, AI 학습 파트너로 넘겨 복습할 수 있습니다. |
| AI | `/ai/` | 한국어/영어 AI 튜터입니다. 개념 설명, 힌트, 연습 문제, 추천 강의 찾기를 도와줍니다. 퀴즈 결과를 받아 오답 복습과 강점·보완점 분석을 하며, 최근 대화 3개를 **저장된 대화**에 자동 저장합니다. |
| 과제 | `/assignments/` | 과목별 과제를 마감(한국 시간)·중요도·예상 작업 시간·체크리스트와 함께 등록합니다. D-day 표시, 마감 임박 알림, 진행률, **AI랑 계획하기**를 지원합니다. |

**공통 기능**

- **다이나믹 아일랜드:** 화면 위에 고정된 메뉴입니다. 이름 첫 글자 버튼에 마우스를 올리면 학년·학번·이름과 비밀번호 변경·로그아웃이 나옵니다.
- **KOR / ENG 전환:** 선택한 언어는 쿠키에 저장됩니다. 번역은 `static/translations.json`에서 관리합니다.
- **비밀번호 규칙:** 5~20자이며 특수문자(`!@#$%^&*`)를 1개 이상 포함해야 합니다. 로그인 칸과 비밀번호 변경 창에 조건이 표시됩니다. 규칙 도입 전에 만든 계정은 그대로 로그인할 수 있습니다.

---

## 실행 방법 (Windows · VS Code)

### 1. Python 환경 준비 (처음 한 번)

```powershell
py -3.15 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install scipy
```

> `scipy`는 예측 기능(`scipy.stats.norm`)에 필요하지만 아직 `requirements.txt`와 `requirements-lock.txt`에 들어 있지 않아 따로 설치해야 합니다.

`START_APP.cmd`를 더블클릭해도 됩니다. `.venv`가 없으면 만들고 `requirements-lock.txt`를 설치합니다. 이때도 `scipy`는 위 명령으로 따로 설치해야 합니다.

### 2. `.env` 설정

`.env.example`을 `.env`로 복사한 뒤 값을 채웁니다. `.env`는 Git에 올리지 않습니다.

| 변수 | 설명 |
|---|---|
| `AI_MODE` | `groq`(기본), `gemini`, `openai`, `demo` 중 하나. AI 퀴즈 생성은 `groq`에서만 동작합니다. |
| `GROQ_API_KEY` / `GROQ_MODEL` | Groq 키와 모델(기본 `openai/gpt-oss-120b`). 모델 이름에 `openai/`가 있어도 Groq 키를 사용합니다. |
| `GEMINI_API_KEY`, `OPENAI_API_KEY` | 다른 AI 모드를 사용할 때만 필요합니다. |
| `YOUTUBE_API_KEY` | 선택 사항. 있으면 추천 강의 카드를, 없으면 YouTube 검색 링크를 보여 줍니다. |
| `FLASK_SECRET_KEY` | 긴 임의 문자열. 비워 두면 서버를 재시작할 때마다 다시 로그인해야 합니다. |

Groq 키 발급 방법과 문제 해결은 [AI_SETUP.md](AI_SETUP.md)를 참고하세요.

### 3. 서버 실행

```powershell
.\.venv\Scripts\python.exe app.py
```

브라우저에서 **http://127.0.0.1:5000** 을 엽니다. 서버가 실행되는 동안 터미널을 열어 둡니다.

> `app.py`는 `app.run(debug=True)`로 실행되므로 기본 포트는 **5000**입니다. `.env`의 `PORT` 값과 `START_APP.cmd`, `SETUP.md`에 적힌 5002는 현재 코드에 반영되어 있지 않습니다.

---

## 데이터 저장

모든 데이터는 SQLite로 저장됩니다. DB 파일은 `.gitignore`에 포함되어 있어 커밋되지 않습니다.

| 파일 | 테이블 | 내용 |
|---|---|---|
| `database.db` (실행 위치) | `students` | 계정. 기본키가 `(student_id, password)`이므로 같은 학번이라도 비밀번호가 다르면 별도의 성적 셋입니다. |
| | `courses` | 과목·학기·학점·등급·평점 |
| | `wrong_answers` | 퀴즈 오답 노트. 계정당 최근 10개, 같은 문제는 중복 없이 갱신됩니다. |
| | `chat_conversations` | AI 대화 기록. 계정당 최근 3개가 남습니다. |
| `data/assignments.db` | `assignments` | 과제, 체크리스트, 예상 시간 |
| `data/ai_quizzes.db` | `quizzes` | 생성된 AI 퀴즈의 정답·해설. 브라우저 세션에 연결되며 24시간 후 삭제됩니다. |

- 성적·오답·대화는 **학번과 비밀번호가 모두 일치할 때만** 조회하고 수정할 수 있습니다.
- 비밀번호를 바꾸면 과목·오답·대화가 새 비밀번호로 함께 옮겨집니다.
- 같은 학번의 다른 성적 셋이 이미 쓰는 비밀번호로는 바꿀 수 없습니다.

---

## 폴더 구조

```
team10/
├── app.py                  # Flask 앱: 로그인, 성적·관리·예측·퀴즈 라우트, 비밀번호 규칙, 교과과정(CURRICULUM)
├── database.py             # SQLite: 계정·과목·오답 노트·AI 대화 저장
├── gpa_calculator.py       # 등급별 평점(GRADE_POINTS)과 전체·학기별 평점 계산
├── assignments.py          # 과제 관리 블루프린트 (/assignments/)
├── study_records.py        # 오답 노트·AI 대화 저장 API (/api/...)
├── localization.py         # 한국어/영어 번역 (t(), ui_text 필터)
├── study_ai/               # AI 학습 파트너 모듈 (/ai/)
│   ├── __init__.py         #   채팅 화면·채팅 API 등록
│   ├── service.py          #   AI 요청 구성 (Groq / Gemini / OpenAI / demo)
│   ├── groq.py, gemini.py  #   제공자별 API 호출
│   ├── generated_quiz.py   #   AI 퀴즈 생성·채점, 오답 자동 저장
│   ├── resources.py        #   YouTube 추천 강의 검색
│   ├── validation.py       #   요청 데이터 검증
│   ├── templates/study_ai/chat.html
│   └── static/             #   chat.js, chat.css, quiz-bridge.js(퀴즈 → AI 연결)
├── templates/              # 화면 (Jinja2)
│   ├── index.html          #   첫 화면 · 로그인
│   ├── scores.html, manage.html, edit.html, predict.html, quiz.html, assignments.html
│   └── island.html, _footer.html, _password_rules.html, _assignment_notice.html,
│       _language_button.html, _language_assets.html   # 공통 조각
├── static/
│   ├── css/style.css       # 공통 디자인 시스템
│   ├── js/                 # main.js(그래프), quiz.js, language.js, assignment-*.js
│   └── translations.json   # 한국어 → 영어 번역표
├── tests/                  # unittest(Python) + Node 테스트
├── requirements.txt / requirements-lock.txt
├── .env.example            # 환경 변수 예시 (실제 키는 .env 에만)
├── START_APP.cmd           # Windows 실행 스크립트
└── SETUP.md, AI_SETUP.md, FEATURE.md, KEY.md   # 이전 단계의 설정·개발 메모
```

---

## API 요약

| 방식 | 주소 | 설명 |
|---|---|---|
| POST | `/login`, `/logout`, `/change-password` | 로그인·로그아웃·비밀번호 변경 |
| POST | `/add`, `/edit/<id>`, `/delete/<id>` | 과목 등록·수정·삭제 |
| POST | `/ai/api/chat` | AI 학습 파트너 질문 |
| POST | `/ai/api/quiz/generate`, `/ai/api/quiz/grade` | AI 퀴즈 생성(15초 간격 제한)·채점 |
| GET | `/ai/api/health` | AI 설정 상태 확인 |
| GET / POST | `/api/wrong-answers`, `/api/wrong-answers/<id>/delete` | 저장된 오답 조회·삭제 (로그인 필요) |
| GET / POST | `/api/conversations`, `/api/conversations/<id>/delete` | 저장된 대화 조회·저장·삭제 (로그인 필요) |

JSON API는 같은 사이트에서 보낸 요청만 받습니다. 다른 Origin에서 보낸 요청은 403으로 거절합니다.



## 알려진 제한

- AI 퀴즈와 답변은 일반적인 과목 내용을 바탕으로 생성되므로 실제 수업 범위와 다르거나 틀릴 수 있습니다. AI는 성적 데이터를 수정하지 않습니다.
- 오답 노트와 저장된 대화는 개수 제한(10개 / 3개)을 넘으면 가장 오래된 항목부터 자동으로 지워집니다.

---

## 팀원

| 이름 | 역할 |
|---|---|
| 권민준 | 팀원, UI제작 및 기타 코드 제작 |
| 김준호 | 팀장, 기본 파일 제작 및 기타 코드 제작 |
| 조셉 커리지 | AI 연동 코드 제작 및 기타 코드 제작 |

