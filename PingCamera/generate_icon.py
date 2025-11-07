#!/usr/bin/env python3
"""
生成 PingCamera 应用的图标
创建一个简洁现代的摄像头图标，支持多种尺寸
"""

from PIL import Image, ImageDraw
import os

def create_camera_icon(size):
    """创建摄像头图标"""
    # 创建透明背景的图片
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 计算比例
    scale = size / 512.0
    
    # 定义颜色
    camera_body_color = (70, 70, 80, 255)  # 深灰色摄像头机身
    lens_color = (40, 40, 50, 255)         # 更深的镜头颜色
    lens_inner_color = (20, 20, 30, 255)   # 镜头内部
    highlight_color = (200, 200, 210, 255) # 高光
    record_dot_color = (255, 80, 80, 255)  # 红色录制指示灯
    
    # 摄像头机身 - 圆角矩形
    body_margin = int(80 * scale)
    body_rect = [body_margin, body_margin + int(60 * scale), 
                 size - body_margin, size - body_margin]
    
    # 绘制机身阴影
    shadow_offset = int(4 * scale)
    shadow_rect = [r + shadow_offset for r in body_rect]
    draw.rounded_rectangle(shadow_rect, radius=int(20 * scale), 
                          fill=(0, 0, 0, 60))
    
    # 绘制机身
    draw.rounded_rectangle(body_rect, radius=int(20 * scale), 
                          fill=camera_body_color)
    
    # 镜头外圈
    lens_center = (size // 2, size // 2 + int(10 * scale))
    lens_radius = int(120 * scale)
    lens_bbox = [lens_center[0] - lens_radius, lens_center[1] - lens_radius,
                 lens_center[0] + lens_radius, lens_center[1] + lens_radius]
    draw.ellipse(lens_bbox, fill=lens_color)
    
    # 镜头内圈
    inner_radius = int(90 * scale)
    inner_bbox = [lens_center[0] - inner_radius, lens_center[1] - inner_radius,
                  lens_center[0] + inner_radius, lens_center[1] + inner_radius]
    draw.ellipse(inner_bbox, fill=lens_inner_color)
    
    # 镜头反光
    highlight_radius = int(35 * scale)
    highlight_center = (lens_center[0] - int(25 * scale), 
                       lens_center[1] - int(25 * scale))
    highlight_bbox = [highlight_center[0] - highlight_radius, 
                     highlight_center[1] - highlight_radius,
                     highlight_center[0] + highlight_radius, 
                     highlight_center[1] + highlight_radius]
    draw.ellipse(highlight_bbox, fill=highlight_color)
    
    # 录制指示灯
    dot_radius = int(12 * scale)
    dot_center = (size - body_margin - int(30 * scale), 
                  body_margin + int(30 * scale))
    dot_bbox = [dot_center[0] - dot_radius, dot_center[1] - dot_radius,
                dot_center[0] + dot_radius, dot_center[1] + dot_radius]
    draw.ellipse(dot_bbox, fill=record_dot_color)
    
    # 顶部小把手/支架
    handle_width = int(60 * scale)
    handle_height = int(15 * scale)
    handle_rect = [size//2 - handle_width//2, body_margin - handle_height,
                   size//2 + handle_width//2, body_margin + int(5 * scale)]
    draw.rounded_rectangle(handle_rect, radius=int(8 * scale), 
                          fill=camera_body_color)
    
    return img

def main():
    """生成所有需要的图标尺寸"""
    # 需要的尺寸
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    
    # 确保目录存在
    icon_dir = "PingCamera/Assets.xcassets/AppIcon.appiconset"
    os.makedirs(icon_dir, exist_ok=True)
    
    print("正在生成 PingCamera 图标...")
    
    for size in sizes:
        print(f"生成 {size}x{size} 图标...")
        icon = create_camera_icon(size)
        
        # 保存为PNG文件
        filename = f"icon_{size}x{size}.png"
        filepath = os.path.join(icon_dir, filename)
        icon.save(filepath, "PNG")
        
        # 如果需要@2x版本
        if size <= 512:
            filename_2x = f"icon_{size}x{size}@2x.png"
            filepath_2x = os.path.join(icon_dir, filename_2x)
            # @2x版本使用双倍尺寸
            icon_2x = create_camera_icon(size * 2)
            icon_2x.save(filepath_2x, "PNG")
            print(f"生成 {filename_2x}")
    
    print("✓ 图标生成完成！")
    print(f"图标文件保存在: {icon_dir}")

if __name__ == "__main__":
    main()
