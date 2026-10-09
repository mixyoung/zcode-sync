use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ConfigFileMeta {
    pub path: String,
    pub label: String,
    pub schema_type: String, // "classic" | "modern"
    pub provider_count: usize,
    pub custom_count: usize,
    pub size_bytes: u64,
    pub updated_at: String,
    pub exists: bool,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct UnifiedProviderItem {
    pub provider_id: String,
    pub name: String,
    pub kind: String,
    pub models: Vec<String>,
    pub enabled: bool,
    pub is_custom: bool,
    pub source_file: String,
    pub source_label: String,
    pub schema_type: String,
    pub raw_data: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct DuplicateOccurrence {
    pub provider: String,
    pub provider_id: String,
    pub file: String,
    pub label: String,
    pub is_custom: bool,
}

pub type DuplicateReport = HashMap<String, Vec<DuplicateOccurrence>>;

// --- Schema 1: 经典 config.json 结构 ---
#[allow(dead_code)]
#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct ClassicConfig {
    #[serde(default)]
    pub provider: HashMap<String, serde_json::Value>,
    #[serde(flatten)]
    pub extra: HashMap<String, serde_json::Value>,
}

// --- Schema 2: 现代 provider_config.json 结构 ---
#[allow(dead_code)]
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ModernProviderConfig {
    #[serde(rename = "schemaVersion")]
    pub schema_version: u32,
    pub config: ModernConfigBody,
}

#[allow(dead_code)]
#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct ModernConfigBody {
    #[serde(rename = "providerOrder", default)]
    pub provider_order: Vec<String>,
    #[serde(rename = "providerConfigRules", default)]
    pub provider_config_rules: ProviderConfigRules,
    #[serde(rename = "modelConfigRules", default)]
    pub model_config_rules: ModelConfigRules,
}

#[allow(dead_code)]
#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct ProviderConfigRules {
    #[serde(rename = "providerRules", default)]
    pub provider_rules: Vec<serde_json::Value>,
}

#[allow(dead_code)]
#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct ModelConfigRules {
    #[serde(rename = "providerModelRules", default)]
    pub provider_model_rules: Vec<serde_json::Value>,
    #[serde(rename = "manualProviderModelRules", default)]
    pub manual_provider_model_rules: Vec<serde_json::Value>,
}

// --- 云存储 S3/R2 与 WebDAV 模型 ---

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct S3Config {
    #[serde(default)]
    pub endpoint: String,
    #[serde(default)]
    pub bucket: String,
    #[serde(default = "default_region")]
    pub region: String,
    #[serde(default)]
    pub access_key: String,
    #[serde(default)]
    pub secret_key: String,
    #[serde(default = "default_s3_prefix")]
    pub prefix: String,
}

fn default_region() -> String {
    "auto".to_string()
}
fn default_s3_prefix() -> String {
    "zcode-backups/".to_string()
}

impl Default for S3Config {
    fn default() -> Self {
        Self {
            endpoint: String::new(),
            bucket: String::new(),
            region: default_region(),
            access_key: String::new(),
            secret_key: String::new(),
            prefix: default_s3_prefix(),
        }
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct WebDavConfig {
    #[serde(default)]
    pub server_url: String,
    #[serde(default)]
    pub username: String,
    #[serde(default)]
    pub password: String,
    #[serde(default = "default_webdav_dir")]
    pub remote_dir: String,
}

fn default_webdav_dir() -> String {
    "zcode-backups".to_string()
}

impl Default for WebDavConfig {
    fn default() -> Self {
        Self {
            server_url: String::new(),
            username: String::new(),
            password: String::new(),
            remote_dir: default_webdav_dir(),
        }
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct RetentionConfig {
    #[serde(default = "default_max_versions")]
    pub max_versions: u32,
    #[serde(default = "default_retention_days")]
    pub retention_days: u32,
}

fn default_max_versions() -> u32 {
    10
}
fn default_retention_days() -> u32 {
    30
}

impl Default for RetentionConfig {
    fn default() -> Self {
        Self {
            max_versions: default_max_versions(),
            retention_days: default_retention_days(),
        }
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct CloudConfig {
    #[serde(default = "default_provider_type")]
    pub provider_type: String, // "s3" | "webdav" | "none"
    #[serde(default)]
    pub s3: S3Config,
    #[serde(default)]
    pub webdav: WebDavConfig,
    #[serde(default)]
    pub retention: RetentionConfig,
}

fn default_provider_type() -> String {
    "s3".to_string()
}

impl Default for CloudConfig {
    fn default() -> Self {
        Self {
            provider_type: default_provider_type(),
            s3: S3Config::default(),
            webdav: WebDavConfig::default(),
            retention: RetentionConfig::default(),
        }
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct CloudBackupItem {
    pub name: String,
    pub size_bytes: u64,
    pub last_modified: String,
    pub provider_count: usize,
}
