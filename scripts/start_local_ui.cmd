@echo off
setlocal
cd /d "%~dp0.."
set "PYTHONPATH=%CD%\src"
title AI Agent Lab - Local Synthetic UI

echo Starting the local synthetic AI Agent Lab interface...
echo The interface is available only on this computer.
echo Close this window to stop the local interface.
start "" "http://127.0.0.1:8000"
python -m uvicorn agent_lab.ui_app:app --host 127.0.0.1 --port 8000

if errorlevel 1 (
  echo.
  echo The local interface could not start. No external connection was attempted.
  pause
)
endlocal
