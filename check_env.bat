@echo off
chcp 65001 >nul 2>&1
title 环境诊断工具
echo ================================
echo      环境诊断工具
echo ================================
echo.

echo 正在诊断运行环境...
echo.

REM 检查Python版本
echo [1/6] Python版本检查:
python --version 2>nul
if errorlevel 1 (
    echo   状态: 未安装 ❌
    echo   解决: 请运行 install.bat 自动安装
) else (
    echo   状态: 已安装 ✓
)
echo.

REM 检查pip
echo [2/6] pip包管理器检查:
pip --version >nul 2>&1
if errorlevel 1 (
    echo   状态: 未安装 ❌
    echo   解决: 通常随Python一起安装
) else (
    echo   状态: 已安装 ✓
)
echo.

REM 检查tkinter
echo [3/6] tkinter GUI库检查:
python -c "import tkinter; print('  版本:', tkinter.TkVersion)" 2>nul
if errorlevel 1 (
    echo   状态: 未安装 ❌
    echo   解决: 重新安装Python时选择tcl/tk组件
) else (
    echo   状态: 已安装 ✓
)
echo.

REM 检查yt-dlp
echo [4/6] yt-dlp下载库检查:
python -c "import yt_dlp; print('  版本:', yt_dlp.version.__version__)" 2>nul
if errorlevel 1 (
    echo   状态: 未安装 ❌
    echo   解决: 运行 pip install yt-dlp
) else (
    echo   状态: 已安装 ✓
)
echo.

REM 检查FFmpeg
echo [5/6] FFmpeg音视频处理检查:
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo   状态: 未安装 ⚠️
    echo   影响: 无法合并高清视频和音频
    echo   解决: 运行 install.bat 自动安装
) else (
    echo   状态: 已安装 ✓
)
echo.

REM 检查网络连接
echo [6/6] 网络连接检查:
ping -n 1 youtube.com >nul 2>&1
if errorlevel 1 (
    echo   状态: 网络连接异常 ⚠️
    echo   影响: 可能无法下载视频
    echo   解决: 检查网络连接或代理设置
) else (
    echo   状态: 网络正常 ✓
)
echo.

echo ================================
echo        诊断完成
echo ================================
echo.
echo 💡 解决方案：
echo   • 如果环境有问题：运行 install.bat 自动修复
echo   • 如果要测试程序：运行 python main.py  
echo   • 如果要打包exe：运行 build.bat
echo.
echo 📝 说明：此工具仅用于诊断，不会修改您的系统
echo.
pause 