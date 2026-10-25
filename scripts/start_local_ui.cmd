@echo off
setlocal
cd /d "%~dp0.."
set "PYTHONPATH=%CD%\src"
title AI Tax Agent - Local Product Dashboard

echo Starting the local AI Tax Agent product dashboard...
echo The interface is available only on this computer.
echo Protected case data remains unavailable until an accepted runtime injects the CaseRegistry source.
echo Close this window to stop the local interface.
start "" "http://127.0.0.1:8000"
python -m uvicorn agent_lab.ui_product_app:app --host 127.0.0.1 --port 8000

if errorlevel 1 (
  echo.
  echo The local interface could not start. No external connection was attempted.
  pause
)
endlocal
