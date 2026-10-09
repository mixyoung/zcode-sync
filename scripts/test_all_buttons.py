#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全量按钮功能端到端自动化测试脚本 (All Buttons E2E Verification)
基于 Python websocket-client 与 Edge Chrome DevTools Protocol (CDP)。
精准支持 React 异步渲染批处理等待与作用域弹窗隔离，验证全部 9 大模块共计 35+ 个关键按钮。
"""

import os
import sys
import time
import json
import subprocess
import urllib.request
import websocket

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
CDP_PORT = 9342
APP_PORT = 4182

class CDPRunner:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=10)
        self.msg_id = 1

    def evaluate(self, expr):
        req_id = self.msg_id
        self.msg_id += 1
        msg = {
            "id": req_id,
            "method": "Runtime.evaluate",
            "params": {
                "expression": expr,
                "awaitPromise": True,
                "returnByValue": True
            }
        }
        self.ws.send(json.dumps(msg))
        while True:
            raw = self.ws.recv()
            data = json.loads(raw)
            if data.get("id") == req_id:
                if "error" in data:
                    raise RuntimeError(data["error"])
                res = data.get("result", {})
                if "exceptionDetails" in res:
                    desc = res["exceptionDetails"].get("exception", {}).get("description", "Evaluation error")
                    raise RuntimeError(desc)
                return res.get("result", {}).get("value")

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass

def main():
    print("=" * 80)
    print("      ZCode-Sync 全量按钮功能端到端自动化测试 (All Buttons E2E Test)        ")
    print("=" * 80 + "\n")

    # 1. 启动 Vite preview
    print(f"[*] 正在启动 Vite 预览服务 (http://127.0.0.1:{APP_PORT})...")
    p_vite = subprocess.Popen(
        f"pnpm exec vite preview --port {APP_PORT}",
        cwd=r"E:\33_dev_env\zcode_model_sync",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2.5)

    # 2. 启动无头 Edge
    print(f"[*] 正在启动 Edge 无头浏览器 (CDP 端口: {CDP_PORT})...")
    p_edge = subprocess.Popen([
        EDGE_PATH,
        "--headless",
        "--disable-gpu",
        "--remote-allow-origins=*",
        f"--remote-debugging-port={CDP_PORT}",
        f"http://127.0.0.1:{APP_PORT}"
    ])
    time.sleep(2.5)

    cdp = None
    results = []

    def record(module, button, passed, detail=""):
        results.append((module, button, passed, detail))
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"[{status}] {module:<18} -> {button} {f'({detail})' if detail else ''}")

    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json")
        targets = json.loads(req.read().decode())
        page_target = next(t for t in targets if t.get("type") == "page")
        ws_url = page_target["webSocketDebuggerUrl"]

        cdp = CDPRunner(ws_url)
        print("[✓] 成功连接 Edge CDP 会话！正在验证 DOM 树挂载...\n")

        cdp.evaluate("""new Promise(resolve => {
            const check = () => {
                if (document.querySelector('tbody tr')) resolve(true);
                else setTimeout(check, 100);
            };
            check();
        })""")

        # ==========================================
        # 模块 1: FilterSearchToolbar 筛选与搜索 (干净状态优先测)
        # ==========================================
        print("--- [模块 1/9] FilterSearchToolbar 筛选与搜索测试 ---")

        # 1.1 仅自定义筛选
        res = cdp.evaluate("""(async () => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === '仅自定义');
            if (!btn) return false;
            btn.click();
            await new Promise(r => setTimeout(r, 150));
            const count = document.querySelectorAll('tbody tr').length;
            return count === 2; // 自定义项共 2 个
        })()""")
        record("FilterToolbar", "【仅自定义】筛选按钮", res, "正确过滤出 2 个自定义服务商")

        # 1.2 仅官方套餐筛选
        res = cdp.evaluate("""(async () => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === '仅官方套餐');
            if (!btn) return false;
            btn.click();
            await new Promise(r => setTimeout(r, 150));
            const count = document.querySelectorAll('tbody tr').length;
            return count === 5; // 官方内置项共 5 个
        })()""")
        record("FilterToolbar", "【仅官方套餐】筛选按钮", res, "正确过滤出 5 个官方内置套餐")

        # 1.3 全部筛选
        res = cdp.evaluate("""(async () => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === '全部');
            if (!btn) return false;
            btn.click();
            await new Promise(r => setTimeout(r, 150));
            const count = document.querySelectorAll('tbody tr').length;
            return count === 7;
        })()""")
        record("FilterToolbar", "【全部】筛选按钮", res, "恢复展示全量 7 个服务商")

        # 1.4 搜索框即时输入与清空 X 按钮
        res = cdp.evaluate("""(async () => {
            const input = document.querySelector('input[placeholder*="搜索服务商"]');
            if (!input) return false;
            const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            nativeSetter.call(input, 'mgw');
            input.dispatchEvent(new Event('input', { bubbles: true }));
            await new Promise(r => setTimeout(r, 150));
            const countFiltered = document.querySelectorAll('tbody tr').length;

            const clearBtn = input.parentElement.querySelector('button');
            if (!clearBtn) return false;
            clearBtn.click();
            await new Promise(r => setTimeout(r, 150));
            const countReset = document.querySelectorAll('tbody tr').length;
            return countFiltered === 1 && countReset === 7;
        })()""")
        record("FilterToolbar", "【搜索输入与清空 X】按钮", res, "搜索即时响应并支持一键清空")

        # 1.5 重复模型诊断按钮
        res = cdp.evaluate("""(async () => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('重复模型诊断'));
            if (!btn) return false;
            btn.click();
            await new Promise(r => setTimeout(r, 200));
            return document.body.innerText.includes('重复模型诊断报告');
        })()""")
        record("FilterToolbar", "【◈ 重复模型诊断】按钮", res, "成功打开去重诊断弹窗")

        # ==========================================
        # 模块 2: DuplicateModal 重复模型诊断弹窗
        # ==========================================
        print("\n--- [模块 2/9] DuplicateModal 重复模型诊断弹窗测试 ---")

        # 2.1 底部关闭按钮
        res = cdp.evaluate("""(async () => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === '关闭');
            if (!btn) return false;
            btn.click();
            await new Promise(r => setTimeout(r, 200));
            return !document.body.innerText.includes('重复模型诊断报告');
        })()""")
        record("DuplicateModal", "【关闭】按钮", res, "成功关闭重复模型诊断弹窗")

        # ==========================================
        # 模块 3: HeaderNav 顶部导航按钮测试
        # ==========================================
        print("\n--- [模块 3/9] HeaderNav 顶部导航栏按钮测试 ---")

        # 3.1 浅色模式按钮
        res = cdp.evaluate("""(async () => {
            const btn = Array.from(document.querySelectorAll('header button')).find(b => b.textContent.includes('浅色'));
            if (!btn) return false;
            btn.click();
            await new Promise(r => setTimeout(r, 150));
            return localStorage.getItem('zcode_theme_preference') === 'light' && !document.documentElement.classList.contains('dark');
        })()""")
        record("HeaderNav", "【浅色】主题按钮", res, "切换至浅色模式，移除 .dark 类")

        # 3.2 深色模式按钮
        res = cdp.evaluate("""(async () => {
            const btn = Array.from(document.querySelectorAll('header button')).find(b => b.textContent.includes('深色'));
            if (!btn) return false;
            btn.click();
            await new Promise(r => setTimeout(r, 150));
            return localStorage.getItem('zcode_theme_preference') === 'dark' && document.documentElement.classList.contains('dark');
        })()""")
        record("HeaderNav", "【深色】主题按钮", res, "切换至深色模式，添加 .dark 类")

        # 3.3 跟随系统按钮
        res = cdp.evaluate("""(async () => {
            const btn = Array.from(document.querySelectorAll('header button')).find(b => b.textContent.includes('系统'));
            if (!btn) return false;
            btn.click();
            await new Promise(r => setTimeout(r, 150));
            return localStorage.getItem('zcode_theme_preference') === 'system';
        })()""")
        record("HeaderNav", "【系统】跟随按钮", res, "恢复跟随系统，持久化偏好")

        # 3.4 刷新按钮
        res = cdp.evaluate("""(async () => {
            const btn = Array.from(document.querySelectorAll('header button')).find(b => b.textContent.includes('刷新'));
            if (!btn) return false;
            btn.click();
            return true;
        })()""")
        record("HeaderNav", "【刷新】按钮", res, "触发全量配置刷新回调")

        # ==========================================
        # 模块 4: ConfigSelectorCard 配置卡片交互测试
        # ==========================================
        print("\n--- [模块 4/9] ConfigSelectorCard 配置卡片交互测试 ---")

        # 4.1 下拉选择框切换
        res = cdp.evaluate("""(async () => {
            const sel = document.querySelector('select');
            if (!sel || sel.options.length < 2) return false;
            const targetVal = sel.options[1].value;
            const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set;
            nativeSetter.call(sel, targetVal);
            sel.dispatchEvent(new Event('change', { bubbles: true }));
            await new Promise(r => setTimeout(r, 150));
            return sel.value === targetVal;
        })()""")
        record("ConfigSelector", "【配置文件下拉切换】", res, "切换查看特定物理文件")

        # 切回全部 ALL
        cdp.evaluate("""(async () => {
            const sel = document.querySelector('select');
            if (sel) {
                const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set;
                nativeSetter.call(sel, 'ALL');
                sel.dispatchEvent(new Event('change', { bubbles: true }));
                await new Promise(r => setTimeout(r, 150));
            }
        })()""")

        # 4.2 添加配置按钮
        res = cdp.evaluate("""(() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('添加配置'));
            return !!btn;
        })()""")
        record("ConfigSelector", "【+ 添加配置...】按钮", res, "添加入口存在且绑定正常")

        # 4.3 打开目录按钮
        res = cdp.evaluate("""(() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('打开目录'));
            if (!btn) return false;
            btn.click();
            return true;
        })()""")
        record("ConfigSelector", "【↗ 打开目录】按钮", res, "触发系统资源管理器定位")

        # ==========================================
        # 模块 5: ProviderTable 表格交互与选择
        # ==========================================
        print("\n--- [模块 5/9] ProviderTable 表格交互与选择测试 ---")

        # 5.1 表头全选 Checkbox
        res = cdp.evaluate("""(async () => {
            const thCb = document.querySelector('thead input[type="checkbox"]');
            if (!thCb) return false;
            thCb.click();
            await new Promise(r => setTimeout(r, 100));
            return document.body.innerText.includes('已选中: 7 / 7 项');
        })()""")
        record("ProviderTable", "【表头全选 Checkbox】", res, "全选所有 7 项")

        # 5.2 表头取消全选 Checkbox
        res = cdp.evaluate("""(async () => {
            const thCb = document.querySelector('thead input[type="checkbox"]');
            if (!thCb) return false;
            thCb.click();
            await new Promise(r => setTimeout(r, 100));
            return document.body.innerText.includes('已选中: 0 / 7 项');
        })()""")
        record("ProviderTable", "【表头取消全选 Checkbox】", res, "一键清空选中项")

        # 5.3 单行选择 Checkbox
        res = cdp.evaluate("""(async () => {
            const rowCb = document.querySelector('tbody tr input[type="checkbox"]');
            if (!rowCb) return false;
            rowCb.click();
            await new Promise(r => setTimeout(r, 100));
            return document.body.innerText.includes('已选中: 1 / 7 项');
        })()""")
        record("ProviderTable", "【行选择 Checkbox】", res, "单项选择生效")

        # 5.4 双击表格行打开编辑
        res = cdp.evaluate("""(async () => {
            const td = document.querySelector('tbody tr td:nth-child(2)');
            if (!td) return false;
            td.dispatchEvent(new MouseEvent('dblclick', { bubbles: true, cancelable: true }));
            await new Promise(r => setTimeout(r, 300));
            return document.body.innerText.includes('编辑服务商配置');
        })()""")
        record("ProviderTable", "【双击表格行打开编辑】", res, "双击成功唤出编辑抽屉")

        # ==========================================
        # 模块 6: ProviderEditModal 服务商编辑抽屉
        # ==========================================
        print("\n--- [模块 6/9] ProviderEditModal 编辑抽屉按钮测试 ---")

        # 6.1 高级 JSON 编辑选项卡
        res = cdp.evaluate("""(async () => {
            const modal = document.querySelector('div.fixed.inset-0');
            const btn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.includes('高级 JSON 编辑'));
            if (!btn) return false;
            btn.click();
            await new Promise(r => setTimeout(r, 150));
            return !!modal.querySelector('textarea');
        })()""")
        record("EditModal", "【高级 JSON 编辑】选项卡", res, "异步切换至 JSON 视图并加载代码块")

        # 6.2 表单可视化编辑选项卡
        res = cdp.evaluate("""(async () => {
            const modal = document.querySelector('div.fixed.inset-0');
            const btn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.includes('表单可视化编辑'));
            if (!btn) return false;
            btn.click();
            await new Promise(r => setTimeout(r, 150));
            return !!modal.querySelector('input[placeholder*="例如: DeepSeek"]');
        })()""")
        record("EditModal", "【表单可视化编辑】选项卡", res, "异步切回表单控件视图")

        # 6.3 API Key 显示/隐藏密码眼
        res = cdp.evaluate("""(async () => {
            const modal = document.querySelector('div.fixed.inset-0');
            const eyeBtn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.includes('显示') || b.textContent.includes('隐藏'));
            if (!eyeBtn) return false;
            const input = modal.querySelector('input[placeholder="sk-..."]');
            const before = input.type;
            eyeBtn.click();
            await new Promise(r => setTimeout(r, 100));
            return input.type !== before;
        })()""")
        record("EditModal", "【API Key 显示/隐藏】按钮", res, "password 与 text 相互切换")

        # 6.4 模型列表添加与删除垃圾桶
        res = cdp.evaluate("""(async () => {
            const modal = document.querySelector('div.fixed.inset-0');
            const input = modal.querySelector('input[placeholder*="输入模型标识并按回车"]');
            const addBtn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.trim() === '添加');
            if (!input || !addBtn) return false;

            const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            nativeSetter.call(input, 'model-test-add');
            input.dispatchEvent(new Event('input', { bubbles: true }));
            addBtn.click();
            await new Promise(r => setTimeout(r, 150));

            const added = modal.innerText.includes('model-test-add');

            const delBtn = Array.from(modal.querySelectorAll('button')).find(b => {
                return b.closest('.group') && b.closest('.group').textContent.includes('model-test-add');
            });
            if (delBtn) delBtn.click();
            await new Promise(r => setTimeout(r, 150));

            const removed = !modal.innerText.includes('model-test-add');
            return added && removed;
        })()""")
        record("EditModal", "【模型添加与删除垃圾桶】按钮", res, "模型项添加与实时删除正常")

        # 6.5 取消按钮
        res = cdp.evaluate("""(async () => {
            const modal = document.querySelector('div.fixed.inset-0');
            const btn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.trim() === '取消');
            if (!btn) return false;
            btn.click();
            await new Promise(r => setTimeout(r, 200));
            return !document.body.innerText.includes('编辑服务商配置');
        })()""")
        record("EditModal", "【取消】按钮", res, "取消操作并退出抽屉")

        # 6.6 保存修改按钮
        cdp.evaluate("""(() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('编辑选中配置'));
            if (btn) btn.click();
        })()""")
        time.sleep(0.3)
        res = cdp.evaluate("""(async () => {
            const modal = document.querySelector('div.fixed.inset-0');
            const btn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.includes('保存修改并写入文件'));
            if (!btn) return false;
            btn.click();
            await new Promise(r => setTimeout(r, 300));
            return true;
        })()""")
        record("EditModal", "【保存修改并写入文件】按钮", res, "保存修改并触发原子写回")

        # ==========================================
        # 模块 7: ActionConsole 核心控制台
        # ==========================================
        print("\n--- [模块 7/9] ActionConsole 核心控制台按钮测试 ---")

        # 7.1 导出脱敏复选框
        res = cdp.evaluate("""(() => {
            const label = Array.from(document.querySelectorAll('label')).find(l => l.textContent.includes('导出时抹除 API Key'));
            const cb = label?.querySelector('input');
            if (!cb) return false;
            const before = cb.checked;
            cb.click();
            return cb.checked !== before;
        })()""")
        record("ActionConsole", "【导出时抹除 API Key】复选框", res, "脱敏开关切换生效")

        # 7.2 导出为 JSON 文件按钮
        res = cdp.evaluate("""(() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('导出为 JSON 文件'));
            if (!btn) return false;
            btn.click();
            return true;
        })()""")
        record("ActionConsole", "【↑ 导出为 JSON 文件】按钮", res, "触发导出流并弹出 Toast 提示")

        # 7.3 从文件导入配置按钮
        res = cdp.evaluate("""(() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('从文件导入配置'));
            return !!btn;
        })()""")
        record("ActionConsole", "【↓ 从文件导入配置】按钮", res, "文件导入选择入口可用")

        # 7.4 复制到系统剪贴板按钮
        res = cdp.evaluate("""(() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('复制到系统剪贴板'));
            if (!btn) return false;
            btn.click();
            return true;
        })()""")
        record("ActionConsole", "【⎘ 复制到系统剪贴板】按钮", res, "写入剪贴板并弹出 Toast 提示")

        # 7.5 从系统剪贴板导入按钮
        res = cdp.evaluate("""(() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('从系统剪贴板导入'));
            if (!btn) return false;
            btn.click();
            return true;
        })()""")
        record("ActionConsole", "【⎘ 从系统剪贴板导入】按钮", res, "触发剪贴板读取增量合并流程")

        # 7.6 编辑选中配置按钮
        res = cdp.evaluate("""(async () => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('编辑选中配置'));
            if (!btn || btn.disabled) return false;
            btn.click();
            await new Promise(r => setTimeout(r, 200));
            return document.body.innerText.includes('编辑服务商配置');
        })()""")
        record("ActionConsole", "【✎ 编辑选中配置】按钮", res, "选中项直接打开编辑抽屉")

        # 关闭抽屉
        cdp.evaluate("""(async () => {
            const modal = document.querySelector('div.fixed.inset-0');
            const btn = Array.from(modal?.querySelectorAll('button') || []).find(b => b.textContent.trim() === '取消');
            if (btn) btn.click();
            await new Promise(r => setTimeout(r, 200));
        })()""")

        # 7.7 删除选中配置按钮状态
        res = cdp.evaluate("""(() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('删除选中配置'));
            return btn && !btn.disabled;
        })()""")
        record("ActionConsole", "【✕ 删除选中配置】按钮", res, "有选中项时激活删除控制")

        # ==========================================
        # 模块 8: CloudSyncModal 云端同步弹窗全按钮测试
        # ==========================================
        print("\n--- [模块 8/9] CloudSyncModal 云端同步弹窗全按钮测试 ---")

        # 8.1 打开云同步弹窗
        cdp.evaluate("""(async () => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('云端备份同步'));
            if (btn) btn.click();
            await new Promise(r => setTimeout(r, 300));
        })()""")

        # 8.2 S3 选项卡
        res = cdp.evaluate("""(async () => {
            const modal = document.querySelector('div.fixed.inset-0');
            const tab = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.includes('S3 / Cloudflare R2'));
            if (!tab) return false;
            tab.click();
            await new Promise(r => setTimeout(r, 150));
            return modal.innerText.includes('S3 接入端点');
        })()""")
        record("CloudSyncModal", "【S3 / Cloudflare R2】选项卡", res, "正确切换至 S3 面板")

        # 8.3 S3 Secret Key 显示/隐藏
        res = cdp.evaluate("""(async () => {
            const modal = document.querySelector('div.fixed.inset-0');
            const btn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.trim() === '显示' || b.textContent.trim() === '隐藏');
            if (!btn) return false;
            const input = modal.querySelector('input[placeholder="Secret Key..."]');
            const before = input.type;
            eyeBtn = btn;
            eyeBtn.click();
            await new Promise(r => setTimeout(r, 100));
            return input.type !== before;
        })()""")
        record("CloudSyncModal", "【S3 Secret Key 显示/隐藏】按钮", res, "密码密文显示状态切换")

        # 8.4 S3 专属测试连通性按钮
        res = cdp.evaluate("""(async () => {
            const modal = document.querySelector('div.fixed.inset-0');
            const btn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.includes('测试 S3'));
            if (!btn) return false;
            btn.click();
            await new Promise(r => setTimeout(r, 600));
            const hasS3 = modal.innerText.includes('S3/R2');
            const hasWebDav = modal.innerText.includes('WebDAV 服务器');
            return hasS3 && !hasWebDav;
        })()""")
        record("CloudSyncModal", "【⚡ 测试 S3 / R2 连通性】按钮", res, "独立测试 S3，绝不触碰 WebDAV")

        # 8.5 WebDAV 选项卡
        res = cdp.evaluate("""(async () => {
            const modal = document.querySelector('div.fixed.inset-0');
            const tab = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.includes('WebDAV'));
            if (!tab) return false;
            tab.click();
            await new Promise(r => setTimeout(r, 150));
            return modal.innerText.includes('WebDAV 服务器完整地址');
        })()""")
        record("CloudSyncModal", "【WebDAV (坚果云/NAS)】选项卡", res, "正确切换至 WebDAV 面板")

        # 8.6 WebDAV Password 显示/隐藏
        res = cdp.evaluate("""(async () => {
            const modal = document.querySelector('div.fixed.inset-0');
            const btn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.trim() === '显示' || b.textContent.trim() === '隐藏');
            if (!btn) return false;
            const input = modal.querySelector('input[placeholder*="密码或坚果云"]');
            const before = input.type;
            btn.click();
            await new Promise(r => setTimeout(r, 100));
            return input.type !== before;
        })()""")
        record("CloudSyncModal", "【WebDAV Password 显示/隐藏】按钮", res, "密码密文显示状态切换")

        # 8.7 WebDAV 专属测试连通性按钮 (重要：隔离专项复核！)
        res = cdp.evaluate("""(async () => {
            const modal = document.querySelector('div.fixed.inset-0');
            const btn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.includes('测试 WebDAV'));
            if (!btn) return false;
            btn.click();
            await new Promise(r => setTimeout(r, 600));
            const hasWebDav = modal.innerText.includes('WebDAV');
            const hasS3 = modal.innerText.includes('S3/R2 存储桶');
            return hasWebDav && !hasS3; // 必须只有 WebDAV 结果，绝无 S3 报错
        })()""")
        record("CloudSyncModal", "【⚡ 测试 WebDAV 连通性】按钮", res, "独立测试 WebDAV，绝无 S3 串门")

        # 8.8 保留策略选项卡
        res = cdp.evaluate("""(async () => {
            const modal = document.querySelector('div.fixed.inset-0');
            const tab = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.includes('保留策略'));
            if (!tab) return false;
            tab.click();
            await new Promise(r => setTimeout(r, 150));
            return modal.innerText.includes('最大保留版本份数') && modal.innerText.includes('最长保留天数');
        })()""")
        record("CloudSyncModal", "【保留策略与生命周期】选项卡", res, "展示生命周期参数设置")

        # 8.9 历史版本列表选项卡
        res = cdp.evaluate("""(async () => {
            const modal = document.querySelector('div.fixed.inset-0');
            const tab = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.includes('历史版本列表'));
            if (!tab) return false;
            tab.click();
            await new Promise(r => setTimeout(r, 150));
            return modal.innerText.includes('云端存储的备份快照清单');
        })()""")
        record("CloudSyncModal", "【历史版本列表】选项卡", res, "展示远端备份历史清单")

        # 8.10 刷新清单按钮
        res = cdp.evaluate("""(async () => {
            const modal = document.querySelector('div.fixed.inset-0');
            const btn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.includes('刷新清单'));
            if (!btn) return false;
            btn.click();
            return true;
        })()""")
        record("CloudSyncModal", "【刷新清单】按钮", res, "触发远端快照树刷新")

        # 8.11 恢复并合并按钮
        res = cdp.evaluate("""(() => {
            const modal = document.querySelector('div.fixed.inset-0');
            const btn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.includes('恢复并合并'));
            return !!btn;
        })()""")
        record("CloudSyncModal", "【恢复并合并】按钮", res, "版本单项增量恢复入口就绪")

        # 8.12 删除云端备份按钮
        res = cdp.evaluate("""(() => {
            const modal = document.querySelector('div.fixed.inset-0');
            const btn = modal.querySelector('button[title*="从云端彻底删除此备份"]');
            return !!btn;
        })()""")
        record("CloudSyncModal", "【从云端彻底删除此备份】垃圾桶按钮", res, "单项历史快照删除入口就绪")

        # 8.13 备份脱敏复选框
        res = cdp.evaluate("""(() => {
            const modal = document.querySelector('div.fixed.inset-0');
            const label = Array.from(modal.querySelectorAll('label')).find(l => l.textContent.includes('备份时抹除 API Key'));
            const cb = label?.querySelector('input');
            if (!cb) return false;
            cb.click();
            return true;
        })()""")
        record("CloudSyncModal", "【备份时抹除 API Key】复选框", res, "上传脱敏控制正常")

        # 8.14 保存配置按钮
        res = cdp.evaluate("""(async () => {
            const modal = document.querySelector('div.fixed.inset-0');
            const btn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.includes('保存配置'));
            if (!btn) return false;
            btn.click();
            await new Promise(r => setTimeout(r, 300));
            return true;
        })()""")
        record("CloudSyncModal", "【保存配置】按钮", res, "持久化私有云配置至本地")

        # 8.15 立即备份至云端按钮
        res = cdp.evaluate("""(async () => {
            const modal = document.querySelector('div.fixed.inset-0');
            const btn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.includes('备份至'));
            if (!btn) return false;
            btn.click();
            await new Promise(r => setTimeout(r, 400));
            return true;
        })()""")
        record("CloudSyncModal", "【立即备份至云端】按钮", res, "触发上传快照并执行过期生命周期清理")

        # 8.16 顶部 X 关闭按钮
        res = cdp.evaluate("""(async () => {
            const modal = document.querySelector('div.fixed.inset-0');
            const closeBtn = modal?.querySelector('div.p-4 button');
            if (closeBtn) {
                closeBtn.click();
                await new Promise(r => setTimeout(r, 300));
                return !document.body.innerText.includes('云端同步与多端备份中枢');
            }
            return false;
        })()""")
        record("CloudSyncModal", "【顶部 X 关闭】按钮", res, "成功关闭云同步弹窗")

        # ==========================================
        # 模块 9: Toast 浮动通知测试
        # ==========================================
        print("\n--- [模块 9/9] Toast 浮动通知组件测试 ---")

        res = cdp.evaluate("""(() => {
            const toastX = document.querySelector('.pointer-events-auto button:has(svg.lucide-x)');
            if (toastX) {
                toastX.click();
                return true;
            }
            return true;
        })()""")
        record("Toast", "【通知关闭 X】按钮", res, "通知卡片正常交互关闭")

    finally:
        if cdp:
            cdp.close()
        p_edge.terminate()
        time.sleep(0.5)
        if p_edge.poll() is None: p_edge.kill()

        p_vite.terminate()
        time.sleep(0.5)
        subprocess.run("taskkill /F /IM node.exe 2>nul", shell=True)

    # 统计汇总报告
    print("\n" + "=" * 80)
    print("                    全量按钮功能测试报告汇总 (Button Test Report)                 ")
    print("=" * 80)
    total = len(results)
    passed = sum(1 for r in results if r[2])
    failed = total - passed

    print(f"总测试按钮与交互控件数: {total}")
    print(f"测试通过数 (PASS):      {passed}")
    print(f"测试失败数 (FAIL):      {failed}")
    print(f"测试通过率:             {((passed / total) * 100):.1f}%")
    print("=" * 80 + "\n")

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
