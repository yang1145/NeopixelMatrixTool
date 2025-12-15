# Python env   : Python v3.12.0
# -*- coding: utf-8 -*-        
# @Time    : 2025/4/16 下午3:05   
# @Author  : 李清水            
# @File    : simulator.py       
# @Description : WS2812矩阵驱动库仿真功能文件，可以模拟WS2812矩阵驱动库的运行效果
# @License : MIT

# ======================================== 导入相关模块 =========================================

import pygame
import glob
import json
import natsort
from threading import Event

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def rgb565_to_rgb888(rgb565):
    """
    高精度RGB565转RGB888（使用硬件级优化算法，提升色彩还原精度）
    :param rgb565: RGB565格式的颜色值（16位整数，结构：高5位红、中间6位绿、低5位蓝）
    :return: 转换后的RGB888格式颜色元组（r, g, b），每个分量为0-255的整数
    """
    r = ((rgb565 >> 11) & 0x1F)
    g = ((rgb565 >> 5) & 0x3F)
    b = (rgb565 & 0x1F)
    return (
        (r * 527 + 23) >> 6,
        (g * 259 + 33) >> 6,
        (b * 527 + 23) >> 6
    )

# ======================================== 自定义类 ============================================

class WS2812Simulator:
    """
    WS2812 LED矩阵仿真器类，基于Pygame实现WS2812矩阵的可视化仿真效果
    核心功能：
        1. 加载JSON格式的帧数据（包含RGB565颜色信息），自动转换为RGB888供渲染
        2. 支持帧的自动播放、暂停，以及上一帧/下一帧手动切换
        3. 支持仿真窗口大小调整，像素显示尺寸自动适配矩阵宽度
        4. 提供线程安全的停止控制机制，支持优雅退出
    """
    def __init__(self, width, height, window_width=1000, fps=30):
        """
        初始化WS2812仿真器的参数和Pygame运行环境
        :param width: WS2812矩阵的宽度（列数，即水平方向LED数量）
        :param height: WS2812矩阵的高度（行数，即垂直方向LED数量）
        :param window_width: 仿真窗口的初始宽度（像素，默认1000）
        :param fps: 帧播放的帧率（默认30帧/秒）
        :return: 无返回值
        """
        # 矩阵尺寸参数
        self.width = width
        self.height = height

        # 计算单个像素的显示尺寸（确保至少为1像素，避免除以零）
        self.pixel_size = max(1, window_width // width)
        # 仿真窗口的实际尺寸（由矩阵尺寸和像素显示尺寸决定）
        self.screen_width = width * self.pixel_size
        self.screen_height = height * self.pixel_size
        # 播放参数
        self.fps = fps
        # 存储所有帧的RGB888颜色数据
        self.frames = []
        # 播放状态标记（True：播放，False：暂停）
        self.current_frame = 0
        # 播放状态标记（True：播放，False：暂停）
        self.playing = False
        # 预留：是否显示像素坐标编号
        self.show_numbers = False
        # 线程停止控制事件（用于优雅退出）
        self.stop_event = Event()

        pygame.init()
        # 创建可调整大小的仿真窗口
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        # 设置窗口标题
        pygame.display.set_caption("WS2812 Simulator")
        # 用于控制帧率的时钟对象
        self.clock = pygame.time.Clock()
        # 用于显示帧信息的字体
        self.font = pygame.font.SysFont('Arial', 16)

    def clear_frames(self):
        """
        清空已加载的帧数据和当前帧索引，为加载新帧数据做准备
        :return: 无返回值
        """
        self.frames.clear()
        self.current_frame = 0

    def load_frames(self, json_pattern):
        """
        根据指定的JSON文件匹配模式加载帧数据，自动将RGB565转换为RGB888格式
        :param json_pattern: JSON帧文件的匹配模式（支持通配符，如"frames/*.json"）
        :return: 无返回值
        """
        # 加载前清空旧数据
        self.clear_frames()
        # 按自然排序获取匹配的JSON文件（确保帧顺序正确）
        files = natsort.natsorted(glob.glob(json_pattern))

        # 遍历每个JSON文件，加载帧数据
        for path in files:
            # 以UTF-8编码打开文件，解决中文内容解码错误
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                # 将帧中的每个RGB565颜色转换为RGB888，存入帧列表
                pixels = [rgb565_to_rgb888(p) for p in data["pixels"]]
                self.frames.append(pixels)

    def draw(self):
        """
        绘制当前帧的WS2812矩阵画面，包括像素点、像素边框和帧信息提示
        :return: 无返回值
        """
        self.screen.fill((0, 0, 0))
        # 无数据时跳过绘制
        if not self.frames: return

        # 遍历每个像素位置，绘制对应的颜色
        for y in range(self.height):
            for x in range(self.width):
                i = y * self.width + x
                color = self.frames[self.current_frame][i] if i < len(self.frames[self.current_frame]) else (0, 0, 0)
                rect = pygame.Rect(x*self.pixel_size, y*self.pixel_size, self.pixel_size, self.pixel_size)
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, (40, 40, 40), rect, 1)

        # 绘制帧信息提示（当前帧/总帧数）
        info = self.font.render(f"Frame: {self.current_frame+1}/{len(self.frames)}", True, (255,255,255))
        self.screen.blit(info, (5, 5))

    def run(self):
        """
        启动仿真器的主循环，处理用户输入事件并播放帧数据
        支持的键盘操作：
            - 空格键：切换播放/暂停状态
            - 左方向键：切换到上一帧（并自动暂停播放）
            - 右方向键：切换到下一帧（并自动暂停播放）
            - 关闭窗口：触发停止事件，退出主循环并释放Pygame资源
        :return: 无返回值
        """
        # 重置停止标志
        self.stop_event.clear()
        # 主循环：直到停止事件被触发
        while not self.stop_event.is_set():
            for event in pygame.event.get():
                # 窗口关闭事件：触发停止事件
                if event.type == pygame.QUIT:
                    self.stop_event.set()
                # 键盘按键事件
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # 空格键：切换播放/暂停
                        self.playing = not self.playing
                    elif event.key == pygame.K_RIGHT:
                        # 右方向键：切换到下一帧（不超过总帧数）
                        self.current_frame = min(self.current_frame + 1, len(self.frames) - 1)
                        self.playing = False
                    elif event.key == pygame.K_LEFT:
                        # 左方向键：切换到上一帧（不小于0）
                        self.current_frame = max(self.current_frame - 1, 0)
                        self.playing = False

            # 播放状态下，自动切换到下一帧（循环播放）
            if self.playing and self.frames:
                self.current_frame = (self.current_frame + 1) % len(self.frames)

            # 绘制当前帧画面
            self.draw()
            pygame.display.flip()
            # 控制帧率，确保运行速度符合设定的FPS
            self.clock.tick(self.fps)
        # 确保退出时释放资源
        pygame.quit()

def run_simulator(json_pattern, width, height, window_width=1000, fps=30):
    """
    快速启动WS2812仿真器的封装函数，简化仿真器的调用流程
    :param json_pattern: JSON帧文件的匹配模式（支持通配符，如"frames/*.json"）
    :param width: WS2812矩阵的宽度（列数）
    :param height: WS2812矩阵的高度（行数）
    :param window_width: 仿真窗口的初始宽度（像素，默认1000）
    :param fps: 帧播放的帧率（默认30帧/秒）
    :return: 无返回值
    """
    # 创建仿真器实例
    sim = WS2812Simulator(width, height, window_width, fps)
    # 加载指定的帧数据
    sim.load_frames(json_pattern)
    # 启动仿真器主循环
    sim.run()

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================