# Python env   : Python v3.12.0
# -*- coding: utf-8 -*-        
# @Time    : 2025/4/16 下午3:10   
# @Author  : 李清水            
# @File    : gui_app.py       
# @Description : 简洁 Tkinter 界面（文件选择 + 开始转换）
# @License : MIT

# ======================================== 导入相关模块 =========================================

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser
from ws_converter.converter import convert_image_to_json, convert_video_to_json
from ws_converter.simulator import WS2812Simulator
from ws_converter.editor import PixelEditor
from ws_converter.char_converter import get_default_font, char_to_matrix
import threading
import os
import json
import glob
import re
import pygame
from PIL import Image, ImageTk
import time
import cv2
import sys

# ======================================== 全局变量 ============================================

# 仿真器实例和对应的线程
simulator = None
sim_thread = None
# 指向 assets 文件夹（存储图片、图标等资源）
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# 像素矩阵编辑器的独立窗口实例
editor_window = None

# ======================================== 功能函数 ============================================

def resource_path(relative_path):
    """
    用于获取资源路径，兼容 PyInstaller 打包后的环境（打包后资源会放在_MEIPASS目录）
    :param relative_path: 资源的相对路径（字符串）
    :return: 资源的绝对路径（字符串）
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def gui_main():
    """
    主函数：创建并运行视频图像取模工具的Tkinter图形界面
    界面包含四个核心功能标签页：
        1. 图像/视频转换：将图片/视频转换为WS2812点阵的JSON数据
        2. 帧播放模拟器：加载JSON帧数据，仿真播放WS2812矩阵效果
        3. 像素矩阵编辑器：可视化编辑WS2812点阵数据，支持绘制、导入导出
        4. 单字符转点阵：将单个字符（中文/英文/数字）转换为点阵JSON数据
    :return: 无返回值
    """
    # 初始化主窗口
    root = tk.Tk()
    root.title("视频图像取模工具平台 v1.0 - Powered by FreakStudio/Freak嵌入式")
    root.geometry("1080x800")

    try:
        # 加载Logo图像（从assets目录）
        logo_path = resource_path(os.path.join("assets", "FreakStudio.png"))
        logo_img = Image.open(logo_path)
        logo_img = logo_img.resize((300, 300), Image.LANCZOS)
        logo_photo = ImageTk.PhotoImage(logo_img)

        # 加载微信二维码图像（从assets目录）
        wechat_path = resource_path(os.path.join("assets", "WeChat.jpg"))
        wechat_img = Image.open(wechat_path)
        wechat_img = wechat_img.resize((215, 300), Image.LANCZOS)
        wechat_photo = ImageTk.PhotoImage(wechat_img)

    except Exception as e:
        print(f"图片加载失败: {e}")
        logo_photo = None
        wechat_photo = None

    # =================== 顶部Logo栏 =====================
    header_frame = tk.Frame(root, bg="white")
    header_frame.pack(fill="x", pady=5)

    # 左侧Logo
    if logo_photo:
        logo_label = tk.Label(header_frame, image=logo_photo, bg="white")
        # 保持图片引用，防止被垃圾回收
        logo_label.image = logo_photo
        # 上移标题
        logo_label.pack(side="left", padx=10)

    # 中间标题
    title_frame = tk.Frame(header_frame, bg="white")
    title_frame.pack(side="left", expand=True)

    tk.Label(title_frame,
             text="视频图像取模工具v1.0",
             font=("Arial", 40, "bold"),
             # 上移标题
             bg="white").pack(pady=(0, 25))

    # 右侧微信二维码（添加在标题右边）
    if wechat_photo:
        wechat_label = tk.Label(header_frame, image=wechat_photo, bg="white")
        # 保持引用
        wechat_label.image = wechat_photo
        wechat_label.pack(side="right", padx=10)

    # =================== 动态广告栏 =====================
    ad_frame = tk.Frame(root, bg="#007acc", height=30)
    ad_frame.pack(fill="x", pady=(0, 10))

    ad_texts = [
        "比赛咨询/专利软著申请/电子成品定制可联系 AAA Freak嵌入式 加我wx：FreakEmbedded",
        "课设毕设/保研加分/软考各类证书可联系 AAA Freak嵌入式 加我wx：FreakEmbedded",
        "创新创业比赛课程/电子计算机类比赛课程可联系 AAA Freak嵌入式 加我wx：FreakEmbedded",
        "安防监控摄像头购买/电气智能化工程安装可联系 AAA Freak嵌入式 加我wx：FreakEmbedded",
        "廉价版智能沙盘/展厅移动机器人可联系 AAA Freak嵌入式 加我wx：FreakEmbedded",
        "无线AP覆盖/音响安装/智慧门禁/车牌识别可联系 AAA Freak嵌入式 加我wx：FreakEmbedded",
        "山西本地无人机高空清洗作业可联系/数字人视频生成可联系 AAA Freak嵌入式 加我wx：FreakEmbedded",
        "项目科技查新/双软评估/科小认证等包过一条龙可联系 AAA Freak嵌入式 加我wx：FreakEmbedded",
        "企业代理记账/知识产权代缴/企业科技项目申报可联系 AAA Freak嵌入式 加我wx：FreakEmbedded",
        "中国创翼创业创新大赛等各类企业创赛可代做可联系 AAA Freak嵌入式 加我wx：FreakEmbedded"
    ]

    ad_label = tk.Label(ad_frame,
                        text=ad_texts[0],
                        font=("微软雅黑", 17),
                        fg="white",
                        bg="#007acc")
    ad_label.pack()

    # =================== 底部联系信息栏 =====================
    contact_frame = tk.Frame(root, bg="#333333", height=30)
    contact_frame.pack(fill="x", side="bottom", pady=(5, 0))

    contact_texts = [
        "关于软件有任何问题，联系开发者Freak：wx扫码即可，也可以通过邮箱1069653183@qq.com",
        "技术支持/商业合作/定制开发请联系：wx扫码或邮件1069653183@qq.com",
        "获取最新版本/提交问题反馈：请扫描右侧微信二维码或邮件1069653183@qq.com"
    ]

    contact_label = tk.Label(contact_frame,
                           text=contact_texts[0],
                           font=("微软雅黑", 12),
                           fg="white",
                           bg="#333333")
    contact_label.pack()

    # 联系信息滚动动画
    def scroll_contact():
        """
        实现底部联系信息的自动滚动切换，每3秒切换一条信息
        :return: 无返回值
        """
        nonlocal contact_texts
        current_text = contact_label.cget("text")
        next_index = (contact_texts.index(current_text) + 1) % len(contact_texts)
        contact_label.config(text=contact_texts[next_index])
        root.after(3000, scroll_contact)  # 每3秒切换一次

    root.after(3000, scroll_contact)

    # 广告滚动动画
    def scroll_ad():
        """
        实现顶部广告栏的自动滚动切换，每1秒切换一条广告
        :return: 无返回值
        """
        nonlocal ad_texts
        current_text = ad_label.cget("text")
        next_index = (ad_texts.index(current_text) + 1) % len(ad_texts)
        ad_label.config(text=ad_texts[next_index])
        # 每3秒切换一次
        root.after(1000, scroll_ad)

    root.after(1000, scroll_ad)

    # =================== 主界面Tab =====================
    tab_control = ttk.Notebook(root)

    # =================== Tab1：图像/视频转换 =====================
    convert_tab = ttk.Frame(tab_control)
    tab_control.add(convert_tab, text="图像/视频转换")

    # 在参数设置部分下方添加提示信息
    param_frame = tk.Frame(convert_tab)

    # 初始化参数变量
    # 输入文件路径
    input_path = tk.StringVar()
    # 输出目录路径
    output_path = tk.StringVar()
    # WS2812矩阵宽度
    width = tk.IntVar(value=24)
    # WS2812矩阵高度
    height = tk.IntVar(value=16)
    # 视频提取帧数
    frame_count = tk.IntVar(value=30)
    # 转换状态提示
    status1 = tk.StringVar()

    # 新增RGB565格式提示
    format_tip = tk.Label(convert_tab,
                         text="特别提示：转换为WS2812点阵数据时，像素点为RGB565格式",
                         fg="red",
                         font=("微软雅黑", 10, "bold"))
    format_tip.pack(pady=(5, 0))

    # 进度相关变量
    # 进度条数值（0-100）
    progress_var = tk.DoubleVar()
    # 进度提示标签
    progress_label = tk.StringVar(value="准备就绪")

    def browse_input():
        """
        打开文件选择对话框，让用户选择输入的图片/视频文件，并更新input_path变量
        :return: 无返回值
        """
        path = filedialog.askopenfilename()
        if path:
            input_path.set(path)

    def browse_output():
        """
        打开目录选择对话框，让用户选择输出目录，并更新output_path变量
        :return: 无返回值
        """
        path = filedialog.askdirectory()
        if path:
            output_path.set(path)

    def update_progress(current, total, message):
        """
        更新进度条和进度提示标签的显示内容
        :param current: 当前进度值（已完成的数量）
        :param total: 总进度值（总数量）
        :param message: 进度提示文字（如“处理区块:”）
        :return: 无返回值
        """
        progress = (current / total) * 100
        progress_var.set(progress)
        progress_label.set(f"{message} {current}/{total} ({progress:.1f}%)")
        convert_tab.update_idletasks()  # 强制更新UI

    def do_convert():
        """
        执行图像/视频到WS2812点阵JSON数据的转换操作，根据文件类型调用对应转换函数
        支持的图片格式：jpg、jpeg、png、bmp
        支持的视频格式：mp4、avi、mov、mkv
        :return: 无返回值
        """
        file = input_path.get()
        out = output_path.get()
        ext = os.path.splitext(file)[1].lower()
        w, h, f = width.get(), height.get(), frame_count.get()

        # 校验输入输出路径
        if not file or not out:
            messagebox.showerror("错误", "请选择输入文件和输出目录")
            return

        try:
            if ext in [".jpg", ".jpeg", ".png", ".bmp"]:
                # 图像转换进度模拟
                img = Image.open(file)
                total_blocks = w * h
                for i in range(total_blocks):
                    update_progress(i+1, total_blocks, "处理区块:")
                    # 模拟处理延迟
                    time.sleep(0.001)
                convert_image_to_json(file, out, w, h)
                status1.set("✅ 图像转换完成")
            elif ext in [".mp4", ".avi", ".mov", ".mkv"]:
                # 视频转换进度
                cap = cv2.VideoCapture(file)
                total_frames = min(int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), f)
                cap.release()

                for i in range(total_frames):
                    update_progress(i+1, total_frames, "处理帧:")
                    # 模拟处理延迟
                    time.sleep(0.001)

                convert_video_to_json(file, out, w, h, f)
                status1.set(f"🎞 视频转换完成，共提取 {f} 帧")
            else:
                status1.set("⚠️ 不支持的文件类型")
        except Exception as e:
            status1.set(f"❌ 出错: {e}")

    # 构建图像/视频转换的UI组件
    tk.Label(convert_tab, text="输入文件路径").pack(anchor="w", padx=10, pady=(10, 0))
    tk.Entry(convert_tab, textvariable=input_path, width=70).pack(padx=10)
    tk.Button(convert_tab, text="选择文件", command=browse_input).pack(pady=5)

    tk.Label(convert_tab, text="输出目录").pack(anchor="w", padx=10)
    tk.Entry(convert_tab, textvariable=output_path, width=70).pack(padx=10)
    tk.Button(convert_tab, text="选择目录", command=browse_output).pack(pady=5)

    # 参数设置框架
    param_frame = tk.Frame(convert_tab)
    tk.Label(param_frame, text="矩阵宽度").grid(row=0, column=0, padx=5)
    tk.Entry(param_frame, textvariable=width, width=5).grid(row=0, column=1)
    tk.Label(param_frame, text="高度").grid(row=0, column=2, padx=5)
    tk.Entry(param_frame, textvariable=height, width=5).grid(row=0, column=3)
    tk.Label(param_frame, text="视频帧数").grid(row=0, column=4, padx=5)
    tk.Entry(param_frame, textvariable=frame_count, width=5).grid(row=0, column=5)
    param_frame.pack(pady=10)

    # 转换按钮和状态提示
    tk.Button(convert_tab, text="开始转换", command=do_convert, bg="#007acc", fg="white", width=20).pack(pady=5)
    tk.Label(convert_tab, textvariable=status1, fg="green").pack()

    # 进度条提示信息
    progress_frame = tk.Frame(convert_tab)
    progress_frame.pack(fill="x", padx=10, pady=5)

    tk.Label(progress_frame, textvariable=progress_label).pack(side="left")
    ttk.Progressbar(progress_frame, variable=progress_var, maximum=100).pack(side="left", expand=True, fill="x", padx=5)

    progress_hint = tk.Label(root, text="⚠ 当前进度条显示可能不同步，请以终端输出为准。", fg="red")
    progress_hint.pack()

    progress_hint = tk.Label(root, text="注意：限制图像分辨率最大为 256×128，建议不要超过该尺寸。", fg="red")
    progress_hint.pack()

    progress_hint = tk.Label(root, text="注意：限制帧数最大为 30 帧，建议不要超过该帧数。", fg="red")
    progress_hint.pack()

    progress_hint = tk.Label(root, text="注意：你可以将要处理的视频提前剪辑分段进行转换！。", fg="red")
    progress_hint.pack()

    # =================== Tab2：播放模拟器 =====================
    play_tab = ttk.Frame(tab_control)
    tab_control.add(play_tab, text="帧播放模拟器")

    # 初始化模拟器参数变量
    # 帧JSON文件路径
    json_path = tk.StringVar()
    # 矩阵宽度（自动读取）
    width2 = tk.IntVar()
    # 矩阵高度（自动读取）
    height2 = tk.IntVar()
    # 模拟器状态提示
    status2 = tk.StringVar()

    def browse_json():
        """
        打开文件选择对话框，让用户选择任一帧JSON文件，并自动读取矩阵尺寸
        :return: 无返回值
        """
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if path:
            json_path.set(path)
            try:
                # 以UTF-8编码打开JSON文件，支持含中文的内容
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                width2.set(data["width"])
                height2.set(data["height"])
                status2.set("已自动读取帧尺寸")
            except Exception as e:
                # 新增打印错误，方便调试
                print(f"解析JSON错误：{e}")
                status2.set("❌ 无法解析JSON文件")

    def start_sim():
        """
        启动WS2812点阵帧播放模拟器，在新线程中运行，避免阻塞UI
        先终止旧的模拟器实例，再加载新的帧数据并启动
        :return: 无返回值
        """
        global simulator, sim_thread
        file = json_path.get()
        if not file:
            status2.set("❗请先选择 JSON 帧文件")
            return

        # 终止旧实例
        if simulator:
            # 发送停止信号
            simulator.stop_event.set()
            if sim_thread:
                sim_thread.join(timeout=0.5)
            pygame.quit()

        # 智能匹配帧文件（支持帧序列的通配符匹配）
        base_prefix = re.sub(r'_frame_\d+\.json$', '_frame_*.json', file)
        if not glob.glob(base_prefix):
            base_prefix = file.replace(".json", "_*.json")

        # 读取矩阵尺寸，失败则提示
        try:
            # 新增 encoding="utf-8"
            with open(file, encoding="utf-8") as f:
                data = json.load(f)
            width2.set(data["width"])
            height2.set(data["height"])
        except Exception as e:
            print(f"读取帧尺寸错误：{e}")
            status2.set("❌ 无法读取帧尺寸")
            return

        # 定义模拟器运行函数，用于线程执行
        def run_sim():
            global simulator
            simulator = WS2812Simulator(width2.get(), height2.get(), 800)
            simulator.load_frames(base_prefix)
            simulator.run()

        # 启动新线程运行模拟器（守护线程，随主程序退出）
        sim_thread = threading.Thread(target=run_sim, daemon=True)
        sim_thread.start()
        status2.set("▶️ 播放中 (空格键暂停/播放)")

    def stop_sim():
        """
        暂停WS2812模拟器的帧播放，仅停止自动播放，不关闭模拟器
        :return: 无返回值
        """
        global simulator
        if simulator:
            simulator.playing = False
            status2.set("⏸ 播放已停止")

    def next_frame():
        """
        切换到模拟器的下一帧，手动控制帧播放
        :return: 无返回值
        """
        global simulator
        if simulator:
            simulator.current_frame = min(simulator.current_frame + 1, len(simulator.frames) - 1)
            status2.set(f"下一帧: {simulator.current_frame}")

    def prev_frame():
        """
        切换到模拟器的上一帧，手动控制帧播放
        :return: 无返回值
        """
        global simulator
        if simulator:
            simulator.current_frame = max(simulator.current_frame - 1, 0)
            status2.set(f"上一帧: {simulator.current_frame}")

    # === Tab3: 像素矩阵编辑器 ===
    editor_tab = ttk.Frame(tab_control)
    tab_control.add(editor_tab, text="像素矩阵编辑器")

    # 添加说明面板
    help_frame = tk.Frame(editor_tab, bg="#f0f0f0", padx=20, pady=20)
    help_frame.pack(expand=True, fill="both")

    # 操作说明文本
    instructions = """
    📖 使用说明：

    1. 点击上方标签页会自动弹出独立编辑窗口
    2. 在独立窗口中可进行以下操作：
       - 点击像素格绘制颜色
       - 拖拽鼠标连续绘制
       - 使用工具栏按钮：新建/导入/保存模板
    3. 文件规范：
       - 支持最大256x128像素矩阵
       - 使用RGB565格式存储
    """

    tk.Label(help_frame,
             text=instructions,
             font=("微软雅黑", 10),
             bg="#f0f0f0",
             justify="left").pack(anchor="w")

    # 添加分割线
    ttk.Separator(help_frame, orient="horizontal").pack(fill="x", pady=10)

    # 添加快速操作按钮
    btn_frame = tk.Frame(help_frame, bg="#f0f0f0")
    btn_frame.pack()

    def create_editor_window(event):
        """
        处理标签页切换事件，当切换到像素矩阵编辑器标签时，创建独立的编辑窗口
        若窗口已存在则提升到顶层，切换其他标签时关闭编辑窗口
        :param event: Tkinter的事件对象（包含标签页切换信息）
        :return: 无返回值
        """
        global editor_window

        # 获取当前选中的标签索引
        try:
            selected_index = tab_control.index(tab_control.select())
        except:
            # 防止初始化时未选择标签
            return

        # 仅当切换到第三个标签（索引2）时触发
        if selected_index == 2:
            # 检查窗口是否已存在
            if editor_window and editor_window.winfo_exists():
                # 将已有窗口提升到顶层
                editor_window.lift()
                return

            # 创建独立窗口
            editor_window = tk.Toplevel(root)
            editor_window.title("WS2812 像素矩阵编辑器")
            # 初始位置偏移
            editor_window.geometry("800x600+100+100")

            # 创建窗口后添加焦点锁定
            editor_window.grab_set()
            editor_window.focus_force()

            # === 窗口行为控制 ===
            def enforce_focus():
                """
                维持编辑窗口的焦点，每0.5秒检测一次，确保窗口在顶层
                :return: 无返回值
                """
                if editor_window.winfo_exists():
                    editor_window.lift()
                    # 每0.5秒检测一次
                    editor_window.after(500, enforce_focus)

            # === 窗口初始化 ===
            try:
                # 创建容器框架
                editor_container = tk.Frame(editor_window)
                editor_container.pack(expand=True, fill="both", padx=10, pady=10)

                # 初始化编辑器
                editor = PixelEditor(editor_container)

                # 绑定父子窗口关系
                editor.root.master = editor_window

                # 窗口关闭协议
                def on_close():
                    """
                    处理编辑窗口的关闭事件，释放焦点并恢复主窗口状态
                    :return: 无返回值
                    """
                    global editor_window
                    # 释放焦点锁定
                    editor_window.grab_release()
                    # 恢复主窗口状态
                    root.attributes('-disabled', 0)
                    root.focus_force()
                    # 销毁子窗口
                    editor_window.destroy()
                    editor_window = None
                    # 切换回第一个标签
                    tab_control.select(0)

                editor_window.protocol("WM_DELETE_WINDOW", on_close)

                # 临时禁用主窗口
                root.attributes('-disabled', 1)

                # 启动焦点维持检测
                enforce_focus()

                # 设置窗口图标（可选）
                try:
                    icon_path = resource_path(os.path.join("assets", "icon.ico"))
                    editor_window.iconbitmap(icon_path)
                except Exception as e:
                    print(f"图标加载失败: {e}")

                # 绑定ESC键关闭窗口
                editor_window.bind("<Escape>", lambda e: on_close())

            except Exception as e:
                messagebox.showerror("窗口初始化错误", f"无法创建编辑器：{str(e)}")
                editor_window.destroy()
                editor_window = None
                root.attributes('-disabled', 0)

        else:
            # 切换到其他标签时关闭编辑器窗口
            if editor_window and editor_window.winfo_exists():
                editor_window.destroy()
                editor_window = None
                root.attributes('-disabled', 0)

    # 绑定标签切换事件
    tab_control.bind("<<NotebookTabChanged>>", create_editor_window)

    def on_closing():
        global simulator, sim_thread
        if simulator:
            # 发送停止信号
            simulator.stop_event.set()
        if sim_thread and sim_thread.is_alive():
            sim_thread.join(timeout=0.5)
        pygame.quit()
        root.destroy()

    # 播放器 UI
    tk.Label(play_tab, text="选择任一帧JSON文件").pack(anchor="w", padx=10, pady=(10, 0))
    tk.Entry(play_tab, textvariable=json_path, width=70).pack(padx=10)
    tk.Button(play_tab, text="选择帧文件", command=browse_json).pack(pady=5)

    param_frame2 = tk.Frame(play_tab)
    tk.Label(param_frame2, text="矩阵宽").grid(row=0, column=0, padx=5)
    tk.Entry(param_frame2, textvariable=width2, width=5).grid(row=0, column=1)
    tk.Label(param_frame2, text="高").grid(row=0, column=2, padx=5)
    tk.Entry(param_frame2, textvariable=height2, width=5).grid(row=0, column=3)
    param_frame2.pack(pady=10)

    ctrl_frame = tk.Frame(play_tab)
    tk.Button(ctrl_frame, text="▶️ 播放", command=start_sim).grid(row=0, column=0, padx=5)
    tk.Button(ctrl_frame, text="⏸ 停止", command=stop_sim).grid(row=0, column=1, padx=5)
    tk.Button(ctrl_frame, text="⏮ 上一帧", command=prev_frame).grid(row=0, column=2, padx=5)
    tk.Button(ctrl_frame, text="⏭ 下一帧", command=next_frame).grid(row=0, column=3, padx=5)
    ctrl_frame.pack(pady=10)

    # =================== Tab4：单字符转点阵 =====================
    char_tab = ttk.Frame(tab_control)
    tab_control.add(char_tab, text="单字符转点阵")

    # 初始化字符转换参数变量
    # 输入的单个字符
    input_char = tk.StringVar()
    # 点阵宽度
    char_width = tk.IntVar(value=24)
    # 点阵高度
    char_height = tk.IntVar(value=16)
    # 输出JSON路径
    char_output_path = tk.StringVar()
    char_status = tk.StringVar(value="准备就绪")
    # 颜色变量（十六进制格式，默认白色字、黑色背景）
    text_color = tk.StringVar(value="#ffffff")
    bg_color = tk.StringVar(value="#000000")
    # 提前定义颜色预览标签
    text_color_preview = None
    bg_color_preview = None

    def hex_to_rgb(hex_str):
        """
        将十六进制颜色字符串转换为RGB元组（适配colorchooser和char_to_matrix的参数要求）
        :param hex_str: 十六进制颜色字符串（如#ffffff或ffffff）
        :return: RGB颜色元组（r, g, b），每个分量为0-255的整数
        """
        hex_str = hex_str.lstrip('#')
        return tuple(int(hex_str[i:i + 2], 16) for i in (0, 2, 4))

    def choose_text_color():
        """
        打开颜色选择器，让用户选择文字颜色，并更新text_color变量和预览标签
        :return: 无返回值
        """
        clr = colorchooser.askcolor(initialcolor=text_color.get(), parent=char_tab)
        if clr[0]:
            # 保存十六进制颜色
            text_color.set(clr[1])
            # 更新预览标签背景
            text_color_preview.config(bg=clr[1])

    def choose_bg_color():
        """
        打开颜色选择器，让用户选择背景颜色，并更新bg_color变量和预览标签
        :return: 无返回值
        """
        clr = colorchooser.askcolor(initialcolor=bg_color.get(), parent=char_tab)
        if clr[0]:
            bg_color.set(clr[1])  # 保存十六进制颜色
            # 更新预览标签背景
            bg_color_preview.config(bg=clr[1])

    def browse_char_output():
        """
        打开保存文件对话框，让用户选择字符点阵JSON的保存路径，并更新char_output_path变量
        :return: 无返回值
        """
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json")],
            title="保存字符点阵JSON"
        )
        if path:
            char_output_path.set(path)

    def do_char_convert():
        """
        执行单个字符到WS2812点阵JSON的转换操作，支持自定义文字和背景颜色
        :return: 无返回值
        """
        try:
            char = input_char.get().strip()
            w = char_width.get()
            h = char_height.get()
            out_path = char_output_path.get()

            if not char or not out_path:
                char_status.set("❌ 请输入字符并选择输出路径")
                return

            # 转换颜色（十六进制→RGB元组）
            text_rgb = hex_to_rgb(text_color.get())
            bg_rgb = hex_to_rgb(bg_color.get())

            # 调用核心转换逻辑（传入颜色参数）
            from ws_converter.char_converter import char_to_matrix
            char_to_matrix(
                char, w, h,
                output_path=out_path,
                # 自定义文字色
                text_color=text_rgb,
                # 自定义背景色
                bg_color=bg_rgb
            )

            char_status.set(f"✅ 字符「{char}」转换完成！已保存至{out_path}")
        except ValueError as e:
            char_status.set(f"❌ 错误：{e}")
        except FileNotFoundError as e:
            char_status.set(f"❌ 字体文件错误：{e}")
        except Exception as e:
            char_status.set(f"❌ 未知错误：{str(e)}")

    # 1. 字符输入区域
    tk.Label(char_tab, text="输入单个字符（中文/英文/数字）：", font=("微软雅黑", 12)).pack(anchor="w", padx=10,
                                                                                         pady=(10, 0))
    char_entry = tk.Entry(char_tab, textvariable=input_char, width=20, font=("微软雅黑", 14))
    char_entry.pack(padx=10, pady=5)
    tk.Label(char_tab, text="⚠ 仅支持单个字符，超出会自动截断", fg="red").pack(anchor="w", padx=10)

    # 2. 颜色选择区域（★★★ 放在字符输入后、尺寸设置前 ★★★）
    color_frame = tk.Frame(char_tab)
    color_frame.pack(pady=10, padx=10, anchor="w")
    # 文字色选择
    tk.Label(color_frame, text="文字颜色：").grid(row=0, column=0, padx=5)
    # 初始化预览标签
    text_color_preview = tk.Label(color_frame, bg=text_color.get(), width=5)
    text_color_preview.grid(row=0, column=1)
    tk.Button(color_frame, text="选择", command=choose_text_color).grid(row=0, column=2, padx=5)
    # 背景色选择
    tk.Label(color_frame, text="背景颜色：").grid(row=0, column=3, padx=5)
    # 初始化预览标签
    bg_color_preview = tk.Label(color_frame, bg=bg_color.get(), width=5)
    bg_color_preview.grid(row=0, column=4)
    tk.Button(color_frame, text="选择", command=choose_bg_color).grid(row=0, column=5, padx=5)

    # 3. 尺寸设置区域（原有代码）
    char_param_frame = tk.Frame(char_tab)
    char_param_frame.pack(pady=10, padx=10, anchor="w")
    tk.Label(char_param_frame, text="点阵宽度：").grid(row=0, column=0, padx=5)
    tk.Entry(char_param_frame, textvariable=char_width, width=5).grid(row=0, column=1)
    tk.Label(char_param_frame, text="点阵高度：").grid(row=0, column=2, padx=5)
    tk.Entry(char_param_frame, textvariable=char_height, width=5).grid(row=0, column=3)

    # 4. 输出路径区域
    tk.Label(char_tab, text="输出JSON路径：", font=("微软雅黑", 12)).pack(anchor="w", padx=10)
    tk.Entry(char_tab, textvariable=char_output_path, width=70).pack(padx=10)
    tk.Button(char_tab, text="选择保存路径", command=browse_char_output).pack(pady=5)

    # 5. 转换按钮 + 状态提示
    tk.Button(char_tab, text="生成点阵JSON", command=do_char_convert, bg="#007acc", fg="white", width=20).pack(pady=10)
    tk.Label(char_tab, textvariable=char_status, fg="green", font=("微软雅黑", 11)).pack(pady=5)

    # 6. 提示信息
    tk.Label(char_tab, text="⚠ 建议尺寸：宽度≤256，高度≤128 | 仅支持单个字符", fg="red").pack(anchor="w", padx=10)

    tk.Label(play_tab, textvariable=status2, fg="blue").pack()

    tab_control.pack(expand=1, fill="both")

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================

if __name__ == "__main__":
    gui_main()