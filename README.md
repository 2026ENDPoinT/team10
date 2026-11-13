# team10 · 대학생 성적·학습 관리 프로그램

ENDPoinT 해커톤 2026 Team 10
https://team10-2e07.onrender.com

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

## 데이터 저장 (Render)

배포 환경에서는 로컬 `.db` 파일 대신 **Render 무료 플랜**을 사용합니다.

| 구성 요소 | Render 서비스 | 역할 |
|---|---|---|
| 웹 서버 | **Web Service (Free)** | Flask 앱을 `gunicorn`으로 실행합니다. GitHub 저장소와 연결되어 push할 때마다 자동 배포됩니다. |
| 데이터베이스 | **Render Postgres (Free)** | 계정·성적·오답·대화·과제·AI 퀴즈를 PostgreSQL 데이터베이스 하나에 저장합니다. |

**SQLite 파일을 쓰지 않는 이유:** Render 무료 Web Service의 파일 시스템은 임시 저장소입니다. 재배포·재시작·휴면(spin-down) 때 서버에 만든 파일이 모두 사라지고, 무료 플랜에서는 영구 디스크(Persistent Disk)를 붙일 수 없습니다. 그래서 `database.db`나 `data/*.db`에 저장하면 데이터가 유지되지 않습니다.

### 테이블

무료 Postgres는 워크스페이스당 1개만 만들 수 있으므로, 기존 DB 파일 3개의 테이블을 데이터베이스 하나에 모읍니다.

| 테이블 | 내용 | 기존 위치 |
|---|---|---|
| `students` | 계정. `id`(기본키), `student_id`(학번), `password_key`(비밀번호로 만든 키), 이름, 학년. `(student_id, password_key)`가 UNIQUE라서 학번·비밀번호 조합마다 별도의 계정입니다. | `database.db` |
| `courses` | 과목·학기·학점·등급·평점 | `database.db` |
| `wrong_answers` | 퀴즈 오답 노트. 계정당 최근 10개, 같은 문제는 중복 없이 갱신됩니다. | `database.db` |
| `chat_conversations` | AI 대화 기록. 계정당 최근 3개가 남습니다. | `database.db` |
| `assignments` | 과제, 체크리스트, 예상 시간 | `data/assignments.db` |
| `quizzes` | 생성된 AI 퀴즈의 정답·해설. 브라우저 세션에 연결되며 24시간 후 삭제됩니다. | `data/ai_quizzes.db` |

- 앱은 Render가 발급하는 **Internal Database URL**을 환경 변수 `DATABASE_URL`로 받아 접속합니다.
- 테이블은 앱이 시작할 때 자동으로 만들어집니다(`database.py`의 `init_db()`). SQL을 따로 실행할 필요가 없습니다.
- 계정과 데이터 접근 규칙
  - **학번 + 비밀번호 조합마다 별도의 계정(성적 셋)입니다.** 예: 학번 22222222에 비밀번호 `!!!!!`와 `@@@@@`는 서로 다른 계정입니다. 처음 쓰는 조합으로 로그인하면 새 계정이 만들어집니다(이때 비밀번호 규칙을 검사합니다).
  - 비밀번호는 평문으로 저장하지 않습니다. `scrypt(비밀번호, salt = PASSWORD_PEPPER + 학번)`으로 만든 키(`password_key`)만 저장하며, 같은 조합이면 항상 같은 키가 나와서 계정을 찾을 수 있습니다. 세션 쿠키에는 비밀번호를 넣지 않습니다(세션에는 `user_id`만).
  - 성적·오답·대화·과제는 로그인한 계정(`user_id`)의 자료만 조회하고 수정할 수 있습니다. 비밀번호를 바꿔도 자료는 그대로 유지되며, 같은 학번의 다른 계정이 쓰는 비밀번호로는 바꿀 수 없습니다.
  - 예전 계정 구조의 테이블은 시작할 때 지우지 않고 `legacy_*` 이름으로 보관합니다.

### 로컬 개발과 테스트

모든 데이터 접근은 `database.py` 한 곳에서 합니다. SQL은 `?` 자리표시자로 작성하며, PostgreSQL에서는 자동으로 `%s`로 바뀝니다.

- `DATABASE_URL`이 **없으면** `data/database.db` SQLite 파일을 씁니다. 노트북에서는 지금처럼 설치 없이 실행됩니다. `data/`는 `.gitignore`에 있어 커밋되지 않습니다.
- 예전 구조(평문 비밀번호)의 로컬 SQLite 테이블은 지우지 않고 `legacy_*` 이름으로 보관합니다.
- 테스트는 임시 SQLite로 돌고, `TEST_DATABASE_URL`을 주면 그 PostgreSQL로 돕니다. 테이블을 비우므로 운영 DB 주소를 넣으면 안 됩니다.

### 무료 Postgres 주의 사항

- **만료:** 무료 데이터베이스는 **생성 후 30일**이 지나면 만료되어 접속할 수 없습니다. 만료 후 **14일 안에** 유료 플랜으로 올리지 않으면 데이터와 함께 삭제됩니다.
- **백업:** 시연이나 제출 일정에 맞춰 만들고, 필요하면 만료 전에 백업합니다(`pg_dump` 또는 Render 대시보드의 백업 기능).
- **용량:** 저장 용량은 **1GB** 고정입니다.

---

## Render 배포 방법

### 1. 데이터베이스 만들기

