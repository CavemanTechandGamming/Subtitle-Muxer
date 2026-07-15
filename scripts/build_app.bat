@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM ──────────────────────────────────────────────────────────────────────────
REM  build_app.bat — versioned portable + installable PyInstaller builds
REM  Version comes from src\__init__.py (single source of truth).
REM  Outputs (example for 1.0.0):
REM    dist\windows\1.0.0\portable\SubtitleMuxer-1.0.0.exe
REM    dist\windows\1.0.0\installable\SubtitleMuxer-1.0.0\...
REM ──────────────────────────────────────────────────────────────────────────

cd /d "%~dp0.."
set "PLATFORM=windows"

echo.
echo === Subtitle Muxer — PyInstaller build (Windows) ===
echo Working directory: %CD%
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Running setup_env.bat ...
    call "scripts\setup_env.bat"
    if errorlevel 1 exit /b 1
)

call ".venv\Scripts\activate.bat"

where pyinstaller >nul 2>&1
if errorlevel 1 (
    echo ERROR: pyinstaller not found in the virtual environment.
    echo Run scripts\setup_env.bat first.
    exit /b 1
)

for /f "usebackq delims=" %%V in (`python scripts\read_version.py`) do set "VERSION=%%V"
if not defined VERSION (
    echo ERROR: Could not read app version from src\__init__.py
    exit /b 1
)

set "APP_NAME=SubtitleMuxer-%VERSION%"
echo App version: %VERSION%
echo Artifact names: subtitle-muxer-%PLATFORM%-%VERSION%-portable / installable
echo.

REM Shared PyInstaller flags for CustomTkinter + tkinterdnd2 + static-ffmpeg
REM --paths=. keeps ``import src...`` working when the entry script lives under src/
set "COMMON_ARGS=--noconfirm --clean --windowed --name %APP_NAME% --paths=. --collect-all customtkinter --collect-all tkinterdnd2 --collect-all static_ffmpeg --hidden-import=tkinterdnd2 --hidden-import=ffmpeg --hidden-import=static_ffmpeg"

echo [1/2] Building portable ^(onefile^) ...
if exist "dist\%PLATFORM%\%VERSION%\portable" rmdir /s /q "dist\%PLATFORM%\%VERSION%\portable"
if exist "build\%PLATFORM%\%VERSION%\portable" rmdir /s /q "build\%PLATFORM%\%VERSION%\portable"
mkdir "dist\%PLATFORM%\%VERSION%\portable" 2>nul
mkdir "build\%PLATFORM%\%VERSION%\portable" 2>nul

pyinstaller %COMMON_ARGS% ^
    --onefile ^
    --distpath "dist\%PLATFORM%\%VERSION%\portable" ^
    --workpath "build\%PLATFORM%\%VERSION%\portable" ^
    --specpath "build\%PLATFORM%\%VERSION%\portable" ^
    src\__main__.py
if errorlevel 1 (
    echo ERROR: portable build failed.
    exit /b 1
)

echo [2/2] Building installable ^(onedir^) ...
if exist "dist\%PLATFORM%\%VERSION%\installable" rmdir /s /q "dist\%PLATFORM%\%VERSION%\installable"
if exist "build\%PLATFORM%\%VERSION%\installable" rmdir /s /q "build\%PLATFORM%\%VERSION%\installable"
mkdir "dist\%PLATFORM%\%VERSION%\installable" 2>nul
mkdir "build\%PLATFORM%\%VERSION%\installable" 2>nul

pyinstaller %COMMON_ARGS% ^
    --onedir ^
    --distpath "dist\%PLATFORM%\%VERSION%\installable" ^
    --workpath "build\%PLATFORM%\%VERSION%\installable" ^
    --specpath "build\%PLATFORM%\%VERSION%\installable" ^
    src\__main__.py
if errorlevel 1 (
    echo ERROR: installable build failed.
    exit /b 1
)

echo.
echo Build complete:
echo   Portable    : dist\%PLATFORM%\%VERSION%\portable\%APP_NAME%.exe
echo   Installable : dist\%PLATFORM%\%VERSION%\installable\%APP_NAME%\
echo.
exit /b 0
