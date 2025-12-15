# Python env   : Python v3.12.0
# -*- coding: utf-8 -*-
# @Time    : 2025/4/14 上午10:44
# @Author  : 李清水
# @File    : converter.py
# @Description : WS2812矩阵驱动库核心功能文件，可以将图片、视频、文字等转换为对应json文件
# @License : MIT

# ======================================== 导入相关模块 =========================================

from PIL import Image
import numpy as np
import json
import os
import cv2
from tqdm import tqdm

try:
    resample = Image.Resampling.LANCZOS
except AttributeError:
    resample = Image.ANTIALIAS

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def apply_color_adjustments(r, g, b, brightness=1.0, contrast=1.0, saturation=1.0):
    """
        对RGB颜色值进行亮度、对比度、饱和度的调整
        :param r: 红色分量（0-255的整数）
        :param g: 绿色分量（0-255的整数）
        :param b: 蓝色分量（0-255的整数）
        :param brightness: 亮度调整系数（默认1.0，大于1增亮，小于1变暗）
        :param contrast: 对比度调整系数（默认1.0，大于1增强对比度，小于1降低对比度）
        :param saturation: 饱和度调整系数（默认1.0，大于1增加饱和度，小于1降低饱和度）
        :return: 调整后的RGB分量（均为0-255的整数）
    """
    # 计算RGB对应的灰度值（使用ITU-R BT.601标准的灰度转换公式）
    gray = int(0.299 * r + 0.587 * g + 0.114 * b)

    # 调整饱和度：基于灰度值和饱和度系数改变RGB分量
    r = gray + (r - gray) * saturation
    g = gray + (g - gray) * saturation
    b = gray + (b - gray) * saturation

    # 调整对比度：以128为中点，根据对比度系数拉伸/压缩RGB分量
    r = (r - 128) * contrast + 128
    g = (g - 128) * contrast + 128
    b = (b - 128) * contrast + 128

    # 调整亮度：直接乘以亮度系数
    r *= brightness
    g *= brightness
    b *= brightness

    # 将结果限制在0-255范围内并转换为整数后返回
    return max(0, min(int(r), 255)), max(0, min(int(g), 255)), max(0, min(int(b), 255))

def rgb888_to_rgb565(r, g, b):
    """
    将RGB888格式的颜色值转换为RGB565格式
    :param r: RGB888的红色分量（0-255的整数）
    :param g: RGB888的绿色分量（0-255的整数）
    :param b: RGB888的蓝色分量（0-255的整数）
    :return: RGB565格式的颜色值（16位整数）
    """
    # RGB565格式：高5位为红，中间6位为绿，低5位为蓝
    # 右移3位取r的高5位，左移11位放到对应位置
    # 右移2位取g的高6位，左移5位放到对应位置
    # 右移3位取b的高5位，放到最低5位
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)

def convert_image_to_json(image_path, output_dir, width, height, description="", brightness=1.0, contrast=1.0, saturation=1.0):
    """
    将图片转换为指定尺寸的RGB565点阵JSON文件（包含颜色调整）
    :param image_path: 输入图片的路径
    :param output_dir: JSON文件的输出目录
    :param width: 点阵的宽度（列数）
    :param height: 点阵的高度（行数）
    :param description: 点阵的描述信息（默认空字符串）
    :param brightness: 亮度调整系数（默认1.0）
    :param contrast: 对比度调整系数（默认1.0）
    :param saturation: 饱和度调整系数（默认1.0）
    :return: 无返回值（直接生成JSON文件）
    """
    # 打开图片并转换为RGB模式（去除透明通道）
    img = Image.open(image_path).convert("RGB")
    # 放大图片（width*10/height*10是为了后续分块取平均更平滑），使用LANCZOS重采样（高质量缩放）
    img = img.resize((width * 10, height * 10), resample)
    # 将图片转换为numpy数组，方便分块计算
    img_array = np.array(img)
    orig_h, orig_w, _ = img_array.shape
    # 计算每个点阵块的高度和宽度
    block_h, block_w = orig_h // height, orig_w // width

    pixels = []
    # 遍历每个点阵位置（按行优先顺序）
    for y in range(height):
        for x in range(width):
            # 截取当前点阵位置对应的图片块
            block = img_array[y*block_h:(y+1)*block_h, x*block_w:(x+1)*block_w]
            # 计算块内的平均颜色（按像素维度求均值）
            avg_color = block.mean(axis=(0, 1))
            r, g, b = map(int, avg_color)
            r, g, b = apply_color_adjustments(r, g, b, brightness, contrast, saturation)
            # 转换为RGB565格式并加入列表
            pixels.append(rgb888_to_rgb565(r, g, b))

    # 构造JSON数据结构
    json_data = {
        "pixels": pixels,
        "width": width,
        "height": height,
        "description": description,
        "version": 1.0
    }

    # 确保输出目录存在（不存在则创建）
    os.makedirs(output_dir, exist_ok=True)
    # 获取图片的基础文件名（不含扩展名）
    base = os.path.splitext(os.path.basename(image_path))[0]

    # 写入JSON文件（缩进2格，增强可读性）
    with open(os.path.join(output_dir, f"{base}.json"), "w") as f:
        json.dump(json_data, f, indent=2)

