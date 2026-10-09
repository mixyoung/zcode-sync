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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_timestamp() {
        let name = "zcode-backup-20261009_153012.json";
        let parsed = RetentionEngine::parse_backup_timestamp(name);
        assert!(parsed.is_some());
        let dt = parsed.unwrap();
        assert_eq!(dt.format("%Y%m%d_%H%M%S").to_string(), "20261009_153012");
    }

    #[test]
    fn test_retention_max_versions_with_safety_floor() {
        let items = vec![
            CloudBackupItem {
                name: "zcode-backup-20261009_120000.json".into(),
                size_bytes: 100,
                last_modified: "".into(),
                provider_count: 5,
            },
            CloudBackupItem {
                name: "zcode-backup-20261008_120000.json".into(),
                size_bytes: 100,
                last_modified: "".into(),
                provider_count: 5,
            },
            CloudBackupItem {
                name: "zcode-backup-20261007_120000.json".into(),
                size_bytes: 100,
                last_modified: "".into(),
                provider_count: 5,
            },
        ];

        // 设定最多保留 2 份
        let config = RetentionConfig {
            max_versions: 2,
            retention_days: 0,
        };

        let expired = RetentionEngine::calculate_expired_backups(&items, &config);
        // 最老的 20261007 应该被淘汰，保留 20261009 与 20261008
        assert_eq!(expired.len(), 1);
        assert_eq!(expired[0], "zcode-backup-20261007_120000.json");
    }

    #[test]
    fn test_retention_safety_floor_never_deletes_latest() {
        let items = vec![
            CloudBackupItem {
                name: "zcode-backup-20200101_000000.json".into(), // 极老备份
                size_bytes: 100,
                last_modified: "".into(),
                provider_count: 1,
            },
        ];

        // 设定只保留 1 天以内
        let config = RetentionConfig {
            max_versions: 1,
            retention_days: 1,
        };

        // 即使已超期，绝对底线保证：只剩 1 份时绝不删除！
        let expired = RetentionEngine::calculate_expired_backups(&items, &config);
        assert!(expired.is_empty(), "绝对底线保证：只剩 1 份时不应被清理");
    }
}
