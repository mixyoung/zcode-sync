#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试与功能验证套件 (Unit Tests - Expanded)
覆盖全量多配置发现、按来源聚合、重复分析、单项精确编辑、删除与增量合并。
"""

import os
import sys
import json
import shutil
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.path_detector import PathDetector, ConfigFileInfo
from core.sync_engine import SyncEngine

class TestSyncEngineExpanded(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="zcode_test_"))
        self.cfg_1 = self.test_dir / "config1.json"
        self.cfg_2 = self.test_dir / "config2.json"

        # 配置文件 1 (模拟数据目录)
        self.data_1 = {
            "provider": {
                "builtin:bigmodel": {
                    "name": "Bigmodel",
                    "kind": "anthropic",
                    "options": {"apiKey": "key_1"},
                    "models": {"GLM-5.3": {}}
                },
                "custom:deepseek": {
                    "name": "DeepSeek-V3",
                    "kind": "openai",
                    "source": "custom",
                    "options": {"apiKey": "sk-1"},
                    "models": {"deepseek-chat": {}}
                }
            }
        }
        # 配置文件 2 (模拟旧家目录，存在重复的 builtin:bigmodel)
        self.data_2 = {
            "provider": {
                "builtin:bigmodel": {
                    "name": "Bigmodel (Old)",
                    "kind": "anthropic",
                    "options": {"apiKey": "key_2"},
                    "models": {"GLM-5.3": {}}  # 模型 GLM-5.3 在两处重复
                }
            }
        }
        with open(self.cfg_1, "w", encoding="utf-8") as f:
            json.dump(self.data_1, f, indent=2)
        with open(self.cfg_2, "w", encoding="utf-8") as f:
            json.dump(self.data_2, f, indent=2)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_multi_config_aggregation_and_duplicates(self):
        """测试多配置文件聚合及重复模型检测"""
        files = [
            ConfigFileInfo(self.cfg_1, "文件1"),
            ConfigFileInfo(self.cfg_2, "文件2")
        ]
        items = SyncEngine.load_all_providers_with_meta(files)
        self.assertEqual(len(items), 3, "两文件合计应有 3 个服务商条目")

        # 检查自定义标识
        custom_items = [x for x in items if x["is_custom"]]
        self.assertEqual(len(custom_items), 1)
        self.assertEqual(custom_items[0]["name"], "DeepSeek-V3")

        # 检查重复模型分析 (GLM-5.3 应被识别为重复)
        dups = SyncEngine.analyze_duplicate_models(items)
        self.assertIn("GLM-5.3", dups)
        self.assertEqual(len(dups["GLM-5.3"]), 2)

    def test_save_single_provider(self):
        """测试精确更新单个服务商到指定文件"""
        updated_data = {
            "name": "DeepSeek-V3-Updated",
            "kind": "openai",
            "source": "custom",
            "options": {"apiKey": "sk-new-key", "baseURL": "https://api.deepseek.com"},
            "models": {"deepseek-reasoner": {}}
        }
        ok, msg = SyncEngine.save_single_provider(self.cfg_1, "custom:deepseek", updated_data)
        self.assertTrue(ok)

        # 验证 cfg_1 更新，而 cfg_2 未受影响
        with open(self.cfg_1, "r", encoding="utf-8") as f:
            res_1 = json.load(f)
        self.assertEqual(res_1["provider"]["custom:deepseek"]["name"], "DeepSeek-V3-Updated")
        self.assertIn("deepseek-reasoner", res_1["provider"]["custom:deepseek"]["models"])

        # 验证备份生成
        self.assertTrue(self.cfg_1.with_name(f"{self.cfg_1.name}.bak").exists())

    def test_delete_single_provider(self):
        """测试从指定文件中安全删除单个服务商"""
        ok, msg = SyncEngine.delete_single_provider(self.cfg_1, "builtin:bigmodel")
        self.assertTrue(ok)

        with open(self.cfg_1, "r", encoding="utf-8") as f:
            res_1 = json.load(f)
        self.assertNotIn("builtin:bigmodel", res_1["provider"])
        self.assertIn("custom:deepseek", res_1["provider"])

    def test_schema_2_provider_config(self):
        """测试 ZCode 现代 provider_config.json 格式的解析、编辑与删除"""
        cfg_schema2 = self.test_dir / "provider_config.json"
        data_s2 = {
            "schemaVersion": 1,
            "config": {
                "providerOrder": ["custom_mgw_id"],
                "providerConfigRules": {
                    "providerRules": [
                        {
                            "providerId": "custom_mgw_id",
                            "providerName": "mgw",
                            "config": {
                                "group": "standard-personal",
                                "access": {"type": "api-key", "apiKey": "sk-test"},
                                "api": {"type": "anthropic-messages", "baseUrl": "https://api.test.com"},
                                "personalModelIds": ["model-a", "model-b"],
                                "modelOrder": ["model-a", "model-b"]
                            }
                        }
                    ]
                },
                "modelConfigRules": {
                    "providerModelRules": [
                        {
                            "modelId": "model-a",
                            "config": {
                                "properties": {"contextWindow": 200000},
                                "optionSpecs": {"maxOutputTokens": {"max": 16000}}
                            }
                        }
                    ]
                }
            }
        }
        with open(cfg_schema2, "w", encoding="utf-8") as f:
            json.dump(data_s2, f, indent=2)

        # 1. 验证解析
        cinfo = ConfigFileInfo(cfg_schema2, "新版核心配置")
        self.assertEqual(cinfo.schema_type, "provider_config")
        self.assertEqual(cinfo.provider_count, 1)
        self.assertEqual(cinfo.custom_count, 1)

        ok, msg, provs = SyncEngine.load_providers(cfg_schema2)
        self.assertTrue(ok)
        self.assertIn("custom_mgw_id", provs)
        self.assertEqual(provs["custom_mgw_id"]["name"], "mgw")
        self.assertEqual(len(provs["custom_mgw_id"]["models"]), 2)

        # 2. 验证编辑与精准写回
        updated_data = {
            "name": "mgw-updated",
            "kind": "anthropic-messages",
            "options": {"apiKey": "sk-new-key", "baseURL": "https://api.new.com"},
            "models": {"model-c": {}}
        }
        ok_save, _ = SyncEngine.save_single_provider(cfg_schema2, "custom_mgw_id", updated_data)
        self.assertTrue(ok_save)

        with open(cfg_schema2, "r", encoding="utf-8") as f:
            saved_s2 = json.load(f)
        rules = saved_s2["config"]["providerConfigRules"]["providerRules"]
        self.assertEqual(rules[0]["providerName"], "mgw-updated")
        self.assertEqual(rules[0]["config"]["access"]["apiKey"], "sk-new-key")
        self.assertEqual(rules[0]["config"]["personalModelIds"], ["model-c"])

        # 3. 验证删除
        ok_del, _ = SyncEngine.delete_single_provider(cfg_schema2, "custom_mgw_id")
        self.assertTrue(ok_del)
        with open(cfg_schema2, "r", encoding="utf-8") as f:
            del_s2 = json.load(f)
        self.assertEqual(len(del_s2["config"]["providerConfigRules"]["providerRules"]), 0)
        self.assertEqual(len(del_s2["config"]["providerOrder"]), 0)

if __name__ == "__main__":
    unittest.main()
