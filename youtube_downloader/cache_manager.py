"""
缓存管理模块 - 处理下载过程中的临时文件
"""
import os
import shutil
import time
import json
from pathlib import Path


class CacheManager:
    """缓存管理类"""
    
    def __init__(self, parent):
        self.parent = parent
        self.cache_dir = self._get_cache_dir()
        self.cache_info_file = os.path.join(self.cache_dir, "cache_info.json")
        self._ensure_cache_dir()
    
    def _get_cache_dir(self):
        """获取缓存目录路径"""
        # 在用户目录下创建缓存文件夹
        user_home = os.path.expanduser("~")
        cache_dir = os.path.join(user_home, ".youtube_downloader_cache")
        return cache_dir
    
    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
            print(f"📁 创建缓存目录: {self.cache_dir}")
    
    def get_cache_size(self):
        """获取缓存大小（字节）"""
        total_size = 0
        try:
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    if file != "cache_info.json":  # 排除缓存信息文件
                        file_path = os.path.join(root, file)
                        if os.path.exists(file_path):
                            total_size += os.path.getsize(file_path)
        except Exception as e:
            print(f"获取缓存大小失败: {e}")
        return total_size
    
    def format_cache_size(self, bytes_val):
        """格式化缓存大小显示"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f}{unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f}TB"
    
    def get_cache_info(self):
        """获取缓存信息"""
        cache_info = {
            'total_size': self.get_cache_size(),
            'file_count': 0,
            'files': []
        }
        
        try:
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    if file != "cache_info.json":
                        file_path = os.path.join(root, file)
                        if os.path.exists(file_path):
                            file_size = os.path.getsize(file_path)
                            file_mtime = os.path.getmtime(file_path)
                            cache_info['files'].append({
                                'name': file,
                                'path': file_path,
                                'size': file_size,
                                'modified': file_mtime
                            })
                            cache_info['file_count'] += 1
        except Exception as e:
            print(f"获取缓存信息失败: {e}")
        
        return cache_info
    
    def create_download_session(self, video_title, quality):
        """创建下载会话，返回会话ID和临时目录"""
        import uuid
        session_id = str(uuid.uuid4())[:8]  # 使用UUID的前8位作为会话ID
        
        # 清理文件名中的非法字符
        safe_title = self._clean_filename(video_title)
        session_dir = os.path.join(self.cache_dir, f"{safe_title}_{session_id}")
        
        # 创建会话目录
        os.makedirs(session_dir, exist_ok=True)
        
        # 记录会话信息
        session_info = {
            'session_id': session_id,
            'video_title': video_title,
            'quality': quality,
            'created_time': time.time(),
            'status': 'downloading'
        }
        
        session_info_file = os.path.join(session_dir, "session_info.json")
        with open(session_info_file, 'w', encoding='utf-8') as f:
            json.dump(session_info, f, ensure_ascii=False, indent=2)
        
        print(f"📁 创建下载会话: {session_id} - {video_title}")
        return session_id, session_dir
    
    def update_session_status(self, session_dir, status):
        """更新会话状态"""
        try:
            session_info_file = os.path.join(session_dir, "session_info.json")
            if os.path.exists(session_info_file):
                with open(session_info_file, 'r', encoding='utf-8') as f:
                    session_info = json.load(f)
                
                session_info['status'] = status
                session_info['updated_time'] = time.time()
                
                with open(session_info_file, 'w', encoding='utf-8') as f:
                    json.dump(session_info, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"更新会话状态失败: {e}")
    
    def cleanup_session(self, session_dir):
        """清理指定会话的临时文件"""
        try:
            if os.path.exists(session_dir):
                shutil.rmtree(session_dir)
                print(f"🗑️ 清理会话目录: {session_dir}")
                return True
        except Exception as e:
            print(f"清理会话目录失败: {e}")
        return False
    
    def cleanup_all_cache(self):
        """清理所有缓存文件"""
        try:
            cache_info = self.get_cache_info()
            cleaned_count = 0
            cleaned_size = 0
            
            for file_info in cache_info['files']:
                try:
                    os.remove(file_info['path'])
                    cleaned_count += 1
                    cleaned_size += file_info['size']
                except Exception as e:
                    print(f"删除文件失败 {file_info['path']}: {e}")
            
            # 清理空目录
            for root, dirs, files in os.walk(self.cache_dir, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        if not os.listdir(dir_path):  # 目录为空
                            os.rmdir(dir_path)
                    except Exception:
                        pass
            
            print(f"🗑️ 清理完成: {cleaned_count} 个文件, {self.format_cache_size(cleaned_size)}")
            return cleaned_count, cleaned_size
            
        except Exception as e:
            print(f"清理缓存失败: {e}")
            return 0, 0
    
    def cleanup_old_sessions(self, max_age_hours=24):
        """清理过期的会话（默认24小时）"""
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            cleaned_count = 0
            
            for root, dirs, files in os.walk(self.cache_dir):
                for dir_name in dirs:
                    session_dir = os.path.join(root, dir_name)
                    session_info_file = os.path.join(session_dir, "session_info.json")
                    
                    if os.path.exists(session_info_file):
                        try:
                            with open(session_info_file, 'r', encoding='utf-8') as f:
                                session_info = json.load(f)
                            
                            created_time = session_info.get('created_time', 0)
                            if current_time - created_time > max_age_seconds:
                                if self.cleanup_session(session_dir):
                                    cleaned_count += 1
                        except Exception as e:
                            print(f"检查会话文件失败 {session_info_file}: {e}")
            
            if cleaned_count > 0:
                print(f"🗑️ 清理过期会话: {cleaned_count} 个")
            
            return cleaned_count
            
        except Exception as e:
            print(f"清理过期会话失败: {e}")
            return 0
    
    def _clean_filename(self, filename):
        """清理文件名中的非法字符"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # 限制文件名长度
        if len(filename) > 50:
            filename = filename[:50]
        
        return filename
    
    def get_cache_summary(self):
        """获取缓存摘要信息"""
        cache_info = self.get_cache_info()
        total_size = cache_info['total_size']
        file_count = cache_info['file_count']
        
        if file_count == 0:
            return "无缓存文件"
        else:
            return f"{file_count} 个文件, {self.format_cache_size(total_size)}"
    
    def open_cache_directory(self):
        """打开缓存目录"""
        try:
            if os.path.exists(self.cache_dir):
                os.startfile(self.cache_dir)  # Windows
            else:
                print("缓存目录不存在")
        except Exception as e:
            print(f"打开缓存目录失败: {e}") 