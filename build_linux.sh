#!/usr/bin/env bash
# ==============================================================================
# Linux 原生单文件可执行程序打包脚本
# 用法: chmod +x build_linux.sh && ./build_linux.sh
# ==============================================================================

set -e

echo "[*] 检查 Python 与依赖环境..."
if ! command -v python3 &> /dev/null; then
    echo "[-] 未找到 python3，请先安装 Python 3"
    exit 1
fi

# 安装打包依赖
python3 -m pip install --quiet pyinstaller

echo "[*] 开始打包 Linux 单文件可执行程序 (ELF)..."
python3 build_executables.py

echo "[✓] Linux 二进制构建完成！产物路径: dist/zcode-model-sync"
chmod +x dist/zcode-model-sync
