@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    set "REVIEW_PYTHON=%~dp0.venv\Scripts\python.exe"
) else (
    set "REVIEW_PYTHON=python"
)
if not exist "data\statements.json" (
    echo Downloading question statements for the first run...
    "%REVIEW_PYTHON%" cache_statements.py
    if errorlevel 1 echo Download incomplete. The app can still start; retry later or paste statements in the app.
)
"%REVIEW_PYTHON%" app.py --open
if errorlevel 1 pause
endlocal
