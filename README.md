# YouTube视频下载器

一个基于Python和yt-dlp的YouTube视频下载工具，具有图形化用户界面。

## 功能特点

- 🎥 支持下载YouTube视频（多种清晰度选择）
- 🎵 支持仅下载音频（MP3格式）
- 🖥️ 简洁的图形化界面
- 📁 自定义下载路径
- ℹ️ 显示视频详细信息
- 🔄 实时下载进度显示

## 一键安装（推荐）

**首次使用请直接运行：**
```bash
双击 install.bat
```

安装脚本会自动：
- ✅ 检查并安装Python环境
- ✅ 检查tkinter GUI库
- ✅ 安装所有Python依赖包
- ✅ 尝试自动安装FFmpeg
- ✅ 创建桌面快捷方式

## 使用方法

**方式一：双击运行**
```bash
双击 run.bat
```

**方式二：命令行运行**
```bash
python main.py
```

**使用步骤：**
1. 在"视频网址"输入框中粘贴YouTube视频链接
2. 点击"获取视频信息"查看视频详情
3. 选择下载质量和保存路径
4. 点击"开始下载"

## 环境诊断

如果遇到问题，可以运行：
```bash
双击 check_env.bat
```
会自动诊断所有环境依赖并给出解决方案。

## 支持的视频质量

- 最佳质量(视频+音频)
- 1080p
- 720p  
- 480p
- 360p
- 仅音频(MP3)

## 打包成exe文件

使用PyInstaller将程序打包成exe文件：

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "YouTube下载器" main.py
```

## 注意事项

- 请确保网络连接正常
- 部分视频可能由于版权限制无法下载
- 建议在下载前先获取视频信息确认可用性

## 依赖库

- yt-dlp: YouTube视频下载核心库
- tkinter: GUI界面库
- threading: 多线程处理 