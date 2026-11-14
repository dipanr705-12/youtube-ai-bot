@echo off
REM ============================================================
REM YouTube AI Bot - Launcher (run.bat)
REM ============================================================
REM Usage:
REM   run.bat           - Start the daily scheduler
REM   run.bat --now     - Run pipeline once (test)
REM   run.bat --auth    - Authorize YouTube account
REM ============================================================

set PYTHON_EXE=C:\Users\dipan roy\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
set FFMPEG_DIR=C:\Users\dipan roy\.gemini\antigravity\scratch\youtube-ai-bot\ffmpeg\ffmpeg-master-latest-win64-gpl\bin
set PROJECT_DIR=C:\Users\dipan roy\.gemini\antigravity\scratch\youtube-ai-bot

REM Add FFmpeg to PATH for this session
set PATH=%FFMPEG_DIR%;%PATH%

cd /d "%PROJECT_DIR%"

echo.
echo ======================================
echo   YouTube AI Bot
echo ======================================
echo   Python: %PYTHON_EXE%
echo   FFmpeg: %FFMPEG_DIR%
echo ======================================
echo.

"%PYTHON_EXE%" main.py %*

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Bot exited with error code %errorlevel%
    pause
)
