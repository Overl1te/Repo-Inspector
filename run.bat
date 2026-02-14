@echo off
setlocal

cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python not found in PATH.
  echo Install Python 3.11+ and try again.
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [INFO] Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    exit /b 1
  )
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
  echo [ERROR] Failed to activate virtual environment.
  exit /b 1
)

echo [INFO] Installing dependencies...
python -m pip install --upgrade pip
if errorlevel 1 (
  echo [ERROR] Failed to upgrade pip.
  exit /b 1
)

python -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Failed to install requirements.
  exit /b 1
)

python -m pip install -e ".[dev]"
if errorlevel 1 (
  echo [ERROR] Failed to install project in editable mode.
  exit /b 1
)

if not exist "config.yml" (
  echo [ERROR] config.yml not found.
  echo Create config.yml in project root and run run.bat again.
  exit /b 1
)

echo [INFO] Starting server on http://127.0.0.1:8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
