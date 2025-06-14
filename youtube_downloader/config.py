import json
import os
from pathlib import Path

class Config:
    def __init__(self):
        self.config_file = "settings.json"
        self.default_settings = {
            "download_path": os.path.join(os.path.expanduser("~"), "Desktop"),
            "default_quality": "最佳质量(视频+音频)",
            "default_format": "MP4",
            "auto_merge": True,
            "download_subtitles": False,
            "theme": "default",
            "language": "zh-CN",
            "max_concurrent_downloads": 3,
            "ffmpeg_path": "",
            "proxy": "",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.settings = self.load_settings()
    
    def load_settings(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                # 合并默认设置和加载的设置
                settings = self.default_settings.copy()
                settings.update(loaded_settings)
                return settings
        except Exception as e:
            print(f"配置文件加载失败: {e}")
        
        return self.default_settings.copy()
    
    def save_settings(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"配置文件保存失败: {e}")
            return False
    
    def get(self, key, default=None):
        """获取配置项"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """设置配置项"""
        self.settings[key] = value
        self.save_settings()
    
    def reset_to_default(self):
        """重置为默认设置"""
        self.settings = self.default_settings.copy()
        self.save_settings()

# 全局配置实例
config = Config() 