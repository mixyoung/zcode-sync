use std::path::{Path, PathBuf};
use std::process::Command;
use crate::models::{ConfigFileMeta, DuplicateReport, UnifiedProviderItem};
use crate::path_detector::PathDetector;
use crate::sync_engine::SyncEngine;

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
