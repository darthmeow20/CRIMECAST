@echo off
cd /d "%~dp0"
echo.
echo  CRIMECAST tests  P0-P4
echo  =====================
echo  P0 core unit  ^|  P1 clean/blend/alerts  ^|  P2 integration
echo  P3 data quality  ^|  P4 UI checklist + optional AppTest
echo.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m unittest discover -s tests -p "test_*.py" -v
) else (
  py -3 -m unittest discover -s tests -p "test_*.py" -v
)
echo.
echo  Exit code %ERRORLEVEL%  (0 = all passed; skips OK if models/data missing)
echo  Manual UI: docs\MANUAL_UI_CHECKLIST.md
echo.
pause
