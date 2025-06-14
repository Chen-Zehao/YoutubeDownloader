@echo off
chcp 65001 >nul 2>&1
title YouTube Downloader
cd /d "%~dp0"

echo ================================
echo      YouTube Downloader
echo ================================
echo.

REM Check Python environment
echo Checking environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not installed!
    echo Please run install.bat to setup environment
    pause
    exit /b 1
)

REM Check essential libraries
python -c "import tkinter; import yt_dlp" >nul 2>&1
if errorlevel 1 (
    echo Warning: Some libraries missing
    echo Running install.bat to fix dependencies...
    call install.bat
    echo.
)

echo Starting YouTube Downloader...
python main.py 