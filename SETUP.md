# Run the integrated Team 10 study app

한국어 VS Code 설정 안내: [AI_SETUP_KO.md](AI_SETUP_KO.md)

This is a separate source copy of your team project, with the AI module connected to the real quiz and score pages. The original GitHub folder has not been edited. The copy uses its own `data/database.db`; no student records or credentials were copied.

## Start on this computer

Double-click **START_APP.cmd** in this folder, or open this folder in VS Code and run:

```powershell
.\.venv\Scripts\python.exe app.py
```

Keep the terminal/window open. After it says `Running on http://127.0.0.1:5002`, open **http://127.0.0.1:5002** in your browser. The original app can keep running on port 5000; the earlier prototype used 5001. If you change `PORT` in `.env`, use that port instead of the default URL printed by the start script.

## Real AI setup

Copy `.env.example` to `.env` if the start script has not created it. In `.env`, fill in `GROQ_API_KEY` with your Groq key, set `AI_MODE=groq`, and set `GROQ_MODEL=openai/gpt-oss-120b`. Stop and restart the app after changing configuration. This version does not silently substitute demo replies when the key is missing: it shows a setup message.

An optional `YOUTUBE_API_KEY` enables real video search results. Without it the tutor provides a topic-search link on YouTube. Keys stay in the local `.env`, which is ignored by Git. Do not put them in chat or browser code. Use your Groq Free plan for this setup; usage limits and model availability depend on your account. The app does not enable billing or automatically switch providers.

