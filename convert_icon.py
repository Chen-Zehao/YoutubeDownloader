#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图标转换脚本 - 将PNG转换为ICO格式
"""

from PIL import Image
import os

def convert_png_to_ico():
    """将PNG图标转换为ICO格式"""
    png_path = "assets/icon.png"
    ico_path = "assets/icon.ico"
    
    try:
        # 检查PNG文件是否存在
        if not os.path.exists(png_path):
            print(f"❌ PNG文件不存在: {png_path}")
            return False
        
        # 打开PNG图像
        print(f"📁 正在读取PNG文件: {png_path}")
        img = Image.open(png_path)
        
        # 获取图像信息
        width, height = img.size
        print(f"📐 图像尺寸: {width}x{height}")
        
        # 转换为RGBA模式（如果需要）
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            print("🔄 已转换为RGBA模式")
        
        # 创建多个尺寸的图标（Windows推荐）
        # 使用128x128作为主要尺寸，这样在任务栏和窗口标题栏显示效果更好
        icon_sizes = [(128, 128), (256, 256), (64, 64), (48, 48), (32, 32), (16, 16)]
        icon_images = []
        
        for size in icon_sizes:
            resized_img = img.resize(size, Image.Resampling.LANCZOS)
            icon_images.append(resized_img)
            print(f"✅ 创建 {size[0]}x{size[1]} 尺寸图标")
        
        # 保存为ICO文件，将128x128作为主要尺寸
        print(f"💾 正在保存ICO文件: {ico_path}")
        icon_images[0].save(
            ico_path, 
            format='ICO', 
            sizes=[(img.width, img.height) for img in icon_images],
            append_images=icon_images[1:]
        )
        
        # 检查文件大小
        file_size = os.path.getsize(ico_path)
        print(f"✅ ICO文件创建成功!")
        print(f"📊 文件大小: {file_size:,} 字节")
        print(f"📁 保存位置: {ico_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        return False

if __name__ == "__main__":
    print("🔄 开始转换PNG图标为ICO格式...")
    print("=" * 50)
    
    success = convert_png_to_ico()
    
    print("=" * 50)
    if success:
        print("🎉 图标转换完成!")
        print("💡 现在可以更新spec文件使用新的ICO图标")
    else:
        print("❌ 图标转换失败!") 