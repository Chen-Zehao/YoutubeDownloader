"""
下载管理模块 - 处理视频下载相关的功能
"""
import yt_dlp
import threading
import os
import time
import shutil


class VideoDownloader:
    """下载管理类"""
    
    def __init__(self, parent):
        self.parent = parent
        
    def get_video_info(self, url):
        """获取视频信息"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            raise Exception(f"获取视频信息失败: {str(e)}")
    
    def format_duration(self, seconds):
        """格式化时长"""
        try:
            seconds = int(seconds)
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes:02d}:{seconds:02d}"
        except:
            return "未知"
    
    def clean_filename(self, filename):
        """清理文件名中的非法字符"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # 限制文件名长度
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200-len(ext)] + ext
        
        return filename
    
    def progress_hook(self, d):
        """下载进度回调"""
        if self.parent.download_paused:
            return
            
        if d['status'] == 'downloading':
            try:
                if 'total_bytes' in d and d['total_bytes']:
                    total_bytes = d['total_bytes']
                elif 'total_bytes_estimate' in d and d['total_bytes_estimate']:
                    total_bytes = d['total_bytes_estimate']
                else:
                    total_bytes = None
                
                if total_bytes and 'downloaded_bytes' in d:
                    downloaded_bytes = d['downloaded_bytes']
                    percentage = (downloaded_bytes / total_bytes) * 100
                    
                    # 格式化文件大小
                    def format_bytes(bytes_val):
                        for unit in ['B', 'KB', 'MB', 'GB']:
                            if bytes_val < 1024.0:
                                return f"{bytes_val:.1f}{unit}"
                            bytes_val /= 1024.0
                        return f"{bytes_val:.1f}TB"
                    
                    downloaded_str = format_bytes(downloaded_bytes)
                    total_str = format_bytes(total_bytes)
                    
                    # 计算速度
                    speed = d.get('speed', 0)
                    if speed:
                        speed_str = format_bytes(speed) + "/s"
                    else:
                        speed_str = "计算中..."
                    
                    # 计算剩余时间
                    eta = d.get('eta', 0)
                    if eta:
                        eta_str = f"{eta}秒"
                    else:
                        eta_str = "计算中..."
                    
                    status_text = f"📥 正在下载: {percentage:.1f}% ({downloaded_str}/{total_str}) - 速度: {speed_str} - 剩余: {eta_str}"
                    
                    self.parent.root.after(0, lambda: self.parent.update_progress(percentage, status_text))
                else:
                    # 无法获取总大小时显示已下载量
                    downloaded_bytes = d.get('downloaded_bytes', 0)
                    if downloaded_bytes:
                        downloaded_str = self.format_bytes(downloaded_bytes)
                        status_text = f"📥 正在下载: {downloaded_str} (大小未知)"
                    else:
                        status_text = "📥 正在下载..."
                    
                    self.parent.root.after(0, lambda: self.parent.update_progress(0, status_text))
                    
            except Exception as e:
                print(f"进度更新错误: {e}")
                
        elif d['status'] == 'finished':
            filename = os.path.basename(d['filename'])
            status_text = f"✅ 下载完成: {filename}"
            self.parent.root.after(0, lambda: self.parent.update_progress(100, status_text))
    
    def video_progress_hook(self, d):
        """视频下载进度回调"""
        if self.parent.download_paused:
            return
            
        if d['status'] == 'downloading':
            try:
                if 'total_bytes' in d and d['total_bytes']:
                    total_bytes = d['total_bytes']
                elif 'total_bytes_estimate' in d and d['total_bytes_estimate']:
                    total_bytes = d['total_bytes_estimate']
                else:
                    total_bytes = None
                
                if total_bytes and 'downloaded_bytes' in d:
                    downloaded_bytes = d['downloaded_bytes']
                    percentage = (downloaded_bytes / total_bytes) * 100
                    
                    status_text = f"🎬 下载视频: {percentage:.1f}%"
                    self.parent.root.after(0, lambda: self.parent.update_progress(percentage * 0.6, status_text))
                else:
                    status_text = "🎬 正在下载视频..."
                    self.parent.root.after(0, lambda: self.parent.update_progress(0, status_text))
                    
            except Exception as e:
                print(f"视频进度更新错误: {e}")
                
        elif d['status'] == 'finished':
            self.parent.video_file = d['filename']
            status_text = "✅ 视频下载完成"
            self.parent.root.after(0, lambda: self.parent.update_progress(60, status_text))
    
    def audio_progress_hook(self, d):
        """音频下载进度回调"""
        if self.parent.download_paused:
            return
            
        if d['status'] == 'downloading':
            try:
                if 'total_bytes' in d and d['total_bytes']:
                    total_bytes = d['total_bytes']
                elif 'total_bytes_estimate' in d and d['total_bytes_estimate']:
                    total_bytes = d['total_bytes_estimate']
                else:
                    total_bytes = None
                
                if total_bytes and 'downloaded_bytes' in d:
                    downloaded_bytes = d['downloaded_bytes']
                    percentage = (downloaded_bytes / total_bytes) * 100
                    
                    status_text = f"🎵 下载音频: {percentage:.1f}%"
                    # 音频下载占30%的进度 (从60%到90%)
                    progress = 60 + (percentage * 0.3)
                    self.parent.root.after(0, lambda: self.parent.update_progress(progress, status_text))
                else:
                    status_text = "🎵 正在下载音频..."
                    self.parent.root.after(0, lambda: self.parent.update_progress(60, status_text))
                    
            except Exception as e:
                print(f"音频进度更新错误: {e}")
                
        elif d['status'] == 'finished':
            self.parent.audio_file = d['filename']
            status_text = "✅ 音频下载完成"
            self.parent.root.after(0, lambda: self.parent.update_progress(90, status_text))
    
    def format_bytes(self, bytes_val):
        """格式化字节数"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f}{unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f}TB"
    
    def check_disk_space(self, path, required_size_mb=1000):
        """检查磁盘空间"""
        try:
            free_bytes = shutil.disk_usage(path).free
            free_mb = free_bytes / (1024 * 1024)
            return free_mb >= required_size_mb
        except:
            return True
    
    def get_estimated_size(self, url):
        """获取预估文件大小"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'listformats': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                
                max_size = 0
                for fmt in formats:
                    if fmt.get('filesize'):
                        max_size = max(max_size, fmt['filesize'])
                    elif fmt.get('filesize_approx'):
                        max_size = max(max_size, fmt['filesize_approx'])
                
                return max_size / (1024 * 1024)  # 转换为MB
        except:
            return 100  # 默认100MB
    
    def execute_download(self, url, download_path, quality):
        """执行下载"""
        try:
            # 获取格式信息
            info = self.get_video_info(url)
            title = info.get('title', 'video')
            clean_title = self.clean_filename(title)
            
            # 设置下载选项
            if quality == "🔧 分离下载合并":
                # 分离下载模式
                self.parent.download_stage = "downloading_video"
                
                # 下载视频（无音频）
                video_opts = {
                    'format': 'bestvideo[ext=mp4]/bestvideo',
                    'outtmpl': os.path.join(download_path, f'{clean_title}_video.%(ext)s'),
                    'progress_hooks': [self.video_progress_hook],
                }
                
                with yt_dlp.YoutubeDL(video_opts) as ydl:
                    ydl.download([url])
                
                # 下载音频
                self.parent.download_stage = "downloading_audio"
                
                audio_opts = {
                    'format': 'bestaudio[ext=m4a]/bestaudio',
                    'outtmpl': os.path.join(download_path, f'{clean_title}_audio.%(ext)s'),
                    'progress_hooks': [self.audio_progress_hook],
                }
                
                with yt_dlp.YoutubeDL(audio_opts) as ydl:
                    ydl.download([url])
                
                # 合并视频和音频
                if self.parent.video_file and self.parent.audio_file:
                    self.parent.download_stage = "merging"
                    output_file = os.path.join(download_path, f'{clean_title}.mp4')
                    self.parent.ffmpeg_manager.merge_video_audio(
                        self.parent.video_file, 
                        self.parent.audio_file, 
                        output_file
                    )
                    
                    # 清理临时文件
                    try:
                        os.remove(self.parent.video_file)
                        os.remove(self.parent.audio_file)
                    except:
                        pass
                        
            else:
                # 普通下载模式
                format_selector = self._get_format_selector(quality)
                
                ydl_opts = {
                    'format': format_selector,
                    'outtmpl': os.path.join(download_path, f'{clean_title}.%(ext)s'),
                    'progress_hooks': [self.progress_hook],
                    'retries': 3,
                    'fragment_retries': 3,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            
            return True
            
        except Exception as e:
            raise Exception(f"下载失败: {str(e)}")
    
    def _get_format_selector(self, quality):
        """根据质量选择获取格式选择器"""
        quality_map = {
            "🎯 最佳质量": "best[ext=mp4]/best",
            "📱 手机友好": "best[height<=480][ext=mp4]/best[height<=480]",
            "💻 电脑观看": "best[height<=720][ext=mp4]/best[height<=720]",
            "🖥️ 高清观看": "best[height<=1080][ext=mp4]/best[height<=1080]",
            "🎬 超高清": "best[height<=1440][ext=mp4]/best[height<=1440]",
            "🔥 极清画质": "best[height<=2160][ext=mp4]/best[height<=2160]",
            "🎵 仅音频": "bestaudio[ext=m4a]/bestaudio",
        }
        
        return quality_map.get(quality, "best[ext=mp4]/best") 