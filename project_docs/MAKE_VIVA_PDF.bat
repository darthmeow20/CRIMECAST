@echo off
cd /d "%~dp0\.."
echo.
echo  CRIMECAST viva PDF
echo.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m pip install reportlab -q
  ".venv\Scripts\python.exe" project_docs\generate_viva_pdf.py
) else (
  py -3 -m pip install reportlab -q
  py -3 project_docs\generate_viva_pdf.py
)
echo.
echo  If PDF exists: project_docs\CRIMECAST_VIVA_PREP.pdf
echo  Else open:     project_docs\CRIMECAST_VIVA_PREP.html  then Ctrl+P - Save as PDF
echo.
start "" "%~dp0CRIMECAST_VIVA_PREP.html"
pause
