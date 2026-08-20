@echo off
setlocal
set "PROJECT_ROOT=%~dp0"
set "BUILD_PYTHON=%PROJECT_ROOT%venv_final\Scripts\python.exe"
set "RELEASE_DIR=%PROJECT_ROOT%release"
set "WORK_DIR=%PROJECT_ROOT%build\onefile"

if not exist "%BUILD_PYTHON%" (
    echo ERROR: Build Python was not found: %BUILD_PYTHON%
    exit /b 1
)

echo Building a standalone CapCap.exe...
if exist "%WORK_DIR%" rmdir /s /q "%WORK_DIR%"
if exist "%RELEASE_DIR%\CapCap.exe" del /q "%RELEASE_DIR%\CapCap.exe"
if not exist "%RELEASE_DIR%" mkdir "%RELEASE_DIR%"

"%BUILD_PYTHON%" -m PyInstaller --noconfirm --clean --workpath "%WORK_DIR%" --distpath "%RELEASE_DIR%" "%PROJECT_ROOT%CapCap.spec"
if errorlevel 1 exit /b %errorlevel%

if not exist "%RELEASE_DIR%\CapCap.exe" (
    echo ERROR: PyInstaller did not produce %RELEASE_DIR%\CapCap.exe
    exit /b 1
)

echo Build complete: %RELEASE_DIR%\CapCap.exe
endlocal
