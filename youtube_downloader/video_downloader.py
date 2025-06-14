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
        # 添加大小缓存，防止总大小动态变化
        self._cached_total_bytes = {}  # 缓存每个下载任务的总大小
        self._download_id = 0  # 下载任务ID计数器
        self._prefetched_sizes = {}  # 预获取的文件大小信息
        self._current_download_type = "main"  # 当前下载类型标识
        
    def get_video_info(self, url):
        """获取视频信息"""
        import signal
        import threading
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'socket_timeout': 20,  # 添加20秒网络超时
        }
        
        result = [None]
        exception = [None]
        
        def extract_info():
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    result[0] = info
            except Exception as e:
                exception[0] = e
        
        # 创建线程执行操作
        thread = threading.Thread(target=extract_info)
        thread.daemon = True
        thread.start()
        
        # 等待最多20秒
        thread.join(20)
        
        if thread.is_alive():
            # 超时了，抛出超时错误
            raise Exception("网络连接超时或无法访问YouTube\n\n请检查：\n1. 网络连接是否正常\n2. 是否能够访问YouTube网站\n3. 防火墙或代理设置\n")
        
        if exception[0]:
            error_msg = str(exception[0])
            # 检查是否为网络连接相关错误
            if any(keyword in error_msg.lower() for keyword in ['timeout', 'connection', 'network', 'resolve', 'unreachable', 'failed to extract']):
                raise Exception(f"网络连接超时或无法访问YouTube\n\n请检查：\n1. 网络连接是否正常\n2. 是否能够访问YouTube网站\n3. 防火墙或代理设置\n\n详细错误信息：{error_msg}")
            else:
                raise Exception(f"获取视频信息失败: {error_msg}")
        
        return result[0]
    
    def _get_stable_total_bytes(self, d, download_type="main"):
        """获取稳定的总字节数，避免动态变化"""
        # 为每个下载任务生成唯一标识
        task_key = f"{download_type}_{self._download_id}"
        
        # 优先使用预获取的大小信息
        if download_type in self._prefetched_sizes:
            prefetched_size = self._prefetched_sizes[download_type]
            if prefetched_size and prefetched_size > 0:
                # 如果还没有缓存，则缓存预获取的大小
                if task_key not in self._cached_total_bytes:
                    self._cached_total_bytes[task_key] = prefetched_size
                    print(f"📏 [{download_type}] 使用预获取的文件大小: {self.format_bytes(prefetched_size)}")
                return prefetched_size
        
        # 如果已经缓存了总大小，直接返回
        if task_key in self._cached_total_bytes:
            cached_size = self._cached_total_bytes[task_key]
            # 验证缓存的数据是否合理
            if cached_size and cached_size > 0:
                return cached_size
            else:
                print(f"⚠️ [{download_type}] 缓存的总大小异常: {cached_size}")
                # 清除异常缓存
                del self._cached_total_bytes[task_key]
        
        # 尝试从下载数据中获取总字节数
        total_bytes = None
        if 'total_bytes' in d and d['total_bytes'] and d['total_bytes'] > 0:
            total_bytes = d['total_bytes']
            print(f"📏 [{download_type}] 从下载数据获取总大小: {self.format_bytes(total_bytes)}")
        elif 'total_bytes_estimate' in d and d['total_bytes_estimate'] and d['total_bytes_estimate'] > 0:
            total_bytes = d['total_bytes_estimate']
            print(f"📏 [{download_type}] 从估算数据获取总大小: {self.format_bytes(total_bytes)}")
        
        # 验证获取到的总大小是否合理
        if total_bytes and total_bytes > 0:
            # 如果总大小小于1KB，可能是异常数据
            if total_bytes < 1024:
                print(f"⚠️ [{download_type}] 获取到的总大小可能异常: {total_bytes} bytes")
                # 不缓存异常数据
                return None
            
            # 检查是否与预获取的大小差异过大
            if download_type in self._prefetched_sizes:
                prefetched_size = self._prefetched_sizes[download_type]
                if prefetched_size and prefetched_size > 0:
                    diff_ratio = abs(total_bytes - prefetched_size) / prefetched_size
                    if diff_ratio > 0.5:  # 差异超过50%
                        print(f"⚠️ [{download_type}] 下载时获取的大小与预获取大小差异过大: " +
                              f"预获取={self.format_bytes(prefetched_size)}, " +
                              f"实际={self.format_bytes(total_bytes)}, " +
                              f"差异={diff_ratio*100:.1f}%")
                        # 优先使用预获取的大小
                        self._cached_total_bytes[task_key] = prefetched_size
                        return prefetched_size
            
            self._cached_total_bytes[task_key] = total_bytes
            print(f"📏 [{download_type}] 缓存文件总大小: {self.format_bytes(total_bytes)}")
            
        return total_bytes
    
    def _clear_size_cache(self):
        """清理大小缓存（在开始新下载时调用）"""
        self._cached_total_bytes.clear()
        self._prefetched_sizes.clear()
        self._download_id += 1
    
    def prefetch_file_sizes(self, url, quality):
        """预获取文件大小信息"""
        try:
            # 获取视频信息
            info = self.get_video_info(url)
            formats = info.get('formats', [])
            
            if not formats:
                print("⚠️ 无法获取视频格式信息")
                return False
            
            # 判断下载模式并获取对应的格式大小
            if ("分离合并" in quality) or (quality.startswith("🎯 最佳画质") and hasattr(self.parent, 'needs_merge') and self.parent.needs_merge):
                # 分离下载模式：获取视频和音频的大小
                video_size = self._get_best_video_size(formats)
                audio_size = self._get_best_audio_size(formats)
                
                self._prefetched_sizes['video'] = video_size
                self._prefetched_sizes['audio'] = audio_size
                
                total_size = (video_size or 0) + (audio_size or 0)
                if total_size > 0:
                    self._prefetched_sizes['total'] = total_size
                
                print(f"📏 预获取大小 - 视频: {self.format_bytes(video_size) if video_size else '未知'}, " +
                      f"音频: {self.format_bytes(audio_size) if audio_size else '未知'}, " +
                      f"总计: {self.format_bytes(total_size) if total_size > 0 else '未知'}")
            else:
                # 普通下载模式：获取完整文件大小
                format_selector = self._get_format_selector(quality)
                file_size = self._get_format_size_by_selector(formats, format_selector)
                
                if file_size:
                    self._prefetched_sizes['main'] = file_size
                    self._prefetched_sizes['total'] = file_size
                    print(f"📏 预获取文件大小: {self.format_bytes(file_size)}")
                else:
                    print("⚠️ 无法预获取文件大小，将在下载时动态计算")
            
            return True
            
        except Exception as e:
            print(f"⚠️ 预获取文件大小失败: {e}")
            return False
    
    def _get_best_video_size(self, formats):
        """获取最佳视频格式的文件大小"""
        try:
            # 按分辨率排序，选择最高质量的视频格式
            video_formats = []
            for fmt in formats:
                if (fmt.get('vcodec') != 'none' and 
                    fmt.get('acodec') == 'none' and 
                    fmt.get('height') and 
                    fmt.get('filesize')):
                    video_formats.append(fmt)
            
            if not video_formats:
                # 如果没有filesize，尝试filesize_approx
                for fmt in formats:
                    if (fmt.get('vcodec') != 'none' and 
                        fmt.get('acodec') == 'none' and 
                        fmt.get('height') and 
                        fmt.get('filesize_approx')):
                        video_formats.append(fmt)
            
            if video_formats:
                # 按分辨率从高到低排序
                video_formats.sort(key=lambda x: x.get('height', 0), reverse=True)
                best_video = video_formats[0]
                return best_video.get('filesize') or best_video.get('filesize_approx')
            
            return None
        except Exception as e:
            print(f"获取最佳视频大小失败: {e}")
            return None
    
    def _get_best_audio_size(self, formats):
        """获取最佳音频格式的文件大小"""
        try:
            # 选择最高质量的音频格式
            audio_formats = []
            for fmt in formats:
                if (fmt.get('acodec') != 'none' and 
                    fmt.get('vcodec') == 'none' and 
                    fmt.get('filesize')):
                    audio_formats.append(fmt)
            
            if not audio_formats:
                # 如果没有filesize，尝试filesize_approx
                for fmt in formats:
                    if (fmt.get('acodec') != 'none' and 
                        fmt.get('vcodec') == 'none' and 
                        fmt.get('filesize_approx')):
                        audio_formats.append(fmt)
            
            if audio_formats:
                # 按比特率从高到低排序
                audio_formats.sort(key=lambda x: x.get('abr', 0), reverse=True)
                best_audio = audio_formats[0]
                return best_audio.get('filesize') or best_audio.get('filesize_approx')
            
            return None
        except Exception as e:
            print(f"获取最佳音频大小失败: {e}")
            return None
    
    def _get_format_size_by_selector(self, formats, format_selector):
        """根据格式选择器获取文件大小"""
        try:
            # 解析格式选择器
            if 'bestvideo' in format_selector:
                return self._get_best_video_size(formats)
            elif 'bestaudio' in format_selector:
                return self._get_best_audio_size(formats)
            elif 'best' in format_selector:
                # 获取最佳完整格式
                best_formats = []
                for fmt in formats:
                    if (fmt.get('vcodec') != 'none' and 
                        fmt.get('acodec') != 'none' and 
                        fmt.get('filesize')):
                        best_formats.append(fmt)
                
                if not best_formats:
                    for fmt in formats:
                        if (fmt.get('vcodec') != 'none' and 
                            fmt.get('acodec') != 'none' and 
                            fmt.get('filesize_approx')):
                            best_formats.append(fmt)
                
                if best_formats:
                    # 按分辨率从高到低排序
                    best_formats.sort(key=lambda x: x.get('height', 0), reverse=True)
                    best_format = best_formats[0]
                    return best_format.get('filesize') or best_format.get('filesize_approx')
            
            # 处理特定分辨率的格式选择器
            import re
            height_match = re.search(r'height<=(\d+)', format_selector)
            if height_match:
                target_height = int(height_match.group(1))
                matching_formats = []
                
                for fmt in formats:
                    if (fmt.get('height') and 
                        fmt.get('height') <= target_height and
                        fmt.get('filesize')):
                        matching_formats.append(fmt)
                
                if not matching_formats:
                    for fmt in formats:
                        if (fmt.get('height') and 
                            fmt.get('height') <= target_height and
                            fmt.get('filesize_approx')):
                            matching_formats.append(fmt)
                
                if matching_formats:
                    # 按分辨率从高到低排序
                    matching_formats.sort(key=lambda x: x.get('height', 0), reverse=True)
                    best_match = matching_formats[0]
                    return best_match.get('filesize') or best_match.get('filesize_approx')
            
            return None
        except Exception as e:
            print(f"根据选择器获取格式大小失败: {e}")
            return None
    
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
        """下载进度回调（用于单一文件下载）"""
        if self.parent.download_paused:
            return
            
        if d['status'] == 'downloading':
            try:
                # 优先使用fragment进度（适用于HLS等流媒体）
                if 'fragment_index' in d and 'fragment_count' in d:
                    fragment_index = d.get('fragment_index', 0)
                    fragment_count = d.get('fragment_count', 1)
                    
                    if fragment_count > 0:
                        percentage = (fragment_index / fragment_count) * 100
                        
                        # 获取文件大小信息
                        downloaded_bytes = d.get('downloaded_bytes', 0)
                        downloaded_str = self.format_bytes(downloaded_bytes) if downloaded_bytes else "未知"
                        
                        # 基于进度估算总大小（不完全精确但给用户参考）
                        if percentage > 0.5 and downloaded_bytes > 1024:  # 至少下载0.5%且超过1KB才估算
                            estimated_total = (downloaded_bytes / percentage) * 100
                            total_str = self.format_bytes(estimated_total)
                            size_info = f"({downloaded_str}/{total_str})"
                        else:
                            size_info = f"({downloaded_str})"
                        
                        # 计算和格式化速度
                        speed = d.get('speed', 0)
                        if speed and speed > 0:
                            speed_str = self.format_bytes(speed) + "/s"
                        else:
                            speed_str = "计算中..."
                        
                        # 计算剩余时间
                        eta = d.get('eta', 0)
                        if eta and eta > 0:
                            if eta < 60:
                                eta_str = f"{eta:.0f}秒"
                            elif eta < 3600:
                                eta_str = f"{eta//60:.0f}分{eta%60:.0f}秒"
                            else:
                                eta_str = f"{eta//3600:.0f}时{(eta%3600)//60:.0f}分"
                        else:
                            eta_str = "计算中..."
                        
                        status_text = f"📥 正在下载: {percentage:.1f}% {size_info} | 速度: {speed_str} | 剩余: {eta_str}"
                        self.parent.root.after(0, lambda: self.parent.update_progress(percentage, status_text))
                        return
                
                # 回退到字节进度计算（适用于普通下载）
                total_bytes = self._get_stable_total_bytes(d, "main")
                
                if total_bytes and 'downloaded_bytes' in d:
                    downloaded_bytes = d['downloaded_bytes']
                    
                    # 验证下载字节数是否合理
                    if downloaded_bytes < 0:
                        print(f"⚠️ [主文件] 异常的下载字节数: {downloaded_bytes}")
                        return
                    
                    percentage = (downloaded_bytes / total_bytes) * 100
                    
                    # HLS流的总大小经常不准确，如果超过120%就改为无百分比模式
                    if percentage > 120:
                        # 使用预获取的大小重新计算
                        if 'main' in self._prefetched_sizes:
                            prefetched_total = self._prefetched_sizes['main']
                            if prefetched_total and prefetched_total > 0:
                                percentage = (downloaded_bytes / prefetched_total) * 100
                                # 如果仍然超过120%，则使用无百分比模式
                                if percentage > 120:
                                    downloaded_str = self.format_bytes(downloaded_bytes)
                                    speed = d.get('speed', 0)
                                    speed_str = self.format_bytes(speed) + "/s" if speed else "计算中..."
                                    status_text = f"📥 正在下载: {downloaded_str} | 速度: {speed_str}"
                                    self.parent.root.after(0, lambda: self.parent.update_progress(50, status_text))
                                    return
                    
                    # 获取文件大小信息
                    downloaded_str = self.format_bytes(downloaded_bytes)
                    total_str = self.format_bytes(total_bytes)
                    size_info = f"({downloaded_str}/{total_str})"
                    
                    # 计算和格式化速度
                    speed = d.get('speed', 0)
                    if speed and speed > 0:
                        speed_str = self.format_bytes(speed) + "/s"
                    else:
                        speed_str = "计算中..."
                    
                    # 计算剩余时间
                    eta = d.get('eta', 0)
                    if eta and eta > 0:
                        if eta < 60:
                            eta_str = f"{eta:.0f}秒"
                        elif eta < 3600:
                            eta_str = f"{eta//60:.0f}分{eta%60:.0f}秒"
                        else:
                            eta_str = f"{eta//3600:.0f}时{(eta%3600)//60:.0f}分"
                    else:
                        eta_str = "计算中..."
                    
                    status_text = f"📥 正在下载: {percentage:.1f}% {size_info} | 速度: {speed_str} | 剩余: {eta_str}"
                    self.parent.root.after(0, lambda: self.parent.update_progress(percentage, status_text))
                else:
                    # 无法获取总大小时显示已下载量和速度
                    downloaded_bytes = d.get('downloaded_bytes', 0)
                    speed = d.get('speed', 0)
                    
                    if downloaded_bytes and speed:
                        downloaded_str = self.format_bytes(downloaded_bytes)
                        speed_str = self.format_bytes(speed) + "/s"
                        status_text = f"📥 正在下载: {downloaded_str} | 速度: {speed_str}"
                    else:
                        status_text = "📥 正在下载..."
                    
                    self.parent.root.after(0, lambda: self.parent.update_progress(50, status_text))
                    
            except Exception as e:
                print(f"进度更新错误: {e}")
                
        elif d['status'] == 'finished':
            file_size = self.format_bytes(os.path.getsize(d['filename']))
            status_text = f"✅ 下载完成 ({file_size})"
            self.parent.root.after(0, lambda: self.parent.update_progress(100, status_text))
    
    def video_progress_hook(self, d):
        """视频下载进度回调（用于分离下载模式）"""
        if self.parent.download_paused:
            return
            
        if d['status'] == 'downloading':
            try:
                # 优先使用fragment进度（适用于HLS等流媒体）
                if 'fragment_index' in d and 'fragment_count' in d:
                    fragment_index = d.get('fragment_index', 0)
                    fragment_count = d.get('fragment_count', 1)
                    
                    if fragment_count > 0:
                        percentage = (fragment_index / fragment_count) * 100
                        
                        # 获取文件大小信息
                        downloaded_bytes = d.get('downloaded_bytes', 0)
                        downloaded_str = self.format_bytes(downloaded_bytes) if downloaded_bytes else "未知"
                        
                        # 基于进度估算总大小（不完全精确但给用户参考）
                        if percentage > 0.5 and downloaded_bytes > 1024:  # 至少下载0.5%且超过1KB才估算
                            estimated_total = (downloaded_bytes / percentage) * 100
                            total_str = self.format_bytes(estimated_total)
                            size_info = f"({downloaded_str}/{total_str})"
                        else:
                            size_info = f"({downloaded_str})"
                        
                        # 计算和格式化速度
                        speed = d.get('speed', 0)
                        if speed and speed > 0:
                            speed_str = self.format_bytes(speed) + "/s"
                        else:
                            speed_str = "计算中..."
                        
                        # 计算剩余时间
                        eta = d.get('eta', 0)
                        if eta and eta > 0:
                            if eta < 60:
                                eta_str = f"{eta:.0f}秒"
                            elif eta < 3600:
                                eta_str = f"{eta//60:.0f}分{eta%60:.0f}秒"
                            else:
                                eta_str = f"{eta//3600:.0f}时{(eta%3600)//60:.0f}分"
                        else:
                            eta_str = "计算中..."
                        
                        status_text = f"🎬 步骤1/3 - 下载视频: {percentage:.1f}% {size_info} | 速度: {speed_str} | 剩余: {eta_str}"
                        
                        # 视频下载占总进度的60%
                        overall_progress = percentage * 0.6
                        self.parent.root.after(0, lambda: self.parent.update_progress(overall_progress, status_text))
                        return
                
                # 回退到字节进度计算（适用于普通下载）
                total_bytes = self._get_stable_total_bytes(d, "video")
                
                if total_bytes and 'downloaded_bytes' in d:
                    downloaded_bytes = d['downloaded_bytes']
                    
                    # 验证下载字节数是否合理
                    if downloaded_bytes < 0:
                        print(f"⚠️ [视频] 异常的下载字节数: {downloaded_bytes}")
                        return
                    
                    percentage = (downloaded_bytes / total_bytes) * 100
                    
                    # HLS流的总大小经常不准确，如果超过120%就改为无百分比模式
                    if percentage > 120:
                        # 使用预获取的大小重新计算
                        if 'video' in self._prefetched_sizes:
                            prefetched_total = self._prefetched_sizes['video']
                            if prefetched_total and prefetched_total > 0:
                                percentage = (downloaded_bytes / prefetched_total) * 100
                                # 如果仍然超过120%，则使用无百分比模式
                                if percentage > 120:
                                    downloaded_str = self.format_bytes(downloaded_bytes)
                                    speed = d.get('speed', 0)
                                    speed_str = self.format_bytes(speed) + "/s" if speed else "计算中..."
                                    status_text = f"🎬 步骤1/3 - 下载视频: {downloaded_str} | 速度: {speed_str}"
                                    self.parent.root.after(0, lambda: self.parent.update_progress(30, status_text))
                                    return
                    
                    # 获取文件大小信息
                    downloaded_str = self.format_bytes(downloaded_bytes)
                    total_str = self.format_bytes(total_bytes)
                    size_info = f"({downloaded_str}/{total_str})"
                    
                    # 计算和格式化速度
                    speed = d.get('speed', 0)
                    if speed and speed > 0:
                        speed_str = self.format_bytes(speed) + "/s"
                    else:
                        speed_str = "计算中..."
                    
                    # 计算剩余时间
                    eta = d.get('eta', 0)
                    if eta and eta > 0:
                        if eta < 60:
                            eta_str = f"{eta:.0f}秒"
                        elif eta < 3600:
                            eta_str = f"{eta//60:.0f}分{eta%60:.0f}秒"
                        else:
                            eta_str = f"{eta//3600:.0f}时{(eta%3600)//60:.0f}分"
                    else:
                        eta_str = "计算中..."
                    
                    status_text = f"🎬 步骤1/3 - 下载视频: {percentage:.1f}% {size_info} | 速度: {speed_str} | 剩余: {eta_str}"
                    
                    # 视频下载占总进度的60%
                    overall_progress = percentage * 0.6
                    self.parent.root.after(0, lambda: self.parent.update_progress(overall_progress, status_text))
                else:
                    # 无法获取总大小时显示已下载量和速度
                    downloaded_bytes = d.get('downloaded_bytes', 0)
                    speed = d.get('speed', 0)
                    
                    if downloaded_bytes and speed:
                        downloaded_str = self.format_bytes(downloaded_bytes)
                        speed_str = self.format_bytes(speed) + "/s"
                        status_text = f"🎬 步骤1/3 - 下载视频: {downloaded_str} | 速度: {speed_str}"
                    else:
                        status_text = "🎬 步骤1/3 - 正在下载视频..."
                    
                    self.parent.root.after(0, lambda: self.parent.update_progress(30, status_text))
                    
            except Exception as e:
                print(f"视频进度更新错误: {e}")
                
        elif d['status'] == 'finished':
            self.parent.video_file = d['filename']
            video_size = self.format_bytes(os.path.getsize(d['filename']))
            status_text = f"✅ 步骤1/3 完成 - 视频已下载 ({video_size})"
            self.parent.root.after(0, lambda: self.parent.update_progress(60, status_text))
    
    def audio_progress_hook(self, d):
        """音频下载进度回调（用于分离下载模式）"""
        if self.parent.download_paused:
            return
            
        if d['status'] == 'downloading':
            try:
                # 优先使用fragment进度（适用于HLS等流媒体）
                if 'fragment_index' in d and 'fragment_count' in d:
                    fragment_index = d.get('fragment_index', 0)
                    fragment_count = d.get('fragment_count', 1)
                    
                    if fragment_count > 0:
                        percentage = (fragment_index / fragment_count) * 100
                        
                        # 获取文件大小信息
                        downloaded_bytes = d.get('downloaded_bytes', 0)
                        downloaded_str = self.format_bytes(downloaded_bytes) if downloaded_bytes else "未知"
                        
                        # 基于进度估算总大小（不完全精确但给用户参考）
                        if percentage > 0.5 and downloaded_bytes > 1024:  # 至少下载0.5%且超过1KB才估算
                            estimated_total = (downloaded_bytes / percentage) * 100
                            total_str = self.format_bytes(estimated_total)
                            size_info = f"({downloaded_str}/{total_str})"
                        else:
                            size_info = f"({downloaded_str})"
                        
                        # 计算和格式化速度
                        speed = d.get('speed', 0)
                        if speed and speed > 0:
                            speed_str = self.format_bytes(speed) + "/s"
                        else:
                            speed_str = "计算中..."
                        
                        # 计算剩余时间
                        eta = d.get('eta', 0)
                        if eta and eta > 0:
                            if eta < 60:
                                eta_str = f"{eta:.0f}秒"
                            elif eta < 3600:
                                eta_str = f"{eta//60:.0f}分{eta%60:.0f}秒"
                            else:
                                eta_str = f"{eta//3600:.0f}时{(eta%3600)//60:.0f}分"
                        else:
                            eta_str = "计算中..."
                        
                        status_text = f"🎵 步骤2/3 - 下载音频: {percentage:.1f}% {size_info} | 速度: {speed_str} | 剩余: {eta_str}"
                        
                        # 音频下载占总进度的30% (从60%到90%)
                        overall_progress = 60 + (percentage * 0.3)
                        self.parent.root.after(0, lambda: self.parent.update_progress(overall_progress, status_text))
                        return
                
                # 回退到字节进度计算（适用于普通下载）
                total_bytes = self._get_stable_total_bytes(d, "audio")
                
                if total_bytes and 'downloaded_bytes' in d:
                    downloaded_bytes = d['downloaded_bytes']
                    
                    # 验证下载字节数是否合理
                    if downloaded_bytes < 0:
                        print(f"⚠️ [音频] 异常的下载字节数: {downloaded_bytes}")
                        return
                    
                    percentage = (downloaded_bytes / total_bytes) * 100
                    
                    # HLS流的总大小经常不准确，如果超过120%就改为无百分比模式
                    if percentage > 120:
                        # 使用预获取的大小重新计算
                        if 'audio' in self._prefetched_sizes:
                            prefetched_total = self._prefetched_sizes['audio']
                            if prefetched_total and prefetched_total > 0:
                                percentage = (downloaded_bytes / prefetched_total) * 100
                                # 如果仍然超过120%，则使用无百分比模式
                                if percentage > 120:
                                    downloaded_str = self.format_bytes(downloaded_bytes)
                                    speed = d.get('speed', 0)
                                    speed_str = self.format_bytes(speed) + "/s" if speed else "计算中..."
                                    status_text = f"🎵 步骤2/3 - 下载音频: {downloaded_str} | 速度: {speed_str}"
                                    self.parent.root.after(0, lambda: self.parent.update_progress(75, status_text))
                                    return
                    
                    # 获取文件大小信息
                    downloaded_str = self.format_bytes(downloaded_bytes)
                    total_str = self.format_bytes(total_bytes)
                    size_info = f"({downloaded_str}/{total_str})"
                    
                    # 计算和格式化速度
                    speed = d.get('speed', 0)
                    if speed and speed > 0:
                        speed_str = self.format_bytes(speed) + "/s"
                    else:
                        speed_str = "计算中..."
                    
                    # 计算剩余时间
                    eta = d.get('eta', 0)
                    if eta and eta > 0:
                        if eta < 60:
                            eta_str = f"{eta:.0f}秒"
                        elif eta < 3600:
                            eta_str = f"{eta//60:.0f}分{eta%60:.0f}秒"
                        else:
                            eta_str = f"{eta//3600:.0f}时{(eta%3600)//60:.0f}分"
                    else:
                        eta_str = "计算中..."
                    
                    status_text = f"🎵 步骤2/3 - 下载音频: {percentage:.1f}% {size_info} | 速度: {speed_str} | 剩余: {eta_str}"
                    
                    # 音频下载占总进度的30% (从60%到90%)
                    overall_progress = 60 + (percentage * 0.3)
                    self.parent.root.after(0, lambda: self.parent.update_progress(overall_progress, status_text))
                else:
                    # 无法获取总大小时显示已下载量和速度
                    downloaded_bytes = d.get('downloaded_bytes', 0)
                    speed = d.get('speed', 0)
                    
                    if downloaded_bytes and speed:
                        downloaded_str = self.format_bytes(downloaded_bytes)
                        speed_str = self.format_bytes(speed) + "/s"
                        status_text = f"🎵 步骤2/3 - 下载音频: {downloaded_str} | 速度: {speed_str}"
                    else:
                        status_text = "🎵 步骤2/3 - 正在下载音频..."
                    
                    self.parent.root.after(0, lambda: self.parent.update_progress(75, status_text))
                    
            except Exception as e:
                print(f"音频进度更新错误: {e}")
                
        elif d['status'] == 'finished':
            self.parent.audio_file = d['filename']
            audio_size = self.format_bytes(os.path.getsize(d['filename']))
            status_text = f"✅ 步骤2/3 完成 - 音频已下载 ({audio_size})"
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
                'socket_timeout': 20,  # 添加20秒网络超时
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
            # 清理大小缓存，开始新的下载任务
            self._clear_size_cache()
            
            # 获取格式信息
            info = self.get_video_info(url)
            title = info.get('title', 'video')
            clean_title = self.clean_filename(title)
            
            # 获取清晰度信息并生成最终文件名
            resolution_suffix = self._get_resolution_suffix(quality)
            final_filename = self._get_final_filename(clean_title, resolution_suffix)
            final_path = os.path.join(download_path, final_filename)
            
            # 检查是否已存在相同清晰度的文件
            if os.path.exists(final_path):
                file_size = os.path.getsize(final_path)
                size_str = self.format_bytes(file_size)
                raise Exception(f"文件已存在: {final_filename}\n\n"
                              f"文件大小: {size_str}\n"
                              f"清晰度: {resolution_suffix}\n\n"
                              f"如需重新下载，请先删除现有文件或选择不同清晰度。")
            
            # 创建下载会话
            session_id, session_dir = self.parent.cache_manager.create_download_session(title, quality)
            
            # 判断下载模式
            if ("分离合并" in quality) or (quality.startswith("🎯 最佳画质") and hasattr(self.parent, 'needs_merge') and self.parent.needs_merge):
                # 分离下载+合并模式
                self.parent.download_stage = "downloading_video"
                
                # 下载视频（无音频）到缓存目录
                video_temp_path = os.path.join(session_dir, f'{clean_title}_video.%(ext)s')
                video_opts = {
                    'format': 'bestvideo[ext=mp4]/bestvideo',
                    'outtmpl': video_temp_path,
                    'progress_hooks': [self.video_progress_hook],
                    'socket_timeout': 20,  # 添加20秒网络超时
                    'retries': 3,
                    'fragment_retries': 3,
                }
                
                with yt_dlp.YoutubeDL(video_opts) as ydl:
                    ydl.download([url])
                
                # 更新会话状态
                self.parent.cache_manager.update_session_status(session_dir, "video_downloaded")
                
                # 下载音频到缓存目录
                self.parent.download_stage = "downloading_audio"
                
                audio_temp_path = os.path.join(session_dir, f'{clean_title}_audio.%(ext)s')
                audio_opts = {
                    'format': 'bestaudio[ext=m4a]/bestaudio',
                    'outtmpl': audio_temp_path,
                    'progress_hooks': [self.audio_progress_hook],
                    'socket_timeout': 20,  # 添加20秒网络超时
                    'retries': 3,
                    'fragment_retries': 3,
                }
                
                with yt_dlp.YoutubeDL(audio_opts) as ydl:
                    ydl.download([url])
                
                # 更新会话状态
                self.parent.cache_manager.update_session_status(session_dir, "audio_downloaded")
                
                # 合并视频和音频
                if self.parent.video_file and self.parent.audio_file:
                    self.parent.download_stage = "merging"
                    
                    # 执行合并
                    success = self.parent.ffmpeg.merge_video_audio(
                        self.parent.video_file, 
                        self.parent.audio_file, 
                        final_path
                    )
                    
                    if success:
                        # 更新会话状态为完成
                        self.parent.cache_manager.update_session_status(session_dir, "completed")
                        
                        # 清理临时文件
                        try:
                            if os.path.exists(self.parent.video_file):
                                os.remove(self.parent.video_file)
                            if os.path.exists(self.parent.audio_file):
                                os.remove(self.parent.audio_file)
                            print(f"✅ 清理临时文件完成")
                        except Exception as e:
                            print(f"清理临时文件时出错: {e}")
                        
                        # 显示最终完成状态
                        print(f"✅ 下载完成: {final_path}")
                    else:
                        # 更新会话状态为失败
                        self.parent.cache_manager.update_session_status(session_dir, "failed")
                        raise Exception("视频合并失败")
                        
            else:
                # 普通下载模式（直接下载完整文件）
                format_selector = self._get_format_selector(quality)
                
                # 下载到缓存目录
                temp_path = os.path.join(session_dir, f'{clean_title}.%(ext)s')
                ydl_opts = {
                    'format': format_selector,
                    'outtmpl': temp_path,
                    'progress_hooks': [self.progress_hook],
                    'socket_timeout': 20,  # 添加20秒网络超时
                    'retries': 3,
                    'fragment_retries': 3,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                # 更新会话状态
                self.parent.cache_manager.update_session_status(session_dir, "downloaded")
                
                # 移动文件到目标目录
                try:
                    # 查找下载的文件
                    downloaded_files = []
                    for file in os.listdir(session_dir):
                        if file != "session_info.json" and not file.endswith('.part'):
                            downloaded_files.append(os.path.join(session_dir, file))
                    
                    if downloaded_files:
                        downloaded_file = downloaded_files[0]  # 取第一个文件
                        
                        # 获取文件扩展名
                        _, ext = os.path.splitext(downloaded_file)
                        
                        # 移动文件到目标目录，使用最终文件名
                        shutil.move(downloaded_file, final_path)
                        
                        # 更新会话状态为完成
                        self.parent.cache_manager.update_session_status(session_dir, "completed")
                        
                        print(f"✅ 下载完成: {final_path}")
                    else:
                        raise Exception("未找到下载的文件")
                        
                except Exception as e:
                    # 更新会话状态为失败
                    self.parent.cache_manager.update_session_status(session_dir, "failed")
                    raise Exception(f"移动文件失败: {e}")
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            # 检查是否为网络连接相关错误
            if any(keyword in error_msg.lower() for keyword in ['timeout', 'connection', 'network', 'resolve', 'unreachable', 'failed to extract']):
                raise Exception(f"网络连接超时或无法访问YouTube\n\n请检查：\n1. 网络连接是否正常\n2. 是否能够访问YouTube网站\n3. 防火墙或代理设置\n\n详细错误信息：{error_msg}")
            else:
                raise Exception(f"下载失败: {error_msg}")
    
    def _get_resolution_suffix(self, quality):
        """根据质量选择获取清晰度后缀"""
        import re
        
        # 提取分辨率信息
        if quality.startswith("🎯 最佳画质") or quality.startswith("🎯 最高画质"):
            match = re.search(r'(\d+)p', quality)
            if match:
                resolution = match.group(1)
                return f"_{resolution}p"
            else:
                return ""
        
        elif quality.startswith("📺"):
            match = re.search(r'(\d+)p', quality)
            if match:
                resolution = match.group(1)
                return f"_{resolution}p"
            else:
                return ""
        
        elif quality == "🎵 仅音频":
            return "_音频"
        
        else:
            return ""
    
    def _get_final_filename(self, clean_title, resolution_suffix):
        """生成最终文件名"""
        # 检查是否已经有清晰度后缀
        if resolution_suffix and not clean_title.endswith(resolution_suffix):
            # 添加清晰度后缀
            final_name = f"{clean_title}{resolution_suffix}.mp4"
        else:
            # 没有清晰度后缀或已经存在，直接使用.mp4扩展名
            final_name = f"{clean_title}.mp4"
        
        return final_name
    
    def _get_format_selector(self, quality):
        """根据质量选择获取格式选择器"""
        # 处理最佳画质选项
        if quality.startswith("🎯 最佳画质") or quality.startswith("🎯 最高画质"):
            # 如果有明确的分辨率信息，使用指定分辨率
            import re
            match = re.search(r'(\d+)p', quality)
            if match:
                height = match.group(1)
                if "仅视频" in quality:
                    # 仅视频格式，选择指定分辨率的视频
                    return f"bestvideo[height<={height}][ext=mp4]/bestvideo[height<={height}]"
                else:
                    # 带音频格式，选择指定分辨率的完整视频
                    return f"best[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}]"
            else:
                return "best[ext=mp4]/best"
        
        # 处理带音频选项（例如：720p带音频、480p带音频等）
        elif quality.startswith("📺"):
            # 提取分辨率数字
            import re
            match = re.search(r'(\d+)p', quality)
            if match:
                height = match.group(1)
                return f"best[height<={height}][acodec!=none][ext=mp4]/best[height<={height}][acodec!=none]"
            else:
                return "best[acodec!=none][ext=mp4]/best[acodec!=none]"
        
        # 处理音频选项
        elif quality == "🎵 仅音频":
            return "bestaudio[ext=m4a]/bestaudio"
        
        # 默认选项
        return "best[ext=mp4]/best" 