#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZCode 模型配置管理器主入口 (Main Entrypoint)
支持无头命令行模式 (CLI) 与桌面图形界面模式 (GUI)。
"""

import sys
import os
import argparse
from pathlib import Path
import tkinter as tk

from core.path_detector import PathDetector
from core.sync_engine import SyncEngine
from ui.app_window import AppWindow

def enable_high_dpi_awareness():
    """在 Windows 平台启用高分屏 DPI 感知，避免界面模糊"""
    if sys.platform == "win32":
        try:
            import ctypes
            # PROCESS_PER_MONITOR_DPI_AWARE
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

def run_cli_export(config_path: Path, output_file: str, mask: bool):
    """无头命令行导出模式"""
    ok, msg, providers = SyncEngine.load_providers(config_path)
    if not ok:
        print(f"[错误] 读取配置失败: {msg}", file=sys.stderr)
        sys.exit(1)

    payload = SyncEngine.prepare_export_payload(providers, mask_keys=mask)
    out_p = Path(output_file)
    try:
        import json
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"[成功] 已导出 {len(payload['provider'])} 个服务商配置至: {out_p.resolve()}")
    except Exception as e:
        print(f"[错误] 写入导出文件失败: {e}", file=sys.stderr)
        sys.exit(1)

def run_cli_import(config_path: Path, input_file: str):
    """无头命令行导入模式"""
    inp_p = Path(input_file)
    if not inp_p.exists():
        print(f"[错误] 导入文件不存在: {inp_p}", file=sys.stderr)
        sys.exit(1)

    import json
    try:
        with open(inp_p, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        print(f"[错误] 解析导入文件失败: {e}", file=sys.stderr)
        sys.exit(1)

    ok, msg, valid_providers = SyncEngine.validate_import_data(raw)
    if not ok:
        print(f"[错误] 校验导入数据失败: {msg}", file=sys.stderr)
        sys.exit(1)

    save_ok, save_msg, count = SyncEngine.merge_and_save(config_path, valid_providers)
    if not save_ok:
        print(f"[错误] 导入失败: {save_msg}", file=sys.stderr)
        sys.exit(1)

    print(f"[成功] 已合并导入 {count} 个服务商配置至 {config_path}！(旧配置已自动备份为 config.json.bak)")

def main():
    parser = argparse.ArgumentParser(description="ZCode 模型配置管理器 (跨平台桌面同步工具)")
    parser.add_argument("--path", type=str, default=None, help="自定义 ZCode config.json 文件路径")
    parser.add_argument("--export", type=str, default=None, metavar="OUT_FILE", help="[CLI 模式] 导出配置到指定 JSON 文件")
    parser.add_argument("--import-file", type=str, default=None, metavar="IN_FILE", help="[CLI 模式] 从指定 JSON 文件导入配置")
    parser.add_argument("--mask", action="store_true", help="[CLI 模式] 导出时脱敏 API Key")

    args = parser.parse_args()

    cfg_path, exists, _ = PathDetector.detect(args.path)

    # 优先执行命令行批处理指令
    if args.export:
        run_cli_export(cfg_path, args.export, args.mask)
        return

    if args.import_file:
        run_cli_import(cfg_path, args.import_file)
        return

    # 默认启动图形界面
    enable_high_dpi_awareness()
    root = tk.Tk()
    app = AppWindow(root, initial_config_path=args.path)
    root.mainloop()

if __name__ == "__main__":
    main()
