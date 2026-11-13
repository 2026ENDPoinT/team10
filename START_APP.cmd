@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  "%LOCALAPPDATA%\Programs\Python\Python315\python.exe" -m venv .venv
  if errorlevel 1 goto setup_failed
  ".venv\Scripts\python.exe" -m pip install -r requirements-lock.txt
  if errorlevel 1 goto setup_failed
)
if not exist ".env" copy ".env.example" ".env" >nul
echo.
echo Team 10 study app - separate project copy
echo Open http://127.0.0.1:5002 in your browser after the server starts.
echo Keep this window open. Press Ctrl+C to stop the server.
echo.
".venv\Scripts\python.exe" app.py
echo.
echo The server stopped. Any error is shown above.
pause

exit /b 0
:setup_failed
echo Setup failed. See SETUP.md and the error above.
pause
exit /b 1
