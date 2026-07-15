@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM ──────────────────────────────────────────────────────────────────────────
REM  build_app.bat — PyInstaller onefile + onedir builds (Windows)
REM  Outputs:
REM    dist\windows\onefile\SubtitleMuxer.exe
REM    dist\windows\onedir\SubtitleMuxer\...
REM ──────────────────────────────────────────────────────────────────────────

cd /d "%~dp0.."
set "PLATFORM=windows"
set "APP_NAME=SubtitleMuxer"

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

REM Shared PyInstaller flags for CustomTkinter + tkinterdnd2 + static-ffmpeg
REM --paths=. keeps ``import src...`` working when the entry script lives under src/
set "COMMON_ARGS=--noconfirm --clean --windowed --name %APP_NAME% --paths=. --collect-all customtkinter --collect-all tkinterdnd2 --collect-all static_ffmpeg --hidden-import=tkinterdnd2 --hidden-import=ffmpeg --hidden-import=static_ffmpeg"

echo [1/2] Building --onefile ^(portable^) ...
if exist "dist\%PLATFORM%\onefile" rmdir /s /q "dist\%PLATFORM%\onefile"
if exist "build\%PLATFORM%\onefile" rmdir /s /q "build\%PLATFORM%\onefile"
mkdir "dist\%PLATFORM%\onefile" 2>nul
mkdir "build\%PLATFORM%\onefile" 2>nul

pyinstaller %COMMON_ARGS% ^
    --onefile ^
    --distpath "dist\%PLATFORM%\onefile" ^
    --workpath "build\%PLATFORM%\onefile" ^
    --specpath "build\%PLATFORM%\onefile" ^
    src\__main__.py
if errorlevel 1 (
    echo ERROR: onefile build failed.
    exit /b 1
)

echo [2/2] Building --onedir ^(installable structure^) ...
if exist "dist\%PLATFORM%\onedir" rmdir /s /q "dist\%PLATFORM%\onedir"
if exist "build\%PLATFORM%\onedir" rmdir /s /q "build\%PLATFORM%\onedir"
mkdir "dist\%PLATFORM%\onedir" 2>nul
mkdir "build\%PLATFORM%\onedir" 2>nul

pyinstaller %COMMON_ARGS% ^
    --onedir ^
    --distpath "dist\%PLATFORM%\onedir" ^
    --workpath "build\%PLATFORM%\onedir" ^
    --specpath "build\%PLATFORM%\onedir" ^
    src\__main__.py
if errorlevel 1 (
    echo ERROR: onedir build failed.
    exit /b 1
)

echo.
echo Build complete:
echo   Portable : dist\%PLATFORM%\onefile\%APP_NAME%.exe
echo   Onedir   : dist\%PLATFORM%\onedir\%APP_NAME%\
echo.
exit /b 0
