#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务商与模型配置编辑对话框 (Provider Edit Dialog) - 现代深色版
支持可视化表单与原始 JSON 高级双向编辑模式。全面采用工业级微边框与卡片设计。
"""

import json
import copy
from pathlib import Path
from typing import Dict, Any, Optional, Callable

import tkinter as tk
from tkinter import ttk, messagebox

from .theme import ThemeEngine

class EditProviderDialog(tk.Toplevel):
    """服务商配置编辑模态对话框 (现代深色版)"""

    def __init__(
        self,
        parent: tk.Tk,
        provider_id: str,
        provider_data: Dict[str, Any],
        source_file: Path,
        on_save_callback: Callable[[str, Dict[str, Any], Path], None]
    ):
        super().__init__(parent)
        self.parent = parent
        self.provider_id = provider_id
        self.provider_data = copy.deepcopy(provider_data)
        self.source_file = source_file
        self.on_save_callback = on_save_callback

        self.title(f"编辑服务商配置 - {self.provider_data.get('name', provider_id)}")
        self.geometry("660x560")
        self.minsize(580, 480)
        self.transient(parent)
        self.grab_set()

        self.configure(bg=ThemeEngine.BG_CANVAS)
        self._build_ui()
        self._populate_fields()

    def _build_ui(self):
        container = tk.Frame(self, bg=ThemeEngine.BG_CANVAS, padx=16, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        # 顶部所属来源卡片 (带 1px 微边框)
        header_card = ThemeEngine.create_bordered_card(container, padding=10)
        header_card.master.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            header_card,
            text=f"● 服务商标识: {self.provider_id}",
            bg=ThemeEngine.BG_SURFACE,
            fg="#ffffff",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        tk.Label(
            header_card,
            text=f"物理所属文件: {self.source_file}",
            bg=ThemeEngine.BG_SURFACE,
            fg=ThemeEngine.TEXT_SECONDARY,
            font=("Consolas", 9)
        ).pack(anchor="w", pady=(3, 0))

        # 选项卡 (表单视图 / JSON 视图)
        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        self.tab_form = tk.Frame(self.notebook, bg=ThemeEngine.BG_SURFACE, padx=12, pady=12)
        self.tab_json = tk.Frame(self.notebook, bg=ThemeEngine.BG_SURFACE, padx=12, pady=12)

        self.notebook.add(self.tab_form, text="表单可视化编辑")
        self.notebook.add(self.tab_json, text="高级 JSON 编辑")

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # --- Tab 1: 表单视图 ---
        self._build_form_tab()

        # --- Tab 2: JSON 视图 ---
        self._build_json_tab()

        # 底部按钮栏
        btn_bar = tk.Frame(container, bg=ThemeEngine.BG_CANVAS)
        btn_bar.pack(fill=tk.X)

        cancel_btn = ThemeEngine.create_secondary_button(
            btn_bar, text="取消", command=self.destroy,
            padx=14, pady=6
        )
        cancel_btn.pack(side=tk.RIGHT, padx=(8, 0))

        save_btn = ThemeEngine.create_primary_button(
            btn_bar, text="保存修改并写入文件", command=self._on_save,
            padx=16, pady=6
        )
        save_btn.pack(side=tk.RIGHT)

    def _create_field_entry(self, parent, textvariable: tk.StringVar, show: str = "") -> tuple[tk.Frame, tk.Entry]:
        """创建带 1px 细微边框的表单输入框"""
        border_frame = tk.Frame(parent, bg=ThemeEngine.BORDER_SUBTLE, padx=1, pady=1)
        inner_frame = tk.Frame(border_frame, bg=ThemeEngine.BG_INPUT)
        inner_frame.pack(fill=tk.BOTH, expand=True)

        entry = tk.Entry(
            inner_frame, textvariable=textvariable, bg=ThemeEngine.BG_INPUT,
            fg=ThemeEngine.TEXT_PRIMARY, insertbackground="#ffffff",
            relief="flat", bd=0, show=show, font=("Segoe UI", 9)
        )
        entry.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        def on_focus_in(e): border_frame.configure(bg=ThemeEngine.BORDER_FOCUS)
        def on_focus_out(e): border_frame.configure(bg=ThemeEngine.BORDER_SUBTLE)
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

        return border_frame, entry

    def _build_form_tab(self):
        # 基本属性表单
        form_frame = tk.Frame(self.tab_form, bg=ThemeEngine.BG_SURFACE)
        form_frame.pack(fill=tk.X, pady=(0, 10))

        # 名称
        tk.Label(form_frame, text="服务商名称:", bg=ThemeEngine.BG_SURFACE, fg=ThemeEngine.TEXT_PRIMARY, font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=4)
        self.name_var = tk.StringVar()
        name_wrap, self.name_entry = self._create_field_entry(form_frame, self.name_var)
        name_wrap.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=4)

        # 协议类型
        tk.Label(form_frame, text="接口协议类型:", bg=ThemeEngine.BG_SURFACE, fg=ThemeEngine.TEXT_PRIMARY, font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=4)
        self.kind_var = tk.StringVar()
        self.kind_combo = ttk.Combobox(form_frame, textvariable=self.kind_var, values=["anthropic", "openai", "gemini", "ollama", "custom"], state="readonly")
        self.kind_combo.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=4)

        # Base URL
        tk.Label(form_frame, text="Base URL (接口地址):", bg=ThemeEngine.BG_SURFACE, fg=ThemeEngine.TEXT_PRIMARY, font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=4)
        self.url_var = tk.StringVar()
        url_wrap, self.url_entry = self._create_field_entry(form_frame, self.url_var)
        url_wrap.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=4)

        # API Key
        tk.Label(form_frame, text="API Key (密钥):", bg=ThemeEngine.BG_SURFACE, fg=ThemeEngine.TEXT_PRIMARY, font=("Segoe UI", 9)).grid(row=3, column=0, sticky="w", pady=4)
        key_box = tk.Frame(form_frame, bg=ThemeEngine.BG_SURFACE)
        key_box.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=4)

        self.key_var = tk.StringVar()
        key_wrap, self.key_entry = self._create_field_entry(key_box, self.key_var, show="•")
        key_wrap.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.show_key_var = tk.BooleanVar(value=False)
        show_key_cb = tk.Checkbutton(
            key_box, text="显示明文", variable=self.show_key_var,
            command=lambda: self.key_entry.config(show="" if self.show_key_var.get() else "•"),
            bg=ThemeEngine.BG_SURFACE, fg=ThemeEngine.TEXT_SECONDARY, selectcolor=ThemeEngine.BG_INPUT,
            activebackground=ThemeEngine.BG_SURFACE, activeforeground=ThemeEngine.TEXT_PRIMARY,
            font=("Segoe UI", 8)
        )
        show_key_cb.pack(side=tk.RIGHT, padx=(8, 0))

        # 是否启用
        self.enabled_var = tk.BooleanVar(value=True)
        enabled_cb = tk.Checkbutton(
            form_frame, text="启用该模型服务商", variable=self.enabled_var,
            bg=ThemeEngine.BG_SURFACE, fg=ThemeEngine.TEXT_PRIMARY, selectcolor=ThemeEngine.BG_INPUT,
            activebackground=ThemeEngine.BG_SURFACE, activeforeground=ThemeEngine.TEXT_PRIMARY,
            font=("Segoe UI", 9)
        )
        enabled_cb.grid(row=4, column=1, sticky="w", padx=(8, 0), pady=4)

        form_frame.columnconfigure(1, weight=1)

        # 分割说明
        tk.Label(
            self.tab_form, text="● 模型清单配置 (Models):",
            bg=ThemeEngine.BG_SURFACE, fg="#ffffff", font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", pady=(8, 4))

        # 模型管理表格 (外层微边框)
        models_wrap = tk.Frame(self.tab_form, bg=ThemeEngine.BORDER_SUBTLE, padx=1, pady=1)
        models_wrap.pack(fill=tk.BOTH, expand=True)

        models_frame = tk.Frame(models_wrap, bg=ThemeEngine.ROW_BG_DARK)
        models_frame.pack(fill=tk.BOTH, expand=True)

        self.model_tree = ttk.Treeview(models_frame, columns=("model_id", "context", "output", "reasoning"), show="headings", height=5)
        self.model_tree.heading("model_id", text="模型标识 (Model ID)")
        self.model_tree.heading("context", text="上下文窗口")
        self.model_tree.heading("output", text="最大输出")
        self.model_tree.heading("reasoning", text="思考链推理")

        self.model_tree.column("model_id", width=180, anchor="w")
        self.model_tree.column("context", width=90, anchor="center")
        self.model_tree.column("output", width=80, anchor="center")
        self.model_tree.column("reasoning", width=90, anchor="center")

        self.model_tree.tag_configure("row_dark", background=ThemeEngine.ROW_BG_DARK, foreground=ThemeEngine.TEXT_PRIMARY)
        self.model_tree.tag_configure("row_alt", background=ThemeEngine.ROW_BG_ALT, foreground=ThemeEngine.TEXT_PRIMARY)

        m_scroll = ttk.Scrollbar(models_frame, orient=tk.VERTICAL, command=self.model_tree.yview, style="Vertical.TScrollbar")
        self.model_tree.configure(yscrollcommand=m_scroll.set)
        self.model_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        m_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 模型快捷操作
        model_btn_bar = tk.Frame(self.tab_form, bg=ThemeEngine.BG_SURFACE)
        model_btn_bar.pack(fill=tk.X, pady=(6, 0))

        add_model_btn = ThemeEngine.create_outline_button(
            model_btn_bar, text="+ 添加模型", command=self._on_add_model,
            font=("Segoe UI", 8), padx=8, pady=2
        )
        add_model_btn.pack(side=tk.LEFT, padx=(0, 6))

        del_model_btn = ThemeEngine.create_danger_button(
            model_btn_bar, text="✕ 删除选中模型", command=self._on_del_model,
            font=("Segoe UI", 8), padx=8, pady=2
        )
        del_model_btn.pack(side=tk.LEFT)

    def _build_json_tab(self):
        json_tip = tk.Label(
            self.tab_json, text="● 直接编辑该 Provider 原始 JSON 结构：",
            bg=ThemeEngine.BG_SURFACE, fg=ThemeEngine.TEXT_SECONDARY, font=("Segoe UI", 9)
        )
        json_tip.pack(anchor="w", pady=(0, 6))

        # 外层微边框
        text_wrap = tk.Frame(self.tab_json, bg=ThemeEngine.BORDER_SUBTLE, padx=1, pady=1)
        text_wrap.pack(fill=tk.BOTH, expand=True)

        text_frame = tk.Frame(text_wrap, bg=ThemeEngine.BG_INPUT)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.json_text = tk.Text(
            text_frame, bg=ThemeEngine.BG_INPUT, fg="#38bdf8", insertbackground="#ffffff",
            font=("Consolas", 10), relief="flat", wrap="none", padx=8, pady=8
        )
        j_scroll_v = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.json_text.yview, style="Vertical.TScrollbar")
        j_scroll_h = ttk.Scrollbar(self.tab_json, orient=tk.HORIZONTAL, command=self.json_text.xview)
        self.json_text.configure(yscrollcommand=j_scroll_v.set, xscrollcommand=j_scroll_h.set)

        self.json_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        j_scroll_v.pack(side=tk.RIGHT, fill=tk.Y)
        j_scroll_h.pack(fill=tk.X)

    def _populate_fields(self):
        """将当前 provider 数据填入界面表单"""
        self.name_var.set(self.provider_data.get("name", self.provider_id))
        self.kind_var.set(self.provider_data.get("kind", "openai"))
        self.enabled_var.set(self.provider_data.get("enabled", True))

        options = self.provider_data.get("options", {})
        self.url_var.set(options.get("baseURL", ""))
        self.key_var.set(options.get("apiKey", ""))

        for row in self.model_tree.get_children():
            self.model_tree.delete(row)

        models = self.provider_data.get("models", {})
        row_i = 0
        for mid, mdata in models.items():
            if not isinstance(mdata, dict):
                mdata = {}
            limit = mdata.get("limit", {})
            ctx = limit.get("context", "-")
            out = limit.get("output", "-")
            reasoning = "开启" if mdata.get("reasoning", {}).get("enabled") else "关闭"
            tag = "row_dark" if row_i % 2 == 0 else "row_alt"
            self.model_tree.insert("", tk.END, iid=mid, values=(mid, ctx, out, reasoning), tags=(tag,))
            row_i += 1

        # JSON 视图初始化
        self.json_text.delete("1.0", tk.END)
        self.json_text.insert("1.0", json.dumps(self.provider_data, indent=2, ensure_ascii=False))

    def _on_tab_changed(self, event):
        """选项卡切换时同步两边数据"""
        selected_tab = self.notebook.tab(self.notebook.select(), "text")
        if selected_tab == "高级 JSON 编辑":
            # 从表单搜集并更新 JSON
            self._sync_form_to_data()
            self.json_text.delete("1.0", tk.END)
            self.json_text.insert("1.0", json.dumps(self.provider_data, indent=2, ensure_ascii=False))
        else:
            # 从 JSON 解析并更新表单
            raw_text = self.json_text.get("1.0", tk.END).strip()
            if raw_text:
                try:
                    parsed = json.loads(raw_text)
                    if isinstance(parsed, dict):
                        self.provider_data = parsed
                        self._populate_fields()
                except Exception:
                    pass

    def _sync_form_to_data(self):
        """将表单内容写回 self.provider_data"""
        self.provider_data["name"] = self.name_var.get().strip()
        self.provider_data["kind"] = self.kind_var.get().strip()
        self.provider_data["enabled"] = self.enabled_var.get()

        options = self.provider_data.setdefault("options", {})
        options["baseURL"] = self.url_var.get().strip()
        options["apiKey"] = self.key_var.get().strip()

    def _on_add_model(self):
        """弹出微型输入框添加模型"""
        add_win = tk.Toplevel(self)
        add_win.title("添加模型")
        add_win.geometry("340x200")
        add_win.minsize(300, 180)
        add_win.transient(self)
        add_win.grab_set()
        add_win.configure(bg=ThemeEngine.BG_CANVAS)

        f = tk.Frame(add_win, bg=ThemeEngine.BG_CANVAS, padx=14, pady=14)
        f.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            f, text="模型标识 (例如 deepseek-chat):",
            bg=ThemeEngine.BG_CANVAS, fg=ThemeEngine.TEXT_PRIMARY, font=("Segoe UI", 9)
        ).pack(anchor="w")
        
        mid_var = tk.StringVar()
        mid_wrap, mid_entry = self._create_field_entry(f, mid_var)
        mid_wrap.pack(fill=tk.X, pady=(2, 6))

        tk.Label(
            f, text="上下文长度 (可选，默认 128000):",
            bg=ThemeEngine.BG_CANVAS, fg=ThemeEngine.TEXT_PRIMARY, font=("Segoe UI", 9)
        ).pack(anchor="w")

        ctx_var = tk.StringVar(value="128000")
        ctx_wrap, ctx_entry = self._create_field_entry(f, ctx_var)
        ctx_wrap.pack(fill=tk.X, pady=(2, 12))

        def confirm_add():
            mid = mid_entry.get().strip()
            if not mid:
                messagebox.showwarning("提示", "模型标识不能为空")
                return
            models = self.provider_data.setdefault("models", {})
            try:
                ctx_val = int(ctx_entry.get().strip())
            except Exception:
                ctx_val = 128000

            models[mid] = {
                "name": mid,
                "limit": {"context": ctx_val},
                "modalities": {"input": ["text"], "output": ["text"]}
            }
            self._populate_fields()
            add_win.destroy()

        btn = ThemeEngine.create_primary_button(f, text="确认添加", command=confirm_add, pady=5)
        btn.pack(anchor="e")

    def _on_del_model(self):
        """删除选中模型"""
        sel = self.model_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先在列表中选中要删除的模型")
            return
        for mid in sel:
            if "models" in self.provider_data and mid in self.provider_data["models"]:
                del self.provider_data["models"][mid]
        self._populate_fields()

    def _on_save(self):
        """保存并回调写回文件"""
        current_tab = self.notebook.tab(self.notebook.select(), "text")
        if current_tab == "高级 JSON 编辑":
            raw_text = self.json_text.get("1.0", tk.END).strip()
            try:
                parsed = json.loads(raw_text)
                if not isinstance(parsed, dict):
                    messagebox.showerror("错误", "JSON 根节点必须为对象")
                    return
                self.provider_data = parsed
            except Exception as e:
                messagebox.showerror("JSON 错误", f"JSON 解析失败:\n{e}")
                return
        else:
            self._sync_form_to_data()

        if not self.provider_data.get("name"):
            messagebox.showwarning("提示", "服务商名称不能为空")
            return

        self.on_save_callback(self.provider_id, self.provider_data, self.source_file)
        self.destroy()
