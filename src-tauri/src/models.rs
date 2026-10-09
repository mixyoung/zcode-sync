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
