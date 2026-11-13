# 한국어 AI 학습 파트너

Branch: `feature/korean-study-partner`. This is a separate local clone of the team repository. Its `origin` points to the original local checkout, not GitHub. No push or merge has been performed.

## Implemented

- Python/Flask API: `POST /ai/api/chat` for general Korean study chat, quiz explanations, hints, lecture search and conversational practice questions.
- Existing quiz result buttons: help with one question, review missed questions, or analyze ALL results for strengths and areas to review.
- Evidence-aware tutoring: the AI sees actual answers; wrong-only context is insufficient to infer strengths. It must describe uncertainty and avoid declaring mastery from a single quiz.
- Korean default responses and Korean main controls; language, level and lecture-length preferences.
- Gemini is the default provider and requires a local Google AI Studio key. OpenAI remains optional. YouTube result cards require an optional YouTube key; otherwise the app shows a labeled topic-search link.
- Separate local database, without importing existing student records. AI cannot edit grades.

## Limits

Strength/weakness feedback currently concerns only the submitted quiz and ongoing conversation. There is no persistent quiz-attempt history or longitudinal learning profile. Practice questions are conversational and are not automatically added to the team's graded question bank. AI content quality and live API access require testing with your own key. Some operational error/status text remains in English.

## Run

Double-click `START_APP.cmd`. On first use it creates this folder's `.venv` and installs dependencies using this computer's Python 3.15 installation. Keep the window open, then open http://127.0.0.1:5002 . Fill in your own key in `.env`, which is ignored by Git. See `SETUP.md` for details. Do not paste keys into chat.

## Tests

`node tests/test_quiz_integration.cjs` exercises the actual question bank and all AI handoff buttons. `python -m unittest discover -s tests -v` checks routes, grade isolation, missing-key behavior, the provider request and video fallbacks. AI responses are mocked for these tests.

## Merge later

The feature is committed locally in this checkout. When ready, your team can fetch this checkout's `feature/korean-study-partner` branch into the original repository and review/merge it on a team feature branch. Do not push to this clone's local `origin`, which may be a checked-out repository. No production merge or GitHub publication is included.
