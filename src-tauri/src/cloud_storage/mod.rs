pub mod config_store;
pub mod retention;
pub mod s3;
pub mod webdav;

use chrono::Local;
use crate::models::{CloudBackupItem, CloudConfig};
use retention::RetentionEngine;
use s3::S3Client;
use webdav::WebDavClient;

pub struct CloudManager;

impl CloudManager {
    pub async fn test_connection(config: &CloudConfig) -> Result<String, String> {
        match config.provider_type.as_str() {
            "s3" => {
                let client = S3Client::new(config.s3.clone());
                client.test_connection().await
            }
            "webdav" => {
                let client = WebDavClient::new(config.webdav.clone());
                client.test_connection().await
            }
            _ => Err("未选择有效的云存储服务商".to_string()),
        }
    }

    pub async fn list_backups(config: &CloudConfig) -> Result<Vec<CloudBackupItem>, String> {
        match config.provider_type.as_str() {
            "s3" => {
                let client = S3Client::new(config.s3.clone());
                client.list_backups().await
            }
            "webdav" => {
                let client = WebDavClient::new(config.webdav.clone());
                client.list_backups().await
            }
            _ => Ok(Vec::new()),
        }
    }

    pub async fn download_backup(config: &CloudConfig, file_name: &str) -> Result<Vec<u8>, String> {
        match config.provider_type.as_str() {
            "s3" => {
                let client = S3Client::new(config.s3.clone());
                client.download(file_name).await
            }
            "webdav" => {
                let client = WebDavClient::new(config.webdav.clone());
                client.download(file_name).await
            }
            _ => Err("未启用云存储".to_string()),
        }
    }

    pub async fn delete_backup(config: &CloudConfig, file_name: &str) -> Result<(), String> {
        match config.provider_type.as_str() {
            "s3" => {
                let client = S3Client::new(config.s3.clone());
                client.delete(file_name).await
            }
            "webdav" => {
                let client = WebDavClient::new(config.webdav.clone());
                client.delete(file_name).await
            }
            _ => Ok(()),
        }
    }

    /// 上传新备份并自动执行生命周期清理
    pub async fn upload_backup(config: &CloudConfig, data: &[u8]) -> Result<String, String> {
        let ts = Local::now().format("%Y%m%d_%H%M%S").to_string();
        let file_name = format!("zcode-backup-{}.json", ts);

        // 1. 上传新备份
        match config.provider_type.as_str() {
            "s3" => {
                let client = S3Client::new(config.s3.clone());
                client.upload(&file_name, data).await?;
            }
            "webdav" => {
                let client = WebDavClient::new(config.webdav.clone());
                client.upload(&file_name, data).await?;
            }
            _ => return Err("未配置云存储提供商".to_string()),
        }

        // 2. 获取最新列表并执行生命周期保留清理
        let mut pruned_count = 0;
        if let Ok(all_items) = Self::list_backups(config).await {
            let expired_files = RetentionEngine::calculate_expired_backups(&all_items, &config.retention);
            for exp_name in expired_files {
                let _ = Self::delete_backup(config, &exp_name).await;
                pruned_count += 1;
            }
        }

        if pruned_count > 0 {
            Ok(format!("成功上传备份 [{}]，并依据保留策略自动清理了 {} 份过期历史备份", file_name, pruned_count))
        } else {
            Ok(format!("成功上传备份 [{}]", file_name))
        }
    }
}
