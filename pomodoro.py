#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
番茄钟 - 桌面番茄工作法计时器
Pomodoro Timer Desktop App
"""

import tkinter as tk
from tkinter import messagebox
import time
import threading
import math

# 预设时长（秒）
WORK_TIME = 25 * 60       # 25分钟专注
SHORT_BREAK = 5 * 60      # 5分钟短休息
LONG_BREAK = 15 * 60      # 15分钟长休息
POMODOROS_BEFORE_LONG = 4  # 完成几个番茄后进入长休息


class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("🍅 番茄钟")
        self.root.geometry("400x520")
        self.root.resizable(False, False)
        self.root.configure(bg="#fff0f5")

        # 状态
        self.running = False
        self.paused = False
        self.seconds_left = WORK_TIME
        self.current_mode = "work"  # work / short_break / long_break
        self.completed_pomodoros = 0
        self.timer_thread = None

        # 样式颜色 - 浅粉色主题
        self.colors = {
            "work": "#e91e63",         # 粉红 - 工作
            "short_break": "#f48fb1",  # 浅粉 - 短休息
            "long_break": "#ce93d8",   # 淡紫粉 - 长休息
            "bg": "#fff0f5",           # 浅粉色背景
            "text": "#5d1037",         # 深玫红文字
            "button_bg": "#fce4ec",    # 按钮背景
            "button_fg": "#5d1037",    # 按钮文字
        }

        self.build_ui()
        self.update_display()

        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def build_ui(self):
        """构建界面"""
        # --- 标题 ---
        title_frame = tk.Frame(self.root, bg=self.colors["bg"])
        title_frame.pack(pady=(30, 10))

        self.title_label = tk.Label(
            title_frame,
            text="🍅 番茄钟",
            font=("Microsoft YaHei", 22, "bold"),
            fg=self.colors["text"],
            bg=self.colors["bg"],
        )
        self.title_label.pack()

        # --- 模式标签 ---
        self.mode_label = tk.Label(
            self.root,
            text="专注工作",
            font=("Microsoft YaHei", 12),
            fg=self.colors["work"],
            bg=self.colors["bg"],
        )
        self.mode_label.pack(pady=(0, 10))

        # --- 画布圆环进度 ---
        self.canvas_size = 240
        self.canvas = tk.Canvas(
            self.root,
            width=self.canvas_size,
            height=self.canvas_size,
            bg=self.colors["bg"],
            highlightthickness=0,
        )
        self.canvas.pack(pady=(0, 10))

        # --- 时间显示（在圆环中央） ---
        self.time_label = tk.Label(
            self.root,
            text="25:00",
            font=("Consolas", 42, "bold"),
            fg=self.colors["text"],
            bg=self.colors["bg"],
        )
        # 用 place 把时间标签放到 canvas 中央
        self.time_label.place(
            x=200, y=238, anchor="center", width=160, height=60
        )

        # --- 番茄计数 ---
        count_frame = tk.Frame(self.root, bg=self.colors["bg"])
        count_frame.pack(pady=(0, 15))

        self.count_label = tk.Label(
            count_frame,
            text="🍅 × 0",
            font=("Microsoft YaHei", 12),
            fg="#e91e63",
            bg=self.colors["bg"],
        )
        self.count_label.pack()

        # --- 按钮区 ---
        btn_frame = tk.Frame(self.root, bg=self.colors["bg"])
        btn_frame.pack(pady=(0, 15))

        button_style = {
            "font": ("Microsoft YaHei", 11),
            "width": 8,
            "height": 1,
            "borderwidth": 1,
            "relief": "solid",
            "cursor": "hand2",
        }

        self.start_btn = tk.Button(
            btn_frame,
            text="▶ 开始",
            command=self.start_timer,
            bg="#ec407a",
            fg="white",
            activebackground="#d81b60",
            activeforeground="white",
            **button_style,
        )
        self.start_btn.pack(side="left", padx=5)

        self.pause_btn = tk.Button(
            btn_frame,
            text="⏸ 暂停",
            command=self.pause_timer,
            bg="#ff8a65",
            fg="white",
            activebackground="#f4511e",
            activeforeground="white",
            state="disabled",
            **button_style,
        )
        self.pause_btn.pack(side="left", padx=5)

        self.reset_btn = tk.Button(
            btn_frame,
            text="↺ 重置",
            command=self.reset_timer,
            bg="#bdbdbd",
            fg="white",
            activebackground="#9e9e9e",
            activeforeground="white",
            **button_style,
        )
        self.reset_btn.pack(side="left", padx=5)

        # --- 模式切换按钮 ---
        mode_btn_frame = tk.Frame(self.root, bg=self.colors["bg"])
        mode_btn_frame.pack(pady=(5, 10))

        small_btn_style = {
            "font": ("Microsoft YaHei", 9),
            "width": 10,
            "height": 1,
            "borderwidth": 1,
            "relief": "solid",
            "cursor": "hand2",
        }

        self.work_btn = tk.Button(
            mode_btn_frame,
            text="🍅 工作 25分",
            command=lambda: self.switch_mode("work"),
            bg="#e91e63",
            fg="white",
            activebackground="#c2185b",
            activeforeground="white",
            **small_btn_style,
        )
        self.work_btn.pack(side="left", padx=4)

        self.short_break_btn = tk.Button(
            mode_btn_frame,
            text="☕ 短休息 5分",
            command=lambda: self.switch_mode("short_break"),
            bg="#f48fb1",
            fg="white",
            activebackground="#f06292",
            activeforeground="white",
            **small_btn_style,
        )
        self.short_break_btn.pack(side="left", padx=4)

        self.long_break_btn = tk.Button(
            mode_btn_frame,
            text="😴 长休息 15分",
            command=lambda: self.switch_mode("long_break"),
            bg="#ce93d8",
            fg="white",
            activebackground="#ba68c8",
            activeforeground="white",
            **small_btn_style,
        )
        self.long_break_btn.pack(side="left", padx=4)

        # --- 置顶复选框 ---
        self.always_on_top_var = tk.BooleanVar(value=False)
        self.top_check = tk.Checkbutton(
            self.root,
            text="窗口置顶",
            variable=self.always_on_top_var,
            command=self.toggle_always_on_top,
            font=("Microsoft YaHei", 9),
            fg=self.colors["text"],
            bg=self.colors["bg"],
            selectcolor=self.colors["bg"],
            activebackground=self.colors["bg"],
        )
        self.top_check.pack(pady=(0, 15))

    def draw_progress_ring(self, fraction):
        """绘制圆环进度条"""
        self.canvas.delete("all")

        cx = self.canvas_size // 2
        cy = self.canvas_size // 2
        radius = 90
        ring_width = 10

        # 背景圆环
        self.canvas.create_oval(
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
            outline="#e0e0e0",
            width=ring_width,
        )

        if fraction > 0:
            # 进度弧线
            angle = fraction * 360
            # tkinter 的 arc 从 3点钟方向开始，逆时针。我们让它从 12 点方向顺时画
            start_angle = 90  # 12点钟方向
            extent = -angle    # 顺时针

            color = self.colors.get(self.current_mode, "#e91e63")
            self.canvas.create_arc(
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
                start=start_angle,
                extent=extent,
                outline=color,
                width=ring_width,
                style="arc",
            )

    def update_display(self):
        """更新时间和进度显示"""
        mins = self.seconds_left // 60
        secs = self.seconds_left % 60
        self.time_label.config(text=f"{mins:02d}:{secs:02d}")

        total = self.get_total_seconds()
        fraction = (total - self.seconds_left) / total if total > 0 else 0
        self.draw_progress_ring(fraction)

        # 更新模式标签
        mode_texts = {
            "work": "专注工作",
            "short_break": "短休息",
            "long_break": "长休息",
        }
        self.mode_label.config(
            text=mode_texts.get(self.current_mode, ""),
            fg=self.colors.get(self.current_mode, "#e91e63"),
        )

    def get_total_seconds(self):
        """获取当前模式总秒数"""
        if self.current_mode == "work":
            return WORK_TIME
        elif self.current_mode == "short_break":
            return SHORT_BREAK
        else:
            return LONG_BREAK

    def start_timer(self):
        """开始计时"""
        if self.running and not self.paused:
            return  # 已经在运行

        if self.paused:
            # 从暂停恢复
            self.paused = False
            self.running = True
        else:
            # 重新开始
            self.running = True
            self.paused = False

        self.set_running_ui()
        self._run_timer()

    def _run_timer(self):
        """计时循环（在单独线程中执行）"""
        if self.timer_thread and self.timer_thread.is_alive():
            return

        def countdown():
            while self.running and self.seconds_left > 0:
                if not self.paused:
                    time.sleep(1)
                    self.seconds_left -= 1
                    self.root.after(0, self.update_display)
                else:
                    time.sleep(0.1)

            if self.seconds_left <= 0 and self.running:
                self.root.after(0, self.timer_finished)

        self.timer_thread = threading.Thread(target=countdown, daemon=True)
        self.timer_thread.start()

    def pause_timer(self):
        """暂停计时"""
        self.paused = True
        self.running = False
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled")

    def reset_timer(self):
        """重置计时器"""
        self.running = False
        self.paused = False
        self.seconds_left = self.get_total_seconds()
        self.update_display()
        self.set_stopped_ui()

    def switch_mode(self, mode):
        """切换模式"""
        if self.running:
            # 确认是否要切换
            if not messagebox.askyesno("切换模式", "计时器正在运行，确定要切换模式吗？"):
                return

        self.running = False
        self.paused = False
        self.current_mode = mode
        self.seconds_left = self.get_total_seconds()
        self.update_display()
        self.set_stopped_ui()

    def timer_finished(self):
        """计时完成"""
        self.running = False
        self.paused = False
        self.seconds_left = 0
        self.update_display()
        self.set_stopped_ui()

        if self.current_mode == "work":
            self.completed_pomodoros += 1
            self.count_label.config(text=f"🍅 × {self.completed_pomodoros}")

            # 弹出提示
            self.root.lift()
            self.root.focus_force()

            # 播放系统提示音
            self._play_notification()

            if self.completed_pomodoros % POMODOROS_BEFORE_LONG == 0:
                msg = f"✅ 完成 {self.completed_pomodoros} 个番茄！\n\n该进入长休息了~"
                if messagebox.askyesno("太棒了！", msg + "\n\n要切换到长休息吗？"):
                    self.switch_mode("long_break")
            else:
                msg = f"✅ 完成 {self.completed_pomodoros} 个番茄！\n\n休息一下吧~"
                if messagebox.askyesno("番茄完成！", msg + "\n\n要切换到短休息吗？"):
                    self.switch_mode("short_break")
        else:
            self._play_notification()
            msg = "休息时间结束！\n\n准备好开始新的番茄了吗？"
            if messagebox.askyesno("休息结束", msg + "\n\n要切换到工作模式吗？"):
                self.switch_mode("work")

    def _play_notification(self):
        """播放系统提示音"""
        try:
            # Windows 系统提示音
            import winsound
            winsound.MessageBeep(winsound.MB_ICONINFORMATION)
            # 再播放一段简单的提示音
            winsound.Beep(1000, 200)
            self.root.after(100, lambda: winsound.Beep(1200, 200))
            self.root.after(200, lambda: winsound.Beep(1400, 300))
        except ImportError:
            # 非 Windows 系统，用 \a 响铃
            print("\a")

    def set_running_ui(self):
        """设置运行中的 UI 状态"""
        self.start_btn.config(state="disabled", bg="#bdc3c7")
        self.pause_btn.config(state="normal")
        self.work_btn.config(state="disabled")
        self.short_break_btn.config(state="disabled")
        self.long_break_btn.config(state="disabled")

    def set_stopped_ui(self):
        """设置停止时的 UI 状态"""
        self.start_btn.config(state="normal", bg="#ec407a")
        self.pause_btn.config(state="disabled")
        self.work_btn.config(state="normal")
        self.short_break_btn.config(state="normal")
        self.long_break_btn.config(state="normal")

    def toggle_always_on_top(self):
        """切换窗口置顶"""
        self.root.attributes("-topmost", self.always_on_top_var.get())

    def on_closing(self):
        """关闭窗口"""
        self.running = False
        self.root.destroy()


def main():
    root = tk.Tk()
    app = PomodoroTimer(root)

    # 窗口居中
    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"+{x}+{y}")

    root.mainloop()


if __name__ == "__main__":
    main()
