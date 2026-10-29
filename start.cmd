@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    set "REVIEW_PYTHON=%~dp0.venv\Scripts\python.exe"
) else (
    set "REVIEW_PYTHON=python"
)
"%REVIEW_PYTHON%" -c "import jedi, psutil" >nul 2>nul
if errorlevel 1 (
    echo Installing local completion and judge dependencies...
    "%REVIEW_PYTHON%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Dependency installation failed. Please check your Python environment and network.
        pause
        exit /b 1
    )
)
if not exist "data\statements.json" (
    echo Downloading question statements for the first run...
    "%REVIEW_PYTHON%" cache_statements.py
    if errorlevel 1 echo Download incomplete. The app can still start; retry later or paste statements in the app.
)
"%REVIEW_PYTHON%" app.py --open
if errorlevel 1 pause
endlocal
