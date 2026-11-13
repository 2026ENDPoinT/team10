# 학습파트너 AI 설정 가이드 — VS Code / Windows

현재 학습파트너는 **Groq API**와 **`openai/gpt-oss-120b` 모델**을 사용합니다. 모델 이름에 `openai/`가 있어도 **Groq에서 발급한 키**를 사용합니다. OpenAI 키는 필요하지 않습니다.

## 1. 프로젝트 폴더 열기

VS Code에서 **파일 → 폴더 열기**로 다음 폴더를 엽니다.

```text
C:\Users\hbnrc\OneDrive\Documents\ChatGPT\hakaton 2026\team10-ai-branch
```

팀원은 본인이 내려받은 프로젝트 폴더를 열면 됩니다. 위 경로는 현재 컴퓨터의 경로입니다.

**터미널 → 새 터미널**에서 PowerShell을 사용합니다. 원본 `team10`이나 이전 `team10-study-app` 폴더와 혼동하지 마세요.

## 2. 처음 설치할 때만: Python 환경 준비

이 컴퓨터는 이미 설치되어 있으므로 다음 단계로 넘어갑니다. 새 컴퓨터에서는 팀에서 사용하는 Python 3.15를 설치한 뒤 실행합니다.

```powershell
py -3.15 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
```

현재 컴퓨터에서 `py`가 Python을 찾지 못하면 다음 명령을 사용합니다.

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python315\python.exe" -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
```

VS Code에서 `Ctrl+Shift+P` → **Python: Select Interpreter** → 프로젝트의 `.venv\Scripts\python.exe`를 선택합니다. 아래 실행 명령은 이 Python을 직접 사용하므로 가상환경 활성화 명령은 따로 필요하지 않습니다.

## 3. Groq 키 발급

1. [Groq Console의 API Keys](https://console.groq.com/keys)에 로그인합니다.
2. **Create API Key**를 선택하고 `study-partner` 같은 이름을 입력합니다.
3. 발급된 키를 복사하여 다음 단계의 로컬 `.env`에 저장합니다.

무료 프로젝트는 Free 플랜을 사용합니다. 이 앱은 결제를 활성화하거나 한도 초과 시 다른 유료 제공자로 자동 전환하지 않습니다.

## 4. `.env` 설정

`app.py`와 같은 위치의 `.env`를 엽니다. 파일이 없을 때만 `.env.example`을 복사하고 이름을 `.env`로 바꿉니다. 기존 `.env`를 덮어쓰지 마세요.

다음 항목을 설정합니다. 같은 항목을 여러 번 추가하지 말고 기존 값을 수정합니다.

```dotenv
AI_MODE=groq
GROQ_API_KEY=여기에_본인의_Groq_API_키_입력
GROQ_MODEL=openai/gpt-oss-120b
PORT=5002
```

`여기에_본인의_Groq_API_키_입력`은 예시 문구입니다. 실제 발급된 키로 바꾼 뒤 `Ctrl+S`로 저장합니다.

- `OPENAI_API_KEY`는 비워 두어도 됩니다. Groq 모드에서는 사용하지 않습니다.
- `YOUTUBE_API_KEY`는 선택 사항입니다. 없으면 주제에 맞는 YouTube 검색 링크를 제공합니다. 설정하면 영상 검색 결과 카드를 제공할 수 있습니다.
- 이 로컬 앱은 `.env` 설정을 우선합니다. 수정 후에는 서버를 다시 실행해야 반영됩니다.
- 실제 키는 `AI_SETUP_KO.md`, `.env.example`, Python/JavaScript 코드, 채팅 또는 GitHub에 넣지 않습니다.

## 5. VS Code에서 실행

프로젝트 폴더의 PowerShell 터미널에서 실행합니다.

```powershell
.\START_APP.cmd
```

또는 환경 설치가 완료되어 있다면 직접 실행할 수 있습니다.

```powershell
.\.venv\Scripts\python.exe app.py
```

두 명령 중 **하나만** 실행합니다. 서버가 실행된 동안 터미널을 열어 둡니다.

- 메인 화면: <http://127.0.0.1:5002>
- 학습파트너: <http://127.0.0.1:5002/ai/>
- 연결 설정 확인: <http://127.0.0.1:5002/ai/api/health>

설정 확인 주소에서 `"mode": "groq"`, `"configured": true`가 보이면 Groq 모드와 키 입력이 확인된 것입니다. **실제 API 연결 성공은 질문을 보내 답변을 받아야 확인됩니다.**

학습파트너의 안내문에 **Groq로 전달됩니다**가 표시되는지 확인하고 다음 질문을 입력해 봅니다.

> C언어 포인터를 처음 배우는 학생에게 한국어로 쉽게 설명하고 연습 문제 하나를 내 주세요.

## 6. 퀴즈와 함께 사용

1. 성적 화면에서 퀴즈 탭으로 이동합니다.
2. 현재 문제가 준비된 **프로그래밍입문(1)** 과목을 선택하고 퀴즈를 풉니다.
3. 결과 화면에서 개별 문제 질문, 오답 복습 또는 전체 결과 분석을 선택합니다.
4. 학습파트너에게 개념 설명, 힌트, 추가 연습 문제 또는 강의 추천을 요청합니다.

강점·약점 분석은 전달된 퀴즈 결과를 기준으로 합니다. 장기간의 학습 기록을 저장해 분석하는 기능은 아직 없습니다. 대화는 페이지를 새로고침하면 유지되지 않습니다. AI는 성적 데이터를 수정하지 않습니다.

## 7. 자주 발생하는 문제

### 여전히 이전 AI 제공자가 표시될 때

1. 현재 실행 중인 서버 터미널에서 `Ctrl+C`로 종료합니다.
2. 올바른 `team10-ai-branch` 폴더의 `.env`에 `AI_MODE=groq`가 있는지 확인합니다.
3. 저장 후 서버를 다시 실행합니다.
4. `http://127.0.0.1:5002/ai/`에서 `Ctrl+F5`로 새로고침합니다.

