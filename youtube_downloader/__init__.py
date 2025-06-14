"""
YouTube Downloader Package
A simple YouTube video downloader with GUI interface.
"""

__version__ = "1.0.0"
__author__ = "Chen-Zehao"
__description__ = "YouTube video downloader with GUI interface"

# 导入主要组件
from .main import main, YouTubeDownloaderApp
from .gui_interface import GuiInterface
from .video_downloader import VideoDownloader
from .ffmpeg_tools import FFmpegTools
from .config import * 