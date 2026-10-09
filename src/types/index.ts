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
