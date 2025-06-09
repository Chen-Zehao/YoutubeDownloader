@echo off
chcp 65001 >nul 2>&1
title YouTube下载器
cd /d "%~dp0"

echo ================================
echo      YouTube下载器
echo ================================
echo.

REM 检查Python环境
echo 正在检查运行环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Python未安装！
    echo 请先运行 install.bat 安装环境
    pause
    exit /b 1
)

REM 检查tkinter
python -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo 错误: tkinter GUI库未安装！
    echo 这通常是因为Python安装不完整
    echo 请先运行 install.bat 修复环境
    pause
    exit /b 1
)

REM 检查yt-dlp
python -c "import yt_dlp" >nul 2>&1
if errorlevel 1 (
    echo 错误: yt-dlp库未安装！
    echo 请先运行 install.bat 安装依赖
    pause
    exit /b 1
)

echo 环境检查通过！
echo.
echo 选择操作:
echo [1] 启动YouTube下载器
echo [2] 重新安装环境
echo [3] 退出
echo.
set /p choice="请选择 (1-3): "

if "%choice%"=="1" (
    echo 正在启动YouTube下载器...
    python main.py
) else if "%choice%"=="2" (
    echo 正在启动环境安装...
    call install.bat
) else if "%choice%"=="3" (
    echo 再见！
    timeout /t 2 >nul
    exit /b 0
) else (
    echo 无效选择，启动YouTube下载器...
    python main.py
)

pause 