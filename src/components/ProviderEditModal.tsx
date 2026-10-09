import React, { useState } from "react";
import { UnifiedProviderItem } from "../types";
import {
  X,
  Save,
  Code2,
  FileEdit,
  Eye,
  EyeOff,
  Plus,
  Trash2,
  AlertTriangle,
} from "lucide-react";

interface ProviderEditModalProps {
  item: UnifiedProviderItem;
  isOpen: boolean;
  onClose: () => void;
  onSave: (updatedItem: UnifiedProviderItem) => Promise<void>;
}

export const ProviderEditModal: React.FC<ProviderEditModalProps> = ({
  item,
  isOpen,
  onClose,
  onSave,
}) => {
  if (!isOpen) return null;

  const [activeTab, setActiveTab] = useState<"form" | "json">("form");
  const [name, setName] = useState(item.name);
  const [kind, setKind] = useState(item.kind);
  const [enabled, setEnabled] = useState(item.enabled);

  const rawOptions = item.raw_data.options || {};
  const [baseURL, setBaseURL] = useState(rawOptions.baseURL || "");
  const [apiKey, setApiKey] = useState(rawOptions.apiKey || "");
  const [showKey, setShowKey] = useState(false);

  const [models, setModels] = useState<string[]>([...item.models]);
  const [newModelName, setNewModelName] = useState("");

  const [jsonText, setJsonText] = useState(() =>
    JSON.stringify(item.raw_data, null, 2)
  );
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const handleTabChange = (tab: "form" | "json") => {
    if (tab === "json") {
      const synData = {
        ...item.raw_data,
        name,
        kind,
        enabled,
        options: {
          ...item.raw_data.options,
          baseURL,
          apiKey,
        },
      };
      setJsonText(JSON.stringify(synData, null, 2));
      setJsonError(null);
    } else {
      try {
        const parsed = JSON.parse(jsonText);
        setName(parsed.name || name);
        setKind(parsed.kind || kind);
        if (parsed.options) {
          setBaseURL(parsed.options.baseURL || "");
          setApiKey(parsed.options.apiKey || "");
        }
        setJsonError(null);
      } catch (err: any) {
        setJsonError(`JSON 格式无效: ${err.message}`);
      }
    }
    setActiveTab(tab);
  };

  const handleAddModel = () => {
    const trimmed = newModelName.trim();
    if (trimmed && !models.includes(trimmed)) {
      setModels([...models, trimmed]);
      setNewModelName("");
    }
  };

  const handleRemoveModel = (m: string) => {
    setModels(models.filter((x) => x !== m));
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      let finalRaw = { ...item.raw_data };
      if (activeTab === "json") {
        finalRaw = JSON.parse(jsonText);
      } else {
        finalRaw.name = name;
        finalRaw.kind = kind;
        finalRaw.enabled = enabled;
        finalRaw.options = {
          ...finalRaw.options,
          baseURL,
          apiKey,
        };
        const modelMap: Record<string, any> = {};
        for (const m of models) {
          modelMap[m] = finalRaw.models?.[m] || {
            limit: { context: 128000, output: 8192 },
          };
        }
        finalRaw.models = modelMap;
      }

      const updated: UnifiedProviderItem = {
        ...item,
        name: finalRaw.name || name,
        kind: finalRaw.kind || kind,
        models:
          activeTab === "form"
            ? models
            : Object.keys(finalRaw.models || {}),
        raw_data: finalRaw,
      };

      await onSave(updated);
      onClose();
    } catch (e: any) {
      alert(`保存出错: ${e.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 dark:bg-black/75 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-surface w-full max-w-2xl rounded-2xl border border-subtle shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        {/* 标题栏 */}
        <div className="p-4 border-b border-subtle flex items-center justify-between bg-surface-alt/50">
          <div>
            <h3 className="text-sm font-bold text-zinc-900 dark:text-white flex items-center gap-2">
              <FileEdit className="w-4 h-4 text-blue-500" />
              <span>编辑服务商配置 - {name || item.provider_id}</span>
            </h3>
            <p className="text-[11px] font-mono text-zinc-500 dark:text-zinc-400 mt-0.5 truncate max-w-md">
              目标落盘文件: {item.source_file}
            </p>
          </div>

          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-zinc-700 dark:hover:text-white p-1 rounded-lg hover:bg-surface-hover transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* 模式切换选项卡 */}
        <div className="flex border-b border-subtle bg-surface px-4 pt-2 gap-4">
          <button
            onClick={() => handleTabChange("form")}
            className={`flex items-center gap-1.5 pb-2.5 text-xs font-semibold border-b-2 transition-all ${
              activeTab === "form"
                ? "border-blue-500 text-blue-600 dark:text-blue-400"
                : "border-transparent text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-zinc-200"
            }`}
          >
            <FileEdit className="w-3.5 h-3.5" />
            <span>表单可视化编辑</span>
          </button>
          <button
            onClick={() => handleTabChange("json")}
            className={`flex items-center gap-1.5 pb-2.5 text-xs font-semibold border-b-2 transition-all ${
              activeTab === "json"
                ? "border-blue-500 text-blue-600 dark:text-blue-400"
                : "border-transparent text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-zinc-200"
            }`}
          >
            <Code2 className="w-3.5 h-3.5" />
            <span>高级 JSON 编辑</span>
          </button>
        </div>

        {/* 内容区 */}
        <div className="p-5 flex-1 overflow-y-auto space-y-4">
          {activeTab === "form" ? (
            <div className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-zinc-700 dark:text-zinc-300 font-medium mb-1.5">
                    服务商显示名称
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full bg-input text-zinc-900 dark:text-zinc-100 rounded-lg px-3 py-2 border border-subtle focus:border-blue-500 focus:outline-none"
                    placeholder="例如: DeepSeek 官方 API"
                  />
                </div>

                <div>
                  <label className="block text-zinc-700 dark:text-zinc-300 font-medium mb-1.5">
                    协议接口类型
                  </label>
                  <select
                    value={kind}
                    onChange={(e) => setKind(e.target.value)}
                    className="w-full bg-input text-zinc-900 dark:text-zinc-100 rounded-lg px-3 py-2 border border-subtle focus:border-blue-500 focus:outline-none cursor-pointer"
                  >
                    <option value="anthropic-messages">anthropic-messages</option>
                    <option value="anthropic">anthropic</option>
                    <option value="openai">openai</option>
                    <option value="gemini">gemini</option>
                    <option value="custom">custom</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-zinc-700 dark:text-zinc-300 font-medium mb-1.5">
                  Base URL (接口接入地址)
                </label>
                <input
                  type="text"
                  value={baseURL}
                  onChange={(e) => setBaseURL(e.target.value)}
                  className="w-full bg-input text-zinc-900 dark:text-zinc-100 rounded-lg px-3 py-2 border border-subtle focus:border-blue-500 focus:outline-none font-mono"
                  placeholder="例如: https://api.deepseek.com"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-zinc-700 dark:text-zinc-300 font-medium">
                    API Key (私有访问密钥)
                  </label>
                  <button
                    type="button"
                    onClick={() => setShowKey(!showKey)}
                    className="text-[11px] text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200 flex items-center gap-1"
                  >
                    {showKey ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                    <span>{showKey ? "隐藏密文" : "显示明文"}</span>
                  </button>
                </div>
                <input
                  type={showKey ? "text" : "password"}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="w-full bg-input text-zinc-900 dark:text-zinc-100 rounded-lg px-3 py-2 border border-subtle focus:border-blue-500 focus:outline-none font-mono"
                  placeholder="sk-..."
                />
              </div>

              {/* 模型清单 */}
              <div className="pt-2 border-t border-subtle">
                <label className="block text-zinc-700 dark:text-zinc-300 font-semibold mb-2">
                  模型清单列表 (Models)
                </label>
                <div className="flex gap-2 mb-3">
                  <input
                    type="text"
                    value={newModelName}
                    onChange={(e) => setNewModelName(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleAddModel()}
                    placeholder="输入模型标识并按回车 (例如: deepseek-chat)"
                    className="flex-1 bg-input text-zinc-900 dark:text-zinc-100 rounded-lg px-3 py-1.5 border border-subtle focus:border-blue-500 focus:outline-none font-mono text-xs"
                  />
                  <button
                    type="button"
                    onClick={handleAddModel}
                    className="px-3 py-1.5 bg-surface-alt hover:bg-surface-hover text-zinc-800 dark:text-zinc-200 rounded-lg border border-subtle flex items-center gap-1 shrink-0"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>添加</span>
                  </button>
                </div>

                <div className="max-h-36 overflow-y-auto space-y-1 p-2 rounded-lg bg-surface-alt/50 border border-subtle">
                  {models.map((m) => (
                    <div
                      key={m}
                      className="flex items-center justify-between px-2.5 py-1 rounded bg-surface border border-subtle/70 text-zinc-800 dark:text-zinc-200 text-xs font-mono group"
                    >
                      <span>{m}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveModel(m)}
                        className="text-zinc-400 hover:text-rose-500 p-0.5 transition-colors"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col space-y-2">
              {jsonError && (
                <div className="p-2.5 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-500/30 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>{jsonError}</span>
                </div>
              )}
              <textarea
                value={jsonText}
                onChange={(e) => {
                  setJsonText(e.target.value);
                  setJsonError(null);
                }}
                className="w-full h-80 bg-input text-blue-600 dark:text-sky-400 font-mono text-xs p-3 rounded-lg border border-subtle focus:border-blue-500 focus:outline-none resize-none leading-relaxed"
                spellCheck={false}
              />
            </div>
          )}
        </div>

        {/* 底部按钮栏 */}
        <div className="p-4 border-t border-subtle flex items-center justify-end gap-3 bg-surface-alt/30">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white bg-surface hover:bg-surface-hover rounded-lg border border-subtle transition-all"
          >
            取消
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-4 py-2 text-xs font-semibold text-white bg-primary hover:bg-primary-hover rounded-lg shadow-lg shadow-blue-600/20 transition-all flex items-center gap-1.5 active:scale-95 disabled:opacity-50"
          >
            <Save className="w-3.5 h-3.5" />
            <span>{isSaving ? "正在保存..." : "保存修改并写入文件"}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
