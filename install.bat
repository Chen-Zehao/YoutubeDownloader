@echo off
title YouTube Downloader - Install
echo ================================
echo    YouTube Downloader - Install
echo ================================
echo.

echo [1/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo Error: Python not installed
        echo Please install Python from: https://www.python.org/downloads/
        echo Make sure to check "Add Python to PATH" during installation
        pause
        exit /b 1
    ) else (
        echo Success: Python found (using py command)
        set PYTHON_CMD=py
    )
) else (
    echo Success: Python found (using python command)
    set PYTHON_CMD=python
)

echo.
echo [2/3] Installing Python packages...
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install yt-dlp>=2023.11.16 Pillow>=8.0.0 requests>=2.25.0 ffmpeg-python>=0.2.0
if errorlevel 1 (
    echo Error: Failed to install packages
    pause
    exit /b 1
) else (
    echo Success: Packages installed
)

echo.
echo [3/3] Creating desktop shortcut...
set "currentDir=%cd%"
set "shortcutPath=%USERPROFILE%\Desktop\YouTube Downloader.lnk"

if "%PYTHON_CMD%"=="py" (
    powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%shortcutPath%'); $Shortcut.TargetPath = 'py'; $Shortcut.Arguments = '%currentDir%\main.py'; $Shortcut.WorkingDirectory = '%currentDir%'; $Shortcut.Save()"
) else (
    powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%shortcutPath%'); $Shortcut.TargetPath = 'python'; $Shortcut.Arguments = '%currentDir%\main.py'; $Shortcut.WorkingDirectory = '%currentDir%'; $Shortcut.Save()"
)

echo.
echo ================================
echo         Installation Complete!
echo ================================
echo.
echo How to use:
echo 1. Double-click "YouTube Downloader" shortcut on desktop
if "%PYTHON_CMD%"=="py" (
    echo 2. Or run: py main.py
    echo 3. Enhanced version: py enhanced_downloader.py
) else (
    echo 2. Or run: python main.py
    echo 3. Enhanced version: python enhanced_downloader.py
)
echo.
echo Starting YouTube Downloader...

REM Try to start the program
%PYTHON_CMD% -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo Warning: GUI library not available
    echo The program may not display properly
    echo Please reinstall Python with tkinter support
    pause
) else (
    echo Starting program...
    start "" %PYTHON_CMD% main.py
    timeout /t 3 /nobreak >nul
    echo If program started, you can close this window
    pause
) 