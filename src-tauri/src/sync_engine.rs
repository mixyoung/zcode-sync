use std::collections::HashMap;
use std::fs;
use std::path::Path;
use chrono::Local;

use crate::models::{
    DuplicateOccurrence, DuplicateReport, UnifiedProviderItem,
};

pub struct SyncEngine;

impl SyncEngine {
    /// 在写入目标文件前，自动创建 .bak 与时间戳备份
    pub fn create_backup(path: &Path) -> Result<(), String> {
        if !path.exists() {
            return Ok(());
        }

        let file_name = path.file_name().ok_or("无效的文件名")?.to_string_lossy();
        let bak_path = path.with_file_name(format!("{}.bak", file_name));
        let ts = Local::now().format("%Y%m%d_%H%M%S").to_string();
        let ts_bak_path = path.with_file_name(format!("{}.bak.{}", file_name, ts));

        fs::copy(path, &bak_path).map_err(|e| format!("创建标准备份失败: {}", e))?;
        fs::copy(path, &ts_bak_path).map_err(|e| format!("创建时间戳备份失败: {}", e))?;

        Ok(())
    }

    /// 原子安全写入文件（先写入 .tmp，再 rename 替换）
    pub fn atomic_write_json(path: &Path, json_value: &serde_json::Value) -> Result<(), String> {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).map_err(|e| format!("创建目录失败: {}", e))?;
        }

        let tmp_path = path.with_extension("tmp");
        let formatted = serde_json::to_string_pretty(json_value)
            .map_err(|e| format!("序列化 JSON 失败: {}", e))?;

        fs::write(&tmp_path, formatted).map_err(|e| format!("写入临时文件失败: {}", e))?;
        fs::rename(&tmp_path, path).map_err(|e| {
            let _ = fs::remove_file(&tmp_path);
            format!("原子替换文件失败: {}", e)
        })?;

        Ok(())
    }

    /// 从单个配置文件载入服务商列表（自动兼容双 Schema）
    pub fn load_providers_from_file(
        path: &Path,
        label: &str,
    ) -> Result<Vec<UnifiedProviderItem>, String> {
        if !path.exists() {
            return Ok(Vec::new());
        }

        let content = fs::read_to_string(path).map_err(|e| format!("读取文件失败: {}", e))?;
        let root: serde_json::Value =
            serde_json::from_str(&content).map_err(|e| format!("解析 JSON 失败: {}", e))?;

        let mut items = Vec::new();

        // 模式 1: 经典 config.json ({"provider": {...}})
        if let Some(provs) = root.get("provider").and_then(|p| p.as_object()) {
            for (pid, pdata) in provs {
                let name = pdata
                    .get("name")
                    .and_then(|n| n.as_str())
                    .unwrap_or(pid)
                    .to_string();
                let kind = pdata
                    .get("kind")
                    .and_then(|k| k.as_str())
                    .unwrap_or("-")
                    .to_string();
                let enabled = pdata
                    .get("enabled")
                    .and_then(|e| e.as_bool())
                    .unwrap_or(true);
                let is_custom = pdata.get("source").and_then(|s| s.as_str()) == Some("custom")
                    && !pid.starts_with("builtin:")
                    && !pid.starts_with("account:");

                let mut models = Vec::new();
                if let Some(m_obj) = pdata.get("models").and_then(|m| m.as_object()) {
                    for m_key in m_obj.keys() {
                        models.push(m_key.clone());
                    }
                }

                items.push(UnifiedProviderItem {
                    provider_id: pid.clone(),
                    name,
                    kind,
                    models,
                    enabled,
                    is_custom,
                    source_file: path.to_string_lossy().to_string(),
                    source_label: label.to_string(),
                    schema_type: "classic".to_string(),
                    raw_data: pdata.clone(),
                });
            }
            return Ok(items);
        }

        // 模式 2: ZCode 新版核心配置 provider_config.json
        if let Some(cfg) = root.get("config").and_then(|c| c.as_object()) {
            if let Some(p_rules) = cfg
                .get("providerConfigRules")
                .and_then(|r| r.get("providerRules"))
                .and_then(|pr| pr.as_array())
            {
                for rule in p_rules {
                    let pid = rule
                        .get("providerId")
                        .and_then(|id| id.as_str())
                        .unwrap_or("")
                        .to_string();
                    if pid.is_empty() {
                        continue;
                    }

                    let name = rule
                        .get("providerName")
                        .and_then(|pn| pn.as_str())
                        .unwrap_or(&pid)
                        .to_string();
                    let r_cfg = rule.get("config").cloned().unwrap_or_default();
                    let group = r_cfg
                        .get("group")
                        .and_then(|g| g.as_str())
                        .unwrap_or("");
                    let is_custom = group == "standard-personal" || !pid.starts_with("account:");

                    let api = r_cfg.get("api").cloned().unwrap_or_default();
                    let kind = api
                        .get("type")
                        .and_then(|t| t.as_str())
                        .unwrap_or("anthropic-messages")
                        .to_string();

                    let mut models = Vec::new();
                    if let Some(m_arr) = r_cfg
                        .get("personalModelIds")
                        .or_else(|| r_cfg.get("modelOrder"))
                        .and_then(|m| m.as_array())
                    {
                        for m in m_arr {
                            if let Some(s) = m.as_str() {
                                models.push(s.to_string());
                            }
                        }
                    }

                    items.push(UnifiedProviderItem {
                        provider_id: pid,
                        name,
                        kind,
                        models,
                        enabled: true,
                        is_custom,
                        source_file: path.to_string_lossy().to_string(),
                        source_label: label.to_string(),
                        schema_type: "modern".to_string(),
                        raw_data: rule.clone(),
                    });
                }
            }
            return Ok(items);
        }

        Ok(items)
    }

    /// 保存单个服务商配置（自动识别文件所属 Schema 并原路写回）
    pub fn save_single_provider(
        path: &Path,
        provider_id: &str,
        updated_data: &serde_json::Value,
    ) -> Result<String, String> {
        Self::create_backup(path)?;

        let content = if path.exists() {
            fs::read_to_string(path).map_err(|e| format!("读取原文件失败: {}", e))?
        } else {
            "{}".to_string()
        };

        let mut root: serde_json::Value =
            serde_json::from_str(&content).unwrap_or(serde_json::json!({}));

        let is_modern = root
            .get("config")
            .and_then(|c| c.get("providerConfigRules"))
            .is_some();

        let new_name = updated_data
            .get("name")
            .and_then(|n| n.as_str())
            .unwrap_or(provider_id);
        let new_kind = updated_data
            .get("kind")
            .and_then(|k| k.as_str())
            .unwrap_or("anthropic-messages");

        let options = updated_data.get("options").cloned().unwrap_or_default();
        let api_key = options
            .get("apiKey")
            .and_then(|k| k.as_str())
            .unwrap_or("");
        let base_url = options
            .get("baseURL")
            .and_then(|u| u.as_str())
            .unwrap_or("");

        let mut model_ids = Vec::new();
        if let Some(m_obj) = updated_data.get("models").and_then(|m| m.as_object()) {
            for k in m_obj.keys() {
                model_ids.push(serde_json::Value::String(k.clone()));
            }
        }

        if is_modern {
            let config_obj = root
                .get_mut("config")
                .and_then(|c| c.as_object_mut())
                .ok_or("格式错误: 缺少 config 节点")?;

            let p_rules = config_obj
                .entry("providerConfigRules")
                .or_insert_with(|| serde_json::json!({}))
                .as_object_mut()
                .ok_or("providerConfigRules 不是对象")?
                .entry("providerRules")
                .or_insert_with(|| serde_json::json!([]))
                .as_array_mut()
                .ok_or("providerRules 不是数组")?;

            let mut found = false;
            for r in p_rules.iter_mut() {
                if r.get("providerId").and_then(|id| id.as_str()) == Some(provider_id) {
                    if let Some(r_obj) = r.as_object_mut() {
                        r_obj.insert(
                            "providerName".to_string(),
                            serde_json::Value::String(new_name.to_string()),
                        );
                        let c = r_obj
                            .entry("config")
                            .or_insert_with(|| serde_json::json!({}))
                            .as_object_mut();
                        if let Some(c_obj) = c {
                            let access = c_obj
                                .entry("access")
                                .or_insert_with(|| serde_json::json!({}))
                                .as_object_mut();
                            if let Some(acc) = access {
                                acc.insert(
                                    "apiKey".to_string(),
                                    serde_json::Value::String(api_key.to_string()),
                                );
                            }

                            let api = c_obj
                                .entry("api")
                                .or_insert_with(|| serde_json::json!({}))
                                .as_object_mut();
                            if let Some(ap) = api {
                                ap.insert(
                                    "baseUrl".to_string(),
                                    serde_json::Value::String(base_url.to_string()),
                                );
                                ap.insert(
                                    "type".to_string(),
                                    serde_json::Value::String(new_kind.to_string()),
                                );
                            }

                            c_obj.insert(
                                "personalModelIds".to_string(),
                                serde_json::Value::Array(model_ids.clone()),
                            );
                            c_obj.insert(
                                "modelOrder".to_string(),
                                serde_json::Value::Array(model_ids.clone()),
                            );
                        }
                    }
                    found = true;
                    break;
                }
            }

            if !found {
                p_rules.push(serde_json::json!({
                    "providerId": provider_id,
                    "providerName": new_name,
                    "config": {
                        "group": "standard-personal",
                        "access": { "type": "api-key", "apiKey": api_key },
                        "api": { "type": new_kind, "baseUrl": base_url },
                        "personalModelIds": model_ids.clone(),
                        "modelOrder": model_ids
                    }
                }));

                let p_order = config_obj
                    .entry("providerOrder")
                    .or_insert_with(|| serde_json::json!([]))
                    .as_array_mut();
                if let Some(order) = p_order {
                    let pid_val = serde_json::Value::String(provider_id.to_string());
                    if !order.contains(&pid_val) {
                        order.push(pid_val);
                    }
                }
            }
        } else {
            let root_obj = root
                .as_object_mut()
                .ok_or("根节点必须是 JSON 对象")?;
            let prov_map = root_obj
                .entry("provider")
                .or_insert_with(|| serde_json::json!({}))
                .as_object_mut()
                .ok_or("provider 节点格式无效")?;
            prov_map.insert(provider_id.to_string(), updated_data.clone());
        }

        Self::atomic_write_json(path, &root)?;
        Ok(format!("成功保存服务商 [{}] 并写入备份", new_name))
    }

    /// 从指定配置文件中安全删除服务商
    pub fn delete_single_provider(path: &Path, provider_id: &str) -> Result<String, String> {
        Self::create_backup(path)?;

        let content = fs::read_to_string(path).map_err(|e| format!("读取文件失败: {}", e))?;
        let mut root: serde_json::Value =
            serde_json::from_str(&content).map_err(|e| format!("解析 JSON 失败: {}", e))?;

        let is_modern = root
            .get("config")
            .and_then(|c| c.get("providerConfigRules"))
            .is_some();

        if is_modern {
            if let Some(cfg) = root.get_mut("config").and_then(|c| c.as_object_mut()) {
                if let Some(p_rules) = cfg
                    .get_mut("providerConfigRules")
                    .and_then(|r| r.get_mut("providerRules"))
                    .and_then(|pr| pr.as_array_mut())
                {
                    p_rules.retain(|r| {
                        r.get("providerId").and_then(|id| id.as_str()) != Some(provider_id)
                    });
                }
                if let Some(p_order) = cfg.get_mut("providerOrder").and_then(|o| o.as_array_mut())
                {
                    p_order.retain(|id| id.as_str() != Some(provider_id));
                }
            }
        } else if let Some(prov_map) = root.get_mut("provider").and_then(|p| p.as_object_mut()) {
            prov_map.remove(provider_id);
        }

        Self::atomic_write_json(path, &root)?;
        Ok(format!("已成功从 {} 删除服务商 [{}]", path.display(), provider_id))
    }

    /// 重复模型检测分析
    pub fn analyze_duplicate_models(items: &[UnifiedProviderItem]) -> DuplicateReport {
        let mut model_map: HashMap<String, Vec<DuplicateOccurrence>> = HashMap::new();

        for item in items {
            for m in &item.models {
                model_map
                    .entry(m.clone())
                    .or_default()
                    .push(DuplicateOccurrence {
                        provider: item.name.clone(),
                        provider_id: item.provider_id.clone(),
                        file: item.source_file.clone(),
                        label: item.source_label.clone(),
                        is_custom: item.is_custom,
                    });
            }
        }

        // 只保留重复出现（大于 1 次）的模型
        model_map.retain(|_, occurrences| occurrences.len() > 1);
        model_map
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    #[test]
    fn test_duplicate_analysis() {
        let items = vec![
            UnifiedProviderItem {
                provider_id: "p1".into(),
                name: "Provider 1".into(),
                kind: "openai".into(),
                models: vec!["model-shared".into(), "model-unique-1".into()],
                enabled: true,
                is_custom: true,
                source_file: "file1.json".into(),
                source_label: "F1".into(),
                schema_type: "classic".into(),
                raw_data: serde_json::json!({}),
            },
            UnifiedProviderItem {
                provider_id: "p2".into(),
                name: "Provider 2".into(),
                kind: "anthropic".into(),
                models: vec!["model-shared".into(), "model-unique-2".into()],
                enabled: true,
                is_custom: false,
                source_file: "file2.json".into(),
                source_label: "F2".into(),
                schema_type: "modern".into(),
                raw_data: serde_json::json!({}),
            },
        ];

        let dups = SyncEngine::analyze_duplicate_models(&items);
        assert_eq!(dups.len(), 1);
        assert!(dups.contains_key("model-shared"));
        assert_eq!(dups["model-shared"].len(), 2);
    }

    #[test]
    fn test_atomic_write_and_backup() {
        let tmp_dir = std::env::temp_dir().join(format!("zcode_rust_test_{}", std::process::id()));
        let _ = fs::create_dir_all(&tmp_dir);
        let test_file = tmp_dir.join("test_cfg.json");

        let initial_json = serde_json::json!({
            "provider": {
                "test_p": { "name": "Initial" }
            }
        });

        // 1. 验证原子写入
        assert!(SyncEngine::atomic_write_json(&test_file, &initial_json).is_ok());
        assert!(test_file.exists());

        // 2. 验证备份生成
        assert!(SyncEngine::create_backup(&test_file).is_ok());
        assert!(tmp_dir.join("test_cfg.json.bak").exists());

        // 3. 验证单项保存
        let updated_item = serde_json::json!({
            "name": "UpdatedName",
            "kind": "openai",
            "options": { "baseURL": "https://api.test.com", "apiKey": "sk-123" }
        });
        assert!(SyncEngine::save_single_provider(&test_file, "test_p", &updated_item).is_ok());

        let read_back = fs::read_to_string(&test_file).unwrap();
        let parsed: serde_json::Value = serde_json::from_str(&read_back).unwrap();
        assert_eq!(parsed["provider"]["test_p"]["name"], "UpdatedName");

        let _ = fs::remove_dir_all(&tmp_dir);
    }
}
