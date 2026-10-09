use std::fs;
use std::path::PathBuf;
use crate::models::CloudConfig;

pub struct CloudConfigStore;

impl CloudConfigStore {
    pub fn get_config_path() -> PathBuf {
        let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
        home.join(".zcode").join("sync_remote.json")
    }

    pub fn load_config() -> CloudConfig {
        let path = Self::get_config_path();
        if path.exists() {
            if let Ok(content) = fs::read_to_string(&path) {
                if let Ok(cfg) = serde_json::from_str::<CloudConfig>(&content) {
                    return cfg;
                }
            }
        }
        CloudConfig::default()
    }

    pub fn save_config(cfg: &CloudConfig) -> Result<(), String> {
        let path = Self::get_config_path();
        if let Some(parent) = path.parent() {
            let _ = fs::create_dir_all(parent);
        }

        let formatted = serde_json::to_string_pretty(cfg)
            .map_err(|e| format!("序列化云配置失败: {}", e))?;

        fs::write(&path, formatted)
            .map_err(|e| format!("写入本地私有配置失败: {}", e))?;

        Ok(())
    }
}
