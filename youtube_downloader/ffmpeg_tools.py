"""
FFmpeg管理模块 - 处理FFmpeg安装、检测和视频合并功能
"""
import os
import subprocess
import shutil
import threading
import requests
import zipfile
import tempfile
from tkinter import messagebox
import tkinter as tk
from tkinter import ttk
import time


class FFmpegTools:
    """FFmpeg管理类"""
    
    def __init__(self, parent):
        self.parent = parent
        
    def check_ffmpeg_installed(self):
        """检查FFmpeg是否已安装"""
        # 创建startupinfo以隐藏命令行窗口
        startupinfo = None
        if os.name == 'nt':  # Windows系统
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        
        # 检查系统PATH中的ffmpeg
        if shutil.which('ffmpeg'):
            try:
                result = subprocess.run(['ffmpeg', '-version'], 
                                      capture_output=True, text=True, timeout=5, startupinfo=startupinfo)
                if result.returncode == 0:
                    return True
            except:
                pass
        
        # 检查本地缓存的ffmpeg
        local_ffmpeg = self.get_local_ffmpeg_path()
        if os.path.exists(local_ffmpeg):
            try:
                result = subprocess.run([local_ffmpeg, '-version'], 
                                      capture_output=True, text=True, timeout=5, startupinfo=startupinfo)
                if result.returncode == 0:
                    return True
            except:
                pass
        
        return False
    
    def get_ffmpeg_cache_dir(self):
        """获取FFmpeg缓存目录"""
        try:
            # 尝试使用用户的AppData目录
            appdata = os.environ.get('APPDATA')
            if appdata:
                cache_dir = os.path.join(appdata, 'YouTubeDownloader', 'ffmpeg')
            else:
                # 回退到当前目录
                cache_dir = os.path.join(os.getcwd(), 'ffmpeg_cache')
            
            os.makedirs(cache_dir, exist_ok=True)
            return cache_dir
        except:
            # 如果都失败了，使用临时目录
            return tempfile.gettempdir()
    
    def get_local_ffmpeg_path(self):
        """获取本地FFmpeg可执行文件路径"""
        cache_dir = self.get_ffmpeg_cache_dir()
        return os.path.join(cache_dir, 'ffmpeg.exe')
    
    def merge_video_audio(self, video_file, audio_file, output_file):
        """合并视频和音频文件"""
        try:
            # 检查FFmpeg
            ffmpeg_path = 'ffmpeg'
            if not shutil.which('ffmpeg'):
                local_ffmpeg = self.get_local_ffmpeg_path()
                if os.path.exists(local_ffmpeg):
                    ffmpeg_path = local_ffmpeg
                else:
                    raise Exception("FFmpeg未安装")
            
            # 获取文件大小信息
            video_size = self.format_bytes(os.path.getsize(video_file))
            audio_size = self.format_bytes(os.path.getsize(audio_file))
            
            # 更新进度 - 开始合并
            self.parent.root.after(0, lambda: self.parent.update_progress(90, f"🔧 步骤3/3 - 正在合并文件: 视频({video_size}) + 音频({audio_size})"))
            
            # 构建FFmpeg命令
            cmd = [
                ffmpeg_path,
                '-i', video_file,
                '-i', audio_file,
                '-c:v', 'copy',    # 直接复制视频流，不重新编码
                '-c:a', 'aac',     # 音频转为AAC格式
                '-y',              # 覆盖输出文件
                output_file
            ]
            
            # 执行合并
            self.parent.root.after(0, lambda: self.parent.update_progress(95, f"🔧 步骤3/3 - 视频与音频合并处理中..."))
            
            # 创建startupinfo以隐藏命令行窗口
            startupinfo = None
            if os.name == 'nt':  # Windows系统
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=300, startupinfo=startupinfo)
            
            if process.returncode == 0:
                # 合并成功，显示简洁的完成信息
                if os.path.exists(output_file):
                    final_size = self.format_bytes(os.path.getsize(output_file))
                    status_text = f"✅ 下载完成！文件: {os.path.basename(output_file)} ({final_size})"
                else:
                    status_text = f"✅ 下载完成: {os.path.basename(output_file)}"
                
                self.parent.root.after(0, lambda: self.parent.update_progress(100, status_text))
                return True
            else:
                error_msg = process.stderr if process.stderr else "未知错误"
                raise Exception(f"FFmpeg合并失败: {error_msg}")
                
        except subprocess.TimeoutExpired:
            raise Exception("合并超时，文件可能过大")
        except Exception as e:
            raise Exception(f"合并失败: {str(e)}")
    
    def format_bytes(self, bytes_val):
        """格式化字节数"""
        try:
            for unit in ['B', 'KB', 'MB', 'GB']:
                if bytes_val < 1024.0:
                    return f"{bytes_val:.1f}{unit}"
                bytes_val /= 1024.0
            return f"{bytes_val:.1f}TB"
        except:
            return "未知大小"
    
    def download_and_extract_ffmpeg(self):
        """下载并解压FFmpeg"""
        try:
            # FFmpeg下载链接 (Windows 64位版本)
            ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
            
            cache_dir = self.get_ffmpeg_cache_dir()
            zip_path = os.path.join(cache_dir, 'ffmpeg.zip')
            
            # 开始下载
            self.parent.root.after(0, lambda: self.parent.update_progress(5, "🌐 连接到FFmpeg下载服务器..."))
            
            # 下载FFmpeg
            response = requests.get(ffmpeg_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            start_time = time.time()
            
            # 显示文件大小信息
            if total_size > 0:
                total_size_str = self.format_bytes(total_size)
                self.parent.root.after(0, lambda: self.parent.update_progress(10, f"📥 开始下载FFmpeg ({total_size_str})..."))
            else:
                self.parent.root.after(0, lambda: self.parent.update_progress(10, "📥 开始下载FFmpeg..."))
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            # 计算进度百分比
                            progress_percent = (downloaded / total_size) * 100
                            overall_progress = 10 + (progress_percent * 0.5)  # 10-60%
                            
                            # 计算下载速度
                            elapsed_time = time.time() - start_time
                            if elapsed_time > 0:
                                speed_bps = downloaded / elapsed_time
                                speed_str = self.format_bytes(speed_bps) + "/s"
                                
                                # 计算剩余时间
                                if speed_bps > 0:
                                    remaining_bytes = total_size - downloaded
                                    eta_seconds = remaining_bytes / speed_bps
                                    
                                    if eta_seconds < 60:
                                        eta_str = f"{eta_seconds:.0f}秒"
                                    elif eta_seconds < 3600:
                                        eta_str = f"{eta_seconds//60:.0f}分{eta_seconds%60:.0f}秒"
                                    else:
                                        eta_str = f"{eta_seconds//3600:.0f}时{(eta_seconds%3600)//60:.0f}分"
                                else:
                                    eta_str = "计算中..."
                                
                                downloaded_str = self.format_bytes(downloaded)
                                total_str = self.format_bytes(total_size)
                                
                                status_text = f"📥 下载FFmpeg: {progress_percent:.1f}% ({downloaded_str}/{total_str}) | 速度: {speed_str} | 剩余: {eta_str}"
                            else:
                                downloaded_str = self.format_bytes(downloaded)
                                total_str = self.format_bytes(total_size)
                                status_text = f"📥 下载FFmpeg: {progress_percent:.1f}% ({downloaded_str}/{total_str})"
                            
                            # 更新进度（每下载1MB或每秒更新一次）
                            if downloaded % (1024 * 1024) < 8192 or elapsed_time > getattr(self, '_last_update_time', 0) + 1:
                                self.parent.root.after(0, lambda p=overall_progress, s=status_text: self.parent.update_progress(p, s))
                                self._last_update_time = elapsed_time
            
            # 下载完成，开始解压
            downloaded_str = self.format_bytes(downloaded)
            self.parent.root.after(0, lambda: self.parent.update_progress(65, f"✅ 下载完成 ({downloaded_str}) - 开始解压..."))
            
            # 解压FFmpeg
            self.parent.root.after(0, lambda: self.parent.update_progress(70, "📦 正在解压FFmpeg压缩包..."))
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 查找ffmpeg.exe文件
                ffmpeg_found = False
                for file_info in zip_ref.filelist:
                    if file_info.filename.endswith('ffmpeg.exe'):
                        # 显示解压进度
                        self.parent.root.after(0, lambda: self.parent.update_progress(80, f"📦 解压FFmpeg可执行文件..."))
                        
                        # 解压到缓存目录
                        with zip_ref.open(file_info) as source, open(self.get_local_ffmpeg_path(), 'wb') as target:
                            shutil.copyfileobj(source, target)
                        ffmpeg_found = True
                        break
                
                if not ffmpeg_found:
                    raise Exception("压缩包中未找到FFmpeg可执行文件")
            
            # 清理下载的zip文件
            self.parent.root.after(0, lambda: self.parent.update_progress(90, "🧹 清理临时文件..."))
            try:
                os.remove(zip_path)
            except:
                pass
            
            # 验证安装
            self.parent.root.after(0, lambda: self.parent.update_progress(95, "🔍 验证FFmpeg安装..."))
            if self.check_ffmpeg_installed():
                # 获取FFmpeg版本信息
                try:
                    # 创建startupinfo以隐藏命令行窗口
                    startupinfo = None
                    if os.name == 'nt':  # Windows系统
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        startupinfo.wShowWindow = subprocess.SW_HIDE
                    
                    result = subprocess.run([self.get_local_ffmpeg_path(), '-version'], 
                                          capture_output=True, text=True, timeout=5, startupinfo=startupinfo)
                    if result.returncode == 0:
                        # 提取版本信息
                        version_line = result.stdout.split('\n')[0]
                        if 'ffmpeg version' in version_line:
                            version_info = version_line.split('ffmpeg version ')[1].split(' ')[0]
                            status_text = f"✅ FFmpeg安装完成 (版本: {version_info}) - 现在支持高画质合并功能！"
                        else:
                            status_text = "✅ FFmpeg安装完成 - 现在支持高画质合并功能！"
                    else:
                        status_text = "✅ FFmpeg安装完成 - 现在支持高画质合并功能！"
                except:
                    status_text = "✅ FFmpeg安装完成 - 现在支持高画质合并功能！"
                
                self.parent.root.after(0, lambda: self.parent.update_progress(100, status_text))
                return True
            else:
                raise Exception("FFmpeg安装验证失败")
                
        except requests.RequestException as e:
            raise Exception(f"下载失败: {str(e)}")
        except zipfile.BadZipFile:
            raise Exception("FFmpeg压缩包损坏")
        except Exception as e:
            raise Exception(f"FFmpeg安装失败: {str(e)}")
    
    def auto_download_ffmpeg(self):
        """自动下载FFmpeg的后台线程"""
        def download_thread():
            try:
                self.download_and_extract_ffmpeg()
                
                # 下载成功后的处理
                def on_success():
                    messagebox.showinfo("安装完成", "FFmpeg安装完成！现在可以使用完整功能了。")
                    self.parent.reset_ffmpeg_download_ui()
                
                self.parent.root.after(0, on_success)
                
            except Exception as e:
                # 下载失败后的处理
                def on_error():
                    messagebox.showerror("安装失败", f"FFmpeg自动安装失败：{str(e)}\n\n请尝试手动安装或检查网络连接。")
                    self.parent.reset_ffmpeg_download_ui()
                
                self.parent.root.after(0, on_error)
        
        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()
    
    def show_ffmpeg_menu(self):
        """显示FFmpeg管理菜单"""
        menu_window = tk.Toplevel(self.parent.root)
        menu_window.title("FFmpeg管理")
        menu_window.geometry("500x400")
        menu_window.transient(self.parent.root)
        menu_window.grab_set()
        
        # 创建主框架
        main_frame = ttk.Frame(menu_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="FFmpeg管理工具", font=('微软雅黑', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 状态检查
        status_frame = ttk.LabelFrame(main_frame, text="FFmpeg状态", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 检查FFmpeg状态
        is_installed = self.check_ffmpeg_installed()
        
        if is_installed:
            status_text = "✅ FFmpeg已安装并可用"
            status_color = "green"
        else:
            status_text = "❌ FFmpeg未安装或不可用"
            status_color = "red"
        
        status_label = tk.Label(status_frame, text=status_text, fg=status_color, font=('微软雅黑', 10))
        status_label.pack()
        
        # 操作按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        def refresh_status():
            menu_window.destroy()
            self.show_ffmpeg_menu()
        
        def install_ffmpeg():
            menu_window.destroy()
            self.auto_download_ffmpeg()
        
        def open_help():
            self.show_ffmpeg_help()
        
        ttk.Button(button_frame, text="刷新状态", command=refresh_status).pack(side=tk.LEFT, padx=(0, 10))
        
        if not is_installed:
            ttk.Button(button_frame, text="自动安装", command=install_ffmpeg).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="帮助说明", command=open_help).pack(side=tk.LEFT, padx=(0, 10))
        
        # 说明文本
        info_frame = ttk.LabelFrame(main_frame, text="说明", padding="10")
        info_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        info_text = tk.Text(info_frame, wrap=tk.WORD, height=8, font=('微软雅黑', 9))
        scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=info_text.yview)
        info_text.configure(yscrollcommand=scrollbar.set)
        
        info_content = """FFmpeg是一个强大的多媒体处理工具，用于：

• 🔧 分离下载模式：下载最高质量的视频和音频，然后合并
• 🎬 本地文件合并：合并本地的视频和音频文件
• 🎵 音频格式转换：支持多种音频格式

自动安装说明：
- 程序会从GitHub下载官方编译版本
- 文件大小约80-100MB
- 安装到用户AppData目录，不影响系统

手动安装方式：
1. 访问 https://ffmpeg.org/download.html
2. 下载Windows版本
3. 解压后将ffmpeg.exe添加到系统PATH
4. 或将ffmpeg.exe放到程序目录"""

        info_text.insert(tk.END, info_content)
        info_text.configure(state=tk.DISABLED)
        
        info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 关闭按钮
        ttk.Button(main_frame, text="关闭", command=menu_window.destroy).pack(pady=(20, 0))
    
    def show_ffmpeg_help(self):
        """显示FFmpeg帮助信息"""
        help_window = tk.Toplevel(self.parent.root)
        help_window.title("FFmpeg帮助")
        help_window.geometry("600x500")
        help_window.transient(self.parent.root)
        
        main_frame = ttk.Frame(help_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(main_frame, text="FFmpeg帮助文档", font=('微软雅黑', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        text_widget = tk.Text(main_frame, wrap=tk.WORD, font=('微软雅黑', 9))
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        help_content = """什么是FFmpeg？

FFmpeg是一个免费的开源软件，用于处理多媒体数据。在YouTube下载器中，它主要用于：

🔧 视频音频合并
当选择"分离下载合并"模式时，程序会：
1. 下载最高质量的视频流（无音频）
2. 下载最高质量的音频流
3. 使用FFmpeg将两者合并成完整视频

📱 格式转换
支持多种视频和音频格式之间的转换

🎵 音频处理
提取音频、调整音质等功能

安装方式：

1. 自动安装（推荐）
   - 点击"自动安装"按钮
   - 程序会自动下载并配置FFmpeg
   - 安装到用户目录，不影响系统

2. 手动安装
   - 访问 https://ffmpeg.org/download.html
   - 下载Windows版本
   - 解压后添加到系统PATH
   - 或放到程序目录

常见问题：

Q: 为什么需要FFmpeg？
A: YouTube等平台的高质量视频通常将视频和音频分开存储，需要FFmpeg合并。

Q: 没有FFmpeg能否使用？
A: 可以，但只能下载较低质量的视频，无法使用分离下载模式。

Q: FFmpeg安全吗？
A: 是的，FFmpeg是著名的开源项目，被广泛使用。

Q: 安装位置在哪里？
A: 自动安装会放在：%APPDATA%\\YouTubeDownloader\\ffmpeg\\

技术支持：
如果遇到问题，请检查：
1. 网络连接是否正常
2. 防火墙是否阻止下载
3. 磁盘空间是否充足"""

        text_widget.insert(tk.END, help_content)
        text_widget.configure(state=tk.DISABLED)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 关闭按钮
        ttk.Button(main_frame, text="关闭", command=help_window.destroy).pack(pady=(20, 0))
    
    def clear_ffmpeg_cache(self):
        """清理FFmpeg缓存"""
        try:
            cache_dir = self.get_ffmpeg_cache_dir()
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir)
                return True
        except:
            pass
        return False
    
    def open_local_merge_dialog(self):
        """打开本地文件合并对话框"""
        merge_window = tk.Toplevel(self.parent.root)
        merge_window.title("本地文件合并")
        merge_window.geometry("600x460")
        merge_window.transient(self.parent.root)
        merge_window.grab_set()
        
        main_frame = ttk.Frame(merge_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(main_frame, text="本地视频音频合并工具", font=('微软雅黑', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="选择文件", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 视频文件选择
        ttk.Label(file_frame, text="视频文件:").grid(row=0, column=0, sticky=tk.W, pady=5)
        video_entry = ttk.Entry(file_frame, width=50)
        video_entry.grid(row=0, column=1, padx=(10, 0), pady=5, sticky=(tk.W, tk.E))
        
        def browse_video():
            file_path = tk.filedialog.askopenfilename(
                title="选择视频文件",
                filetypes=[("视频文件", "*.mp4 *.avi *.mkv *.mov *.webm"), ("所有文件", "*.*")]
            )
            if file_path:
                video_entry.delete(0, tk.END)
                video_entry.insert(0, file_path)
        
        ttk.Button(file_frame, text="浏览", command=browse_video).grid(row=0, column=2, padx=(10, 0), pady=5)
        
        # 音频文件选择
        ttk.Label(file_frame, text="音频文件:").grid(row=1, column=0, sticky=tk.W, pady=5)
        audio_entry = ttk.Entry(file_frame, width=50)
        audio_entry.grid(row=1, column=1, padx=(10, 0), pady=5, sticky=(tk.W, tk.E))
        
        def browse_audio():
            file_path = tk.filedialog.askopenfilename(
                title="选择音频文件",
                filetypes=[("音频文件", "*.mp3 *.aac *.m4a *.wav *.ogg"), ("所有文件", "*.*")]
            )
            if file_path:
                audio_entry.delete(0, tk.END)
                audio_entry.insert(0, file_path)
        
        ttk.Button(file_frame, text="浏览", command=browse_audio).grid(row=1, column=2, padx=(10, 0), pady=5)
        
        # 输出设置
        output_frame = ttk.LabelFrame(main_frame, text="输出设置", padding="10")
        output_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(output_frame, text="输出文件:").grid(row=0, column=0, sticky=tk.W, pady=5)
        output_entry = ttk.Entry(output_frame, width=50)
        output_entry.grid(row=0, column=1, padx=(10, 0), pady=5, sticky=(tk.W, tk.E))
        
        def browse_output():
            file_path = tk.filedialog.asksaveasfilename(
                title="保存合并文件",
                defaultextension=".mp4",
                filetypes=[("MP4文件", "*.mp4"), ("所有文件", "*.*")]
            )
            if file_path:
                output_entry.delete(0, tk.END)
                output_entry.insert(0, file_path)
        
        ttk.Button(output_frame, text="浏览", command=browse_output).grid(row=0, column=2, padx=(10, 0), pady=5)
        
        # 进度显示
        progress_frame = ttk.LabelFrame(main_frame, text="合并进度", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        progress_var = tk.StringVar()
        progress_var.set("等待开始...")
        progress_label = ttk.Label(progress_frame, textvariable=progress_var)
        progress_label.pack(pady=(0, 5))
        
        progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        progress_bar.pack(fill=tk.X)
        
        # 配置权重
        file_frame.columnconfigure(1, weight=1)
        output_frame.columnconfigure(1, weight=1)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        def start_merge():
            video_path = video_entry.get().strip()
            audio_path = audio_entry.get().strip()
            output_path = output_entry.get().strip()
            
            if not all([video_path, audio_path, output_path]):
                messagebox.showerror("错误", "请选择所有必要的文件")
                return
            
            if not os.path.exists(video_path):
                messagebox.showerror("错误", f"视频文件不存在: {video_path}")
                return
                
            if not os.path.exists(audio_path):
                messagebox.showerror("错误", f"音频文件不存在: {audio_path}")
                return
            
            # 开始合并
            self.start_local_merge(video_path, audio_path, output_path, progress_var, progress_bar, merge_window)
        
        ttk.Button(button_frame, text="开始合并", command=start_merge).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="关闭", command=merge_window.destroy).pack(side=tk.LEFT)
    
    def start_local_merge(self, video_path, audio_path, output_path, progress_var, progress_bar, parent_window):
        """开始本地文件合并"""
        def merge_thread():
            try:
                progress_var.set("🔧 正在合并文件...")
                progress_bar['value'] = 10
                
                result = self.merge_video_audio(video_path, audio_path, output_path)
                
                if result:
                    progress_var.set("✅ 合并完成!")
                    progress_bar['value'] = 100
                    messagebox.showinfo("成功", f"文件已成功合并到:\n{output_path}")
                else:
                    progress_var.set("❌ 合并失败")
                    progress_bar['value'] = 0
                    
            except Exception as e:
                progress_var.set(f"❌ 错误: {str(e)}")
                progress_bar['value'] = 0
                messagebox.showerror("错误", f"合并失败:\n{str(e)}")
        
        thread = threading.Thread(target=merge_thread, daemon=True)
        thread.start() 