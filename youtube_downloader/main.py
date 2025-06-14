#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube视频下载器

作者：没脖子的猫

功能特色：
🎯 支持多种质量选择
🤖 智能下载和分离合并
🔄 断点续传和网络重试
🔧 自动分离下载合并功能
⚡ FFmpeg自动下载安装
🗑️ 智能缓存管理
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import time
from .config import config
from .gui_interface import GuiInterface
from .video_downloader import VideoDownloader
from .ffmpeg_tools import FFmpegTools
from .cache_manager import CacheManager
from PIL import Image, ImageTk


class YouTubeDownloaderApp:
    """YouTube下载器主应用程序"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("YouTube视频下载器 - by 没脖子的猫")
        self.root.geometry("800x760")
        self.root.configure(bg='#f0f0f0')
        self.root.minsize(800, 760)
        
        # 应用程序状态
        self.download_path = config.get("download_path")
        self.download_paused = False
        self.current_download = None
        self.download_stage = "waiting"
        self.video_file = None
        self.audio_file = None
        self.pending_merge = None
        self.available_formats = None
        self.default_quality_options = []
        
        # 格式分析属性
        self.max_video_height = 0
        self.max_combined_height = 0
        self.needs_merge = False
        self.best_quality_text = ""
        self.direct_download_text = ""
        
        # 初始化组件
        self.gui = GuiInterface(self)
        self.downloader = VideoDownloader(self)
        self.ffmpeg = FFmpegTools(self)
        self.cache_manager = CacheManager(self)
        
        # 设置窗口图标
        self.set_window_icon()
        
        # 设置界面
        self.gui.setup_main_gui()
        
        # 启动时检查环境
        self.root.after(1000, self.check_environment_on_startup)
    
    def set_window_icon(self):
        """设置窗口图标"""
        try:
            # 获取图标文件路径
            icon_path = self.gui.get_resource_path("assets/icon.png")
            
            # 检查图标文件是否存在
            if os.path.exists(icon_path):
                # 加载图标
                icon_image = Image.open(icon_path)
                # 转换为PhotoImage
                icon_photo = ImageTk.PhotoImage(icon_image)
                # 设置窗口图标
                self.root.iconphoto(True, icon_photo)
                print(f"✅ 窗口图标设置成功: {icon_path}")
            else:
                print(f"⚠️ 图标文件不存在: {icon_path}")
        except Exception as e:
            print(f"❌ 设置窗口图标失败: {e}")
    
    def check_environment_on_startup(self):
        """启动时检查环境"""
        if self.ffmpeg.check_ffmpeg_installed():
            self.progress_var.set("🚀 环境就绪 - 支持所有下载功能")
        else:
            self.progress_var.set("⚡ 程序就绪 - 可使用基础下载功能")
            # 可选择是否自动安装FFmpeg
            response = messagebox.askyesno(
                "环境配置", 
                "🔧 检测到FFmpeg未安装\n\n"
                "FFmpeg用于高质量视频下载和合并功能\n"
                "是否现在自动安装？\n\n"
                "• 选择'是'：自动下载安装FFmpeg (约100MB)\n"
                "• 选择'否'：使用基础下载功能"
            )
            if response:
                self.ffmpeg.auto_download_ffmpeg()
        
        # 启动时清理过期缓存
        self.root.after(2000, self.cleanup_old_cache_on_startup)
    
    def cleanup_old_cache_on_startup(self):
        """启动时清理过期缓存"""
        try:
            cleaned_count = self.cache_manager.cleanup_old_sessions()
            if cleaned_count > 0:
                print(f"🗑️ 启动时清理过期缓存: {cleaned_count} 个会话")
                # 更新缓存按钮显示
                self.gui.update_cache_button()
        except Exception as e:
            print(f"启动时清理缓存失败: {e}")
    
    # ================================
    # 视频信息获取相关方法
    # ================================
    
    def get_video_info(self):
        """获取视频信息"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入视频网址")
            return
        
        self.info_button.configure(state='disabled', text="获取中...")
        self.update_info_display("🔍 正在获取视频信息...")
        self.update_progress(0, "🔍 正在获取视频信息...")
        self.gui.reset_thumbnail_display()
        
        def get_info_thread():
            try:
                # 更新进度
                self.root.after(0, lambda: self.update_progress(30, "📡 连接视频源..."))
                info = self.downloader.get_video_info(url)
                self.root.after(0, lambda: self.update_progress(70, "📋 解析视频信息..."))
                
                # 格式化视频信息
                title = info.get('title', '未知标题')
                duration = self.downloader.format_duration(info.get('duration', 0))
                uploader = info.get('uploader', '未知上传者')
                view_count = info.get('view_count', 0)
                upload_date = info.get('upload_date', '')
                
                # 格式化上传日期
                if upload_date and len(upload_date) == 8:
                    formatted_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
                else:
                    formatted_date = "未知日期"
                
                # 格式化观看次数
                if view_count:
                    if view_count >= 1000000:
                        view_str = f"{view_count/1000000:.1f}M"
                    elif view_count >= 1000:
                        view_str = f"{view_count/1000:.1f}K"
                    else:
                        view_str = str(view_count)
                else:
                    view_str = "未知"
                
                description = info.get('description', '无描述')
                # 显示更多描述内容，不截断太多
                if len(description) > 800:
                    desc_text = description[:800] + '...'
                else:
                    desc_text = description
                
                info_text = f"""📺 标题: {title}

⏱️ 时长: {duration}
👤 上传者: {uploader}
📅 上传日期: {formatted_date}
👀 观看次数: {view_str}

📝 描述: {desc_text}"""
                
                # 在主线程中更新UI
                self.root.after(0, lambda: self.update_info_display(info_text))
                self.root.after(0, lambda: self.update_quality_options(info))
                self.root.after(0, lambda: self.display_available_formats(info))
                
                # 下载缩略图
                thumbnail_url = info.get('thumbnail')
                if thumbnail_url:
                    self.gui.download_and_display_thumbnail(thumbnail_url)
                
                # 启用下载按钮
                self.root.after(0, lambda: self.download_button.configure(state='normal'))
                self.root.after(0, lambda: self.update_progress(100, "✅ 视频信息获取完成"))
                
            except Exception as e:
                error_msg = str(e)
                # 根据错误类型显示不同的提示信息
                if "网络连接超时或无法访问YouTube" in error_msg:
                    display_msg = f"❌ {error_msg}"
                else:
                    display_msg = f"❌ 获取视频信息失败:\n{error_msg}"
                self.root.after(0, lambda: self.update_info_display(display_msg))
            
            finally:
                self.root.after(0, self.reset_info_button)
                # 3秒后清除进度信息
                self.root.after(3000, lambda: self.update_progress(0, "⚡ 程序就绪"))
        
        thread = threading.Thread(target=get_info_thread, daemon=True)
        thread.start()
    
    def update_info_display(self, text):
        """更新信息显示"""
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, text)
    
    def reset_info_button(self):
        """重置获取信息按钮"""
        self.info_button.configure(state='normal', text="获取视频信息")
    
    def display_available_formats(self, info):
        """显示可用的视频格式信息"""
        if not info or not info.get('formats'):
            return
        
        formats = info.get('formats', [])
        
        # 分析格式信息
        video_with_audio = []    # 有音频的视频格式
        video_only = []          # 仅视频格式
        audio_only = []          # 仅音频格式
        
        for fmt in formats:
            height = fmt.get('height', 0)
            vcodec = fmt.get('vcodec', 'none')
            acodec = fmt.get('acodec', 'none')
            fps = fmt.get('fps', '')
            ext = fmt.get('ext', '')
            
            if vcodec != 'none' and height > 0:
                # 构建格式描述
                format_desc = f"{height}p"
                if fps:
                    format_desc += f"@{fps:.0f}fps" if isinstance(fps, (int, float)) else f"@{fps}fps"
                if ext:
                    format_desc += f" ({ext})"
                
                if acodec != 'none':
                    # 有音频的视频
                    format_desc += " 🔊"
                    video_with_audio.append((height, format_desc))
                else:
                    # 仅视频
                    format_desc += " 📹"
                    video_only.append((height, format_desc))
            elif acodec != 'none' and vcodec == 'none':
                # 仅音频
                audio_only.append(fmt)
        
        # 去重并排序
        video_with_audio = list(set(video_with_audio))
        video_with_audio.sort(key=lambda x: x[0], reverse=True)
        
        video_only = list(set(video_only))
        video_only.sort(key=lambda x: x[0], reverse=True)
        
        # 构建显示文本
        format_text = "\n\n📋 可用画质分析:"
        
        # 显示有音频的格式
        if video_with_audio:
            format_text += "\n\n🔊 带音频格式:"
            for height, desc in video_with_audio[:5]:
                format_text += f"\n• {desc}"
        
        # 显示仅视频格式（通常画质更高）
        if video_only:
            format_text += "\n\n📹 仅视频格式（需合并音频）:"
            for height, desc in video_only[:5]:
                format_text += f"\n• {desc}"
        
        # 显示最佳合并建议
        max_video_only = max([h for h, _ in video_only], default=0)
        max_with_audio = max([h for h, _ in video_with_audio], default=0)
        
        if max_video_only > max_with_audio and audio_only:
            format_text += f"\n\n💡 建议: {max_video_only}p视频 + 音频合并 = 最佳画质"
        
        # 添加到当前信息显示中
        current_text = self.info_text.get(1.0, tk.END)
        if "📋 可用画质分析:" not in current_text:
            self.info_text.insert(tk.END, format_text)
    
    # ================================
    # 质量选择相关方法
    # ================================
    
    def update_quality_options(self, info=None):
        """更新质量选项"""
        if info:
            self.available_formats = info.get('formats', [])
        
        # 分析可用格式
        max_video_only_height = 0      # 最高画质的仅视频格式
        max_combined_height = 0        # 最高画质的带音频格式
        has_audio_stream = False       # 是否有独立音频流
        
        video_with_audio_formats = []  # 带音频的格式列表
        video_only_formats = []        # 仅视频的格式列表
        
        if self.available_formats:
            for fmt in self.available_formats:
                height = fmt.get('height', 0)
                vcodec = fmt.get('vcodec', 'none')
                acodec = fmt.get('acodec', 'none')
                
                if height and vcodec != 'none':
                    if acodec != 'none':
                        # 带音频的视频格式
                        max_combined_height = max(max_combined_height, height)
                        video_with_audio_formats.append((height, fmt))
                    else:
                        # 仅视频格式
                        max_video_only_height = max(max_video_only_height, height)
                        video_only_formats.append((height, fmt))
                elif acodec != 'none' and vcodec == 'none':
                    # 独立音频流
                    has_audio_stream = True
                elif acodec != 'none':
                    # 任何包含音频的格式都表示有音频流
                    has_audio_stream = True
        
        # 构建质量选项
        quality_options = []
        
        # 第一优先选项：如果有更高画质的仅视频格式+独立音频，优先推荐合并
        if max_video_only_height > max_combined_height and has_audio_stream:
            best_option = f"🎯 最佳画质 ({max_video_only_height}p分离合并，耗时较长)"
            quality_options.append(best_option)
            self.best_quality_text = best_option
            self.max_video_height = max_video_only_height
            self.needs_merge = True
        elif max_video_only_height > max_combined_height:
            # 有更高画质但没有音频流，标注无音频
            best_option = f"🎯 最高画质 ({max_video_only_height}p仅视频，无音频)"
            quality_options.append(best_option)
            self.best_quality_text = best_option
            self.max_video_height = max_video_only_height
            self.needs_merge = False
        else:
            # 最高画质就是带音频的
            best_option = f"🎯 最佳画质 ({max_combined_height}p)"
            quality_options.append(best_option)
            self.best_quality_text = best_option
            self.max_video_height = max_combined_height
            self.needs_merge = False
        
        # 添加所有可用的带音频格式选项
        if video_with_audio_formats:
            # 去重并按分辨率从高到低排序
            unique_heights = list(set([height for height, fmt in video_with_audio_formats]))
            unique_heights.sort(reverse=True)
            
            for height in unique_heights:
                # 只有当该分辨率已经在"最佳画质"中显示为"带音频"时才跳过
                should_skip = (max_video_only_height <= max_combined_height and 
                              height == max_combined_height and 
                              not self.needs_merge)
                
                if should_skip:
                    continue
                    
                option = f"📺 {height}p"
                quality_options.append(option)
            
            # 保存信息供下载时使用
            self.max_combined_height = max_combined_height
        
        # 最后选项：仅音频
        if has_audio_stream:
            quality_options.append("🎵 仅音频")
        else:
            print("⚠️ 未检测到音频流，跳过仅音频选项")
        
        # 保存选项信息供下载时使用
        self.quality_combo['values'] = quality_options
        if quality_options:
            self.quality_combo.set(quality_options[0])  # 默认选择第一个（最佳）选项
        self.update_quality_description()
    
    def on_quality_change(self, event=None):
        """质量选择改变时的回调"""
        self.update_quality_description()
    
    def update_quality_description(self):
        """更新质量说明"""
        selected = self.quality_combo.get()
        
        # 处理动态选项
        if selected.startswith("🎯 最佳画质") and "分离合并" in selected:
            desc = f"{self.max_video_height}p视频+音频分别下载后合并，画质最佳但耗时较长"
        elif selected.startswith("🎯 最佳画质") and "仅视频" in selected:
            desc = f"下载{self.max_video_height}p最高画质视频，但该格式无音频"
        elif selected.startswith("🎯 最佳画质"):
            desc = f"下载{self.max_video_height}p最高画质视频，已包含音频"
        elif selected.startswith("📺"):
            # 处理带电视图标的视频质量选项
            import re
            match = re.search(r'(\d+)p', selected)
            if match:
                resolution = match.group(1)
                desc = f"下载{resolution}p视频，包含音频"
            else:
                desc = "下载带音频的视频文件"
        elif selected == "🎵 仅音频":
            desc = "提取音频文件，转换为MP3格式"
        else:
            desc = ""
        
        self.quality_desc.configure(text=desc)
    
    def reset_quality_options(self):
        """重置质量选项"""
        self.quality_combo['values'] = []
        self.quality_combo.set("")
        self.available_formats = None
        self.download_button.configure(state='disabled')
    
    # ================================
    # 下载相关方法
    # ================================
    
    def start_download(self):
        """开始下载"""
        url = self.url_entry.get().strip()
        download_path = self.path_entry.get().strip()
        quality = self.quality_combo.get()
        
        if not all([url, download_path, quality]):
            messagebox.showerror("错误", "请填写完整的下载信息")
            return
        
        if not os.path.exists(download_path):
            messagebox.showerror("错误", f"下载路径不存在: {download_path}")
            return
        
        # 重置状态
        self.download_paused = False
        self.video_file = None
        self.audio_file = None
        
        # 更新UI状态
        self.download_button.configure(state='disabled')
        self.pause_button.configure(state='normal')
        # 确保进度条重置为0
        self.progress_bar['value'] = 0
        self.update_progress(0, "🚀 准备下载...")
        
        def download_thread():
            try:
                # 第一步：预获取文件大小信息
                self.root.after(0, lambda: self.update_progress(5, "📏 正在获取文件大小信息..."))
                prefetch_success = self.downloader.prefetch_file_sizes(url, quality)
                
                if prefetch_success:
                    self.root.after(0, lambda: self.update_progress(10, "✅ 文件大小信息获取完成，开始下载..."))
                else:
                    self.root.after(0, lambda: self.update_progress(10, "⚠️ 无法预获取文件大小，将动态计算进度..."))
                
                # 第二步：执行实际下载
                self.downloader.execute_download(url, download_path, quality)
                self.root.after(0, lambda: self.update_progress(100, "✅ 下载完成!"))
                
                # 更新缓存状态显示
                self.root.after(0, lambda: self.gui.update_cache_button())
                
            except Exception as e:
                error_msg = str(e)
                # 检查是否为文件已存在错误
                if "文件已存在" in error_msg:
                    # 显示文件已存在的详细信息
                    self.root.after(0, lambda: messagebox.showwarning("文件已存在", error_msg))
                # 检查是否为网络连接相关错误
                elif any(keyword in error_msg.lower() for keyword in ['timeout', 'connection', 'network', 'resolve', 'unreachable', 'failed to extract']):
                    display_msg = f"❌ {error_msg}"
                    self.root.after(0, lambda: self.update_progress(0, display_msg))
                else:
                    display_msg = f"❌ 下载失败: {error_msg}"
                    self.root.after(0, lambda: self.update_progress(0, display_msg))
            finally:
                self.root.after(0, self.reset_download_button)
        
        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()
    
    def toggle_pause(self):
        """切换暂停/恢复下载"""
        self.download_paused = not self.download_paused
        if self.download_paused:
            self.pause_button.configure(text="恢复下载")
            self.update_progress(self.progress_bar['value'], "⏸️ 下载已暂停")
        else:
            self.pause_button.configure(text="暂停下载")
            self.update_progress(self.progress_bar['value'], "▶️ 恢复下载中...")
    
    def reset_download_button(self):
        """重置下载按钮状态"""
        self.download_button.configure(state='normal')
        self.pause_button.configure(state='disabled', text="暂停下载")
        self.download_paused = False
    
    def update_progress(self, percentage, status_text):
        """更新进度显示"""
        try:
            # 确保百分比在0-100范围内
            percentage = max(0, min(100, percentage))
            self.progress_bar['value'] = percentage
            self.progress_var.set(status_text)
            self.root.update_idletasks()
        except Exception as e:
            print(f"更新进度时出错: {e}")
            pass
    
    # ================================
    # 路径选择相关方法
    # ================================
    
    def browse_path(self):
        """浏览选择保存路径"""
        folder = filedialog.askdirectory(initialdir=self.download_path)
        if folder:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder)
            # 保存到配置
            config.set("download_path", folder)
            self.download_path = folder
    
    # ================================
    # FFmpeg相关方法桥接
    # ================================
    
    def show_ffmpeg_menu(self):
        """显示FFmpeg管理菜单"""
        self.ffmpeg.show_ffmpeg_menu()
    
    def open_local_merge_dialog(self):
        """打开本地合并对话框"""
        self.ffmpeg.open_local_merge_dialog()
    
    def reset_ffmpeg_download_ui(self):
        """重置FFmpeg下载UI状态"""
        # 重置进度条
        self.root.after(3000, lambda: self.update_progress(0, "⚡ 程序就绪"))
    
    # ================================
    # 缓存管理相关方法
    # ================================
    
    def clear_cache_simple(self):
        """简化的缓存清理功能"""
        cache_info = self.cache_manager.get_cache_info()
        
        if cache_info['file_count'] == 0:
            messagebox.showinfo("提示", "当前没有缓存文件需要清理")
            return
        
        # 显示确认对话框
        size_str = self.cache_manager.format_cache_size(cache_info['total_size'])
        result = messagebox.askyesno(
            "确认清理", 
            f"确定要清理缓存吗？\n\n"
            f"这将删除 {cache_info['file_count']} 个文件，"
            f"释放空间 {size_str}"
        )
        
        if result:
            try:
                cleaned_count, cleaned_size = self.cache_manager.cleanup_all_cache()
                cleaned_size_str = self.cache_manager.format_cache_size(cleaned_size)
                
                messagebox.showinfo(
                    "清理完成", 
                    f"成功清理 {cleaned_count} 个文件，"
                    f"释放空间 {cleaned_size_str}"
                )
                
                # 更新缓存按钮显示
                self.gui.update_cache_button()
                
            except Exception as e:
                messagebox.showerror("清理失败", f"清理缓存时出错：{e}")
    
    def show_cache_dialog(self):
        """显示缓存管理对话框"""
        cache_window = tk.Toplevel(self.root)
        cache_window.title("缓存管理")
        cache_window.geometry("500x400")
        cache_window.resizable(False, False)
        cache_window.transient(self.root)
        cache_window.grab_set()
        
        # 居中显示
        cache_window.update_idletasks()
        x = (cache_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (cache_window.winfo_screenheight() // 2) - (400 // 2)
        cache_window.geometry(f"500x400+{x}+{y}")
        
        # 主框架
        main_frame = ttk.Frame(cache_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🗑️ 缓存管理", 
                               font=('微软雅黑', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 缓存信息显示
        info_frame = ttk.LabelFrame(main_frame, text="缓存信息", padding="15")
        info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 获取缓存信息
        cache_info = self.cache_manager.get_cache_info()
        
        if cache_info['file_count'] == 0:
            info_text = "✅ 当前没有缓存文件"
            info_label = ttk.Label(info_frame, text=info_text, 
                                  font=('微软雅黑', 10), foreground='#28a745')
            info_label.pack(pady=20)
        else:
            # 显示详细缓存信息
            info_text = f"""📊 缓存统计:
• 文件数量: {cache_info['file_count']} 个
• 总大小: {self.cache_manager.format_cache_size(cache_info['total_size'])}
• 缓存目录: {self.cache_manager.cache_dir}"""
            
            info_label = ttk.Label(info_frame, text=info_text, 
                                  font=('微软雅黑', 10), justify=tk.LEFT)
            info_label.pack(pady=10, anchor=tk.W)
            
            # 文件列表
            if cache_info['files']:
                list_frame = ttk.Frame(info_frame)
                list_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
                
                # 创建树形视图
                columns = ('文件名', '大小', '修改时间')
                tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
                
                # 设置列标题
                tree.heading('文件名', text='文件名')
                tree.heading('大小', text='大小')
                tree.heading('修改时间', text='修改时间')
                
                # 设置列宽
                tree.column('文件名', width=250)
                tree.column('大小', width=100)
                tree.column('修改时间', width=150)
                
                # 添加滚动条
                scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
                tree.configure(yscrollcommand=scrollbar.set)
                
                tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                
                # 填充数据
                import datetime
                for file_info in cache_info['files']:
                    file_name = os.path.basename(file_info['path'])
                    file_size = self.cache_manager.format_cache_size(file_info['size'])
                    mod_time = datetime.datetime.fromtimestamp(file_info['modified']).strftime('%Y-%m-%d %H:%M')
                    
                    tree.insert('', tk.END, values=(file_name, file_size, mod_time))
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 清理所有缓存按钮
        clear_all_button = ttk.Button(
            button_frame, text="🗑️ 清理所有缓存", 
            command=lambda: self.clear_all_cache(cache_window)
        )
        clear_all_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 清理过期缓存按钮
        clear_old_button = ttk.Button(
            button_frame, text="⏰ 清理过期缓存", 
            command=lambda: self.clear_old_cache(cache_window)
        )
        clear_old_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 打开缓存目录按钮
        open_dir_button = ttk.Button(
            button_frame, text="📁 打开缓存目录", 
            command=self.cache_manager.open_cache_directory
        )
        open_dir_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 刷新按钮
        refresh_button = ttk.Button(
            button_frame, text="🔄 刷新", 
            command=lambda: self.refresh_cache_dialog(cache_window)
        )
        refresh_button.pack(side=tk.LEFT)
        
        # 关闭按钮
        close_button = ttk.Button(
            button_frame, text="关闭", 
            command=cache_window.destroy
        )
        close_button.pack(side=tk.RIGHT)
    
    def clear_all_cache(self, cache_window):
        """清理所有缓存"""
        cache_info = self.cache_manager.get_cache_info()
        if cache_info['file_count'] == 0:
            messagebox.showinfo("提示", "当前没有缓存文件需要清理")
            return
        
        result = messagebox.askyesno(
            "确认清理", 
            f"确定要清理所有缓存文件吗？\n\n"
            f"这将删除 {cache_info['file_count']} 个文件，"
            f"总计 {self.cache_manager.format_cache_size(cache_info['total_size'])}"
        )
        
        if result:
            try:
                cleaned_count, cleaned_size = self.cache_manager.cleanup_all_cache()
                messagebox.showinfo(
                    "清理完成", 
                    f"成功清理 {cleaned_count} 个文件，"
                    f"释放空间 {self.cache_manager.format_cache_size(cleaned_size)}"
                )
                # 刷新缓存状态显示
                self.gui.update_cache_status()
                # 关闭对话框
                cache_window.destroy()
            except Exception as e:
                messagebox.showerror("清理失败", f"清理缓存时出错：{e}")
    
    def clear_old_cache(self, cache_window):
        """清理过期缓存"""
        try:
            cleaned_count = self.cache_manager.cleanup_old_sessions()
            if cleaned_count > 0:
                messagebox.showinfo(
                    "清理完成", 
                    f"成功清理 {cleaned_count} 个过期会话"
                )
            else:
                messagebox.showinfo("提示", "没有找到过期的缓存文件")
            
            # 刷新缓存状态显示
            self.gui.update_cache_status()
            # 关闭对话框
            cache_window.destroy()
        except Exception as e:
            messagebox.showerror("清理失败", f"清理过期缓存时出错：{e}")
    
    def refresh_cache_dialog(self, cache_window):
        """刷新缓存对话框"""
        cache_window.destroy()
        self.show_cache_dialog()
    
    # ================================
    # 应用程序控制
    # ================================
    
    def run(self):
        """运行应用程序"""
        self.root.mainloop()


def main():
    """主函数"""
    try:
        app = YouTubeDownloaderApp()
        app.run()
    except Exception as e:
        print(f"程序启动失败: {e}")
        input("按Enter键退出...")


if __name__ == "__main__":
    main() 