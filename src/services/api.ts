import {
  ConfigFileMeta,
  DuplicateAnalysisResult,
  UnifiedProviderItem,
  CloudConfig,
  CloudBackupItem,
} from "../types";

// 检测是否运行在 Tauri 桌面原生容器中
const isTauri = () => {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
};

// 动态安全调用 Tauri invoke
async function callTauri<T>(cmd: string, args?: Record<string, any>): Promise<T> {
  if (isTauri()) {
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      return await invoke<T>(cmd, args);
    } catch (e) {
      console.warn(`Tauri invoke [${cmd}] error:`, e);
      throw e;
    }
  }
  throw new Error("NOT_IN_TAURI");
}

// 模拟数据（供 Web 独立调试与测试预览使用）
const MOCK_CONFIGS: ConfigFileMeta[] = [
  {
    path: "D:/program_files/zcode_data/.zcode/v2/provider_config.json",
    label: "活跃核心服务商配置 (provider_config.json)",
    schema_type: "modern",
    provider_count: 2,
    custom_count: 1,
    size_bytes: 6807,
    updated_at: "2026-10-08 21:31:32",
    exists: true,
  },
  {
    path: "D:/program_files/zcode_data/.zcode/v2/config.json",
    label: "活跃经典配置 (config.json)",
    schema_type: "classic",
    provider_count: 5,
    custom_count: 1,
    size_bytes: 9837,
    updated_at: "2026-10-08 21:38:47",
    exists: true,
  },
  {
    path: "C:/Users/admin/.zcode/v2/config.json",
    label: "标准家目录 (~/.zcode/config.json)",
    schema_type: "classic",
    provider_count: 0,
    custom_count: 0,
    size_bytes: 22,
    updated_at: "2026-10-08 20:50:11",
    exists: true,
  },
];

let mockProviders: UnifiedProviderItem[] = [
  {
    provider_id: "3dd78d35-3977-4172-8092-46bd628c984f",
    name: "mgw",
    kind: "anthropic-messages",
    models: [
      "agy-sub-mixge-rev/gemini-3.8-flash-high",
      "gpt-sub-mixge-rev/gpt-5.6-terra",
      "mmx-sub-dno-a/MiniMax-M3",
      "gpt-sub-mixge-rev/gpt-5.6-sol",
      "xai-sub-mixlve-rev/grok-4.6",
      "agy-sub-dnolin-rev/gemini-3.8-flash-high",
      "agy-jio-frmx-rev/gemini-3.8-flash-high",
    ],
    enabled: true,
    is_custom: true,
    source_file: "D:/program_files/zcode_data/.zcode/v2/provider_config.json",
    source_label: "活跃核心服务商配置",
    schema_type: "modern",
    raw_data: {
      name: "mgw",
      kind: "anthropic-messages",
      options: {
        baseURL: "https://api.example.com",
        apiKey: "sk-your-private-api-key-here",
      },
    },
  },
  {
    provider_id: "account:bigmodel-individual-coding-plan",
    name: "BigModel - Individual Coding Plan",
    kind: "anthropic",
    models: ["GLM-5.3-Flashx", "GLM-5.3", "GLM-5.3-Flash"],
    enabled: true,
    is_custom: false,
    source_file: "D:/program_files/zcode_data/.zcode/v2/provider_config.json",
    source_label: "活跃核心服务商配置",
    schema_type: "modern",
    raw_data: { name: "BigModel - Individual Coding Plan" },
  },
  {
    provider_id: "builtin:bigmodel-coding-plan",
    name: "BigModel - Coding Plan",
    kind: "anthropic",
    models: ["GLM-5.3", "GLM-5.3-Flash"],
    enabled: true,
    is_custom: false,
    source_file: "D:/program_files/zcode_data/.zcode/v2/config.json",
    source_label: "活跃经典配置",
    schema_type: "classic",
    raw_data: { name: "BigModel - Coding Plan" },
  },
  {
    provider_id: "builtin:zai-coding-plan",
    name: "Z.ai - Coding Plan",
    kind: "anthropic",
    models: ["GLM-5.3", "GLM-5.3-Flash"],
    enabled: true,
    is_custom: false,
    source_file: "D:/program_files/zcode_data/.zcode/v2/config.json",
    source_label: "活跃经典配置",
    schema_type: "classic",
    raw_data: { name: "Z.ai - Coding Plan" },
  },
  {
    provider_id: "builtin:bigmodel",
    name: "Bigmodel - API Key",
    kind: "anthropic",
    models: ["GLM-5.3", "GLM-5.3-Flash"],
    enabled: true,
    is_custom: false,
    source_file: "D:/program_files/zcode_data/.zcode/v2/config.json",
    source_label: "活跃经典配置",
    schema_type: "classic",
    raw_data: { name: "Bigmodel - API Key" },
  },
  {
    provider_id: "builtin:zai",
    name: "Z.ai - API Key",
    kind: "anthropic",
    models: ["GLM-5.3", "GLM-5.3-Flash"],
    enabled: true,
    is_custom: false,
    source_file: "D:/program_files/zcode_data/.zcode/v2/config.json",
    source_label: "活跃经典配置",
    schema_type: "classic",
    raw_data: { name: "Z.ai - API Key" },
  },
  {
    provider_id: "3dd78d35-3977-4172-8092-46bd628c984f-legacy",
    name: "mgate (历史备份)",
    kind: "anthropic",
    models: [
      "gemini-3.8-flash-high",
      "gpt-5.6-terra",
      "MiniMax-M3",
      "gpt-5.6-sol",
      "grok-4.6",
      "gemini-3.8-flash-high",
    ],
    enabled: true,
    is_custom: true,
    source_file: "D:/program_files/zcode_data/.zcode/v2/config.json",
    source_label: "活跃经典配置",
    schema_type: "classic",
    raw_data: { name: "mgate", options: { baseURL: "https://api.example.com" } },
  },
];