서버가 다른 창이나 백그라운드에서 이미 실행 중이면 기존 서버를 먼저 종료해야 합니다. 새 서버가 시작되었다는 로그 없이 브라우저만 새로고침하면 이전 설정이 계속 보일 수 있습니다.

### 포트가 이미 사용 중이라고 나올 때

같은 포트의 서버가 이미 실행 중인지 확인합니다. 기존 서버를 종료하거나 `.env`의 `PORT`를 다른 번호로 바꾸고 다시 실행합니다. 포트를 변경했다면 브라우저 주소의 `5002`도 변경한 번호로 바꿉니다.

### 사이트에 연결할 수 없을 때

터미널에 서버 실행 주소가 표시되는지 확인합니다. 서버가 종료되었거나 오류가 났다면 오류 내용을 먼저 확인합니다. 브라우저만 열어서는 Flask 서버가 시작되지 않습니다.

### `No module named flask`가 나올 때

프로젝트 폴더에서 다음 명령으로 가상환경에 필요한 패키지를 설치합니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
```

### API 키 오류 또는 사용 한도 오류가 나올 때

Groq에서 발급한 키인지, `.env`를 저장하고 서버를 재시작했는지 확인합니다. 한도 오류는 잠시 기다린 뒤 다시 시도합니다. Flask를 재시작해도 API 사용량은 초기화되지 않습니다.

정확한 계정별 한도는 Groq Console의 **Settings → Limits**에서 확인합니다. 같은 조직의 키로 사용하는 팀원들은 사용 한도를 공유합니다. 질문뿐 아니라 시스템 지침, 퀴즈 내용, 대화 기록 및 생성된 답변도 토큰 사용량에 영향을 줍니다. [공식 사용 한도 안내](https://console.groq.com/docs/rate-limits)

## 8. 팀 공유 및 GitHub

- `AI_SETUP_KO.md`와 키가 비어 있는 `.env.example`은 공유할 수 있습니다.
- `.env`, `.venv/`, 로컬 데이터베이스는 공유하거나 커밋하지 않습니다.
- 현재 `.env`가 Git 제외 대상인지 다음 명령으로 확인할 수 있습니다.

```powershell
git check-ignore .env
```

결과에 `.env`가 나오면 제외 규칙이 적용됩니다. 이미 과거에 커밋된 키를 지워 주는 명령은 아닙니다. 키를 GitHub 등에 노출했다면 Groq에서 해당 키를 폐기하고 새로 발급합니다.

현재 작업은 원본 프로젝트와 분리된 `team10-ai-branch`에서 진행합니다. 팀 프로젝트에 합칠 때는 소스 변경 사항을 검토하여 병합하고, 팀원의 `.env`나 데이터베이스를 덮어쓰지 않습니다.
