use chrono::{Local, NaiveDateTime};
use crate::models::{CloudBackupItem, RetentionConfig};

pub struct RetentionEngine;

impl RetentionEngine {
    /// 从文件名中解析生成时间戳 (例如 zcode-backup-20261009_153012.json)
    pub fn parse_backup_timestamp(name: &str) -> Option<NaiveDateTime> {
        let clean = name.trim_end_matches(".json");
        let prefix = "zcode-backup-";
        if let Some(pos) = clean.find(prefix) {
            let ts_part = &clean[pos + prefix.len()..];
            if let Ok(dt) = NaiveDateTime::parse_from_str(ts_part, "%Y%m%d_%H%M%S") {
                return Some(dt);
            }
        }
        None
    }

    /// 依据保留策略计算应被删除的文件名列表
    pub fn calculate_expired_backups(
        items: &[CloudBackupItem],
        config: &RetentionConfig,
    ) -> Vec<String> {
        if items.len() <= 1 {
            return Vec::new();
        }

        // 按文件名时间逆序排序 (最新的在最前)
        let mut sorted = items.to_vec();
        sorted.sort_by(|a, b| b.name.cmp(&a.name));

        let now = Local::now().naive_local();
        let mut to_delete = Vec::new();

        for (idx, item) in sorted.iter().enumerate() {
            // 绝对底线保护：时间最新的第 0 份永不删除
            if idx == 0 {
                continue;
            }

            let mut should_prune = false;

            // 1. 份数限制
            if config.max_versions > 0 && idx >= (config.max_versions as usize) {
                should_prune = true;
            }

            // 2. 天数限制
            if config.retention_days > 0 {
                if let Some(dt) = Self::parse_backup_timestamp(&item.name) {
                    let diff_days = (now - dt).num_days();
                    if diff_days > (config.retention_days as i64) {
                        should_prune = true;
                    }
                }
            }

            if should_prune {
                to_delete.push(item.name.clone());
            }
        }

        to_delete
    }
}
