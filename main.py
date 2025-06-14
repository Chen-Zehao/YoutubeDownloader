#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube下载器 - 启动入口

从youtube-downloader包启动应用程序
"""

import sys
import os
20秒
# 将当前目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # 导入并启动应用程序
    from youtube_downloader.main import main
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有依赖已安装：pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"启动错误: {e}")
    sys.exit(1) 