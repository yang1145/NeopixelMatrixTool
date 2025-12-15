# Python env   : Python v3.12.0
# -*- coding: utf-8 -*-        
# @Time    : 2025/12/6 下午2:45   
# @Author  : 李清水            
# @File    : char_converter.py       
# @Description : 单字符转WS2812点阵JSON文件
# @License : MIT

# ======================================== 导入相关模块 =========================================

import json
import os
from PIL import Image, ImageDraw, ImageFont
from ws_converter.editor import rgb888_to_rgb565

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def get_default_font():
    """
    获取默认中文字体（兼容Windows/Linux/Mac）
    """
    # ws_converter的上级是NeopixelMatrixTool
    root_dir = os.path.dirname(os.path.dirname(__file__))
    font_paths = [
        os.path.join(root_dir, "assets", "simhei.ttf"),
        "simhei.ttf",  # Windows备用
        "/System/Library/Fonts/PingFang.ttc",  # Mac
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
    ]
    for path in font_paths:
        print(f"尝试字体路径：{path}，是否存在：{os.path.exists(path)}")
        if os.path.exists(path):
            return path
    raise FileNotFoundError("未找到中文字体文件，请将simhei.ttf放入NeopixelMatrixTool/assets目录")

def char_to_matrix(char, width, height, font_size=None, output_path=None,
                   text_color=(255, 255, 255), bg_color=(0, 0, 0)):
    """
    单字符转WS2812点阵JSON（先二值化→再替换颜色）
    :param char: 单个字符（中文/英文/数字）
    :param width: 点阵宽度
    :param height: 点阵高度
    :param font_size: 字体大小（默认适配高度）
    :param output_path: JSON输出路径
    :param text_color: 文字RGB颜色（默认白色）
    :param bg_color: 背景RGB颜色（默认黑色）
    :return: 点阵数据（RGB565）+ JSON字典
    """
    # 校验：仅允许单字符
    if len(char) != 1:
        raise ValueError("仅支持单个字符输入！")

    # ===================== 第一步：生成纯黑白二值化掩码 =====================
    # 1. 初始化灰度画布（背景=黑）
    mask_img = Image.new("L", (width, height), 0)  # L=灰度模式，0=黑色背景
    mask_draw = ImageDraw.Draw(mask_img)

    # 2. 加载字体（适配尺寸：避免字符超出画布）
    font_size = font_size or max(1, height - 2)  # 字体大小=高度-2，最小1
    font = ImageFont.truetype(get_default_font(), font_size)

    # 3. 手动计算字符居中位置（兼容所有PIL版本，替代anchor）
    bbox = mask_draw.textbbox((0, 0), char, font=font)
    char_w = bbox[2] - bbox[0]
    char_h = bbox[3] - bbox[1]
    x = max(0, (width - char_w) // 2)  # 防止x为负
    y = max(0, (height - char_h) // 2)  # 防止y为负

    # 4. 绘制白色字符（灰度值255），关闭抗锯齿
    mask_draw.text(
        (x, y),
        char,
        fill=255,  # 纯白色绘制字符
        font=font,
        antialias=False  # 严格二值化，无灰色边缘
    )

    # 5. 严格二值化掩码（确保只有0/255两种值）
    threshold = 127
    # 高于阈值=白，否则=黑
    binary_mask = mask_img.point(lambda p: 255 if p > threshold else 0)

    # ===================== 第二步：替换为用户自定义颜色 =====================
    # 1. 初始化RGB画布（最终颜色画布）
    final_img = Image.new("RGB", (width, height), bg_color)
    final_draw = ImageDraw.Draw(final_img)

    # 2. 遍历二值化掩码，替换颜色
    for y_pixel in range(height):
        for x_pixel in range(width):
            mask_pixel = binary_mask.getpixel((x_pixel, y_pixel))
            # 掩码中白色=文字→替换为用户选的文字色
            if mask_pixel == 255:
                final_img.putpixel((x_pixel, y_pixel), text_color)
            # 掩码中黑色=背景→保持初始化的背景色，无需操作

    # ===================== 第三步：转换为RGB565点阵 =====================
    pixels = []
    for y_pixel in range(height):
        for x_pixel in range(width):
            r, g, b = final_img.getpixel((x_pixel, y_pixel))
            pixels.append(rgb888_to_rgb565(r, g, b))

    # ===================== 第四步：保存JSON和预览图 =====================
    json_data = {
        "pixels": pixels,
        "width": width,
        "height": height,
        "char": char,
        "text_color": text_color,
        "bg_color": bg_color,
        "description": f"Character '{char}' matrix ({width}x{height})",
        "version": 1.2
    }
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)

    # 保存预览图（验证效果）
    final_img.save(f"char_preview_{char}.png")

    # 调试信息：统计文字像素数
    text_pixel_count = sum(1 for p in binary_mask.getdata() if p == 255)
    print(f"调试：总像素={width * height}，文字像素数={text_pixel_count}")

    return pixels, json_data

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================