Official setup: [OpenAI](https://developers.openai.com/api/docs/quickstart), [YouTube](https://developers.google.com/youtube/v3/getting-started).

## Try the existing quiz with AI help

1. Enter a test student name, year and valid eight-digit student ID on the existing home page.
2. From the scores page, choose **학습 퀴즈로 이동**.
3. Choose **프로그래밍입문(1)** or **Introduction to Programming 1**, the subjects currently containing your team's question bank.
4. Finish a quiz. Choose **AI에게 이 문제 질문하기** beside any result, or **AI와 오답 복습하기** to send all missed/unanswered questions.
5. The tutor receives the exact questions and selected answers. Choose explain, hint, practice or video lessons; set language, level and video length as needed.
6. Use the back link to return to the score page. The score page also has a general **AI 학습 도우미** link.

All AI and video lookup logic is Python. JavaScript handles the existing quiz and the small browser handoff. The AI cannot change grades. Quiz data is study context, not an authenticated grade record. Chat history lasts for the open page, not across logins or reloads.

## Fresh environment on another machine

```powershell
py -3.15 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
```

On this computer, if `py` cannot find Python:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python315\python.exe" -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
```

## Scope and merging

This is a local development copy, not a public deployment. Existing account/grade routes retain the team's prototype behavior. Public deployment needs authentication, per-user data access, rate limits, and usage controls.

`SOURCE_SNAPSHOT.json` records hashes of the original files copied. `integration.patch` records the initial quiz/score UI changes and has ALREADY been applied to this copy. Do not apply it again here. Merge reviewed source changes on a team feature branch later; do not overwrite your team's database, `.env`, `.venv`, or Git history.

Groq requests go to Groq, even though the model name starts with `openai/`. No OpenAI key is needed for this mode. Free account limits still apply; a limit error asks you to wait and never switches to a paid provider. Gemini remains available with `AI_MODE=gemini`.


## AI 퀴즈 생성

퀴즈 탭에서 **AI 새 문제**를 선택하고 `app.py` 교과과정의 과목과 1~5문제를 선택합니다. 학습 주제는 선택 입력입니다. 실제 강의계획서가 없으므로 일반적인 과목 내용을 기반으로 생성하며 AI 정답에 오류가 있을 수 있습니다.

정답·해설은 별도 `data/ai_quizzes.db`에 저장됩니다. 제출 전에는 문제와 보기만 전달하고, 제출 후 Python이 채점하여 해설을 보여 줍니다. **같은 문제 다시 풀기**는 AI 재호출 없이 동작합니다. 결과에서 기존 학습파트너로 오답이나 전체 결과를 전달할 수 있습니다. 기존 문제은행 모드도 유지합니다.

생성된 퀴즈는 현재 브라우저 세션에 연결되며 24시간 후 만료됩니다. 서버 재시작으로 세션이 변경되면 새로 생성해야 할 수 있습니다. 성공한 생성 후 15초 대기 제한과 Groq 자체 한도가 적용됩니다. 생성 토큰 사용량은 설정 영역에 표시됩니다. 공식 성적은 변경하지 않습니다.


## 과제 관리

로그인 후 상단 **과제** 탭을 엽니다. 과목·과제명·한국 시간 기준 마감 일시·중요도를 등록하고 수정 또는 삭제할 수 있습니다. 미완료 목록은 마감 오름차순, 같은 마감이면 중요도 내림차순으로 표시됩니다. 제출 완료하면 완료 목록으로 이동하고 다시 할 일로 되돌릴 수도 있습니다.

성적 화면 상단 알림은 아직 마감하지 않은 오늘 과제와 내일부터 3일 뒤까지의 과제를 중복 없이 집계합니다. 기한이 지난 미완료 과제는 별도로 안내합니다. 알림과 D-day는 페이지를 열거나 새로고침할 때 갱신됩니다. 푸시 알림은 없습니다.

과제는 `data/assignments.db`에 따로 저장되며 기존 students 테이블의 계정 ID와 연결합니다. 설치 후 한 번 다시 로그인해야 세션이 생성됩니다. `FLASK_SECRET_KEY`를 로컬 `.env`에 지정하지 않은 경우 서버 재시작 때 다시 로그인해야 합니다. 기존 로그인/등록 방식은 유지되며 실제 서비스용 인증 체계로 교체한 것은 아닙니다. DB 파일과 `.env`는 커밋하지 않습니다.


## 한국어 / English

각 화면 상단의 작은 **ENG / 한국어** 버튼으로 표시 언어를 바꿉니다. 브라우저 쿠키에 저장되므로 페이지 이동·로그아웃 후에도 선택이 유지됩니다. 입력 중이거나 AI 대화가 있는 경우 새로고침 전에 확인을 표시합니다.

메뉴·버튼·설명과 과제 남은 시간은 표시 언어를 따릅니다. 과목은 화면의 이름만 번역하며 저장·전송되는 원래 값은 유지합니다. 사용자가 작성한 이름·과제명, 기존 문제은행의 문제/해설, 이미 생성한 퀴즈와 대화는 자동 번역하지 않습니다. 영어 모드에서 새로 생성하는 AI 퀴즈는 영어로 요청하며 AI 대화의 기본 응답 언어도 영어로 선택됩니다. `static/translations.json`에서 UI 번역을 관리합니다.


## 과제 체크리스트와 AI 계획

과제 등록·수정에서 예상 작업 시간을 시간/분으로 입력하고, 체크리스트를 한 줄에 하나씩 작성합니다(최대 20개, 각 100자, 중복 불가). 체크박스는 즉시 저장되며 완료 항목 수로 진행률을 계산합니다. 같은 문구의 항목은 수정 후에도 체크 상태를 유지하고, 문구가 바뀐 항목은 미완료로 시작합니다. 체크리스트 완료와 실제 제출 완료는 별개입니다.

**AI랑 계획하기**는 과제명·과목·한국 시간 기준 마감·예상 시간·진행률·체크리스트를 학습파트너의 질문 초안으로 가져옵니다. 내용을 확인한 뒤 보내면 대화를 시작합니다. 화면을 여는 것만으로는 AI를 호출하지 않으며, AI가 과제를 자동 수정하거나 제출하지 않습니다. 예상 시간은 전체 과제에 대한 사용자 추정치입니다. 기존 과제 DB는 새 컬럼을 자동 추가하여 보존합니다.
