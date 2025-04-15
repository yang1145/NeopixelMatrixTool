# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/4/14 上午10:44
# @Author  : 李清水
# @File    : main.py
# @Description : WS2812矩阵驱动工具，可以将图片、视频、文字等转换为对应json文件

# ======================================== 导入相关模块 =========================================

import os
import argparse
import json
import cv2
from PIL import Image, ImageDraw
import numpy as np
import imageio

# ======================================== 全局变量 ============================================

# RGB565颜色表对应的RGB值（按顺序）
colors_rgb = [
    (255, 0, 0),    # 纯红
    (0, 255, 0),    # 纯绿
    (0, 0, 255),    # 纯蓝
    (255, 255, 255),# 纯白
    (255, 255, 0),  # 纯黄
    (255, 0, 255),  # 纯紫
    (0, 255, 255),  # 纯青
    (0, 0, 0),      # 纯黑
    (128, 128, 128),# 50%灰
    (255, 165, 0),  # 橙色
    (255, 192, 203),# 粉色
    (0, 100, 0),    # 深绿
    (0, 0, 128),    # 海军蓝
    (255, 0, 127),  # 品红
    (204, 255, 0),  # 柠檬绿
    (135, 206, 235) # 天蓝
]

# 动画参数
FRAMES = 30  # 总帧数
DURATION = 1.0  # 动画总时长(秒)
FPS = FRAMES / DURATION  # 帧率

# ======================================== 功能函数 ============================================

def rgb888_to_rgb565(r, g, b):
    """将 8 位 RGB 转换为 16 位 RGB565 格式"""
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)

def process_image(image_path, output_dir, width, height, description=""):
    """将高分辨率图片分成 width x height 块，每块取平均色并转换为 RGB565"""
    img = Image.open(image_path).convert("RGB")
    img_array = np.array(img)
    orig_h, orig_w, _ = img_array.shape

    block_h = orig_h // height
    block_w = orig_w // width

    pixels = []
    for y in range(height):
        for x in range(width):
            block = img_array[
                y * block_h : (y + 1) * block_h,
                x * block_w : (x + 1) * block_w
            ]
            avg_color = block.mean(axis=(0, 1)).astype(int)
            r, g, b = avg_color
            pixels.append(int(rgb888_to_rgb565(r, g, b)))

    # 生成 JSON 数据
    json_data = {
        "pixels": pixels,
        "width": width,
        "height": height,
        "description": description,
        "version": 1.0
    }

    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}.json")
    with open(output_path, "w") as f:
        json.dump(json_data, f, indent=2)

    print(f"图片已保存至: {output_path}")

def process_video(video_path, output_dir, width, height, frame_interval=30, description=""):
    """将视频帧转为低分辨率平均色 RGB565 数据，按帧保存为 JSON"""
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    interval = max(1, int(fps / frame_interval))

    frame_count = 0
    saved_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % interval == 0:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_array = np.array(frame_rgb)
            orig_h, orig_w, _ = img_array.shape

            block_h = orig_h // height
            block_w = orig_w // width

            pixels = []
            for y in range(height):
                for x in range(width):
                    block = img_array[
                        y * block_h : (y + 1) * block_h,
                        x * block_w : (x + 1) * block_w
                    ]
                    avg_color = block.mean(axis=(0, 1)).astype(int)
                    r, g, b = avg_color
                    pixels.append(int(rgb888_to_rgb565(r, g, b)))

            json_data = {
                "pixels": pixels,
                "width": width,
                "height": height,
                "frame_index": frame_count,
                "timestamp": frame_count / fps,
                "description": description,
                "version": 1.0
            }

            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = os.path.join(output_dir, f"{base_name}_frame_{frame_count:06d}.json")
            with open(output_path, "w") as f:
                json.dump(json_data, f, indent=2)

            saved_count += 1
            print(f"已处理帧: {frame_count}/{total_frames} -> {output_path}")

        frame_count += 1

    cap.release()
    print(f"视频处理完成，共保存 {saved_count} 帧")

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 创建4x4图像
img_array = np.array(colors_rgb, dtype=np.uint8).reshape((4,4,3))
img = Image.fromarray(img_array, 'RGB')

# 放大显示（100x100像素/格子）
img_upscaled = img.resize((400, 400), Image.NEAREST)
img_upscaled.save('test_image.png')

# # 彩虹颜色列表
# RAINBOW = [
#     (255, 0, 0),    # 红
#     (255, 165, 0),  # 橙
#     (255, 255, 0),  # 黄
#     (0, 255, 0),    # 绿
#     (0, 127, 255),  # 蓝
#     (75, 0, 130),   # 靛
#     (148, 0, 211)   # 紫
# ]
#
# def create_arrow_pixel_frame(step):
#     img = Image.new('RGB', (4, 4), (0, 0, 0))  # 真正的 4x4 图像
#     pixels = img.load()
#
#     y = 1
#     for i in range(3):
#         x = (step + i) % 4
#         color = RAINBOW[(step + i) % len(RAINBOW)]
#         pixels[x, y] = color
#
#     # 箭头尖端为白色
#     arrow_x = (step + 2) % 4
#     pixels[arrow_x, y] = (255, 255, 255)
#
#     return img
#
# # 生成30帧动画
# frames = [create_arrow_pixel_frame(i) for i in range(FRAMES)]
#
# # 保存为GIF (每帧时长33ms≈30FPS)
# imageio.mimsave(
#     'test_image.gif',
#     frames,
#     duration=DURATION / FRAMES,
#     loop=0
# )
#
# print(f"已生成 {FRAMES}帧 红色箭头动画 (FPS={FPS:.1f})")

# ========================================  主程序  ===========================================

def main():
    parser = argparse.ArgumentParser(description="图片/视频转 RGB565 JSON 工具")
    parser.add_argument("-i", "--input", required=True, help="输入文件路径（图片或视频）")
    parser.add_argument("-o", "--output", required=True, help="输出目录")
    parser.add_argument("-W", "--width", type=int, required=True, help="目标宽度（像素）")
    parser.add_argument("-H", "--height", type=int, required=True, help="目标高度（像素）")
    parser.add_argument("-f", "--frames", type=int, default=0,
                        help="视频帧率（每秒抽取帧数，0 表示图片模式）")
    parser.add_argument("-d", "--desc", default="", help="描述信息")

    args = parser.parse_args()

    # 创建输出目录
    os.makedirs(args.output, exist_ok=True)

    # 判断文件类型
    if args.frames > 0:
        process_video(
            video_path=args.input,
            output_dir=args.output,
            width=args.width,
            height=args.height,
            frame_interval=args.frames,
            description=args.desc
        )
    else:
        process_image(
            image_path=args.input,
            output_dir=args.output,
            width=args.width,
            height=args.height,
            description=args.desc
        )

if __name__ == "__main__":
    main()