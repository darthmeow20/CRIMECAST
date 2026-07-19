@echo off
cd /d "%~dp0"
echo ============================================
echo  CRIMECAST verify + run
echo  Folder: %CD%
echo ============================================
echo.
echo [1] Does THIS dashboard.py still have open_alerts ticker?
findstr /N /C:"LIVE WIRE" /C:"HIGH {open_alerts}" dashboard.py
if %ERRORLEVEL%==0 (
  echo.
  echo  FAILED: old ticker text is still in dashboard.py on disk.
  echo  Close the editor tab for dashboard.py without saving.
  pause
  exit /b 1
) else (
  echo  GOOD: no LIVE WIRE / open_alerts ticker in dashboard.py
)
echo.
echo [2] Build stamp:
findstr /C:"BUILD_ID" dashboard.py
echo.
echo [3] Kill port 8501...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :8501 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
echo.
echo [4] Clear __pycache__
if exist "__pycache__" rd /s /q "__pycache__"
echo.
echo [5] Start Streamlit with FULL path to run_crimecast.py
echo     Sidebar MUST show: build 20260719f-safe
echo     and the full path to dashboard.py
echo.
if exist ".venv\Scripts\streamlit.exe" (
  ".venv\Scripts\streamlit.exe" run "%~dp0run_crimecast.py" --server.headless true
) else (
  py -3 -m streamlit run "%~dp0run_crimecast.py"
)
pause
