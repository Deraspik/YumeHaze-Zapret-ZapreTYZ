@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === ZapreTYZ build ===
where python >nul 2>&1 || (echo Установите Python 3.11+ с python.org & pause & exit /b 1)
python -m pip install -r requirements.txt || goto :err
echo --- Скачивание Zapret и TG WS Proxy ---
python packaging\fetch_components.py || goto :err
echo --- PyInstaller ---
python -m PyInstaller --noconfirm --clean --distpath dist --workpath "%TEMP%\zapretyz_build" packaging\ZapreTYZ.spec || goto :err
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
  echo Inno Setup 6 не найден. Установите: winget install JRSoftware.InnoSetup
  echo Готовая программа без установщика: dist\ZapreTYZ\ZapreTYZ.exe
  pause & exit /b 0
)
"%ISCC%" packaging\installer.iss || goto :err
echo.
echo ГОТОВО: release\ZapreTYZ_Setup_1.0.0.exe
pause & exit /b 0
:err
echo ОШИБКА сборки & pause & exit /b 1
