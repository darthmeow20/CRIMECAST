@echo off
cd /d "%~dp0"
echo Stopping old Streamlit on port 8501 (if any)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8501 ^| findstr LISTENING') do (
  taskkill /F /PID %%a >nul 2>&1
)
if exist "__pycache__" rd /s /q "__pycache__" 2>nul
if exist ".venv\Scripts\streamlit.exe" (
  echo Starting Streamlit...
  ".venv\Scripts\streamlit.exe" run dashboard.py --server.runOnSave true
) else (
  echo Starting Streamlit with python -m streamlit...
  py -3 -m streamlit run dashboard.py --server.runOnSave true
)
pause
