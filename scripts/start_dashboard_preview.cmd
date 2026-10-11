@echo off
setlocal
cd /d "%~dp0.."
set "PYTHONPATH=%CD%\src"
title AI Tax Agent - Dashboard Preview (Read Only)
echo AI Tax Agent - read-only dashboard preview
echo No verified case source is configured. No real cases will be shown.
echo Local address: http://127.0.0.1:8765
echo Close this window to stop the server.
if exist "%CD%\.venv\Scripts\python.exe" (
  set "PYTHON=%CD%\.venv\Scripts\python.exe"
) else (
  set "PYTHON=python"
)
start "" "http://127.0.0.1:8765"
"%PYTHON%" -m uvicorn agent_lab.ui_dashboard:create_dashboard_app --factory --host 127.0.0.1 --port 8765
if errorlevel 1 (
  echo Dashboard preview could not start. Check Python dependencies and port 8765.
  pause
)
endlocal
