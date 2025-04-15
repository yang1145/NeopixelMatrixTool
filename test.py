# Python env   :               
# -*- coding: utf-8 -*-        
# @Time    : 2025/4/15 下午11:04   
# @Author  : 李清水            
# @File    : test.py       
# @Description :

# ======================================== 导入相关模块 =========================================

import pygame
import json
import os
import argparse
import glob
from pygame import gfxdraw

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def rgb565_to_rgb888(rgb565):
    """将RGB565转换为RGB888"""
    r = ((rgb565 >> 11) & 0x1F)
    g = ((rgb565 >> 5) & 0x3F)
    b = (rgb565 & 0x1F)

    r8 = int(((r * 527 + 23) >> 6)*0.2)
    g8 = int(((g * 259 + 33) >> 6)*0.2)
    b8 = int(((b * 527 + 23) >> 6)*0.2)

    return (r8, g8, b8)

# ======================================== 自定义类 ============================================

class WS2812Simulator:
    def __init__(self, width, height, pixel_size=40, fps=30):
        self.width = width
        self.height = height
        self.pixel_size = pixel_size
        self.fps = fps
        self.screen_width = width * pixel_size
        self.screen_height = height * pixel_size
        self.clock = pygame.time.Clock()

        pygame.init()
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("WS2812 Simulator")
        self.font = pygame.font.SysFont('Arial', 16)

        self.frames = []
        self.current_frame = 0
        self.playing = False
        self.show_numbers = False

    def load_frames(self, json_pattern):
        """加载JSON帧文件"""
        file_list = sorted(glob.glob(json_pattern))
        self.frames = []

        for file_path in file_list:
            with open(file_path, 'r') as f:
                data = json.load(f)
                pixels = [rgb565_to_rgb888(p) for p in data['pixels']]
                self.frames.append(pixels)

        print(f"Loaded {len(self.frames)} frames")

    def draw_grid(self):
        """绘制LED网格"""
        for y in range(self.height):
            for x in range(self.width):
                index = y * self.width + x
                if index < len(self.frames[self.current_frame]):
                    color = self.frames[self.current_frame][index]
                else:
                    color = (0, 0, 0)

                rect = pygame.Rect(
                    x * self.pixel_size,
                    y * self.pixel_size,
                    self.pixel_size,
                    self.pixel_size
                )

                # 绘制LED
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, (40, 40, 40), rect, 1)  # 网格线

                # 显示编号
                if self.show_numbers:
                    text = self.font.render(str(index), True, (255, 255, 255))
                    text_rect = text.get_rect(center=rect.center)
                    self.screen.blit(text, text_rect)

        # 显示帧信息
        info_text = f"Frame: {self.current_frame + 1}/{len(self.frames)} | Size: {self.width}x{self.height}"
        text_surface = self.font.render(info_text, True, (255, 255, 255))
        self.screen.blit(text_surface, (5, 5))

    def run(self):
        """运行模拟器"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.playing = not self.playing
                    elif event.key == pygame.K_RIGHT:
                        self.current_frame = min(self.current_frame + 1, len(self.frames) - 1)
                        self.playing = False
                    elif event.key == pygame.K_LEFT:
                        self.current_frame = max(self.current_frame - 1, 0)
                        self.playing = False
                    elif event.key == pygame.K_n:
                        self.show_numbers = not self.show_numbers
                    elif event.key == pygame.K_ESCAPE:
                        running = False

            if self.playing:
                self.current_frame = (self.current_frame + 1) % len(self.frames)

            self.screen.fill((0, 0, 0))
            self.draw_grid()
            pygame.display.flip()
            self.clock.tick(self.fps)

        pygame.quit()

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================

def main():
    parser = argparse.ArgumentParser(description='WS2812 LED矩阵模拟器')
    parser.add_argument('-p', '--path', default='test_image_frame_*.json',
                        help='JSON帧文件路径模式 (默认: test_image_frame_*.json)')
    parser.add_argument('-W', '--width', type=int, required=True, help='LED矩阵宽度')
    parser.add_argument('-H', '--height', type=int, required=True, help='LED矩阵高度')
    parser.add_argument('-s', '--size', type=int, default=40,
                        help='每个LED的显示大小(像素) (默认: 40)')
    parser.add_argument('-f', '--fps', type=int, default=30,
                        help='播放帧率 (默认: 30)')

    args = parser.parse_args()

    simulator = WS2812Simulator(args.width, args.height, args.size, args.fps)
    simulator.load_frames(args.path)
    simulator.run()


if __name__ == "__main__":
    main()