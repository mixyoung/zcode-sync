#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZCode 模型同步核心引擎 (Sync Engine) - 双 Schema 兼容版
支持经典 config.json ({"provider": {...}}) 与
ZCode 现代核心 provider_config.json ({"schemaVersion": 1, "config": {"providerConfigRules": ...}})
的双向解析、安全备份、增量合并、API Key 脱敏、单项编辑及精准原路写回。
"""

import json
import copy
import shutil
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

class SyncEngine:
    """负责所有模型配置数据处理与安全读写 (支持全量版本 Schema 1 & Schema 2)"""

    @staticmethod
    def load_config(cfg_path: Path) -> Tuple[bool, str, Dict[str, Any]]:
        """读取完整原始配置文件"""
        if not cfg_path.exists():
            return False, f"文件不存在: {cfg_path}", {}

        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return False, "配置文件格式错误，根节点非 JSON Object", {}
            return True, "读取成功", data
        except json.JSONDecodeError as e:
            return False, f"JSON 语法解析错误: {e}", {}
        except Exception as e:
            return False, f"读取失败: {e}", {}

    @classmethod
    def load_providers(cls, cfg_path: Path) -> Tuple[bool, str, Dict[str, Any]]:
        """提取单个配置文件的所有 provider 节点，自动识别 Schema 1 与 Schema 2"""
        success, msg, full_cfg = cls.load_config(cfg_path)
        if not success:
            return False, msg, {}

        # 模式 1: 经典 config.json ({"provider": {...}})
        if "provider" in full_cfg and isinstance(full_cfg["provider"], dict):
            return True, "获取成功", full_cfg["provider"]

        # 模式 2: ZCode 新版核心配置 provider_config.json
        if "config" in full_cfg and isinstance(full_cfg["config"], dict):
            cfg_obj = full_cfg["config"]
            p_rules = cfg_obj.get("providerConfigRules", {}).get("providerRules", [])
            m_rules = cfg_obj.get("modelConfigRules", {}).get("providerModelRules", [])

            # 构建 modelId 对应限制映射
            model_limits = {}
            if isinstance(m_rules, list):
                for mr in m_rules:
                    if isinstance(mr, dict) and "modelId" in mr:
                        model_limits[mr["modelId"]] = mr.get("config", {})

            providers: Dict[str, Any] = {}
            if isinstance(p_rules, list):
                for rule in p_rules:
                    if not isinstance(rule, dict):
                        continue
                    pid = rule.get("providerId", "")
                    if not pid:
                        continue
                    pname = rule.get("providerName", pid)
                    c = rule.get("config", {})
                    group = c.get("group", "")
                    is_custom = group == "standard-personal" or not str(pid).startswith("account:")

                    access = c.get("access", {})
                    api = c.get("api", {})
                    models_list = c.get("personalModelIds") or c.get("modelOrder") or []

                    models_dict = {}
                    for mid in models_list:
                        m_cfg = model_limits.get(mid, {})
                        prop = m_cfg.get("properties", {})
                        opt = m_cfg.get("optionSpecs", {})
                        ctx = prop.get("contextWindow", 128000)
                        out = opt.get("maxOutputTokens", {}).get("max", 8192)
                        reasoning = prop.get("supportsMidConversationSystem", False)
                        models_dict[mid] = {
                            "name": mid,
                            "limit": {"context": ctx, "output": out},
                            "reasoning": {"enabled": reasoning}
                        }

                    providers[pid] = {
                        "name": pname,
                        "kind": api.get("type", "anthropic-messages"),
                        "enabled": True,
                        "source": "custom" if is_custom else "builtin",
                        "options": {
                            "apiKey": access.get("apiKey", ""),
                            "baseURL": api.get("baseUrl", "")
                        },
                        "models": models_dict,
                        "_schema": "provider_config",
                        "_raw_rule": rule
                    }
                return True, "获取成功", providers

        return False, "未能识别配置文件格式", {}

    @classmethod
    def load_all_providers_with_meta(
        cls,
        config_files: List[Any]
    ) -> List[Dict[str, Any]]:
        """从多个配置文件中读取并聚合全部服务商，附加来源元数据"""
        items: List[Dict[str, Any]] = []
        for cinfo in config_files:
            cfg_p = cinfo.path if hasattr(cinfo, "path") else Path(cinfo)
            cfg_label = cinfo.label if hasattr(cinfo, "label") else cfg_p.name
            ok, _, providers = cls.load_providers(cfg_p)
            if not ok:
                continue

            for pid, pdata in providers.items():
                if not isinstance(pdata, dict):
                    continue
                is_custom = pdata.get("source") == "custom" and not pid.startswith("builtin:") and not pid.startswith("account:")
                items.append({
                    "provider_id": pid,
                    "name": pdata.get("name", pid),
                    "kind": pdata.get("kind", "-"),
                    "models": list(pdata.get("models", {}).keys()),
                    "enabled": pdata.get("enabled", True),
                    "is_custom": is_custom,
                    "source_file": cfg_p,
                    "source_label": cfg_label,
                    "raw_data": copy.deepcopy(pdata)
                })
        return items

    @staticmethod
    def analyze_duplicate_models(items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, str]]]:
        """统计分析在多个服务商或多个配置文件中重复出现的模型"""
        model_map: Dict[str, List[Dict[str, str]]] = {}
        for item in items:
            for m in item.get("models", []):
                if m not in model_map:
                    model_map[m] = []
                model_map[m].append({
                    "provider": item["name"],
                    "provider_id": item["provider_id"],
                    "file": str(item["source_file"]),
                    "label": item["source_label"],
                    "is_custom": item["is_custom"]
                })
        duplicates = {m: occurrences for m, occurrences in model_map.items() if len(occurrences) > 1}
        return duplicates

    @staticmethod
    def mask_api_key(provider_obj: Dict[str, Any]) -> Dict[str, Any]:
        """将单个 provider 对象中的 apiKey 字段安全脱敏"""
        cleaned = copy.deepcopy(provider_obj)
        if "options" in cleaned and isinstance(cleaned["options"], dict):
            if "apiKey" in cleaned["options"]:
                cleaned["options"]["apiKey"] = "YOUR_API_KEY_HERE"
        return cleaned

    @classmethod
    def prepare_export_payload(
        cls,
        providers: Dict[str, Any],
        mask_keys: bool = False
    ) -> Dict[str, Any]:
        """准备用于导出的标准 JSON 数据"""
        export_dict: Dict[str, Any] = {}
        for pid, pdata in providers.items():
            item = copy.deepcopy(pdata)
            # 移除内部元标记
            item.pop("_schema", None)
            item.pop("_raw_rule", None)
            if mask_keys:
                item = cls.mask_api_key(item)
            export_dict[pid] = item
        return {"provider": export_dict}

    @staticmethod
    def validate_import_data(raw_data: Any) -> Tuple[bool, str, Dict[str, Any]]:
        """校验待导入数据是否合法"""
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except Exception as e:
                return False, f"JSON 语法解析失败: {e}", {}

        if not isinstance(raw_data, dict):
            return False, "导入数据不是有效的 JSON 字典对象", {}

        # 模式 1: 根为 {"provider": {...}}
        if "provider" in raw_data and isinstance(raw_data["provider"], dict):
            return True, "校验通过", raw_data["provider"]

        # 模式 2: 根即为 providers 字典
        valid_count = 0
        for k, v in raw_data.items():
            if isinstance(v, dict) and ("kind" in v or "models" in v or "name" in v):
                valid_count += 1

        if valid_count > 0:
            return True, "校验通过", raw_data

        return False, "未能识别有效的模型服务商配置内容", {}

    @staticmethod
    def create_backup(target_path: Path) -> Tuple[bool, str, Optional[Path]]:
        """在修改目标文件前自动创建 .bak 历史安全备份"""
        if not target_path.exists():
            return True, "目标文件不存在，无需创建备份", None

        try:
            bak_path = target_path.with_name(f"{target_path.name}.bak")
            shutil.copy2(target_path, bak_path)

            now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            ts_bak = target_path.with_name(f"{target_path.name}.bak.{now_str}")
            shutil.copy2(target_path, ts_bak)

            return True, f"已安全备份至 {bak_path.name}", bak_path
        except Exception as e:
            return False, f"创建备份失败: {e}", None

    @classmethod
    def save_single_provider(
        cls,
        cfg_path: Path,
        provider_id: str,
        updated_provider_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """更新或新增单个 Provider 到指定的配置文件中，兼容 Schema 1 与 Schema 2"""
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        backup_ok, backup_msg, _ = cls.create_backup(cfg_path)
        if not backup_ok:
            return False, f"安全写入中止: {backup_msg}"

        ok, msg, full_cfg = cls.load_config(cfg_path)
        if not ok and cfg_path.exists():
            return False, f"读取原文件失败: {msg}"

        # 判定 Schema 模式
        is_schema_2 = "config" in full_cfg and "providerConfigRules" in full_cfg.get("config", {})

        new_name = updated_provider_data.get("name", provider_id)
        new_kind = updated_provider_data.get("kind", "anthropic-messages")
        opts = updated_provider_data.get("options", {})
        new_key = opts.get("apiKey", "")
        new_url = opts.get("baseURL", "")
        new_models = list(updated_provider_data.get("models", {}).keys())

        if is_schema_2:
            cfg_obj = full_cfg["config"]
            p_rules = cfg_obj.setdefault("providerConfigRules", {}).setdefault("providerRules", [])
            found_rule = None
            for r in p_rules:
                if r.get("providerId") == provider_id:
                    found_rule = r
                    break

            if found_rule:
                found_rule["providerName"] = new_name
                r_cfg = found_rule.setdefault("config", {})
                r_cfg.setdefault("access", {})["apiKey"] = new_key
                r_cfg.setdefault("api", {})["baseUrl"] = new_url
                r_cfg.setdefault("api", {})["type"] = new_kind
                r_cfg["personalModelIds"] = new_models
                r_cfg["modelOrder"] = new_models
            else:
                p_rules.append({
                    "providerId": provider_id,
                    "providerName": new_name,
                    "config": {
                        "group": "standard-personal",
                        "access": {"type": "api-key", "apiKey": new_key},
                        "api": {"type": new_kind, "baseUrl": new_url},
                        "personalModelIds": new_models,
                        "modelOrder": new_models
                    }
                })
                p_order = cfg_obj.setdefault("providerOrder", [])
                if provider_id not in p_order:
                    p_order.append(provider_id)
        else:
            providers = full_cfg.setdefault("provider", {})
            cleaned = copy.deepcopy(updated_provider_data)
            cleaned.pop("_schema", None)
            cleaned.pop("_raw_rule", None)
            providers[provider_id] = cleaned

        tmp_path = cfg_path.with_suffix(".tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(full_cfg, f, indent=2, ensure_ascii=False)
            tmp_path.replace(cfg_path)
            return True, f"成功保存服务商 [{new_name}] 至 {cfg_path.name}"
        except Exception as e:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            return False, f"写回文件失败: {e}"

    @classmethod
    def delete_single_provider(
        cls,
        cfg_path: Path,
        provider_id: str
    ) -> Tuple[bool, str]:
        """从指定的配置文件中删除指定的 Provider，兼容 Schema 1 与 Schema 2"""
        if not cfg_path.exists():
            return False, f"文件不存在: {cfg_path}"

        backup_ok, backup_msg, _ = cls.create_backup(cfg_path)
        if not backup_ok:
            return False, f"删除中止: {backup_msg}"

        ok, msg, full_cfg = cls.load_config(cfg_path)
        if not ok:
            return False, f"读取配置失败: {msg}"

        is_schema_2 = "config" in full_cfg and "providerConfigRules" in full_cfg.get("config", {})

        if is_schema_2:
            cfg_obj = full_cfg["config"]
            p_rules = cfg_obj.get("providerConfigRules", {}).get("providerRules", [])
            cfg_obj["providerConfigRules"]["providerRules"] = [
                r for r in p_rules if r.get("providerId") != provider_id
            ]
            p_order = cfg_obj.get("providerOrder", [])
            cfg_obj["providerOrder"] = [pid for pid in p_order if pid != provider_id]
        else:
            providers = full_cfg.get("provider", {})
            if provider_id not in providers:
                return False, f"服务商 ID 未找到: {provider_id}"
            del providers[provider_id]

        tmp_path = cfg_path.with_suffix(".tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(full_cfg, f, indent=2, ensure_ascii=False)
            tmp_path.replace(cfg_path)
            return True, f"已成功从 {cfg_path.name} 删除服务商 [{provider_id}]"
        except Exception as e:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            return False, f"保存删除变更失败: {e}"

    @classmethod
    def merge_and_save(
        cls,
        cfg_path: Path,
        new_providers: Dict[str, Any]
    ) -> Tuple[bool, str, int]:
        """批量智能增量合并并写回配置文件，兼容 Schema 1 与 Schema 2"""
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        backup_ok, backup_msg, _ = cls.create_backup(cfg_path)
        if not backup_ok:
            return False, f"安全写入中止: {backup_msg}", 0

        current_cfg = {}
        if cfg_path.exists():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    current_cfg = json.load(f)
                if not isinstance(current_cfg, dict):
                    current_cfg = {}
            except Exception:
                current_cfg = {}

        is_schema_2 = "config" in current_cfg and "providerConfigRules" in current_cfg.get("config", {})
        count_updated = 0

        if is_schema_2:
            cfg_obj = current_cfg["config"]
            p_rules = cfg_obj.setdefault("providerConfigRules", {}).setdefault("providerRules", [])
            p_order = cfg_obj.setdefault("providerOrder", [])

            for pid, pdata in new_providers.items():
                pname = pdata.get("name", pid)
                pkind = pdata.get("kind", "anthropic-messages")
                opts = pdata.get("options", {})
                pkey = opts.get("apiKey", "")
                purl = opts.get("baseURL", "")
                pmodels = list(pdata.get("models", {}).keys())

                found_rule = None
                for r in p_rules:
                    if r.get("providerId") == pid:
                        found_rule = r
                        break

                if found_rule:
                    found_rule["providerName"] = pname
                    rcfg = found_rule.setdefault("config", {})
                    rcfg.setdefault("access", {})["apiKey"] = pkey
                    rcfg.setdefault("api", {})["baseUrl"] = purl
                    rcfg.setdefault("api", {})["type"] = pkind
                    rcfg["personalModelIds"] = pmodels
                    rcfg["modelOrder"] = pmodels
                else:
                    p_rules.append({
                        "providerId": pid,
                        "providerName": pname,
                        "config": {
                            "group": "standard-personal",
                            "access": {"type": "api-key", "apiKey": pkey},
                            "api": {"type": pkind, "baseUrl": purl},
                            "personalModelIds": pmodels,
                            "modelOrder": pmodels
                        }
                    })
                    if pid not in p_order:
                        p_order.append(pid)
                count_updated += 1
        else:
            current_providers = current_cfg.setdefault("provider", {})
            for pid, pdata in new_providers.items():
                cleaned = copy.deepcopy(pdata)
                cleaned.pop("_schema", None)
                cleaned.pop("_raw_rule", None)
                current_providers[pid] = cleaned
                count_updated += 1

        tmp_path = cfg_path.with_suffix(".tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(current_cfg, f, indent=2, ensure_ascii=False)
            tmp_path.replace(cfg_path)
            return True, f"成功合并写入 {count_updated} 个模型服务商配置", count_updated
        except Exception as e:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            return False, f"保存写入失败: {e}", 0
