@echo off
chcp 65001 >nul
title YouTube下载器 - 打包构建脚本

echo.
echo ========================================
echo    YouTube下载器 自动打包构建脚本
echo ========================================
echo.

REM 检查Python是否安装
echo [1/6] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到Python，请先安装Python
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python版本：%PYTHON_VERSION%

REM 检查pip是否可用
echo.
echo [2/6] 检查pip环境...
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：pip不可用
    pause
    exit /b 1
)
echo ✅ pip检查通过

REM 安装依赖包
echo.
echo [3/6] 安装项目依赖...
if exist requirements.txt (
    echo 正在安装requirements.txt中的依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 部分依赖包安装失败，尝试逐个安装...
        
        echo 安装最新版本的yt-dlp...
        pip install --upgrade yt-dlp
        
        echo 安装Pillow...
        pip install Pillow>=8.0.0
        
        echo 安装requests...
        pip install requests>=2.25.0
        
        echo 安装ffmpeg-python...
        pip install ffmpeg-python>=0.2.0
    ) else (
        echo 强制更新yt-dlp到最新版本（解决YouTube API变化问题）...
        pip install --upgrade yt-dlp
    )
    echo ✅ 依赖包安装完成
) else (
    echo ⚠️  未找到requirements.txt文件，安装核心依赖...
    echo 安装最新版本的yt-dlp...
    pip install --upgrade yt-dlp
    echo 安装其他核心依赖...
    pip install Pillow>=8.0.0 requests>=2.25.0 ffmpeg-python>=0.2.0
)

REM 安装PyInstaller
echo.
echo [4/6] 安装PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo ❌ PyInstaller安装失败
    pause
    exit /b 1
)
echo ✅ PyInstaller安装完成

REM 清理之前的构建文件
echo.
echo [5/6] 清理构建环境...
if exist "dist" (
    echo 清理dist目录...
    rmdir /s /q "dist" 2>nul
)
if exist "build" (
    echo 清理build目录...
    rmdir /s /q "build" 2>nul
)
if exist "*.spec" (
    echo 发现现有的spec文件，将使用现有配置
)
echo ✅ 构建环境清理完成

REM 开始打包
echo.
echo [6/6] 开始打包exe文件...
echo 这个过程可能需要几分钟，请耐心等待...
echo.

REM 检查是否存在spec文件
if exist "YouTube下载器.spec" (
    echo 使用现有的spec配置文件进行打包...
    pyinstaller "YouTube下载器.spec"
) else (
    echo 使用默认配置进行打包...
    pyinstaller --onefile --windowed --name="YouTube下载器" --add-data="config.py;." --hidden-import=requests --hidden-import=PIL --hidden-import=PIL.Image --hidden-import=PIL.ImageTk --hidden-import=yt_dlp --hidden-import=tkinter main.py
)

if errorlevel 1 (
    echo.
    echo ❌ 打包失败！
    echo 可能的原因：
    echo 1. 缺少依赖模块
    echo 2. main.py文件有错误
    echo 3. 系统权限不足
    echo.
    echo 建议解决方案：
    echo 1. 运行 python main.py 检查程序是否正常运行
    echo 2. 确保所有依赖都已正确安装
    echo 3. 以管理员身份运行此脚本
    pause
    exit /b 1
)

echo.
echo ========================================
echo          🎉 打包完成！ 🎉
echo ========================================
echo.
echo 生成的exe文件位置：
if exist "dist\YouTube下载器.exe" (
    echo ✅ dist\YouTube下载器.exe
    echo.
    echo 文件大小：
    for %%A in ("dist\YouTube下载器.exe") do (
        echo %%~zA 字节
    )
) else (
    if exist "dist\main.exe" (
        echo ✅ dist\main.exe
        echo.
        echo 文件大小：
        for %%A in ("dist\main.exe") do (
            echo %%~zA 字节
        )
    ) else (
        echo ❓ 在dist目录中查找exe文件...
        dir /b "dist\*.exe" 2>nul
    )
)

echo.
echo 📁 打开输出目录？
choice /c YN /n /m "按 Y 打开dist目录，按 N 退出 [Y/N]: "
if errorlevel 2 goto :end
if errorlevel 1 (
    if exist "dist" (
        start "" "dist"
    ) else (
        echo 未找到dist目录
    )
)

:end
echo.
echo ========================================
echo          📝 重要提示
echo ========================================
echo.
echo 🔄 关于"Failed to extract any player response"错误：
echo    这通常是因为YouTube更新了API，需要更新yt-dlp
echo.    
echo    解决方案：
echo    1. 本脚本已自动更新yt-dlp到最新版本
echo    2. 如果仍有问题，请在命令行运行: pip install --upgrade yt-dlp
echo    3. 或者直接运行生成的exe文件，它包含最新版本
echo.
echo 🛡️  如果在其他电脑上使用exe文件时出现此错误：
echo    说明该电脑的网络环境或yt-dlp版本有问题
echo    exe文件已包含最新版本，通常可以正常工作
echo.
echo 构建脚本执行完成！
echo 如有问题，请检查上方的错误信息。
echo.
pause 