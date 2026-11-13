# Run the integrated Team 10 study app

This is a separate source copy of your team project, with the AI module connected to the real quiz and score pages. The original GitHub folder has not been edited. The copy uses its own `data/database.db`; no student records or credentials were copied.

## Start on this computer

Double-click **START_APP.cmd** in this folder, or open this folder in VS Code and run:

```powershell
.\.venv\Scripts\python.exe app.py
```

Keep the terminal/window open. After it says `Running on http://127.0.0.1:5002`, open **http://127.0.0.1:5002** in your browser. The original app can keep running on port 5000; the earlier prototype used 5001. If you change `PORT` in `.env`, use that port instead of the default URL printed by the start script.

## Real AI setup

Copy `.env.example` to `.env` if the start script has not created it. In `.env`, fill in `OPENAI_API_KEY` with your own OpenAI API key and keep `AI_MODE=openai`. Stop and restart the app after changing configuration. This version does not silently substitute demo replies when the key is missing: it shows a setup message.

An optional `YOUTUBE_API_KEY` enables real video search results. Without it the tutor provides a topic-search link on YouTube. Keys stay in the local `.env`, which is ignored by Git. Do not put them in chat or browser code. OpenAI API usage requires an API account with access/billing; a ChatGPT subscription alone is not the API configuration.

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
