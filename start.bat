@echo off
setlocal EnableDelayedExpansion

set ROOT=%~dp0
cd /d %ROOT%

set PY=
for /f "delims=" %%P in ('where python 2^>nul') do (
  set PY=%%P
  goto :pyfound
)
for /f "delims=" %%P in ('where py 2^>nul') do (
  set PY=py -3
  goto :pyfound
)

:pyfound
if "%PY%"=="" (
  echo [ERROR] Python not found. Install Python 3.11+ and add it to PATH.
  pause
  exit /b 1
)

powershell -NoProfile -Command "Write-Host '== Signature Verification: Setup & Launch ==' -ForegroundColor Cyan"

if not exist "%ROOT%\.venv\Scripts\python.exe" (
  powershell -NoProfile -Command "Write-Host 'Creating virtual environment...' -ForegroundColor Yellow"
  %PY% -m venv .venv
)

set VENV_PY=%ROOT%\.venv\Scripts\python.exe

powershell -NoProfile -Command "Write-Host 'Installing dependencies...' -ForegroundColor Yellow"
%VENV_PY% -m pip install -r requirements.txt

set MODEL=%ROOT%artifacts\model.keras
set THRESH=%ROOT%artifacts\threshold.json
set LABELS=%ROOT%artifacts\label_map.json

if exist "%MODEL%" if exist "%THRESH%" if exist "%LABELS%" (
  powershell -NoProfile -Command "Write-Host 'Model artifacts found. Skipping download and training.' -ForegroundColor Green"
) else (
  if not exist "%USERPROFILE%\.kaggle\kaggle.json" (
    powershell -NoProfile -Command "Write-Host 'Kaggle token missing at %USERPROFILE%\.kaggle\kaggle.json' -ForegroundColor Red"
    powershell -NoProfile -Command "Write-Host 'Download it from https://www.kaggle.com/account and retry.' -ForegroundColor Red"
    pause
    exit /b 1
  )

  powershell -NoProfile -Command "Write-Host 'Downloading dataset (more data)...' -ForegroundColor Yellow"
  %VENV_PY% scripts\fetch_data.py --source kaggle --dataset robinreni/signature-verification-dataset

  powershell -NoProfile -Command "Write-Host 'Preparing data...' -ForegroundColor Yellow"
  %VENV_PY% scripts\prepare_data.py

  powershell -NoProfile -Command "Write-Host 'Training model...' -ForegroundColor Yellow"
  %VENV_PY% scripts\train.py
)

powershell -NoProfile -Command "Write-Host 'Starting server...' -ForegroundColor Green"
start "Signature Server" "%VENV_PY%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

powershell -NoProfile -Command "Start-Sleep -Seconds 2"
start "" "http://127.0.0.1:8000"

powershell -NoProfile -Command "Write-Host 'Server running at http://127.0.0.1:8000' -ForegroundColor Green"
