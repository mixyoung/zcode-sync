use std::collections::HashSet;
use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use chrono::{DateTime, Local};

use crate::models::ConfigFileMeta;

pub struct PathDetector;

impl PathDetector {
    pub fn get_candidate_locations() -> Vec<(PathBuf, String)> {
        let mut locs = Vec::new();

        // 1. 环境变量 ZCODE_DATA_BASE_DIR
        if let Ok(data_base) = env::var("ZCODE_DATA_BASE_DIR") {
            let p = PathBuf::from(data_base.trim());
            locs.push((p.join(".zcode").join("v2").join("provider_config.json"), "活跃核心服务商配置 (provider_config.json)".into()));
            locs.push((p.join(".zcode").join("v2").join("config.json"), "活跃经典配置 (config.json)".into()));
            locs.push((p.join("v2").join("provider_config.json"), "数据目录 v2 (provider_config.json)".into()));
            locs.push((p.join("v2").join("config.json"), "数据目录 v2 (config.json)".into()));
        }

        // 2. 环境变量 ZCODE_HOME
        if let Ok(zcode_home) = env::var("ZCODE_HOME") {
            let p = PathBuf::from(zcode_home.trim());
            locs.push((p.join("v2").join("provider_config.json"), "ZCODE_HOME (provider_config.json)".into()));
            locs.push((p.join("v2").join("config.json"), "ZCODE_HOME (config.json)".into()));
        }

        // 3. Windows 固定数据目录
        #[cfg(target_os = "windows")]
        {
            let fixed = PathBuf::from("D:/program_files/zcode_data/.zcode/v2");
            locs.push((fixed.join("provider_config.json"), "核心服务商配置 (D:/zcode_data/provider_config.json)".into()));
            locs.push((fixed.join("config.json"), "固定数据目录 (D:/zcode_data/config.json)".into()));
        }

        // 4. 标准用户家目录
        if let Some(home) = dirs::home_dir() {
            let v2_dir = home.join(".zcode").join("v2");
            locs.push((v2_dir.join("provider_config.json"), "标准家目录 (provider_config.json)".into()));
            locs.push((v2_dir.join("config.json"), "标准家目录 (~/.zcode/config.json)".into()));
        }

        locs
    }

    pub fn inspect_file(path: &Path, label: &str) -> Option<ConfigFileMeta> {
        if !path.exists() || !path.is_file() {
            return None;
        }

        let metadata = fs::metadata(path).ok()?;
        let size_bytes = metadata.len();
        let modified: DateTime<Local> = metadata.modified().ok()?.into();
        let updated_at = modified.format("%Y-%m-%d %H:%M:%S").to_string();

        let mut provider_count = 0;
        let mut custom_count = 0;
        let mut schema_type = "classic".to_string();

        if let Ok(content) = fs::read_to_string(path) {
            if let Ok(val) = serde_json::from_str::<serde_json::Value>(&content) {
                if let Some(provs) = val.get("provider").and_then(|p| p.as_object()) {
                    schema_type = "classic".to_string();
                    provider_count = provs.len();
                    for (pid, pdata) in provs {
                        let is_custom = pdata.get("source").and_then(|s| s.as_str()) == Some("custom")
                            && !pid.starts_with("builtin:");
                        if is_custom {
                            custom_count += 1;
                        }
                    }
                } else if let Some(cfg) = val.get("config").and_then(|c| c.as_object()) {
                    schema_type = "modern".to_string();
                    if let Some(rules) = cfg.get("providerConfigRules")
                        .and_then(|p| p.get("providerRules"))
                        .and_then(|r| r.as_array())
                    {
                        provider_count = rules.len();
                        for r in rules {
                            let pid = r.get("providerId").and_then(|id| id.as_str()).unwrap_or("");
                            let group = r.get("config")
                                .and_then(|c| c.get("group"))
                                .and_then(|g| g.as_str())
                                .unwrap_or("");
                            let is_custom = group == "standard-personal" || !pid.starts_with("account:");
                            if is_custom {
                                custom_count += 1;
                            }
                        }
                    }
                }
            }
        }

        Some(ConfigFileMeta {
            path: path.to_string_lossy().to_string(),
            label: label.to_string(),
            schema_type,
            provider_count,
            custom_count,
            size_bytes,
            updated_at,
            exists: true,
        })
    }

    pub fn discover_all(extra_paths: Option<Vec<String>>) -> Vec<ConfigFileMeta> {
        let mut results = Vec::new();
        let mut seen = HashSet::new();

        for (p, label) in Self::get_candidate_locations() {
            if let Ok(canonical) = p.canonicalize() {
                if seen.insert(canonical.clone()) {
                    if let Some(meta) = Self::inspect_file(&p, &label) {
                        results.push(meta);
                    }
                }
            }
        }

        if let Some(extras) = extra_paths {
            for ep in extras {
                let p = PathBuf::from(ep.trim());
                if let Ok(canonical) = p.canonicalize() {
                    if seen.insert(canonical) {
                        if let Some(meta) = Self::inspect_file(&p, "用户手动指定") {
                            results.push(meta);
                        }
                    }
                }
            }
        }

        results
    }
}
