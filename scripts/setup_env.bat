@echo off
REM ──────────────────────────────────────────────────────────────────────────
REM  setup_env.bat — create/refresh the local virtual environment (Windows)
REM ──────────────────────────────────────────────────────────────────────────

cd /d "%~dp0.."
echo.
echo === Subtitle Muxer — environment setup (Windows) ===
echo Working directory: %CD%
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found on PATH.
    echo Install Python 3.10+ from https://www.python.org/downloads/
    exit /b 1
)

echo [1/4] Creating virtual environment at .venv ...
python -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment.
    exit /b 1
)

echo [2/4] Upgrading pip ...
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
if errorlevel 1 (
    echo ERROR: Failed to upgrade pip.
    exit /b 1
)

echo [3/4] Installing dependencies from requirements\requirements.txt ...
python -m pip install -r requirements\requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install requirements.
    exit /b 1
)

echo [4/4] Downloading bundled FFmpeg into the virtualenv ^(first run may take a bit^) ...
python -c "from src.core.ffmpeg_paths import ensure_ffmpeg_on_path, ffmpeg_binary, ffprobe_binary; ensure_ffmpeg_on_path(); print('ffmpeg :', ffmpeg_binary()); print('ffprobe:', ffprobe_binary())"
if errorlevel 1 (
    echo ERROR: Failed to fetch bundled FFmpeg binaries.
    exit /b 1
)

echo.
echo Setup complete. This shell is now using .venv.
echo Re-activate later with:
echo   .venv\Scripts\activate.bat
echo.
exit /b 0
