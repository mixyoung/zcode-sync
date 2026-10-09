export interface ConfigFileMeta {
  path: string;
  label: string;
  schema_type: "classic" | "modern";
  provider_count: number;
  custom_count: number;
  size_bytes: number;
  updated_at: string;
  exists: boolean;
}

export interface ModelDetail {
  name: string;
  limit?: {
    context?: number;
    output?: number;
  };
  reasoning?: {
    enabled?: boolean;
  };
}

export interface UnifiedProviderItem {
  provider_id: string;
  name: string;
  kind: string;
  models: string[];
  enabled: boolean;
  is_custom: boolean;
  source_file: string;
  source_label: string;
  schema_type: "classic" | "modern";
  raw_data: Record<string, any>;
}

export interface DuplicateOccurrence {
  provider: string;
  provider_id: string;
  file: string;
  label: string;
  is_custom: boolean;
}

export type DuplicateAnalysisResult = Record<string, DuplicateOccurrence[]>;

export interface ToastMessage {
  id: string;
  type: "success" | "error" | "info";
  title: string;
  message?: string;
}

// --- 云存储同步与生命周期保留策略类型 ---

export type CloudProviderType = "s3" | "webdav" | "none";

export interface S3Config {
  endpoint: string;
  bucket: string;
  region: string;
  access_key: string;
  secret_key: string;
  prefix: string;
}

export interface WebDavConfig {
  server_url: string;
  username: string;
  password: string;
  remote_dir: string;
}

export interface RetentionConfig {
  max_versions: number; // 0 表示不限份数
  retention_days: number; // 0 表示永久保留
}

export interface CloudConfig {
  provider_type: CloudProviderType;
  s3: S3Config;
  webdav: WebDavConfig;
  retention: RetentionConfig;
}

export interface CloudBackupItem {
  name: string;
  size_bytes: number;
  last_modified: string;
  provider_count: number;
}
