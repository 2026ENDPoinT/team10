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
