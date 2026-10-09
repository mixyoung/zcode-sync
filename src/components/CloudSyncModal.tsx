import React, { useState, useEffect } from "react";
import {
  Cloud,
  X,
  Server,
  FolderSync,
  Clock,
  History,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
  Trash2,
  Download,
  Upload,
  Save,
  RotateCw,
  Info,
  Shield,
  Layers,
  Check,
} from "lucide-react";
import { CloudConfig, CloudBackupItem, CloudProviderType } from "../types";
import { ApiService } from "../services/api";

interface CloudSyncModalProps {
  isOpen: boolean;
  onClose: () => void;
  onBackupNow: (maskKey: boolean) => Promise<void>;
  onRestoreFromCloud: (backupData: any, fileName: string) => Promise<void>;
  onShowToast: (type: "success" | "error" | "info", title: string, message?: string) => void;
}

export const CloudSyncModal: React.FC<CloudSyncModalProps> = ({
  isOpen,
  onClose,
  onBackupNow,
  onRestoreFromCloud,
  onShowToast,
}) => {
  if (!isOpen) return null;

  const [activeTab, setActiveTab] = useState<"s3" | "webdav" | "retention" | "history">("s3");
  const [providerType, setProviderType] = useState<CloudProviderType>("s3");

  // S3 配置
  const [s3Endpoint, setS3Endpoint] = useState("");
  const [s3Bucket, setS3Bucket] = useState("");
  const [s3Region, setS3Region] = useState("auto");
  const [s3AccessKey, setS3AccessKey] = useState("");
  const [s3SecretKey, setS3SecretKey] = useState("");
  const [s3Prefix, setS3Prefix] = useState("zcode-backups/");
  const [showSecretKey, setShowSecretKey] = useState(false);

  // WebDAV 配置
  const [davUrl, setDavUrl] = useState("");
  const [davUsername, setDavUsername] = useState("");
  const [davPassword, setDavPassword] = useState("");
  const [davRemoteDir, setDavRemoteDir] = useState("zcode-backups");
  const [showDavPassword, setShowDavPassword] = useState(false);

  // 保留策略
  const [maxVersions, setMaxVersions] = useState<number>(10);
  const [retentionDays, setRetentionDays] = useState<number>(30);

  // 历史备份列表与状态
  const [remoteBackups, setRemoteBackups] = useState<CloudBackupItem[]>([]);
  const [isLoadingBackups, setIsLoadingBackups] = useState(false);

  // 独立的 S3 与 WebDAV 测试状态与结果反馈（严格隔离，绝不串门）
  const [isTestingS3, setIsTestingS3] = useState(false);
  const [s3TestResult, setS3TestResult] = useState<{ success: boolean; msg: string } | null>(null);

  const [isTestingDav, setIsTestingDav] = useState(false);
  const [davTestResult, setDavTestResult] = useState<{ success: boolean; msg: string } | null>(null);

  const [isSaving, setIsSaving] = useState(false);
  const [isBackingUp, setIsBackingUp] = useState(false);
  const [maskKeyOnUpload, setMaskKeyOnUpload] = useState(false);

  // 载入已有云配置
  useEffect(() => {
    (async () => {
      try {
        const cfg = await ApiService.getCloudConfig();
        if (cfg.provider_type) {
          setProviderType(cfg.provider_type);
        }
        if (cfg.s3) {
          setS3Endpoint(cfg.s3.endpoint || "");
          setS3Bucket(cfg.s3.bucket || "");
          setS3Region(cfg.s3.region || "auto");
          setS3AccessKey(cfg.s3.access_key || "");
          setS3SecretKey(cfg.s3.secret_key || "");
          setS3Prefix(cfg.s3.prefix || "zcode-backups/");
        }
        if (cfg.webdav) {
          setDavUrl(cfg.webdav.server_url || "");
          setDavUsername(cfg.webdav.username || "");
          setDavPassword(cfg.webdav.password || "");
          setDavRemoteDir(cfg.webdav.remote_dir || "zcode-backups");
        }
        if (cfg.retention) {
          setMaxVersions(cfg.retention.max_versions);
          setRetentionDays(cfg.retention.retention_days);
        }
      } catch (err: any) {
        console.warn("载入云配置失败:", err);
      }
    })();
  }, []);

  // 刷新云端历史备份
  const fetchRemoteBackups = async () => {
    setIsLoadingBackups(true);
    try {
      const list = await ApiService.listCloudBackups();
      setRemoteBackups(list);
    } catch (e: any) {
      onShowToast("error", "获取云端备份列表失败", e.message);
    } finally {
      setIsLoadingBackups(false);
    }
  };

  useEffect(() => {
    if (activeTab === "history") {
      fetchRemoteBackups();
    }
  }, [activeTab]);

  // 构造指定类型的云存储配置对象 (严格支持覆盖 targetType)
  const buildCurrentConfig = (targetType?: CloudProviderType): CloudConfig => ({
    provider_type: targetType || providerType,
    s3: {
      endpoint: s3Endpoint.trim(),
      bucket: s3Bucket.trim(),
      region: s3Region.trim(),
      access_key: s3AccessKey.trim(),
      secret_key: s3SecretKey.trim(),
      prefix: s3Prefix.trim(),
    },
    webdav: {
      server_url: davUrl.trim(),
      username: davUsername.trim(),
      password: davPassword.trim(),
      remote_dir: davRemoteDir.trim(),
    },
    retention: {
      max_versions: Number(maxVersions),
      retention_days: Number(retentionDays),
    },
  });

  // 针对 S3 / R2 专门的连通性测试（绝不触发 WebDAV）
  const handleTestS3 = async () => {
    setIsTestingS3(true);
    setS3TestResult(null);
    try {
      const config = buildCurrentConfig("s3");
      const msg = await ApiService.testCloudConnection(config);
      setS3TestResult({ success: true, msg });
      onShowToast("success", "S3/R2 连接成功", msg);
    } catch (e: any) {
      setS3TestResult({ success: false, msg: e.message });
      onShowToast("error", "S3/R2 连接失败", e.message);
    } finally {
      setIsTestingS3(false);
    }
  };

  // 针对 WebDAV 专门的连通性测试（绝不触发 S3 / R2）
  const handleTestWebDav = async () => {
    setIsTestingDav(true);
    setDavTestResult(null);
    try {
      const config = buildCurrentConfig("webdav");
      const msg = await ApiService.testCloudConnection(config);
      setDavTestResult({ success: true, msg });
      onShowToast("success", "WebDAV 连接成功", msg);
    } catch (e: any) {
      setDavTestResult({ success: false, msg: e.message });
      onShowToast("error", "WebDAV 连接失败", e.message);
    } finally {
      setIsTestingDav(false);
    }
  };

  // 保存当前配置
  const handleSaveConfig = async () => {
    setIsSaving(true);
    try {
      const config = buildCurrentConfig();
      const msg = await ApiService.saveCloudConfig(config);
      onShowToast("success", "配置已保存", msg);
    } catch (e: any) {
      onShowToast("error", "保存配置失败", e.message);
    } finally {
      setIsSaving(false);
    }
  };

  // 立即备份至云端
  const handleDoBackupNow = async () => {
    setIsBackingUp(true);
    try {
      await handleSaveConfig();
      await onBackupNow(maskKeyOnUpload);
      onShowToast(
        "success",
        "云端备份成功",
        `已成功将配置快照同步至 ${providerType === "s3" ? "S3/R2" : "WebDAV"} 并执行生命周期清理`
      );
      if (activeTab === "history") {
        fetchRemoteBackups();
      }
    } catch (e: any) {
      onShowToast("error", "云端备份失败", e.message);
    } finally {
      setIsBackingUp(false);
    }
  };

  // 恢复指定云端备份
  const handleRestoreBackup = async (fileName: string) => {
    if (
      !confirm(
        `确定要从云端备份 [${fileName}] 恢复配置并合并至本地吗？本地原有文件将自动生成 .bak 安全备份。`
      )
    ) {
      return;
    }

    try {
      const data = await ApiService.restoreCloudBackup(fileName);
      await onRestoreFromCloud(data, fileName);
    } catch (e: any) {
      onShowToast("error", "恢复失败", e.message);
    }
  };

  // 删除云端指定备份
  const handleDeleteBackup = async (fileName: string) => {
    if (!confirm(`确定要从远端存储中永久删除备份 [${fileName}] 吗？`)) {
      return;
    }

    try {
      const msg = await ApiService.deleteCloudBackup(fileName);
      onShowToast("success", "删除成功", msg);
      setRemoteBackups((prev) => prev.filter((b) => b.name !== fileName));
    } catch (e: any) {
      onShowToast("error", "删除失败", e.message);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 dark:bg-black/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-surface w-full max-w-2xl rounded-2xl border border-subtle shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        {/* 标题栏 */}
        <div className="p-4 border-b border-subtle flex items-center justify-between bg-surface-alt/50">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 shadow-sm">
              <Cloud className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-zinc-900 dark:text-white flex items-center gap-2">
                <span>云端同步与多端备份中枢</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface border border-subtle text-zinc-500 dark:text-zinc-400">
                  S3 / R2 / WebDAV
                </span>
              </h3>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                当前同步生效源:{" "}
                <span className="text-blue-600 dark:text-blue-400 font-semibold">
                  {providerType === "s3"
                    ? "☁️ S3 / Cloudflare R2"
                    : providerType === "webdav"
                    ? "📁 WebDAV (坚果云/NAS)"
                    : "未启用"}
                </span>
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-zinc-700 dark:hover:text-white p-1 rounded-lg hover:bg-surface-hover transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* 顶部四选项卡切换 */}
        <div className="flex border-b border-subtle bg-surface px-4 pt-2 gap-4 text-xs font-semibold">
          <button
            onClick={() => setActiveTab("s3")}
            className={`flex items-center gap-1.5 pb-2.5 border-b-2 transition-all ${
              activeTab === "s3"
                ? "border-blue-500 text-blue-600 dark:text-blue-400"
                : "border-transparent text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-zinc-200"
            }`}
          >
            <Server className="w-3.5 h-3.5" />
            <span>S3 / Cloudflare R2</span>
            {providerType === "s3" && (
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500" title="当前激活源" />
            )}
          </button>

          <button
            onClick={() => setActiveTab("webdav")}
            className={`flex items-center gap-1.5 pb-2.5 border-b-2 transition-all ${
              activeTab === "webdav"
                ? "border-blue-500 text-blue-600 dark:text-blue-400"
                : "border-transparent text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-zinc-200"
            }`}
          >
            <FolderSync className="w-3.5 h-3.5" />
            <span>WebDAV (坚果云/NAS)</span>
            {providerType === "webdav" && (
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500" title="当前激活源" />
            )}
          </button>

          <button
            onClick={() => setActiveTab("retention")}
            className={`flex items-center gap-1.5 pb-2.5 border-b-2 transition-all ${
              activeTab === "retention"
                ? "border-blue-500 text-blue-600 dark:text-blue-400"
                : "border-transparent text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-zinc-200"
            }`}
          >
            <Clock className="w-3.5 h-3.5" />
            <span>保留策略与生命周期</span>
          </button>

          <button
            onClick={() => setActiveTab("history")}
            className={`flex items-center gap-1.5 pb-2.5 border-b-2 transition-all ${
              activeTab === "history"
                ? "border-blue-500 text-blue-600 dark:text-blue-400"
                : "border-transparent text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-zinc-200"
            }`}
          >
            <History className="w-3.5 h-3.5" />
            <span>历史版本列表</span>
            {remoteBackups.length > 0 && (
              <span className="text-[10px] font-mono px-1.5 rounded-full bg-surface-alt border border-subtle text-zinc-400">
                {remoteBackups.length}
              </span>
            )}
          </button>
        </div>

        {/* 内容展示区 */}
        <div className="p-5 flex-1 overflow-y-auto space-y-4 text-xs">
          {/* Tab 1: S3 / Cloudflare R2 */}
          {activeTab === "s3" && (
            <div className="space-y-3.5 animate-in fade-in duration-100">
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-surface-alt/60 border border-subtle">
                <div className="flex items-center gap-2">
                  <span className="text-zinc-700 dark:text-zinc-300 font-semibold">
                    云备份存储源:
                  </span>
                  <span className="text-[11px] text-zinc-500">
                    {providerType === "s3" ? "当前已激活 S3 / R2" : "当前未激活"}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setProviderType("s3")}
                  className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
                    providerType === "s3"
                      ? "bg-blue-600 text-white shadow-sm"
                      : "bg-surface hover:bg-surface-hover text-zinc-700 dark:text-zinc-200 border border-subtle"
                  }`}
                >
                  {providerType === "s3" && <Check className="w-3.5 h-3.5" />}
                  <span>{providerType === "s3" ? "已激活 S3" : "设为同步激活源"}</span>
                </button>
              </div>

              <div>
                <label className="block text-zinc-700 dark:text-zinc-300 font-medium mb-1">
                  S3 接入端点 (Endpoint URL)
                </label>
                <input
                  type="text"
                  value={s3Endpoint}
                  onChange={(e) => setS3Endpoint(e.target.value)}
                  placeholder="例如: https://<account_id>.r2.cloudflarestorage.com"
                  className="w-full bg-input text-zinc-900 dark:text-zinc-100 font-mono text-xs rounded-lg px-3 py-2 border border-subtle focus:border-blue-500 focus:outline-none shadow-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-zinc-700 dark:text-zinc-300 font-medium mb-1">
                    存储桶名称 (Bucket Name)
                  </label>
                  <input
                    type="text"
                    value={s3Bucket}
                    onChange={(e) => setS3Bucket(e.target.value)}
                    placeholder="例如: zcode-backups"
                    className="w-full bg-input text-zinc-900 dark:text-zinc-100 font-mono text-xs rounded-lg px-3 py-2 border border-subtle focus:border-blue-500 focus:outline-none shadow-sm"
                  />
                </div>

                <div>
                  <label className="block text-zinc-700 dark:text-zinc-300 font-medium mb-1">
                    区域代号 (Region)
                  </label>
                  <input
                    type="text"
                    value={s3Region}
                    onChange={(e) => setS3Region(e.target.value)}
                    placeholder="R2 默认填 auto，AWS 如 us-east-1"
                    className="w-full bg-input text-zinc-900 dark:text-zinc-100 font-mono text-xs rounded-lg px-3 py-2 border border-subtle focus:border-blue-500 focus:outline-none shadow-sm"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-zinc-700 dark:text-zinc-300 font-medium mb-1">
                    Access Key ID
                  </label>
                  <input
                    type="text"
                    value={s3AccessKey}
                    onChange={(e) => setS3AccessKey(e.target.value)}
                    placeholder="AKIA..."
                    className="w-full bg-input text-zinc-900 dark:text-zinc-100 font-mono text-xs rounded-lg px-3 py-2 border border-subtle focus:border-blue-500 focus:outline-none shadow-sm"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-zinc-700 dark:text-zinc-300 font-medium">
                      Secret Access Key
                    </label>
                    <button
                      type="button"
                      onClick={() => setShowSecretKey(!showSecretKey)}
                      className="text-[11px] text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 flex items-center gap-1"
                    >
                      {showSecretKey ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3 text-zinc-400" />}
                      <span>{showSecretKey ? "隐藏" : "显示"}</span>
                    </button>
                  </div>
                  <input
                    type={showSecretKey ? "text" : "password"}
                    value={s3SecretKey}
                    onChange={(e) => setS3SecretKey(e.target.value)}
                    placeholder="Secret Key..."
                    className="w-full bg-input text-zinc-900 dark:text-zinc-100 font-mono text-xs rounded-lg px-3 py-2 border border-subtle focus:border-blue-500 focus:outline-none shadow-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-zinc-700 dark:text-zinc-300 font-medium mb-1">
                  桶内路径前缀 (Path Prefix)
                </label>
                <input
                  type="text"
                  value={s3Prefix}
                  onChange={(e) => setS3Prefix(e.target.value)}
                  placeholder="默认: zcode-backups/"
                  className="w-full bg-input text-zinc-900 dark:text-zinc-100 font-mono text-xs rounded-lg px-3 py-2 border border-subtle focus:border-blue-500 focus:outline-none shadow-sm"
                />
              </div>

              {/* S3 专属测试连通性按钮与反馈 */}
              <div className="pt-2 flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleTestS3}
                  disabled={isTestingS3}
                  className="px-3.5 py-1.5 text-xs font-semibold text-zinc-700 dark:text-zinc-200 hover:text-zinc-900 dark:hover:text-white bg-surface hover:bg-surface-hover rounded-lg border border-subtle transition-all active:scale-95 disabled:opacity-50 shadow-sm"
                >
                  {isTestingS3 ? "正在测试 S3 / R2..." : "⚡ 测试 S3 / R2 连通性"}
                </button>
                <span className="text-[11px] text-zinc-500">仅校验上方 S3 / R2 端点与凭证，不影响 WebDAV</span>
              </div>

              {s3TestResult && (
                <div
                  className={`p-3 rounded-xl border text-xs flex items-center gap-2.5 transition-all ${
                    s3TestResult.success
                      ? "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-300 dark:border-emerald-500/30 text-emerald-800 dark:text-emerald-300"
                      : "bg-rose-50 dark:bg-rose-950/40 border-rose-300 dark:border-rose-500/30 text-rose-800 dark:text-rose-300"
                  }`}
                >
                  {s3TestResult.success ? (
                    <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
                  ) : (
                    <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 dark:text-rose-400" />
                  )}
                  <span className="font-medium leading-relaxed">{s3TestResult.msg}</span>
                </div>
              )}
            </div>
          )}

          {/* Tab 2: WebDAV */}
          {activeTab === "webdav" && (
            <div className="space-y-3.5 animate-in fade-in duration-100">
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-surface-alt/60 border border-subtle">
                <div className="flex items-center gap-2">
                  <span className="text-zinc-700 dark:text-zinc-300 font-semibold">
                    云备份存储源:
                  </span>
                  <span className="text-[11px] text-zinc-500">
                    {providerType === "webdav" ? "当前已激活 WebDAV" : "当前未激活"}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setProviderType("webdav")}
                  className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
                    providerType === "webdav"
                      ? "bg-blue-600 text-white shadow-sm"
                      : "bg-surface hover:bg-surface-hover text-zinc-700 dark:text-zinc-200 border border-subtle"
                  }`}
                >
                  {providerType === "webdav" && <Check className="w-3.5 h-3.5" />}
                  <span>{providerType === "webdav" ? "已激活 WebDAV" : "设为同步激活源"}</span>
                </button>
              </div>

              <div>
                <label className="block text-zinc-700 dark:text-zinc-300 font-medium mb-1">
                  WebDAV 服务器完整地址 (Server URL)
                </label>
                <input
                  type="text"
                  value={davUrl}
                  onChange={(e) => setDavUrl(e.target.value)}
                  placeholder="例如: https://dav.jianguoyun.com/dav/ 或 https://nas.local:5005/dav/"
                  className="w-full bg-input text-zinc-900 dark:text-zinc-100 font-mono text-xs rounded-lg px-3 py-2 border border-subtle focus:border-blue-500 focus:outline-none shadow-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-zinc-700 dark:text-zinc-300 font-medium mb-1">
                    账号 / 邮箱 (Username)
                  </label>
                  <input
                    type="text"
                    value={davUsername}
                    onChange={(e) => setDavUsername(e.target.value)}
                    placeholder="user@example.com"
                    className="w-full bg-input text-zinc-900 dark:text-zinc-100 font-mono text-xs rounded-lg px-3 py-2 border border-subtle focus:border-blue-500 focus:outline-none shadow-sm"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-zinc-700 dark:text-zinc-300 font-medium">
                      密码 / 应用授权码 (Password)
                    </label>
                    <button
                      type="button"
                      onClick={() => setShowDavPassword(!showDavPassword)}
                      className="text-[11px] text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 flex items-center gap-1"
                    >
                      {showDavPassword ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3 text-zinc-400" />}
                      <span>{showDavPassword ? "隐藏" : "显示"}</span>
                    </button>
                  </div>
                  <input
                    type={showDavPassword ? "text" : "password"}
                    value={davPassword}
                    onChange={(e) => setDavPassword(e.target.value)}
                    placeholder="密码或坚果云应用授权码..."
                    className="w-full bg-input text-zinc-900 dark:text-zinc-100 font-mono text-xs rounded-lg px-3 py-2 border border-subtle focus:border-blue-500 focus:outline-none shadow-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-zinc-700 dark:text-zinc-300 font-medium mb-1">
                  远端备份子目录 (Remote Directory)
                </label>
                <input
                  type="text"
                  value={davRemoteDir}
                  onChange={(e) => setDavRemoteDir(e.target.value)}
                  placeholder="默认: zcode-backups (将自动探测并创建)"
                  className="w-full bg-input text-zinc-900 dark:text-zinc-100 font-mono text-xs rounded-lg px-3 py-2 border border-subtle focus:border-blue-500 focus:outline-none shadow-sm"
                />
              </div>

              {/* WebDAV 专属测试连通性按钮与反馈 */}
              <div className="pt-2 flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleTestWebDav}
                  disabled={isTestingDav}
                  className="px-3.5 py-1.5 text-xs font-semibold text-zinc-700 dark:text-zinc-200 hover:text-zinc-900 dark:hover:text-white bg-surface hover:bg-surface-hover rounded-lg border border-subtle transition-all active:scale-95 disabled:opacity-50 shadow-sm"
                >
                  {isTestingDav ? "正在测试 WebDAV..." : "⚡ 测试 WebDAV 连通性"}
                </button>
                <span className="text-[11px] text-zinc-500">仅校验上方 WebDAV 地址与认证，绝不触发 S3 / R2</span>
              </div>

              {davTestResult && (
                <div
                  className={`p-3 rounded-xl border text-xs flex items-center gap-2.5 transition-all ${
                    davTestResult.success
                      ? "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-300 dark:border-emerald-500/30 text-emerald-800 dark:text-emerald-300"
                      : "bg-rose-50 dark:bg-rose-950/40 border-rose-300 dark:border-rose-500/30 text-rose-800 dark:text-rose-300"
                  }`}
                >
                  {davTestResult.success ? (
                    <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
                  ) : (
                    <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 dark:text-rose-400" />
                  )}
                  <span className="font-medium leading-relaxed">{davTestResult.msg}</span>
                </div>
              )}
            </div>
          )}

          {/* Tab 3: 保留策略与生命周期 */}
          {activeTab === "retention" && (
            <div className="space-y-4 animate-in fade-in duration-100">
              <div className="p-3.5 rounded-xl bg-surface-alt/60 border border-subtle space-y-3">
                <h4 className="font-semibold text-zinc-900 dark:text-white flex items-center gap-2">
                  <Clock className="w-4 h-4 text-blue-500" />
                  <span>远端备份自动清理规则 (Retention Lifecycle)</span>
                </h4>
                <p className="text-zinc-500 dark:text-zinc-400 leading-relaxed text-[11px]">
                  每次您在本地点击“备份至云端”成功后，系统将在后台自动扫描远端历史对象，并按照以下规则执行智能归档淘汰。
                </p>

                <div className="grid grid-cols-2 gap-4 pt-1">
                  <div>
                    <label className="block text-zinc-700 dark:text-zinc-300 font-medium mb-1.5">
                      最大保留版本份数 (Max Versions)
                    </label>
                    <select
                      value={maxVersions}
                      onChange={(e) => setMaxVersions(Number(e.target.value))}
                      className="w-full bg-input text-zinc-900 dark:text-zinc-100 text-xs rounded-lg px-3 py-2 border border-subtle focus:border-blue-500 focus:outline-none cursor-pointer shadow-sm"
                    >
                      <option value={5}>保留最近 5 份</option>
                      <option value={10}>保留最近 10 份 (推荐默认)</option>
                      <option value={20}>保留最近 20 份</option>
                      <option value={50}>保留最近 50 份</option>
                      <option value={0}>不限制份数 (永久保存全部历史)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-zinc-700 dark:text-zinc-300 font-medium mb-1.5">
                      最长保留天数 (Retention Days)
                    </label>
                    <select
                      value={retentionDays}
                      onChange={(e) => setRetentionDays(Number(e.target.value))}
                      className="w-full bg-input text-zinc-900 dark:text-zinc-100 text-xs rounded-lg px-3 py-2 border border-subtle focus:border-blue-500 focus:outline-none cursor-pointer shadow-sm"
                    >
                      <option value={7}>保留 7 天以内的备份</option>
                      <option value={30}>保留 30 天以内的备份 (推荐默认)</option>
                      <option value={90}>保留 90 天以内的备份</option>
                      <option value={180}>保留 180 天以内的备份</option>
                      <option value={0}>永久保留 (按天不过期)</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* 安全底线说明 */}
              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-800 dark:text-emerald-300 flex items-start gap-2.5">
                <Shield className="w-4 h-4 shrink-0 mt-0.5" />
                <div className="text-[11px] leading-relaxed">
                  <strong className="font-semibold">绝对底线防空保护机制：</strong>
                  即使所有备份的时间均已超出设定的天数，清理引擎也绝不删除时间最近的至少 1 份完整备份，确保任何情况下远端备份都不为空。
                </div>
              </div>
            </div>
          )}

          {/* Tab 4: 历史版本列表 */}
          {activeTab === "history" && (
            <div className="space-y-3 animate-in fade-in duration-100">
              <div className="flex items-center justify-between">
                <span className="text-zinc-500 dark:text-zinc-400 font-medium">
                  云端存储的备份快照清单 ({providerType === "s3" ? "S3/R2" : "WebDAV"}):
                </span>
                <button
                  type="button"
                  onClick={fetchRemoteBackups}
                  disabled={isLoadingBackups}
                  className="flex items-center gap-1 text-[11px] text-zinc-600 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white bg-surface-alt px-2.5 py-1 rounded-md border border-subtle transition-all active:scale-95 disabled:opacity-50"
                >
                  <RotateCw className={`w-3 h-3 ${isLoadingBackups ? "animate-spin" : ""}`} />
                  <span>刷新清单</span>
                </button>
              </div>

              <div className="max-h-64 overflow-y-auto divide-y divide-subtle/50 rounded-xl bg-input/40 border border-subtle">
                {remoteBackups.length === 0 ? (
                  <div className="py-12 text-center text-zinc-400 dark:text-zinc-500 space-y-1.5">
                    <Layers className="w-7 h-7 mx-auto text-zinc-400 dark:text-zinc-600" />
                    <p className="font-medium text-xs">云端暂无备份记录</p>
                    <p className="text-[11px]">点击底部“立即备份至云端”创建第一份快照</p>
                  </div>
                ) : (
                  remoteBackups.map((b) => (
                    <div
                      key={b.name}
                      className="p-3 flex items-center justify-between hover:bg-surface-hover/70 transition-colors group"
                    >
                      <div className="space-y-0.5">
                        <div className="font-mono font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                          <span>{b.name}</span>
                          <span className="text-[10px] font-sans px-1.5 py-0.5 rounded bg-surface border border-subtle text-zinc-500">
                            {b.provider_count} 服务商
                          </span>
                        </div>
                        <div className="text-[11px] text-zinc-500 dark:text-zinc-400 flex items-center gap-3">
                          <span>时间: {b.last_modified}</span>
                          <span>大小: {(b.size_bytes / 1024).toFixed(1)} KB</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => handleRestoreBackup(b.name)}
                          className="flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-md bg-blue-50 dark:bg-blue-950/60 hover:bg-blue-100 dark:hover:bg-blue-900/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-500/30 transition-all active:scale-95 shadow-sm"
                        >
                          <Download className="w-3 h-3" />
                          <span>恢复并合并</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteBackup(b.name)}
                          className="p-1 text-zinc-400 hover:text-rose-500 hover:bg-surface rounded transition-colors"
                          title="从云端彻底删除此备份"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* 底部按钮栏 */}
        <div className="p-4 border-t border-subtle flex items-center justify-between bg-surface-alt/30">
          <label className="flex items-center gap-2 text-xs text-zinc-600 dark:text-zinc-400 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={maskKeyOnUpload}
              onChange={() => setMaskKeyOnUpload(!maskKeyOnUpload)}
              className="rounded bg-input border-subtle text-blue-600 focus:ring-0 cursor-pointer"
            />
            <span>备份时抹除 API Key (脱敏)</span>
          </label>

          <div className="flex items-center gap-2.5">
            {/* 智能针对当前选项卡的测试按钮 */}
            {activeTab === "s3" && (
              <button
                type="button"
                onClick={handleTestS3}
                disabled={isTestingS3}
                className="px-3.5 py-1.5 text-xs font-semibold text-zinc-700 dark:text-zinc-200 hover:text-zinc-900 dark:hover:text-white bg-surface hover:bg-surface-hover rounded-lg border border-subtle transition-all active:scale-95 disabled:opacity-50 shadow-sm"
              >
                {isTestingS3 ? "正在测试 S3..." : "测试 S3 / R2"}
              </button>
            )}

            {activeTab === "webdav" && (
              <button
                type="button"
                onClick={handleTestWebDav}
                disabled={isTestingDav}
                className="px-3.5 py-1.5 text-xs font-semibold text-zinc-700 dark:text-zinc-200 hover:text-zinc-900 dark:hover:text-white bg-surface hover:bg-surface-hover rounded-lg border border-subtle transition-all active:scale-95 disabled:opacity-50 shadow-sm"
              >
                {isTestingDav ? "正在测试 WebDAV..." : "测试 WebDAV"}
              </button>
            )}

            <button
              type="button"
              onClick={handleSaveConfig}
              disabled={isSaving}
              className="px-3.5 py-1.5 text-xs font-semibold text-zinc-700 dark:text-zinc-200 hover:text-zinc-900 dark:hover:text-white bg-surface hover:bg-surface-hover rounded-lg border border-subtle transition-all active:scale-95 disabled:opacity-50 shadow-sm"
            >
              <Save className="w-3.5 h-3.5 inline mr-1" />
              <span>{isSaving ? "保存中..." : "保存配置"}</span>
            </button>

            <button
              type="button"
              onClick={handleDoBackupNow}
              disabled={isBackingUp}
              className="px-4 py-1.5 text-xs font-bold text-white bg-primary hover:bg-primary-hover rounded-lg shadow-lg shadow-blue-600/20 transition-all flex items-center gap-1.5 active:scale-95 disabled:opacity-50"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>
                {isBackingUp
                  ? "正在备份..."
                  : `备份至 ${providerType === "s3" ? "S3/R2" : "WebDAV"}`}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
