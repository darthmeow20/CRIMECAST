@echo off
cd /d "%~dp0\.."
echo.
echo  [1/3] Regenerating CURRENT figures + form screenshots...
echo.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m pip install python-docx pillow matplotlib pandas numpy seaborn -q
  ".venv\Scripts\python.exe" project_docs\regenerate_report_figures.py
  echo.
  echo  [2/3] Capturing run_tests.py terminal screenshot...
  ".venv\Scripts\python.exe" project_docs\capture_test_terminal.py
  echo.
  echo  [3/3] Building Word report with NEW figures...
  ".venv\Scripts\python.exe" project_docs\generate_full_report_docx.py
) else (
  py -3 -m pip install python-docx pillow matplotlib pandas numpy seaborn -q
  py -3 project_docs\regenerate_report_figures.py
  echo.
  echo  [2/3] Capturing run_tests.py terminal screenshot...
  py -3 project_docs\capture_test_terminal.py
  echo.
  echo  [3/3] Building Word report with NEW figures...
  py -3 project_docs\generate_full_report_docx.py
)
echo.
echo  Figures:     project_docs\figures\results\
echo  Screenshots: project_docs\figures\screenshots\
echo  Word:        project_docs\CRIMECAST_FULL_PROJECT_REPORT.docx
echo.
echo  Open Word - fill [STUDENT NAME] etc. - Print hard copy.
echo.
pause
