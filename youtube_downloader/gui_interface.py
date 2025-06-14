"""
UI组件模块 - 处理界面相关的功能
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import io
import requests
import os
import sys


class GuiInterface:
    """UI组件管理类"""
    
    def __init__(self, parent):
        self.parent = parent
    
    def get_resource_path(self, relative_path):
        """获取资源文件的绝对路径，兼容开发环境和打包后环境"""
        try:
            # PyInstaller创建临时文件夹，将路径存储在_MEIPASS中
            base_path = sys._MEIPASS
        except Exception:
            # 如果没有_MEIPASS，说明是在开发环境中运行
            base_path = os.path.abspath(".")
        
        return os.path.join(base_path, relative_path)
        
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
        
        author_label = ttk.Label(parent, text="作者：没脖子的猫", 
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
        self.parent.info_text = tk.Text(parent, height=13, width=50, font=('微软雅黑', 9), wrap=tk.WORD)
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
        
        # 添加缓存清理按钮
        self.parent.cache_button = ttk.Button(
            download_frame, text="清理缓存 (0MB)", 
            command=self.parent.clear_cache_simple
        )
        self.parent.cache_button.grid(row=0, column=3, padx=(0, 10))
        
        # 添加打赏按钮
        self.parent.donate_button = ttk.Button(
            download_frame, text="☕ 打赏支持", 
            command=self.show_donation_dialog
        )
        self.parent.donate_button.grid(row=0, column=4, padx=(0, 10))
        
        # 更新缓存按钮显示
        self.update_cache_button()
        
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
    
    def show_donation_dialog(self):
        """显示打赏对话框"""
        
        # 创建对话框窗口
        donate_window = tk.Toplevel(self.parent.root)
        donate_window.title("☕ 支持作者")
        donate_window.geometry("720x600")
        donate_window.transient(self.parent.root)
        donate_window.grab_set()
        donate_window.resizable(False, False)
        
        # 居中显示
        donate_window.update_idletasks()
        x = (donate_window.winfo_screenwidth() // 2) - (720 // 2)
        y = (donate_window.winfo_screenheight() // 2) - (600 // 2)
        donate_window.geometry(f"720x600+{x}+{y}")
        
        # 主框架
        main_frame = ttk.Frame(donate_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="☕ 支持作者", 
                               font=('微软雅黑', 16, 'bold'))
        title_label.pack(pady=(0, 15))
        
        # 感谢信息
        thanks_text = """如果这个工具对您有帮助，欢迎请作者喝杯咖啡！
您的支持是作者持续开发的动力 💪

扫描下方二维码即可打赏："""
        
        thanks_label = ttk.Label(main_frame, text=thanks_text, 
                                font=('微软雅黑', 11), justify=tk.CENTER)
        thanks_label.pack(pady=(0, 25))
        
        # 二维码框架
        qr_frame = ttk.Frame(main_frame)
        qr_frame.pack(pady=10)
        
        # 尝试加载二维码
        try:
            # 支付宝二维码
            zfb_frame = ttk.LabelFrame(qr_frame, text="🟡 支付宝", padding="20")
            zfb_frame.pack(side=tk.LEFT, padx=(0, 20))
            
            zfb_path = self.get_resource_path(os.path.join("assets", "zfb_pay_qr_code.png"))
            if os.path.exists(zfb_path):
                zfb_image = Image.open(zfb_path)
                # 保持原始比例，调整到合适的显示尺寸
                zfb_image.thumbnail((280, 280), Image.Resampling.LANCZOS)
                zfb_photo = ImageTk.PhotoImage(zfb_image)
                
                zfb_label = tk.Label(zfb_frame, image=zfb_photo, bg='white')
                zfb_label.image = zfb_photo  # 保持引用
                zfb_label.pack(pady=5)
            else:
                zfb_label = tk.Label(zfb_frame, text="支付宝二维码\n文件未找到", 
                                   font=('微软雅黑', 10), fg='red')
                zfb_label.pack(pady=40)
            
            # 微信二维码
            wechat_frame = ttk.LabelFrame(qr_frame, text="🟢 微信", padding="20")
            wechat_frame.pack(side=tk.RIGHT, padx=(20, 0))
            
            wechat_path = self.get_resource_path(os.path.join("assets", "wechat_pay_qr_code.png"))
            if os.path.exists(wechat_path):
                wechat_image = Image.open(wechat_path)
                # 保持原始比例，调整到合适的显示尺寸
                wechat_image.thumbnail((280, 280), Image.Resampling.LANCZOS)
                wechat_photo = ImageTk.PhotoImage(wechat_image)
                
                wechat_label = tk.Label(wechat_frame, image=wechat_photo, bg='white')
                wechat_label.image = wechat_photo  # 保持引用
                wechat_label.pack(pady=5)
            else:
                wechat_label = tk.Label(wechat_frame, text="微信二维码\n文件未找到", 
                                      font=('微软雅黑', 10), fg='red')
                wechat_label.pack(pady=40)
                
        except Exception as e:
            error_label = tk.Label(qr_frame, text=f"加载二维码失败：{str(e)}", 
                                 font=('微软雅黑', 10), fg='red')
            error_label.pack(pady=20)
        
        # 底部信息
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=30)
        
        bottom_text = """感谢您的支持！🙏
作者：没脖子的猫"""
        
        bottom_label = ttk.Label(bottom_frame, text=bottom_text, 
                                font=('微软雅黑', 10), justify=tk.CENTER,
                                foreground='#666666')
        bottom_label.pack()
        
        # 关闭按钮
        close_button = ttk.Button(main_frame, text="关闭", 
                                 command=donate_window.destroy)
        close_button.pack(pady=(15, 0))
    
    def update_cache_button(self):
        """更新缓存按钮显示"""
        try:
            cache_info = self.parent.cache_manager.get_cache_info()
            total_size = cache_info['total_size']
            
            if total_size == 0:
                button_text = "清理缓存 (0MB)"
            else:
                size_str = self.parent.cache_manager.format_cache_size(total_size)
                button_text = f"清理缓存 ({size_str})"
            
            self.parent.cache_button.configure(text=button_text)
        except Exception as e:
            print(f"更新缓存按钮失败: {e}")
            self.parent.cache_button.configure(text="清理缓存 (0MB)") 