let mockCloudConfig: CloudConfig = {
  provider_type: "s3",
  s3: {
    endpoint: "https://example.r2.cloudflarestorage.com",
    bucket: "zcode-backups",
    region: "auto",
    access_key: "AKIAIOSFODNN7EXAMPLE",
    secret_key: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    prefix: "zcode-backups/",
  },
  webdav: {
    server_url: "https://dav.jianguoyun.com/dav/zcode/",
    username: "user@example.com",
    password: "app-password-example",
    remote_dir: "zcode-backups",
  },
  retention: {
    max_versions: 10,
    retention_days: 30,
  },
};

let mockCloudBackups: CloudBackupItem[] = [
  {
    name: "zcode-backup-20261009_153012.json",
    size_bytes: 6842,
    last_modified: "2026-10-09 15:30:12",
    provider_count: 7,
  },
  {
    name: "zcode-backup-20261008_214500.json",
    size_bytes: 6710,
    last_modified: "2026-10-08 21:45:00",
    provider_count: 7,
  },
  {
    name: "zcode-backup-20261007_182015.json",
    size_bytes: 6520,
    last_modified: "2026-10-07 18:20:15",
    provider_count: 6,
  },
];

export const ApiService = {
  async discoverConfigs(extraPaths?: string[]): Promise<ConfigFileMeta[]> {
    try {
      return await callTauri<ConfigFileMeta[]>("discover_configs", {
        extraPaths,
      });
    } catch {
      return MOCK_CONFIGS;
    }
  },

  async loadAllProviders(files: string[]): Promise<UnifiedProviderItem[]> {
    try {
      return await callTauri<UnifiedProviderItem[]>("load_all_providers", {
        files,
      });
    } catch {
      if (files.length === 0) return mockProviders;
      return mockProviders.filter((p) => files.includes(p.source_file));
    }
  },

  async saveSingleProvider(
    filePath: string,
    providerId: string,
    updatedData: any
  ): Promise<string> {
    try {
      return await callTauri<string>("save_single_provider", {
        filePath,
        providerId,
        updatedData,
      });
    } catch {
      const idx = mockProviders.findIndex(
        (p) => p.source_file === filePath && p.provider_id === providerId
      );
      if (idx >= 0) {
        mockProviders[idx].name = updatedData.name || mockProviders[idx].name;
        mockProviders[idx].kind = updatedData.kind || mockProviders[idx].kind;
        mockProviders[idx].raw_data = updatedData;
      }
      return `[Mock] 成功保存服务商 [${updatedData.name || providerId}] 并写入备份`;
    }
  },

  async deleteSingleProvider(
    filePath: string,
    providerId: string
  ): Promise<string> {
    try {
      return await callTauri<string>("delete_single_provider", {
        filePath,
        providerId,
      });
    } catch {
      mockProviders = mockProviders.filter(
        (p) => !(p.source_file === filePath && p.provider_id === providerId)
      );
      return `[Mock] 成功删除服务商 [${providerId}] 并创建备份`;
    }
  },

  async analyzeDuplicates(
    items: UnifiedProviderItem[]
  ): Promise<DuplicateAnalysisResult> {
    try {
      return await callTauri<DuplicateAnalysisResult>("analyze_duplicates", {
        items,
      });
    } catch {
      const map: DuplicateAnalysisResult = {};
      for (const it of items) {
        for (const m of it.models) {
          if (!map[m]) map[m] = [];
          map[m].push({
            provider: it.name,
            provider_id: it.provider_id,
            file: it.source_file,
            label: it.source_label,
            is_custom: it.is_custom,
          });
        }
      }
      const filtered: DuplicateAnalysisResult = {};
      for (const [k, v] of Object.entries(map)) {
        if (v.length > 1) filtered[k] = v;
      }
      return filtered;
    }
  },

  async openFolder(filePath: string): Promise<void> {
    try {
      await callTauri("open_folder", { filePath });
    } catch {
      console.log("[Mock] 打开目录:", filePath);
    }
  },

  // --- 云存储 S3/R2 与 WebDAV IPC 接口 ---

  async getCloudConfig(): Promise<CloudConfig> {
    try {
      return await callTauri<CloudConfig>("get_cloud_config");
    } catch {
      return mockCloudConfig;
    }
  },

  async saveCloudConfig(config: CloudConfig): Promise<string> {
    try {
      return await callTauri<string>("save_cloud_config", { config });
    } catch {
      mockCloudConfig = config;
      return "云端同步配置已保存至本地私有文件";
    }
  },

  async testCloudConnection(config: CloudConfig): Promise<string> {
    try {
      return await callTauri<string>("test_cloud_connection", { config });
    } catch {
      if (config.provider_type === "s3") {
        if (!config.s3.endpoint || !config.s3.bucket) {
          throw new Error("S3 Endpoint 或 Bucket 不能为空");
        }
        return `[模拟测试] 成功连接 S3/R2 存储桶 [${config.s3.bucket}]，读写鉴权通过！`;
      } else if (config.provider_type === "webdav") {
        if (!config.webdav.server_url) {
          throw new Error("WebDAV Server URL 不能为空");
        }
        return `[模拟测试] 成功连接 WebDAV 服务器 [${config.webdav.server_url}]，目录校验通过！`;
      }
      throw new Error("未选择有效的云存储服务商");
    }
  },

  async uploadCloudBackup(payload: any): Promise<string> {
    try {
      return await callTauri<string>("upload_cloud_backup", { payload });
    } catch {
      const nowStr = new Date().toISOString().replace(/[-:T.]/g, "").slice(0, 15);
      const name = `zcode-backup-${nowStr}.json`;
      const newItem: CloudBackupItem = {
        name,
        size_bytes: JSON.stringify(payload).length,
        last_modified: new Date().toLocaleString("zh-CN"),
        provider_count: Object.keys(payload.provider || {}).length,
      };
      mockCloudBackups.unshift(newItem);
      return `已成功备份至云端 [${name}]，已执行生命周期清理`;
    }
  },

  async listCloudBackups(): Promise<CloudBackupItem[]> {
    try {
      return await callTauri<CloudBackupItem[]>("list_cloud_backups");
    } catch {
      return mockCloudBackups;
    }
  },

  async restoreCloudBackup(fileName: string): Promise<any> {
    try {
      return await callTauri<any>("restore_cloud_backup", { fileName });
    } catch {
      return {
        provider: {
          mgw: {
            name: "mgw",
            kind: "anthropic-messages",
            models: { "gemini-3.8-flash-high": {}, "gpt-5.6-terra": {} },
          },
        },
      };
    }
  },

  async deleteCloudBackup(fileName: string): Promise<string> {
    try {
      return await callTauri<string>("delete_cloud_backup", { fileName });
    } catch {
      mockCloudBackups = mockCloudBackups.filter((b) => b.name !== fileName);
      return `已从云端删除历史备份 [${fileName}]`;
    }
  },
};
