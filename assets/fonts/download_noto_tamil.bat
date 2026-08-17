@echo off
setlocal
cd /d "%~dp0"
echo Fetching Tamil font into: %CD%
where python >nul 2>&1
if %ERRORLEVEL%==0 (
  python "%~dp0fetch_noto_tamil.py"
  if %ERRORLEVEL%==0 goto :list
)
where py >nul 2>&1
if %ERRORLEVEL%==0 (
  py -3 "%~dp0fetch_noto_tamil.py"
  if %ERRORLEVEL%==0 goto :list
)
where curl >nul 2>&1
if %ERRORLEVEL%==0 (
  curl -L --fail -o "%~dp0NotoSansTamil-Regular.ttf" "https://notofonts.github.io/tamil/fonts/NotoSansTamil/full/ttf/NotoSansTamil-Regular.ttf"
  if %ERRORLEVEL%==0 goto :list
  curl -L --fail -o "%~dp0NotoSansTamil-Regular.ttf" "https://cdn.jsdelivr.net/gh/openmaptiles/fonts@master/noto-sans/NotoSansTamil-Regular.ttf"
  if %ERRORLEVEL%==0 goto :list
)
if exist "%WINDIR%\Fonts\Nirmala.ttc" (
  copy /Y "%WINDIR%\Fonts\Nirmala.ttc" "%~dp0Nirmala.ttc" >nul
  echo Copied Nirmala.ttc as backup.
  goto :list
)
echo ERROR: python/curl unavailable and no Nirmala.ttc found.
exit /b 1

:list
echo.
echo Files under assets\fonts:
dir "%~dp0" | findstr /i "ttf ttc bat py"
exit /b 0
