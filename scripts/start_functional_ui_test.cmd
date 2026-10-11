@echo off
setlocal
cd /d "%~dp0.."
set "PYTHONPATH=%CD%\src"
set "AI_TAX_UI_FUNCTIONAL_TEST=I_UNDERSTAND_TEST_ONLY"
set "AI_TAX_UI_TEST_DB=%LOCALAPPDATA%\AI-Tax-Agent\ui-functional-test.sqlite3"
if not exist "%LOCALAPPDATA%\AI-Tax-Agent" mkdir "%LOCALAPPDATA%\AI-Tax-Agent"
title AI Tax Agent - Isolated Functional Test
echo Functional TEST ONLY - no real taxpayer documents.
echo http://127.0.0.1:8766
if exist "%CD%\.venv\Scripts\python.exe" (
 set "PYTHON=%CD%\.venv\Scripts\python.exe"
) else (
 set "PYTHON=C:\Users\rezag\ai-agent-lab\.venv\Scripts\python.exe"
)
start "" "http://127.0.0.1:8766/?tab=cases"
"%PYTHON%" -m uvicorn agent_lab.ui_functional_test_app:create_functional_test_app --factory --host 127.0.0.1 --port 8766
if errorlevel 1 pause
endlocal
