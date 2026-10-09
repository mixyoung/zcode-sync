#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZCode 跨平台路径探测器 (Path Detector)
自动探测各操作系统 (Windows / Linux / macOS) 下 ZCode 模型配置文件的真实落盘路径。
支持扫描系统上全部存在的配置文件（包括 provider_config.json 与经典 config.json）并提取元数据。
"""

import os
import json
import datetime
import platform
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

class ConfigFileInfo:
    """配置文件元数据信息对象"""
    def __init__(self, path: Path, label: str):
        self.path = path.resolve()
        self.label = label
        self.exists = self.path.exists() and self.path.is_file()
        self.provider_count = 0
        self.custom_count = 0
        self.size_bytes = 0
        self.updated_at = ""
        self.schema_type = "config"  # "config" 或 "provider_config"
        self.load_metadata()

    def load_metadata(self):
        if not self.exists:
            return
        try:
            stat = self.path.stat()
            self.size_bytes = stat.st_size
            dt = datetime.datetime.fromtimestamp(stat.st_mtime)
            self.updated_at = dt.strftime("%Y-%m-%d %H:%M:%S")

            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 模式 1: 经典 config.json ({"provider": {...}})
            if "provider" in data and isinstance(data["provider"], dict):
                self.schema_type = "config"
                provs = data["provider"]
                self.provider_count = len(provs)
                for pid, pdata in provs.items():
                    if isinstance(pdata, dict):
                        is_custom = pdata.get("source") == "custom" and not pid.startswith("builtin:")
                        if is_custom:
                            self.custom_count += 1
            # 模式 2: 新版 provider_config.json ({"schemaVersion": 1, "config": {"providerConfigRules": ...}})
            elif "config" in data and isinstance(data["config"], dict):
                self.schema_type = "provider_config"
                p_rules = data["config"].get("providerConfigRules", {}).get("providerRules", [])
                if isinstance(p_rules, list):
                    self.provider_count = len(p_rules)
                    for rule in p_rules:
                        if isinstance(rule, dict):
                            pid = rule.get("providerId", "")
                            group = rule.get("config", {}).get("group", "")
                            is_custom = group == "standard-personal" or not str(pid).startswith("account:")
                            if is_custom:
                                self.custom_count += 1
        except Exception:
            pass

    def get_display_name(self) -> str:
        """用于下拉列表展示的友好名称"""
        return f"{self.label} ({self.provider_count}个服务商, {self.custom_count}个自定义) - {self.path.name}"

class PathDetector:
    """负责跨平台定位、探测与多配置文件发现"""

    @staticmethod
    def get_system_name() -> str:
        """获取规范化系统名称"""
        sys_name = platform.system()
        if sys_name == "Darwin":
            return "macOS"
        return sys_name

    @classmethod
    def get_candidate_locations(cls) -> List[Tuple[Path, str]]:
        """获取所有潜在的探测位置与标签说明，覆盖 provider_config.json 与 config.json"""
        locs: List[Tuple[Path, str]] = []

        # 1. 环境变量 ZCODE_DATA_BASE_DIR
        data_base = os.environ.get("ZCODE_DATA_BASE_DIR")
        if data_base and data_base.strip():
            p = Path(data_base.strip()).expanduser()
            locs.append((p / ".zcode" / "v2" / "provider_config.json", "活跃核心服务商配置 (provider_config.json)"))
            locs.append((p / ".zcode" / "v2" / "config.json", "活跃经典配置 (config.json)"))
            locs.append((p / "v2" / "provider_config.json", "数据目录 v2 (provider_config.json)"))
            locs.append((p / "v2" / "config.json", "数据目录 v2 (config.json)"))
            locs.append((p / "provider_config.json", "数据根目录 (provider_config.json)"))
            locs.append((p / "config.json", "数据根目录 (config.json)"))

        # 2. 环境变量 ZCODE_HOME
        zcode_home = os.environ.get("ZCODE_HOME")
        if zcode_home and zcode_home.strip():
            p = Path(zcode_home.strip()).expanduser()
            locs.append((p / "v2" / "provider_config.json", "ZCODE_HOME (provider_config.json)"))
            locs.append((p / "v2" / "config.json", "ZCODE_HOME (config.json)"))
            locs.append((p / "provider_config.json", "ZCODE_HOME (provider_config.json)"))
            locs.append((p / "config.json", "ZCODE_HOME (config.json)"))

        # 3. 常见 Windows 固定数据目录
        if platform.system() == "Windows":
            locs.append((Path("D:/program_files/zcode_data/.zcode/v2/provider_config.json"), "核心服务商配置 (D:/zcode_data/provider_config.json)"))
            locs.append((Path("D:/program_files/zcode_data/.zcode/v2/config.json"), "固定数据目录 (D:/zcode_data/config.json)"))

        # 4. 操作系统标准用户家目录
        home = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or "~").expanduser()
        locs.append((home / ".zcode" / "v2" / "provider_config.json", "标准用户家目录 (provider_config.json)"))
        locs.append((home / ".zcode" / "v2" / "config.json", "标准用户家目录 (~/.zcode/config.json)"))

        return locs

    @classmethod
    def discover_all_configs(cls, extra_paths: Optional[List[str]] = None) -> List[ConfigFileInfo]:
        """
        全量扫描并返回所有实际存在的有效配置文件列表 (去重)
        """
        results: List[ConfigFileInfo] = []
        seen_resolved = set()

        # 预设候选位置
        for path_obj, label in cls.get_candidate_locations():
            resolved = path_obj.resolve()
            if path_obj.exists() and path_obj.is_file() and resolved not in seen_resolved:
                seen_resolved.add(resolved)
                results.append(ConfigFileInfo(path_obj, label))

        # 用户手动添加过的额外路径
        if extra_paths:
            for ep in extra_paths:
                p = Path(ep.strip()).expanduser()
                resolved = p.resolve()
                if p.exists() and p.is_file() and resolved not in seen_resolved:
                    seen_resolved.add(resolved)
                    results.append(ConfigFileInfo(p, "用户手动指定"))

        return results

    @classmethod
    def detect(cls, override_path: Optional[str] = None) -> Tuple[Path, bool, str]:
        """单文件探测兼容接口"""
        if override_path:
            p = Path(override_path).expanduser().resolve()
            return p, p.exists() and p.is_file(), f"用户显式指定: {p}"

        all_found = cls.discover_all_configs()
        if all_found:
            first = all_found[0]
            return first.path, True, f"已自动发现: {first.label}"

        fallback = cls.get_default_config_path()
        return fallback, fallback.exists() and fallback.is_file(), f"默认路径: {fallback}"

    @classmethod
    def get_default_config_path(cls) -> Path:
        """获取系统默认配置文件路径"""
        home = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or "~").expanduser()
        return home / ".zcode" / "v2" / "config.json"
