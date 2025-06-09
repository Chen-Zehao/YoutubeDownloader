#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube视频下载器

作者：二号饺

功能特色：
🎯 支持多种质量选择
🤖 智能下载和分离合并
🔄 断点续传和网络重试
🔧 自动分离下载合并功能
⚡ FFmpeg自动下载安装
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import time
from config import config
from gui_interface import GuiInterface
from video_downloader import VideoDownloader
from ffmpeg_tools import FFmpegTools


class YouTubeDownloaderApp:
    """YouTube下载器主应用程序"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("YouTube视频下载器 - by 二号饺")
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
        
        # 初始化组件
        self.gui = GuiInterface(self)
        self.downloader = VideoDownloader(self)
        self.ffmpeg = FFmpegTools(self)
        
        # 设置界面
        self.gui.setup_main_gui()
        
        # 启动时检查环境
        self.root.after(1000, self.check_environment_on_startup)
    
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
        self.gui.reset_thumbnail_display()
        
        def get_info_thread():
            try:
                info = self.downloader.get_video_info(url)
                
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
                
                info_text = f"""📺 标题: {title}

⏱️ 时长: {duration}
👤 上传者: {uploader}
📅 上传日期: {formatted_date}
👀 观看次数: {view_str}

📝 描述: {info.get('description', '无描述')[:200]}{'...' if len(info.get('description', '')) > 200 else ''}"""
                
                # 在主线程中更新UI
                self.root.after(0, lambda: self.update_info_display(info_text))
                self.root.after(0, lambda: self.update_quality_options(info))
                
                # 下载缩略图
                thumbnail_url = info.get('thumbnail')
                if thumbnail_url:
                    self.gui.download_and_display_thumbnail(thumbnail_url)
                
                # 启用下载按钮
                self.root.after(0, lambda: self.download_button.configure(state='normal'))
                
            except Exception as e:
                error_msg = f"❌ 获取视频信息失败:\n{str(e)}"
                self.root.after(0, lambda: self.update_info_display(error_msg))
            
            finally:
                self.root.after(0, self.reset_info_button)
        
        thread = threading.Thread(target=get_info_thread, daemon=True)
        thread.start()
    
    def update_info_display(self, text):
        """更新信息显示"""
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, text)
    
    def reset_info_button(self):
        """重置获取信息按钮"""
        self.info_button.configure(state='normal', text="获取视频信息")
    
    # ================================
    # 质量选择相关方法
    # ================================
    
    def update_quality_options(self, info=None):
        """更新质量选项"""
        if info:
            self.available_formats = info.get('formats', [])
        
        # 基础质量选项
        quality_options = [
            "🎯 最佳质量",
            "🖥️ 高清观看 (1080p)",
            "💻 电脑观看 (720p)",
            "📱 手机友好 (480p)",
            "🎵 仅音频",
            "🔧 分离下载合并"
        ]
        
        self.quality_combo['values'] = quality_options
        self.quality_combo.set("🎯 最佳质量")
        self.update_quality_description()
    
    def on_quality_change(self, event=None):
        """质量选择改变时的回调"""
        self.update_quality_description()
    
    def update_quality_description(self):
        """更新质量说明"""
        selected = self.quality_combo.get()
        descriptions = {
            "🎯 最佳质量": "自动选择最高可用质量",
            "🖥️ 高清观看 (1080p)": "适合大屏幕观看",
            "💻 电脑观看 (720p)": "平衡质量与文件大小",
            "📱 手机友好 (480p)": "适合移动设备",
            "🎵 仅音频": "提取音频文件",
            "🔧 分离下载合并": "最高质量，需要FFmpeg"
        }
        
        desc = descriptions.get(selected, "")
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
        self.update_progress(0, "🚀 准备下载...")
        
        def download_thread():
            try:
                self.downloader.execute_download(url, download_path, quality)
                self.root.after(0, lambda: self.update_progress(100, "✅ 下载完成!"))
            except Exception as e:
                error_msg = f"❌ 下载失败: {str(e)}"
                self.root.after(0, lambda: self.update_progress(0, error_msg))
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
            self.progress_bar['value'] = percentage
            self.progress_var.set(status_text)
            self.root.update_idletasks()
        except:
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