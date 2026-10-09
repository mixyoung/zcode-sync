#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI 主题引擎 (Theme Engine) - 现代工业深色版本
提供符合 ZCode 桌面端工业级规范的设计令牌 (Design Tokens)、
按钮工厂 (Button Factory)、微边框输入组件与深色样式注册。
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Any

class ThemeEngine:
    """定义工业级深色设计令牌并为组件提供统一现代化渲染支持"""

    # 调色盘 Design Tokens (Zinc-based Modern Dark Palette)
    BG_CANVAS = "#0f0f11"      # 底层画布 (Deep Charcoal)
    BG_SURFACE = "#18181b"     # 卡片容器 (Zinc-900)
    BG_SURFACE_ALT = "#202024" # 次级悬浮容器 / 表头 (Zinc-800 Dark)
    BG_INPUT = "#141417"       # 输入框底色 (Deep Input Surface)
    
    BORDER_SUBTLE = "#2e2e33"  # 1px 微边框 (Subtle Border)
    BORDER_HOVER = "#3f3f46"   # 悬停微边框
    BORDER_FOCUS = "#3b82f6"   # 聚焦高亮微边框 (Blue-500 Focus Ring)

    TEXT_PRIMARY = "#f4f4f5"    # 主文本 (Zinc-100)
    TEXT_SECONDARY = "#a1a1aa"  # 次级文本 (Zinc-400)
    TEXT_MUTED = "#71717a"      # 弱化文本 (Zinc-500)
    TEXT_ACCENT = "#60a5fa"     # 强调亮蓝文本

    # 按钮色彩与交互规范
    BTN_PRIMARY_BG = "#2563eb"       # Blue-600 (主操作实心蓝)
    BTN_PRIMARY_HOVER = "#1d4ed8"    # Blue-700
    BTN_PRIMARY_FG = "#ffffff"

    BTN_SECONDARY_BG = "#222226"     # 深色卡片次级操作
    BTN_SECONDARY_HOVER = "#2a2a30"
    BTN_SECONDARY_BORDER = "#3b3b44"
    BTN_SECONDARY_HOVER_BORDER = "#4f4f5a"
    BTN_SECONDARY_FG = "#f4f4f5"

    BTN_DANGER_BG = "#241416"        # 暗红微警示操作
    BTN_DANGER_HOVER = "#35191c"
    BTN_DANGER_BORDER = "#7f1d1d"
    BTN_DANGER_HOVER_BORDER = "#991b1b"
    BTN_DANGER_FG = "#f87171"

    BTN_OUTLINE_BG = "#18181b"       # 极简轮廓操作
    BTN_OUTLINE_HOVER = "#242428"
    BTN_OUTLINE_BORDER = "#2e2e33"
    BTN_OUTLINE_HOVER_BORDER = "#3f3f46"
    BTN_OUTLINE_FG = "#d4d4d8"

    # 表格行与高亮色彩
    ROW_BG_DARK = "#141417"
    ROW_BG_ALT = "#1a1a1e"
    ROW_SELECTED = "#1e3a5f"
    ROW_SELECTED_FG = "#ffffff"

    # 徽章色彩
    BADGE_CUSTOM_BG = "#064e3b"      # 深翠绿背景
    BADGE_CUSTOM_FG = "#6ee7b7"      # 浅青绿文字
    BADGE_OFFICIAL_BG = "#27272a"    # 稳重暗灰背景
    BADGE_OFFICIAL_FG = "#94a3b8"    # 浅银灰文字

    # 向后兼容常量
    ACCENT_BLUE = BTN_PRIMARY_BG
    ACCENT_BLUE_HOVER = BTN_PRIMARY_HOVER
    ACCENT_CYAN = "#0284c7"
    ACCENT_CYAN_HOVER = "#0369a1"
    ACCENT_EMERALD = "#059669"
    ACCENT_EMERALD_HOVER = "#047857"
    ACCENT_GREEN = "#10b981"
    ACCENT_GREEN_HOVER = "#059669"

    @classmethod
    def apply(cls, root: tk.Tk) -> ttk.Style:
        """为根窗口和 ttk 组件注入现代化深色主题配置"""
        root.configure(bg=cls.BG_CANVAS)
        style = ttk.Style()
        style.theme_use("clam")

        # 基础字体体系
        base_font = ("Segoe UI", 9)
        title_font = ("Segoe UI", 12, "bold")
        sub_font = ("Segoe UI", 8)
        mono_font = ("Consolas", 8)

        style.configure(".", background=cls.BG_CANVAS, foreground=cls.TEXT_PRIMARY, font=base_font)
        style.configure("TFrame", background=cls.BG_CANVAS)
        style.configure("Card.TFrame", background=cls.BG_SURFACE, relief="flat")
        style.configure("CardAlt.TFrame", background=cls.BG_SURFACE_ALT, relief="flat")
        style.configure("TLabel", background=cls.BG_CANVAS, foreground=cls.TEXT_PRIMARY)
        style.configure("Card.TLabel", background=cls.BG_SURFACE, foreground=cls.TEXT_PRIMARY)
        style.configure("CardMono.TLabel", background=cls.BG_SURFACE, foreground=cls.TEXT_SECONDARY, font=mono_font)
        style.configure("Sub.TLabel", background=cls.BG_CANVAS, foreground=cls.TEXT_SECONDARY, font=sub_font)
        style.configure("Title.TLabel", background=cls.BG_CANVAS, foreground="#ffffff", font=title_font)

        # Treeview 表格组件
        style.configure("Treeview",
            background=cls.ROW_BG_DARK,
            foreground=cls.TEXT_PRIMARY,
            fieldbackground=cls.ROW_BG_DARK,
            rowheight=28,
            borderwidth=0,
            font=base_font
        )
        style.map("Treeview",
            background=[("selected", cls.ROW_SELECTED)],
            foreground=[("selected", cls.ROW_SELECTED_FG)]
        )
        style.configure("Treeview.Heading",
            background=cls.BG_SURFACE_ALT,
            foreground="#cbd5e1",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padding=(6, 6)
        )
        style.map("Treeview.Heading",
            background=[("active", cls.BORDER_SUBTLE)]
        )

        # 滚动条组件
        style.configure("Vertical.TScrollbar",
            background=cls.BG_SURFACE_ALT,
            troughcolor=cls.BG_CANVAS,
            bordercolor=cls.BG_CANVAS,
            arrowcolor=cls.TEXT_SECONDARY,
            relief="flat",
            width=10
        )

        # 下拉选择框组件 (Combobox)
        style.configure("TCombobox",
            background=cls.BG_SURFACE_ALT,
            foreground=cls.TEXT_PRIMARY,
            fieldbackground=cls.BG_INPUT,
            arrowcolor=cls.TEXT_SECONDARY,
            bordercolor=cls.BORDER_SUBTLE,
            lightcolor=cls.BORDER_SUBTLE,
            darkcolor=cls.BORDER_SUBTLE,
            relief="flat",
            padding=3
        )
        style.map("TCombobox",
            fieldbackground=[("readonly", cls.BG_INPUT)],
            foreground=[("readonly", cls.TEXT_PRIMARY)],
            selectbackground=[("readonly", cls.BG_INPUT)],
            selectforeground=[("readonly", cls.TEXT_PRIMARY)],
            background=[("active", cls.BORDER_HOVER)]
        )

        # 选项卡 (Notebook)
        style.configure("TNotebook", background=cls.BG_CANVAS, borderwidth=0)
        style.configure("TNotebook.Tab",
            background=cls.BG_SURFACE,
            foreground=cls.TEXT_SECONDARY,
            padding=(14, 6),
            font=("Segoe UI", 9),
            borderwidth=0
        )
        style.map("TNotebook.Tab",
            background=[("selected", cls.BG_SURFACE_ALT)],
            foreground=[("selected", "#ffffff")]
        )

        return style

    # --- 按钮工厂方法 (Button Factories) ---

    @classmethod
    def create_primary_button(
        cls, parent: Any, text: str, command: Optional[Callable] = None,
        font: Optional[tuple] = None, pady: int = 7, padx: int = 12, **kwargs
    ) -> tk.Button:
        """主操作按钮：实心品牌蓝高亮，唯一视觉强锚点"""
        btn = tk.Button(
            parent, text=text, command=command,
            bg=cls.BTN_PRIMARY_BG, fg=cls.BTN_PRIMARY_FG,
            activebackground=cls.BTN_PRIMARY_HOVER, activeforeground=cls.BTN_PRIMARY_FG,
            relief="flat", bd=0, padx=padx, pady=pady,
            font=font or ("Segoe UI", 9, "bold"), cursor="hand2", **kwargs
        )
        btn.bind("<Enter>", lambda e: btn.configure(bg=cls.BTN_PRIMARY_HOVER))
        btn.bind("<Leave>", lambda e: btn.configure(bg=cls.BTN_PRIMARY_BG))
        return btn

    @classmethod
    def create_secondary_button(
        cls, parent: Any, text: str, command: Optional[Callable] = None,
        font: Optional[tuple] = None, pady: int = 7, padx: int = 12, **kwargs
    ) -> tk.Button:
        """次级协同按钮：深色卡片质感 + 1px 精细微边框 + 平滑悬停"""
        btn = tk.Button(
            parent, text=text, command=command,
            bg=cls.BTN_SECONDARY_BG, fg=cls.BTN_SECONDARY_FG,
            activebackground=cls.BTN_SECONDARY_HOVER, activeforeground=cls.BTN_SECONDARY_FG,
            relief="flat", bd=0,
            highlightthickness=1,
            highlightbackground=cls.BTN_SECONDARY_BORDER,
            highlightcolor=cls.BTN_SECONDARY_BORDER,
            padx=padx, pady=pady,
            font=font or ("Segoe UI", 9), cursor="hand2", **kwargs
        )
        def on_enter(e):
            btn.configure(bg=cls.BTN_SECONDARY_HOVER, highlightbackground=cls.BTN_SECONDARY_HOVER_BORDER)
        def on_leave(e):
            btn.configure(bg=cls.BTN_SECONDARY_BG, highlightbackground=cls.BTN_SECONDARY_BORDER)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    @classmethod
    def create_danger_button(
        cls, parent: Any, text: str, command: Optional[Callable] = None,
        font: Optional[tuple] = None, pady: int = 5, padx: int = 10, **kwargs
    ) -> tk.Button:
        """危险操作按钮：暗红深邃背景 + 暗红微边框 + 克制警示"""
        btn = tk.Button(
            parent, text=text, command=command,
            bg=cls.BTN_DANGER_BG, fg=cls.BTN_DANGER_FG,
            activebackground=cls.BTN_DANGER_HOVER, activeforeground=cls.BTN_DANGER_FG,
            relief="flat", bd=0,
            highlightthickness=1,
            highlightbackground=cls.BTN_DANGER_BORDER,
            highlightcolor=cls.BTN_DANGER_BORDER,
            padx=padx, pady=pady,
            font=font or ("Segoe UI", 9), cursor="hand2", **kwargs
        )
        def on_enter(e):
            btn.configure(bg=cls.BTN_DANGER_HOVER, highlightbackground=cls.BTN_DANGER_HOVER_BORDER)
        def on_leave(e):
            btn.configure(bg=cls.BTN_DANGER_BG, highlightbackground=cls.BTN_DANGER_BORDER)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    @classmethod
    def create_outline_button(
        cls, parent: Any, text: str, command: Optional[Callable] = None,
        font: Optional[tuple] = None, pady: int = 3, padx: int = 8, **kwargs
    ) -> tk.Button:
        """轮廓/辅助按钮：低调暗灰边框 + 浅灰文字"""
        btn = tk.Button(
            parent, text=text, command=command,
            bg=cls.BTN_OUTLINE_BG, fg=cls.BTN_OUTLINE_FG,
            activebackground=cls.BTN_OUTLINE_HOVER, activeforeground="#ffffff",
            relief="flat", bd=0,
            highlightthickness=1,
            highlightbackground=cls.BTN_OUTLINE_BORDER,
            highlightcolor=cls.BTN_OUTLINE_BORDER,
            padx=padx, pady=pady,
            font=font or ("Segoe UI", 8), cursor="hand2", **kwargs
        )
        def on_enter(e):
            btn.configure(bg=cls.BTN_OUTLINE_HOVER, highlightbackground=cls.BTN_OUTLINE_HOVER_BORDER)
        def on_leave(e):
            btn.configure(bg=cls.BTN_OUTLINE_BG, highlightbackground=cls.BTN_OUTLINE_BORDER)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    # --- 现代输入框与卡片容器辅助类 ---

    @classmethod
    def create_bordered_entry(
        cls, parent: Any, textvariable: tk.StringVar, placeholder: str = "",
        width: int = 24, show_icon: bool = True
    ) -> tuple[tk.Frame, tk.Entry]:
        """创建带 1px 细微边框与聚焦发光动效的现代化输入框"""
        # 外层边框容器 (提供 1px 描边)
        border_frame = tk.Frame(parent, bg=cls.BORDER_SUBTLE, padx=1, pady=1)
        # 内层背景容器
        inner_frame = tk.Frame(border_frame, bg=cls.BG_INPUT)
        inner_frame.pack(fill=tk.BOTH, expand=True)

        if show_icon:
            icon_lbl = tk.Label(
                inner_frame, text="⌕", bg=cls.BG_INPUT, fg=cls.TEXT_MUTED,
                font=("Segoe UI", 9)
            )
            icon_lbl.pack(side=tk.LEFT, padx=(6, 2))

        entry = tk.Entry(
            inner_frame, textvariable=textvariable, bg=cls.BG_INPUT,
            fg=cls.TEXT_PRIMARY, insertbackground="#ffffff",
            relief="flat", bd=0, width=width, font=("Segoe UI", 9)
        )
        entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(2, 6), pady=3)

        def on_focus_in(e):
            border_frame.configure(bg=cls.BORDER_FOCUS)
        def on_focus_out(e):
            border_frame.configure(bg=cls.BORDER_SUBTLE)
        def on_mouse_enter(e):
            if not entry.focus_get() == entry:
                border_frame.configure(bg=cls.BORDER_HOVER)
        def on_mouse_leave(e):
            if not entry.focus_get() == entry:
                border_frame.configure(bg=cls.BORDER_SUBTLE)

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        border_frame.bind("<Enter>", on_mouse_enter)
        border_frame.bind("<Leave>", on_mouse_leave)

        return border_frame, entry

    @classmethod
    def create_bordered_card(cls, parent: Any, padding: int = 10, bg: Optional[str] = None) -> tk.Frame:
        """创建具有 1px 微边框的现代卡片容器"""
        card_border = tk.Frame(parent, bg=cls.BORDER_SUBTLE, padx=1, pady=1)
        card_content = tk.Frame(card_border, bg=bg or cls.BG_SURFACE, padx=padding, pady=padding)
        card_content.pack(fill=tk.BOTH, expand=True)
        return card_content
