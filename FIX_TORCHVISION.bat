@echo off
cd /d "%~dp0"
echo Installing torchvision into project venv (fixes Streamlit + transformers noise)...
if exist ".venv\Scripts\pip.exe" (
  .venv\Scripts\pip.exe install "torchvision==0.16.0"
) else (
  py -3 -m pip install "torchvision==0.16.0"
)
echo.
echo Done. Restart: streamlit run dashboard.py
pause