1. [Render 대시보드](https://dashboard.render.com)에서 **New → Postgres**를 선택합니다.
2. 이름을 정하고 Instance Type을 **Free**로 선택한 뒤 만듭니다.
3. 데이터베이스 화면의 **Connections**에서 **Internal Database URL**을 복사합니다. 같은 Render 지역의 서비스끼리 연결할 때 사용하는 주소입니다.

### 2. 웹 서비스 만들기

**New → Web Service**에서 이 GitHub 저장소를 연결하고 다음과 같이 설정합니다.

| 항목 | 값 |
|---|---|
| Language | Python 3 |
| Branch | 배포할 브랜치 (예: `main`) |
| Region | 데이터베이스와 같은 지역 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app` |
| Instance Type | **Free** |

`gunicorn app:app`은 `app.py`의 `app` 객체를 실행합니다. `app.run(debug=True)`는 직접 `python app.py`로 실행할 때만 동작하므로, Render에서는 디버그 모드가 켜지지 않습니다.

### 3. 환경 변수 설정

`.env` 파일은 Git에 올리지 않으므로 Render에 올라가지 않습니다. 웹 서비스의 **Environment** 탭에 직접 입력합니다.

| 변수 | 값 |
|---|---|
| `DATABASE_URL` | 1단계에서 복사한 Internal Database URL |
| `FLASK_SECRET_KEY` | **필수.** 긴 임의 문자열. 비워 두면 재시작·휴면 때마다 모두 로그아웃되고, gunicorn 작업 프로세스마다 키가 달라져 로그인이 풀릴 수 있습니다. |
| `PASSWORD_PEPPER` | **필수(`DATABASE_URL`을 쓸 때).** 긴 임의 문자열. 비밀번호 키를 만들 때 쓰며, 없으면 서버가 시작되지 않습니다. **한 번 정한 뒤 바꾸면 모든 계정에 로그인할 수 없으니 절대 바꾸지 마세요.** 로컬 SQLite에서는 없어도 됩니다. |
| `AI_MODE`, `GROQ_API_KEY`, `GROQ_MODEL` | AI 기능 설정 (위 `.env` 설정 표와 같음) |
| `YOUTUBE_API_KEY` | 선택 사항 |
| `PYTHON_VERSION` | Render에서 쓸 Python 버전. 지원 버전은 [Render 문서](https://render.com/docs/python-version)를 확인합니다. |

### 4. 배포와 접속

- 저장하면 빌드와 배포가 시작됩니다. 완료 후 `https://<서비스 이름>.onrender.com`으로 접속합니다.
- 연결된 브랜치에 push하면 자동으로 다시 배포됩니다.

### 무료 Web Service 동작

| 항목 | 내용 |
|---|---|
| 휴면 | 요청이 **15분** 동안 없으면 서버가 멈춥니다. |
| 첫 접속 지연 | 휴면 후 첫 요청 때 다시 켜지는 데 **약 1분**이 걸리며, 그동안 로딩 화면이 보입니다. 시연 전에 미리 한 번 접속해 두세요. |
| 사용 시간 | 워크스페이스당 매월 **750시간**. 다 쓰면 다음 달까지 무료 서비스가 정지됩니다. |
| 파일 저장 | 임시 저장소라 재배포·재시작·휴면 때 사라집니다. 데이터는 반드시 Postgres에 저장합니다. |

무료 플랜의 정확한 조건은 [Render 무료 플랜 문서](https://render.com/docs/free)를 확인하세요. 위 내용은 2026년 11월 기준입니다.

---

## 폴더 구조

```
team10/
├── app.py                  # Flask 앱: 로그인, 성적·관리·예측·퀴즈 라우트, 비밀번호 규칙, 교과과정(CURRICULUM)
├── database.py             # 계정·과목·오답 노트·AI 대화 저장 (현재 SQLite → Render Postgres 전환 대상)
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
├── requirements.txt        # Render 빌드에 사용 (gunicorn, psycopg, scipy 추가 필요)
├── requirements-lock.txt   # 로컬 개발용 고정 버전
├── .env.example            # 환경 변수 예시 (로컬은 .env, Render는 Environment 탭)
├── START_APP.cmd           # Windows 로컬 실행 스크립트
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

JSON API는 같은 사이트에서 보낸 요청만 받습니다. 다른 Origin에서 보낸 요청은 403으로 거절합니다. Render에 배포하면 `https://<서비스 이름>.onrender.com`이 같은 사이트 기준이 됩니다.

---

## 알려진 제한

- AI 퀴즈와 답변은 일반적인 과목 내용을 바탕으로 생성되므로 실제 수업 범위와 다르거나 틀릴 수 있습니다. AI는 성적 데이터를 수정하지 않습니다.
- 오답 노트와 저장된 대화는 개수 제한(10개 / 3개)을 넘으면 가장 오래된 항목부터 자동으로 지워집니다.
- **공개 주소 보안:** Render에 배포하면 누구나 접속할 수 있습니다. 로그인은 학번 + 비밀번호로 데이터를 구분하는 해커톤용 방식이고 비밀번호가 평문으로 저장되므로, 실제 개인정보나 실제 비밀번호를 입력하지 않도록 안내합니다.
- **AI 사용량 공유:** Render에 등록한 Groq 키 하나를 모든 방문자가 함께 사용합니다. 무료 한도를 넘으면 모든 사용자의 AI 기능이 잠시 멈춥니다. AI 퀴즈의 15초 간격 제한은 브라우저 세션 단위로만 적용됩니다.
- **무료 플랜 제약:** 휴면 후 첫 접속에 약 1분이 걸리고, 무료 Postgres는 30일 후 만료됩니다.

---

## 팀원

| 이름 | 역할 |
|---|---|
| 권민준 | 팀원, UI제작 및 기타 코드 제작 |
| 김준호 | 팀장, 기본 파일 제작 및 기타 코드 제작 |
| 조셉 커리지 | 팀원, AI 연동 코드 제작 및 기타 코드 제작 |

