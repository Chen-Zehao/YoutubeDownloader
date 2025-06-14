@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title YouTube Downloader - Build Script

echo.
echo ========================================
echo    YouTube Downloader Build Script
echo ========================================
echo.

REM Check Python installation
echo [1/6] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found, please install Python first
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo OK: Python version: !PYTHON_VERSION!

REM Check pip availability
echo.
echo [2/6] Checking pip environment...
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    pause
    exit /b 1
)
echo OK: pip check passed

REM Install dependencies
echo.
echo [3/6] Installing project dependencies...
if exist requirements.txt (
    echo Installing dependencies from requirements.txt...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo WARNING: Some dependencies failed to install, trying individual installation...
        
        echo Installing latest yt-dlp...
        pip install --upgrade yt-dlp
        
        echo Installing Pillow...
        pip install Pillow>=8.0.0
        
        echo Installing requests...
        pip install requests>=2.25.0
        
        echo Installing ffmpeg-python...
        pip install ffmpeg-python>=0.2.0
    ) else (
        echo Force updating yt-dlp to latest version...
        pip install --upgrade yt-dlp
    )
    echo OK: Dependencies installation completed
) else (
    echo WARNING: requirements.txt not found, installing core dependencies...
    echo Installing latest yt-dlp...
    pip install --upgrade yt-dlp
    echo Installing other core dependencies...
    pip install Pillow>=8.0.0 requests>=2.25.0 ffmpeg-python>=0.2.0
)

REM Install PyInstaller
echo.
echo [4/6] Installing PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo ERROR: PyInstaller installation failed
    pause
    exit /b 1
)
echo OK: PyInstaller installation completed

REM Clean previous build files
echo.
echo [5/6] Cleaning build environment...
if exist "dist" (
    echo Cleaning dist directory...
    rmdir /s /q "dist" 2>nul
)
if exist "build" (
    echo Cleaning build directory...
    rmdir /s /q "build" 2>nul
)
if exist "*.spec" (
    echo Found existing spec file, will use existing configuration
)
echo OK: Build environment cleanup completed

REM Start packaging
echo.
echo [6/6] Starting exe packaging...
echo This process may take several minutes, please wait...
echo.

REM Check if spec file exists
if exist "YouTube下载器.spec" (
    echo Using existing spec configuration file for packaging...
    pyinstaller "YouTube下载器.spec"
) else (
    echo Using default configuration for packaging...
    pyinstaller --onefile --windowed --name="YouTube下载器" --add-data="config.py;." --hidden-import=requests --hidden-import=PIL --hidden-import=PIL.Image --hidden-import=PIL.ImageTk --hidden-import=yt_dlp --hidden-import=tkinter main.py
)

if errorlevel 1 (
    echo.
    echo ERROR: Packaging failed!
    echo Possible causes:
    echo 1. Missing dependency modules
    echo 2. Errors in main.py file
    echo 3. Insufficient system permissions
    echo.
    echo Suggested solutions:
    echo 1. Run 'python main.py' to check if program runs normally
    echo 2. Ensure all dependencies are correctly installed
    echo 3. Run this script as administrator
    pause
    exit /b 1
)

echo.
echo ========================================
echo          BUILD COMPLETED!
echo ========================================
echo.
echo Generated exe file location:
if exist "dist\YouTube下载器.exe" (
    echo OK: dist\YouTube下载器.exe
    echo.
    echo File size:
    for %%A in ("dist\YouTube下载器.exe") do (
        echo %%~zA bytes
    )
) else (
    if exist "dist\main.exe" (
        echo OK: dist\main.exe
        echo.
        echo File size:
        for %%A in ("dist\main.exe") do (
            echo %%~zA bytes
        )
    ) else (
        echo Searching for exe files in dist directory...
        dir /b "dist\*.exe" 2>nul
    )
)

echo.
echo Open output directory?
choice /c YN /n /m "Press Y to open dist directory, N to exit [Y/N]: "
if errorlevel 2 goto :end
if errorlevel 1 (
    if exist "dist" (
        start "" "dist"
    ) else (
        echo dist directory not found
    )
)

:end
echo.
echo ========================================
echo          IMPORTANT NOTES
echo ========================================
echo.
echo About "Failed to extract any player response" error:
echo This usually happens when YouTube updates API, need to update yt-dlp
echo.    
echo Solutions:
echo 1. This script has automatically updated yt-dlp to latest version
echo 2. If still having issues, run: pip install --upgrade yt-dlp
echo 3. Or directly run the generated exe file with latest version
echo.
echo If encountering this error on other computers:
echo The exe file contains the latest version and should work normally
echo.
echo Build script execution completed!
echo If there are issues, please check the error messages above.
echo.
pause 