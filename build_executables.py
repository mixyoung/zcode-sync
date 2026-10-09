#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多平台可执行程序打包构建器 (Multi-platform Executable Builder)
使用 PyInstaller 将应用打包为独立免安装的单文件可执行程序。
支持 Windows (.exe) 与 Linux (ELF 二进制)。
"""

import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
SPEC_FILE = PROJECT_ROOT / "zcode-model-sync.spec"

def clean():
    """清理历史构建产物"""
    print("[*] 正在清理旧构建临时文件...")
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR, ignore_errors=True)
    if SPEC_FILE.exists():
        SPEC_FILE.unlink(missing_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

def build_current_platform():
    """打包当前操作系统对应的独立单文件"""
    sys_name = platform.system()
    app_name = "zcode-model-sync"
    if sys_name == "Windows":
        target_name = f"{app_name}.exe"
    else:
        target_name = app_name

    print(f"[*] 当前构建目标操作系统: {sys_name} ({platform.machine()})")
    print(f"[*] 目标输出文件: {DIST_DIR / target_name}")

    # 构造 PyInstaller 参数
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", app_name,
        "--onefile",
        "--noconsole",            # 纯 GUI 模式，不弹出命令行控制台
        "--clean",
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
        "--specpath", str(PROJECT_ROOT),
        "--paths", str(PROJECT_ROOT),
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.ttk",
        "--hidden-import", "tkinter.messagebox",
        "--hidden-import", "tkinter.filedialog",
        str(PROJECT_ROOT / "main.py")
    ]

    print(f"[*] 执行构建命令: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("[-] 构建失败！请检查上方 PyInstaller 错误日志。", file=sys.stderr)
        sys.exit(result.returncode)

    output_exe = DIST_DIR / target_name
    if output_exe.exists():
        size_mb = output_exe.stat().st_size / (1024 * 1024)
        print(f"[✓] 构建成功！")
        print(f"    可执行程序位置: {output_exe.resolve()}")
        print(f"    产物体积: {size_mb:.2f} MB")
    else:
        print("[-] 构建完成但未找到产物文件，请检查 dist 目录。", file=sys.stderr)

if __name__ == "__main__":
    clean()
    build_current_platform()
