use std::path::{Path, PathBuf};
use std::process::Command;
use crate::models::{CloudBackupItem, CloudConfig, ConfigFileMeta, DuplicateReport, UnifiedProviderItem};
use crate::path_detector::PathDetector;
use crate::sync_engine::SyncEngine;
use crate::cloud_storage::config_store::CloudConfigStore;
use crate::cloud_storage::CloudManager;

#[tauri::command]
pub fn discover_configs(extra_paths: Option<Vec<String>>) -> Result<Vec<ConfigFileMeta>, String> {
    Ok(PathDetector::discover_all(extra_paths))
}

#[tauri::command]
pub fn load_all_providers(files: Vec<String>) -> Result<Vec<UnifiedProviderItem>, String> {
    let mut all_items = Vec::new();

    for f_str in files {
        let p = PathBuf::from(&f_str);
        let label = p.file_name().unwrap_or_default().to_string_lossy().to_string();
        if let Ok(mut items) = SyncEngine::load_providers_from_file(&p, &label) {
            all_items.append(&mut items);
        }
    }

    Ok(all_items)
}

#[tauri::command]
pub fn save_single_provider(
    file_path: String,
    provider_id: String,
    updated_data: serde_json::Value,
) -> Result<String, String> {
    let p = PathBuf::from(file_path);
    SyncEngine::save_single_provider(&p, &provider_id, &updated_data)
}

#[tauri::command]
pub fn delete_single_provider(file_path: String, provider_id: String) -> Result<String, String> {
    let p = PathBuf::from(file_path);
    SyncEngine::delete_single_provider(&p, &provider_id)
}

#[tauri::command]
pub fn analyze_duplicates(items: Vec<UnifiedProviderItem>) -> Result<DuplicateReport, String> {
    Ok(SyncEngine::analyze_duplicate_models(&items))
}

#[tauri::command]
pub fn open_folder(file_path: String) -> Result<(), String> {
    let p = PathBuf::from(&file_path);
    let folder = if p.is_dir() {
        p
    } else {
        p.parent().unwrap_or(Path::new(".")).to_path_buf()
    };

    #[cfg(target_os = "windows")]
    {
        Command::new("explorer")
            .arg(folder)
            .spawn()
            .map_err(|e| format!("打开文件夹失败: {}", e))?;
    }

    #[cfg(target_os = "macos")]
    {
        Command::new("open")
            .arg(folder)
            .spawn()
            .map_err(|e| format!("打开文件夹失败: {}", e))?;
    }

    #[cfg(target_os = "linux")]
    {
        Command::new("xdg-open")
            .arg(folder)
            .spawn()
            .map_err(|e| format!("打开文件夹失败: {}", e))?;
    }

    Ok(())
}

// --- 云端存储与备份 IPC 命令 ---

#[tauri::command]
pub fn get_cloud_config() -> Result<CloudConfig, String> {
    Ok(CloudConfigStore::load_config())
}

#[tauri::command]
pub fn save_cloud_config(config: CloudConfig) -> Result<String, String> {
    CloudConfigStore::save_config(&config)?;
    Ok("云端存储配置已安全保存至本地私有文件".to_string())
}

#[tauri::command]
pub async fn test_cloud_connection(config: CloudConfig) -> Result<String, String> {
    CloudManager::test_connection(&config).await
}

#[tauri::command]
pub async fn upload_cloud_backup(payload: serde_json::Value) -> Result<String, String> {
    let cfg = CloudConfigStore::load_config();
    let json_bytes = serde_json::to_vec_pretty(&payload)
        .map_err(|e| format!("序列化配置失败: {}", e))?;
    CloudManager::upload_backup(&cfg, &json_bytes).await
}

#[tauri::command]
pub async fn list_cloud_backups() -> Result<Vec<CloudBackupItem>, String> {
    let cfg = CloudConfigStore::load_config();
    CloudManager::list_backups(&cfg).await
}

#[tauri::command]
pub async fn restore_cloud_backup(file_name: String) -> Result<serde_json::Value, String> {
    let cfg = CloudConfigStore::load_config();
    let bytes = CloudManager::download_backup(&cfg, &file_name).await?;
    serde_json::from_slice(&bytes).map_err(|e| format!("解析云端备份内容失败: {}", e))
}

#[tauri::command]
pub async fn delete_cloud_backup(file_name: String) -> Result<String, String> {
    let cfg = CloudConfigStore::load_config();
    CloudManager::delete_backup(&cfg, &file_name).await?;
    Ok(format!("已从云端删除历史备份 [{}]", file_name))
}
