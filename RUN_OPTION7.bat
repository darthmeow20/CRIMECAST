@echo off
title CRIMECAST Option 7 FIXED-NO-SKLEARN-v4
cd /d "%~dp0"

echo.
echo ============================================================
echo  MUST SEE:  FIXED-NO-SKLEARN-v4
echo  If you see [ERROR] Failed + columns/dataframes, WRONG folder
echo ============================================================
echo.
echo Folder: %CD%
echo.

set "PY="
if exist "%~dp0..\env\Scripts\python.exe" set "PY=%~dp0..\env\Scripts\python.exe"
if not defined PY if exist "C:\Python311\python.exe" set "PY=C:\Python311\python.exe"
if not defined PY set "PY=python"

echo Python: %PY%
echo.

REM Wipe stale bytecode so old sklearn path cannot load
if exist "%~dp0__pycache__\predict_2026_rape_all_districts*.pyc" del /q "%~dp0__pycache__\predict_2026_rape_all_districts*.pyc" 2>nul
if exist "%~dp0__pycache__\rape_2026_engine*.pyc" del /q "%~dp0__pycache__\rape_2026_engine*.pyc" 2>nul

"%PY%" -B "%~dp0predict_2026_rape_all_districts.py"
set ERR=%ERRORLEVEL%

echo.
if %ERR% neq 0 (
  echo [ERROR] Exit code %ERR%
) else (
  echo [OK] Open model_outputs\rape_predictions_2026_all_districts.csv
)
echo.
pause
