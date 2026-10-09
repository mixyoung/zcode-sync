#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主应用窗口 (App Window) - 现代工业深色升级版
支持全量配置文件发现与下拉切换、所属文件明细列、自定义/内置分类过滤、
模型重复检测、单个服务商可视化编辑与删除。全面采用工业级沉浸深色设计系统。
"""

import os
import json
import copy
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from core.path_detector import PathDetector, ConfigFileInfo
from core.sync_engine import SyncEngine
from .theme import ThemeEngine
from .edit_dialog import EditProviderDialog

class AppWindow:
    """ZCode 模型配置管理器主窗口控制器 (工业级深色美化版)"""

    def __init__(self, root: tk.Tk, initial_config_path: Optional[str] = None):
        self.root = root
        self.root.title("ZCode 模型配置管理器 - 现代深色管理中心")
        self.root.geometry("900x660")
        self.root.minsize(780, 540)

        self.extra_paths: List[str] = []
        if initial_config_path:
            self.extra_paths.append(initial_config_path)

        self.all_config_files: List[ConfigFileInfo] = []
        self.current_items: List[Dict[str, Any]] = []

        ThemeEngine.apply(self.root)
        self._build_layout()
        self.reload_all_configs()

    def _build_layout(self):
        """构建整体页面布局"""
        main_container = ttk.Frame(self.root, padding=16)
        main_container.pack(fill=tk.BOTH, expand=True)

        # 1. 头部标题与系统环境
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        title_lbl = ttk.Label(header_frame, text="ZCode 模型服务商配置管理", style="Title.TLabel")
        title_lbl.pack(side=tk.LEFT)

        sys_desc = f"● {PathDetector.get_system_name()}  •  {Path.home()}"
        env_lbl = ttk.Label(header_frame, text=sys_desc, style="Sub.TLabel")
        env_lbl.pack(side=tk.RIGHT, pady=(4, 0))

        # 2. 配置文件选择器面板 (带 1px 微边框深色卡片)
        selector_card = ThemeEngine.create_bordered_card(main_container, padding=10)
        selector_card.master.pack(fill=tk.X, pady=(0, 10))

        sel_top = tk.Frame(selector_card, bg=ThemeEngine.BG_SURFACE)
        sel_top.pack(fill=tk.X)

        tk.Label(
            sel_top, text="当前查看的配置文件:", bg=ThemeEngine.BG_SURFACE,
            fg=ThemeEngine.TEXT_PRIMARY, font=("Segoe UI", 9, "bold")
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.config_combo_var = tk.StringVar()
        self.config_combo = ttk.Combobox(sel_top, textvariable=self.config_combo_var, state="readonly", width=55)
        self.config_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.config_combo.bind("<<ComboboxSelected>>", self._on_config_selected)

        add_file_btn = ThemeEngine.create_outline_button(
            sel_top, text="+ 添加其他配置...", command=self._on_add_custom_file
        )
        add_file_btn.pack(side=tk.LEFT, padx=(0, 4))

        open_folder_btn = ThemeEngine.create_outline_button(
            sel_top, text="↗ 打开所在目录", command=self._on_open_folder
        )
        open_folder_btn.pack(side=tk.LEFT)

        # 状态简报行
        self.file_detail_lbl = tk.Label(
            selector_card, text="● 正在扫描本地配置文件...",
            bg=ThemeEngine.BG_SURFACE, fg=ThemeEngine.TEXT_SECONDARY,
            font=("Consolas", 9)
        )
        self.file_detail_lbl.pack(anchor="w", pady=(6, 0))

        # 3. 过滤与搜索工具栏
        filter_bar = ttk.Frame(main_container)
        filter_bar.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(filter_bar, text="筛选:").pack(side=tk.LEFT, padx=(0, 4))

        self.filter_type_var = tk.StringVar(value="全部")
        filter_combo = ttk.Combobox(
            filter_bar, textvariable=self.filter_type_var,
            values=["全部", "仅自定义模型", "仅内置官方套餐"],
            state="readonly", width=14
        )
        filter_combo.pack(side=tk.LEFT, padx=(0, 12))
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_table_view())

        # 现代微边框搜索框
        ttk.Label(filter_bar, text="搜索:").pack(side=tk.LEFT, padx=(0, 4))
        self.search_var = tk.StringVar()
        search_wrap, self.search_entry = ThemeEngine.create_bordered_entry(
            filter_bar, textvariable=self.search_var, width=22, show_icon=True
        )
        search_wrap.pack(side=tk.LEFT, padx=(0, 8))
        self.search_var.trace_add("write", lambda *args: self._refresh_table_view())

        # 重复模型诊断按钮 (极简轮廓样式)
        dup_check_btn = ThemeEngine.create_outline_button(
            filter_bar, text="◈ 重复模型检测分析", command=self._on_show_duplicates_dialog,
            font=("Segoe UI", 9)
        )
        dup_check_btn.pack(side=tk.RIGHT)

        # 4. 数据表格视图 (带外层 1px 微边框容器)
        table_outer = tk.Frame(main_container, bg=ThemeEngine.BORDER_SUBTLE, padx=1, pady=1)
        table_outer.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        table_container = tk.Frame(table_outer, bg=ThemeEngine.ROW_BG_DARK)
        table_container.pack(fill=tk.BOTH, expand=True)

        cols = ("name", "type", "kind", "models_count", "source", "models_list")
        self.tree = ttk.Treeview(
            table_container, columns=cols, show="headings", selectmode="extended"
        )
        self.tree.heading("name", text="服务商名称 (Provider)")
        self.tree.heading("type", text="分类类型")
        self.tree.heading("kind", text="协议")
        self.tree.heading("models_count", text="模型数")
        self.tree.heading("source", text="所属配置文件")
        self.tree.heading("models_list", text="模型清单预览")

        self.tree.column("name", width=175, anchor="w")
        self.tree.column("type", width=85, anchor="center")
        self.tree.column("kind", width=75, anchor="center")
        self.tree.column("models_count", width=60, anchor="center")
        self.tree.column("source", width=195, anchor="w")
        self.tree.column("models_list", width=260, anchor="w")

        # 斑马纹与徽章标签样式注入
        self.tree.tag_configure("row_dark", background=ThemeEngine.ROW_BG_DARK)
        self.tree.tag_configure("row_alt", background=ThemeEngine.ROW_BG_ALT)
        self.tree.tag_configure("custom_tag", foreground=ThemeEngine.BADGE_CUSTOM_FG)
        self.tree.tag_configure("official_tag", foreground=ThemeEngine.BADGE_OFFICIAL_FG)

        v_scroll = ttk.Scrollbar(
            table_container, orient=tk.VERTICAL, command=self.tree.yview, style="Vertical.TScrollbar"
        )
        self.tree.configure(yscrollcommand=v_scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 双击表格行直接打开编辑
        self.tree.bind("<Double-1>", lambda event: self.on_edit_selected())

        # 5. 单项编辑与管理栏 (针对选中的 Provider)
        manage_bar = ttk.Frame(main_container)
        manage_bar.pack(fill=tk.X, pady=(0, 10))

        edit_btn = ThemeEngine.create_secondary_button(
            manage_bar, text="✎ 编辑选中配置", command=self.on_edit_selected,
            font=("Segoe UI", 9, "bold"), padx=12, pady=5
        )
        edit_btn.pack(side=tk.LEFT, padx=(0, 8))

        del_btn = ThemeEngine.create_danger_button(
            manage_bar, text="✕ 删除选中配置", command=self.on_delete_selected,
            padx=10, pady=5
        )
        del_btn.pack(side=tk.LEFT, padx=(0, 16))

        self.mask_key_var = tk.BooleanVar(value=False)
        mask_cb = tk.Checkbutton(
            manage_bar, text="导出时抹除 API Key (安全脱敏)",
            variable=self.mask_key_var, bg=ThemeEngine.BG_CANVAS, fg=ThemeEngine.TEXT_PRIMARY,
            selectcolor=ThemeEngine.BG_SURFACE, activebackground=ThemeEngine.BG_CANVAS,
            activeforeground=ThemeEngine.TEXT_PRIMARY, font=("Segoe UI", 8)
        )
        mask_cb.pack(side=tk.LEFT)

        refresh_btn = ThemeEngine.create_outline_button(
            manage_bar, text="↻ 刷新全部", command=self.reload_all_configs,
            font=("Segoe UI", 8), padx=10, pady=4
        )
        refresh_btn.pack(side=tk.RIGHT)

        # 6. 核心导入导出按钮组 (2x2 对称现代化排布，规范按钮层级)
        btn_grid = ttk.Frame(main_container)
        btn_grid.pack(fill=tk.X, pady=(0, 6))

        row1 = ttk.Frame(btn_grid)
        row1.pack(fill=tk.X, pady=(0, 6))

        self.btn_export_file = ThemeEngine.create_primary_button(
            row1, text="↑  导出为 JSON 文件 (主要操作)", command=self.on_export_file,
            pady=8
        )
        self.btn_export_file.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        self.btn_import_file = ThemeEngine.create_secondary_button(
            row1, text="↓  从文件导入配置", command=self.on_import_file,
            pady=8
        )
        self.btn_import_file.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))

        row2 = ttk.Frame(btn_grid)
        row2.pack(fill=tk.X)

        self.btn_copy_clip = ThemeEngine.create_secondary_button(
            row2, text="⎘  复制到系统剪贴板", command=self.on_copy_clipboard,
            pady=8
        )
        self.btn_copy_clip.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        self.btn_import_clip = ThemeEngine.create_secondary_button(
            row2, text="⎘  从系统剪贴板导入", command=self.on_import_clipboard,
            pady=8
        )
        self.btn_import_clip.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))

        # 7. 底部保障说明状态栏
        tip_frame = tk.Frame(main_container, bg=ThemeEngine.BG_CANVAS)
        tip_frame.pack(fill=tk.X, pady=(8, 0))

        tip_lbl = tk.Label(
            tip_frame,
            text="● 安全保障：双击表格行直接编辑 | 写入前自动创建 .bak 历史备份 | 增量合并绝不冲掉未冲突配置",
            bg=ThemeEngine.BG_CANVAS, fg=ThemeEngine.TEXT_MUTED, font=("Segoe UI", 8)
        )
        tip_lbl.pack(side=tk.LEFT)

    def reload_all_configs(self):
        """扫描全量配置文件并重载"""
        self.all_config_files = PathDetector.discover_all_configs(self.extra_paths)

        options = ["【全部配置文件】(聚合查看所有服务商)"]
        for c in self.all_config_files:
            options.append(c.get_display_name())

        self.config_combo["values"] = options
        if not self.config_combo_var.get() or self.config_combo_var.get() not in options:
            self.config_combo.current(0)

        # 读取全部数据
        self.current_items = SyncEngine.load_all_providers_with_meta(self.all_config_files)
        self._update_status_bar()
        self._refresh_table_view()

    def _on_config_selected(self, event=None):
        """当用户在下拉框中切换特定文件时"""
        self._update_status_bar()
        self._refresh_table_view()

    def _get_active_target_file(self) -> Path:
        """获取当前活跃的配置文件路径，用于导入或默认操作"""
        idx = self.config_combo.current()
        if idx > 0 and (idx - 1) < len(self.all_config_files):
            return self.all_config_files[idx - 1].path
        return self.all_config_files[0].path if self.all_config_files else PathDetector.get_default_config_path()

    def _update_status_bar(self):
        idx = self.config_combo.current()
        if idx == 0:
            custom_total = sum(1 for x in self.current_items if x["is_custom"])
            self.file_detail_lbl.config(
                text=f"● 聚合视图: 已发现 {len(self.all_config_files)} 个配置文件，共载入 {len(self.current_items)} 个服务商 (其中 {custom_total} 个为自定义模型)",
                fg="#38bdf8"
            )
        else:
            cinfo = self.all_config_files[idx - 1]
            self.file_detail_lbl.config(
                text=f"● 物理路径: {cinfo.path}  |  文件大小: {cinfo.size_bytes} 字节  |  更新于: {cinfo.updated_at}",
                fg="#a1a1aa"
            )

    def _refresh_table_view(self):
        """根据当前的下拉选择、类型过滤与搜索词重新渲染表格"""
        for row in self.tree.get_children():
            self.tree.delete(row)

        idx = self.config_combo.current()
        active_file_filter = None
        if idx > 0 and (idx - 1) < len(self.all_config_files):
            active_file_filter = self.all_config_files[idx - 1].path

        filter_type = self.filter_type_var.get()
        search_kw = self.search_var.get().strip().lower()

        row_idx = 0
        for item in self.current_items:
            # 文件过滤
            if active_file_filter and item["source_file"] != active_file_filter:
                continue

            # 类型过滤
            if filter_type == "仅自定义模型" and not item["is_custom"]:
                continue
            if filter_type == "仅内置官方套餐" and item["is_custom"]:
                continue

            # 搜索过滤
            if search_kw:
                match_name = search_kw in item["name"].lower()
                match_pid = search_kw in item["provider_id"].lower()
                match_models = any(search_kw in m.lower() for m in item["models"])
                if not (match_name or match_pid or match_models):
                    continue

            # 徽章式文本格式化
            type_badge = "[自定义]" if item["is_custom"] else "[官方内置]"
            source_display = f"{item['source_file'].parent.parent.name if item['source_file'].parent.name == 'v2' else item['source_file'].name} ({item['source_label']})"
            models_text = ", ".join(item["models"]) if item["models"] else "(未定义模型)"

            row_id = f"{item['source_file']}@@{item['provider_id']}"
            
            # 斑马纹与分类标签
            row_tag = "row_dark" if row_idx % 2 == 0 else "row_alt"
            cat_tag = "custom_tag" if item["is_custom"] else "official_tag"
            
            self.tree.insert("", tk.END, iid=row_id, values=(
                item["name"],
                type_badge,
                item["kind"],
                len(item["models"]),
                source_display,
                models_text
            ), tags=(row_tag, cat_tag))
            row_idx += 1

    def _on_add_custom_file(self):
        """手动添加其他位置的配置文件"""
        chosen = filedialog.askopenfilename(
            title="选择 ZCode 配置文件 (config.json)",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
        )
        if chosen and chosen not in self.extra_paths:
            self.extra_paths.append(chosen)
            self.reload_all_configs()
            # 切换到新增的那个
            self.config_combo.current(len(self.all_config_files))
            self._on_config_selected()

    def _on_open_folder(self):
        """在系统资源管理器中打开当前选中的配置文件所在文件夹"""
        target_path = self._get_active_target_file()
        if not target_path.exists():
            messagebox.showwarning("提示", f"路径不存在: {target_path}")
            return
        folder = target_path.parent
        try:
            if os.name == 'nt':
                os.startfile(folder)
            elif os.uname().sysname == 'Darwin':
                subprocess.run(['open', str(folder)])
            else:
                subprocess.run(['xdg-open', str(folder)])
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件夹:\n{e}")

    def _on_show_duplicates_dialog(self):
        """弹出重复模型分析与去重诊断窗口"""
        duplicates = SyncEngine.analyze_duplicate_models(self.current_items)
        if not duplicates:
            messagebox.showinfo("检测结果", "未发现重复模型！所有模型定义均唯一。")
            return

        diag_win = tk.Toplevel(self.root)
        diag_win.title("重复模型诊断报告 - 现代分析视图")
        diag_win.geometry("660x500")
        diag_win.minsize(580, 420)
        diag_win.transient(self.root)
        diag_win.configure(bg=ThemeEngine.BG_CANVAS)

        f = ttk.Frame(diag_win, padding=16)
        f.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            f, text=f"● 检测到 {len(duplicates)} 个在多个服务商中重复声明的模型：",
            bg=ThemeEngine.BG_CANVAS, fg="#ffffff", font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(0, 8))

        # 外层微边框
        box_wrap = tk.Frame(f, bg=ThemeEngine.BORDER_SUBTLE, padx=1, pady=1)
        box_wrap.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        txt_frame = tk.Frame(box_wrap, bg=ThemeEngine.BG_INPUT)
        txt_frame.pack(fill=tk.BOTH, expand=True)

        text_box = tk.Text(
            txt_frame, bg=ThemeEngine.BG_INPUT, fg="#e2e8f0", insertbackground="#ffffff",
            font=("Consolas", 9), relief="flat", wrap="word", padx=8, pady=8
        )
        sb = ttk.Scrollbar(txt_frame, orient=tk.VERTICAL, command=text_box.yview, style="Vertical.TScrollbar")
        text_box.configure(yscrollcommand=sb.set)
        text_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        for model_id, occurrences in duplicates.items():
            text_box.insert(tk.END, f"● 模型 [{model_id}] 共在 {len(occurrences)} 处出现:\n")
            for occ in occurrences:
                custom_tag = "[自定义]" if occ["is_custom"] else "[官方内置]"
                text_box.insert(tk.END, f"   • {custom_tag} 服务商: {occ['provider']} (ID: {occ['provider_id']})\n")
                text_box.insert(tk.END, f"     配置文件: {occ['file']}\n")
            text_box.insert(tk.END, "\n" + "-" * 55 + "\n\n")

        text_box.config(state="disabled")

        tk.Label(
            f, text="说明：官方 BigModel / Z.ai 的各套餐（Coding Plan、Start Plan、API Key）默认自带相同模型，属于正常现象。",
            bg=ThemeEngine.BG_CANVAS, fg=ThemeEngine.TEXT_MUTED, font=("Segoe UI", 8)
        ).pack(anchor="w")

    def _get_item_by_row_id(self, row_id: str) -> Optional[Dict[str, Any]]:
        parts = row_id.split("@@", 1)
        if len(parts) != 2:
            return None
        src_file, pid = Path(parts[0]), parts[1]
        for it in self.current_items:
            if it["source_file"] == src_file and it["provider_id"] == pid:
                return it
        return None

    def on_edit_selected(self):
        """编辑选中的单条 Provider 配置"""
        selected_rows = self.tree.selection()
        if not selected_rows:
            messagebox.showwarning("提示", "请先在表格中选中要编辑的服务商配置行。")
            return

        row_id = selected_rows[0]
        item = self._get_item_by_row_id(row_id)
        if not item:
            messagebox.showerror("错误", "无法定位该项的元数据。")
            return

        def handle_save_callback(provider_id, updated_data, source_file):
            ok, msg = SyncEngine.save_single_provider(source_file, provider_id, updated_data)
            if ok:
                messagebox.showinfo("保存成功", f"{msg}\n已自动生成历史备份。重启 ZCode 客户端后生效。")
                self.reload_all_configs()
            else:
                messagebox.showerror("保存失败", msg)

        EditProviderDialog(
            parent=self.root,
            provider_id=item["provider_id"],
            provider_data=item["raw_data"],
            source_file=item["source_file"],
            on_save_callback=handle_save_callback
        )

    def on_delete_selected(self):
        """从对应文件中安全删除选中的 Provider"""
        selected_rows = self.tree.selection()
        if not selected_rows:
            messagebox.showwarning("提示", "请先选中要删除的服务商配置行。")
            return

        items_to_delete = [self._get_item_by_row_id(r) for r in selected_rows if self._get_item_by_row_id(r)]
        if not items_to_delete:
            return

        confirm_msg = f"即将删除以下 {len(items_to_delete)} 个服务商配置：\n\n"
        for it in items_to_delete:
            confirm_msg += f"• [{it['name']}] 来自 {it['source_file'].name}\n"
        confirm_msg += "\n系统将在删除前为目标文件自动创建 .bak 备份副本。\n是否确认删除？"

        if not messagebox.askyesno("确认删除", confirm_msg):
            return

        del_count = 0
        for it in items_to_delete:
            ok, msg = SyncEngine.delete_single_provider(it["source_file"], it["provider_id"])
            if ok:
                del_count += 1
            else:
                messagebox.showerror("删除失败", f"删除 [{it['name']}] 失败:\n{msg}")

        messagebox.showinfo("操作完成", f"已成功删除 {del_count} 个服务商配置！\n已自动备份原文件，重启 ZCode 生效。")
        self.reload_all_configs()

    def _get_export_dict(self) -> Dict[str, Any]:
        """按当前选中或当前视图提取待导出的 providers 字典"""
        selected_rows = self.tree.selection()
        target_items = []
        if selected_rows:
            for r in selected_rows:
                it = self._get_item_by_row_id(r)
                if it: target_items.append(it)
        else:
            # 导出当前表格呈现的所有项
            for row in self.tree.get_children():
                it = self._get_item_by_row_id(row)
                if it: target_items.append(it)

        export_providers = {}
        for it in target_items:
            export_providers[it["provider_id"]] = copy.deepcopy(it["raw_data"])
        return export_providers

    def on_export_file(self):
        """处理导出为 JSON 文件"""
        providers = self._get_export_dict()
        if not providers:
            messagebox.showwarning("提示", "当前没有可导出的服务商配置。")
            return

        payload = SyncEngine.prepare_export_payload(
            providers, mask_keys=self.mask_key_var.get()
        )

        out_path = filedialog.asksaveasfilename(
            title="保存 ZCode 模型配置文件",
            defaultextension=".json",
            initialfile="zcode-models-export.json",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
        )
        if not out_path:
            return

        try:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            count = len(payload["provider"])
            mask_text = " (已脱敏 API Key)" if self.mask_key_var.get() else ""
            messagebox.showinfo("导出成功", f"成功导出 {count} 个模型服务商配置{mask_text}至:\n{out_path}")
        except Exception as e:
            messagebox.showerror("导出失败", f"写入文件时出错:\n{e}")

    def on_copy_clipboard(self):
        """处理复制到系统剪贴板"""
        providers = self._get_export_dict()
        if not providers:
            messagebox.showwarning("提示", "当前没有可导出的服务商配置。")
            return

        payload = SyncEngine.prepare_export_payload(
            providers, mask_keys=self.mask_key_var.get()
        )

        json_text = json.dumps(payload, indent=2, ensure_ascii=False)
        self.root.clipboard_clear()
        self.root.clipboard_append(json_text)
        self.root.update()

        count = len(payload["provider"])
        mask_text = " (已脱敏 API Key)" if self.mask_key_var.get() else ""
        messagebox.showinfo(
            "复制成功",
            f"已将 {count} 个模型服务商配置{mask_text}复制到系统剪贴板！\n您可在目标电脑上直接点击【从剪贴板导入】。"
        )

    def _execute_import(self, raw_data: Any, source_name: str):
        """统一执行导入"""
        ok, msg, valid_providers = SyncEngine.validate_import_data(raw_data)
        if not ok:
            messagebox.showerror("格式错误", f"导入数据校验失败:\n{msg}")
            return

        target_file = self._get_active_target_file()
        confirm_msg = (
            f"检测到来自 [{source_name}] 的 {len(valid_providers)} 个服务商配置。\n\n"
            f"目标导入文件: {target_file}\n\n"
            f"系统将自动为您创建 .bak 历史备份并执行安全增量合并。\n\n"
            f"是否确认立即导入？"
        )
        if not messagebox.askyesno("确认导入", confirm_msg):
            return

        save_ok, save_msg, count_applied = SyncEngine.merge_and_save(target_file, valid_providers)
        if not save_ok:
            messagebox.showerror("导入失败", save_msg)
            return

        self.reload_all_configs()
        messagebox.showinfo(
            "导入成功",
            f"成功导入并合并 {count_applied} 个服务商配置至 {target_file.name}！\n"
            f"已自动备份原文件，重启 ZCode 客户端后生效。"
        )

    def on_import_file(self):
        """处理从文件导入"""
        file_path = filedialog.askopenfilename(
            title="选择要导入的 ZCode 模型配置文件",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._execute_import(data, source_name=Path(file_path).name)
        except Exception as e:
            messagebox.showerror("读取错误", f"解析导入文件失败:\n{e}")

    def on_import_clipboard(self):
        """处理从系统剪贴板导入"""
        try:
            clip_text = self.root.clipboard_get()
        except Exception:
            messagebox.showwarning("剪贴板为空", "系统剪贴板中未获取到文本内容。")
            return

        if not clip_text or not clip_text.strip():
            messagebox.showwarning("剪贴板为空", "剪贴板内容为空。")
            return

        self._execute_import(clip_text, source_name="系统剪贴板")