def convert_video_to_json(video_path, output_dir, width, height, total_frames=30, description="", brightness=1.0, contrast=1.0, saturation=1.0):
    """
    将视频的指定帧数转换为RGB565点阵JSON文件（包含颜色调整）
    :param video_path: 输入视频的路径
    :param output_dir: JSON文件的输出目录
    :param width: 点阵的宽度（列数）
    :param height: 点阵的高度（行数）
    :param total_frames: 要转换的总帧数（默认30，最多不超过视频总帧数）
    :param description: 点阵的描述信息（默认空字符串）
    :param brightness: 亮度调整系数（默认1.0）
    :param contrast: 对比度调整系数（默认1.0）
    :param saturation: 饱和度调整系数（默认1.0）
    :return: 无返回值（直接生成多个JSON文件，对应不同帧）
    """
    # 打开视频文件
    cap = cv2.VideoCapture(video_path)
    # 获取视频的总帧数和帧率
    total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    # 限制转换的帧数不超过视频总帧数
    total_frames = min(total_frames, total_video_frames)
    # 计算帧间隔，均匀选取指定数量的帧
    interval = total_video_frames // total_frames
    frame_indices = [min(i * interval, total_video_frames - 1) for i in range(total_frames)]

    os.makedirs(output_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(video_path))[0]

    # 遍历帧索引，使用tqdm显示进度条
    for idx in tqdm(frame_indices, desc="正在转换视频帧为JSON"):
        # 设置视频读取的位置为指定帧
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)

        # 读取帧（ret为是否读取成功，frame为帧数据）
        ret, frame = cap.read()
        if not ret:
            continue
        img_array = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = img_array.shape
        block_h, block_w = h // height, w // width

        pixels = []
        # 遍历每个点阵位置（按行优先顺序）
        for y in range(height):
            for x in range(width):
                # 截取当前点阵位置对应的帧块
                block = img_array[y*block_h:(y+1)*block_h, x*block_w:(x+1)*block_w]
                # 计算块内的平均颜色
                avg_color = block.mean(axis=(0, 1))
                r, g, b = map(int, avg_color)
                r, g, b = apply_color_adjustments(r, g, b, brightness, contrast, saturation)
                # 转换为RGB565格式并加入列表
                pixels.append(rgb888_to_rgb565(r, g, b))

        # 构造单帧的JSON数据结构（包含帧索引和时间戳）
        json_data = {
            "pixels": pixels,
            "width": width,
            "height": height,
            "frame_index": idx,
            "timestamp": round(idx / fps, 2), # 计算帧对应的时间戳（保留2位小数）
            "description": description,
            "version": 1.0
        }

        # 写入JSON文件（文件名包含帧索引，补零到4位）
        outpath = os.path.join(output_dir, f"{base}_frame_{idx:04d}.json")
        with open(outpath, "w") as f:
            json.dump(json_data, f, indent=2)

    cap.release()

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================