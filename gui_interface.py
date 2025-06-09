"""
UI组件模块 - 处理界面相关的功能
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import io
import requests


class GuiInterface:
    """UI组件管理类"""
    
    def __init__(self, parent):
        self.parent = parent
        
    def setup_main_gui(self):
        """设置主界面"""
        # 主框架
        main_frame = ttk.Frame(self.parent.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题和作者信息
        self._setup_header(main_frame)
        
        # URL输入区域
        self._setup_url_input(main_frame)
        
        # 视频信息显示区域
        self._setup_info_display(main_frame)
        
        # 下载选项区域
        self._setup_download_options(main_frame)
        
        # 下载按钮区域
        self._setup_download_buttons(main_frame)
        
        # 进度显示区域
        self._setup_progress_display(main_frame)
        
        # 配置权重
        self._configure_weights(main_frame)
        
    def _setup_header(self, parent):
        """设置标题和作者信息"""
        title_label = ttk.Label(parent, text="YouTube视频下载器", 
                               font=('微软雅黑', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 5))
        
        author_label = ttk.Label(parent, text="作者：二号饺", 
                                font=('微软雅黑', 9), foreground='#666666')
        author_label.grid(row=1, column=0, columnspan=3, pady=(0, 15))
        
    def _setup_url_input(self, parent):
        """设置URL输入区域"""
        ttk.Label(parent, text="视频网址:", font=('微软雅黑', 10)).grid(
            row=2, column=0, sticky=tk.W, pady=5)
        
        self.parent.url_entry = ttk.Entry(parent, width=60, font=('微软雅黑', 10))
        self.parent.url_entry.grid(row=2, column=1, padx=(10, 0), pady=5, sticky=(tk.W, tk.E))
        
        self.parent.info_button = ttk.Button(parent, text="获取视频信息", 
                                            command=self.parent.get_video_info)
        self.parent.info_button.grid(row=2, column=2, padx=(10, 0), pady=5)
        
    def _setup_info_display(self, parent):
        """设置视频信息显示区域"""
        info_frame = ttk.LabelFrame(parent, text="视频信息", padding="10")
        info_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # 左右布局
        info_left_frame = ttk.Frame(info_frame)
        info_left_frame.grid(row=0, column=0, sticky=(tk.N, tk.W), padx=(0, 10))
        
        info_right_frame = ttk.Frame(info_frame)
        info_right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 视频封面预览
        self._setup_thumbnail_display(info_left_frame)
        
        # 视频信息文本
        self._setup_info_text(info_right_frame)
        
        # 配置权重
        info_frame.columnconfigure(1, weight=1)
        info_right_frame.columnconfigure(0, weight=1)
        
    def _setup_thumbnail_display(self, parent):
        """设置缩略图显示"""
        self.parent.thumbnail_frame = tk.Frame(parent, bg='#f0f0f0', relief='sunken', bd=2)
        self.parent.thumbnail_frame.grid(row=0, column=0, padx=5, pady=5)
        
        self.parent.thumbnail_label = tk.Label(
            self.parent.thumbnail_frame, 
            text="封面预览\n(获取视频信息后显示)", 
            font=('微软雅黑', 9), bg='#f0f0f0', anchor='center'
        )
        self.parent.thumbnail_label.pack(padx=10, pady=10)
        
        # 设置固定尺寸
        self.parent.thumbnail_frame.configure(width=280, height=210)
        self.parent.thumbnail_frame.pack_propagate(False)
        
    def _setup_info_text(self, parent):
        """设置信息文本显示"""
        self.parent.info_text = tk.Text(parent, height=8, width=50, font=('微软雅黑', 9))
        info_scrollbar = ttk.Scrollbar(parent, orient="vertical", 
                                      command=self.parent.info_text.yview)
        self.parent.info_text.configure(yscrollcommand=info_scrollbar.set)
        self.parent.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        info_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
    def _setup_download_options(self, parent):
        """设置下载选项区域"""
        options_frame = ttk.LabelFrame(parent, text="下载选项", padding="10")
        options_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # 质量选择
        self._setup_quality_selection(options_frame)
        
        # 下载路径
        self._setup_path_selection(options_frame)
        
        # 配置权重
        options_frame.columnconfigure(1, weight=1)
        
    def _setup_quality_selection(self, parent):
        """设置质量选择"""
        ttk.Label(parent, text="视频质量:", font=('微软雅黑', 10)).grid(
            row=0, column=0, sticky=tk.W, pady=5)
        
        self.parent.quality_container = ttk.Frame(parent)
        self.parent.quality_container.grid(row=0, column=1, padx=(10, 0), pady=5, sticky=(tk.W, tk.E))
        
        self.parent.default_quality_options = []
        self.parent.quality_combo = ttk.Combobox(
            self.parent.quality_container, 
            values=self.parent.default_quality_options, 
            state="readonly", width=25
        )
        self.parent.quality_combo.set("")
        self.parent.quality_combo.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.parent.quality_desc = ttk.Label(
            self.parent.quality_container, text="", 
            font=('微软雅黑', 8), foreground='#666666'
        )
        self.parent.quality_desc.grid(row=1, column=0, sticky=tk.W, pady=(2, 0))
        
        # 绑定选择事件
        self.parent.quality_combo.bind('<<ComboboxSelected>>', self.parent.on_quality_change)
        
        # 配置权重
        self.parent.quality_container.columnconfigure(0, weight=1)
        
    def _setup_path_selection(self, parent):
        """设置路径选择"""
        ttk.Label(parent, text="保存路径:", font=('微软雅黑', 10)).grid(
            row=1, column=0, sticky=tk.W, pady=5)
        
        self.parent.path_entry = ttk.Entry(parent, width=40, font=('微软雅黑', 9))
        self.parent.path_entry.insert(0, self.parent.download_path)
        self.parent.path_entry.grid(row=1, column=1, padx=(10, 0), pady=5, sticky=(tk.W, tk.E))
        
        self.parent.browse_button = ttk.Button(parent, text="浏览", command=self.parent.browse_path)
        self.parent.browse_button.grid(row=1, column=2, padx=(10, 0), pady=5)
        
    def _setup_download_buttons(self, parent):
        """设置下载按钮区域"""
        download_frame = ttk.Frame(parent)
        download_frame.grid(row=5, column=0, columnspan=3, pady=20)
        
        self.parent.download_button = ttk.Button(
            download_frame, text="开始下载", 
            command=self.parent.start_download, state='disabled'
        )
        self.parent.download_button.grid(row=0, column=0, padx=(0, 10))
        
        self.parent.pause_button = ttk.Button(
            download_frame, text="暂停下载", 
            command=self.parent.toggle_pause, state='disabled'
        )
        self.parent.pause_button.grid(row=0, column=1, padx=(0, 10))
        
        self.parent.merge_button = ttk.Button(
            download_frame, text="本地视频、音频合并", 
            command=self.parent.open_local_merge_dialog
        )
        self.parent.merge_button.grid(row=0, column=2, padx=(0, 10))
        
        self.parent.ffmpeg_button = ttk.Button(
            download_frame, text="FFmpeg管理", 
            command=self.parent.show_ffmpeg_menu
        )
        self.parent.ffmpeg_button.grid(row=0, column=3)
        
    def _setup_progress_display(self, parent):
        """设置进度显示区域"""
        progress_frame = ttk.LabelFrame(parent, text="下载进度", padding="10")
        progress_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # 进度文本
        self.parent.progress_var = tk.StringVar()
        self.parent.progress_var.set("⚡ 程序启动中...")
        self.parent.progress_label = ttk.Label(
            progress_frame, textvariable=self.parent.progress_var, 
            font=('微软雅黑', 10)
        )
        self.parent.progress_label.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # 进度条
        self.parent.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', maximum=100)
        self.parent.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # 配置权重
        progress_frame.columnconfigure(0, weight=1)
        
    def _configure_weights(self, main_frame):
        """配置组件权重"""
        main_frame.columnconfigure(1, weight=1)
        self.parent.root.columnconfigure(0, weight=1)
        
    def update_thumbnail_display(self, photo):
        """更新缩略图显示"""
        self.parent.thumbnail_label.configure(image=photo, text="")
        self.parent.thumbnail_label.image = photo
        
    def reset_thumbnail_display(self):
        """重置缩略图显示"""
        self.parent.thumbnail_label.configure(
            image="", 
            text="封面预览\n(获取视频信息后显示)"
        )
        self.parent.thumbnail_label.image = None
        
    def download_and_display_thumbnail(self, thumbnail_url):
        """下载并显示缩略图"""
        try:
            response = requests.get(thumbnail_url, timeout=10)
            if response.status_code == 200:
                image_data = response.content
                image = Image.open(io.BytesIO(image_data))
                
                # 调整图片大小以适应显示区域
                display_width, display_height = 260, 195
                image.thumbnail((display_width, display_height), Image.Resampling.LANCZOS)
                
                # 创建居中的背景
                background = Image.new('RGB', (display_width, display_height), (240, 240, 240))
                
                # 计算居中位置
                x = (display_width - image.width) // 2
                y = (display_height - image.height) // 2
                background.paste(image, (x, y))
                
                # 转换为tkinter可用的格式
                photo = ImageTk.PhotoImage(background)
                
                # 在主线程中更新显示
                self.parent.root.after(0, lambda: self.update_thumbnail_display(photo))
                
        except Exception as e:
            print(f"缩略图下载失败: {e}")
            # 在主线程中重置显示
            self.parent.root.after(0, self.reset_thumbnail_display) 