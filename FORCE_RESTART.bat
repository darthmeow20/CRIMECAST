@echo off
cd /d "%~dp0"
echo === Kill Streamlit / Python on port 8501 ===
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :8501 ^| findstr LISTENING') do (
  echo Killing PID %%a
  taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul
echo === Clear pycache ===
if exist "__pycache__" rd /s /q "__pycache__"
for /d /r %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
echo === Verify LIVE WIRE is gone from dashboard.py ===
findstr /C:"LIVE WIRE" dashboard.py >nul
if %ERRORLEVEL%==0 (
  echo ERROR: LIVE WIRE still in dashboard.py
) else (
  echo OK: no LIVE WIRE string in dashboard.py
)
findstr /C:"v20260719c" dashboard.py >nul
if %ERRORLEVEL%==0 (
  echo OK: new Live Feed stamp v20260719c present
) else (
  echo WARN: stamp not found
)
echo === Start Streamlit ===
if exist ".venv\Scripts\streamlit.exe" (
  ".venv\Scripts\streamlit.exe" run dashboard.py --server.runOnSave true
) else (
  py -3 -m streamlit run dashboard.py
)
pause
