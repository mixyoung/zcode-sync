import React from "react";
import { FolderOpen, Plus, Database } from "lucide-react";
import { ConfigFileMeta } from "../types";

interface ConfigSelectorCardProps {
  configs: ConfigFileMeta[];
  selectedPath: string;
  onSelect: (path: string) => void;
  onAddCustom: () => void;
  onOpenFolder: () => void;
}

export const ConfigSelectorCard: React.FC<ConfigSelectorCardProps> = ({
  configs,
  selectedPath,
  onSelect,
  onAddCustom,
  onOpenFolder,
}) => {
  const currentConfig = configs.find((c) => c.path === selectedPath);

  return (
    <div className="bg-surface rounded-xl p-3.5 border border-subtle shadow-sm">
      <div className="flex items-center gap-2.5">
        <label className="text-xs font-semibold text-zinc-700 dark:text-zinc-300 shrink-0 flex items-center gap-1.5">
          <Database className="w-3.5 h-3.5 text-zinc-500 dark:text-zinc-400" />
          <span>当前查看的配置文件:</span>
        </label>

        <div className="relative flex-1 min-w-0">
          <select
            value={selectedPath}
            onChange={(e) => onSelect(e.target.value)}
            className="w-full bg-input text-zinc-900 dark:text-zinc-100 text-xs rounded-lg px-3 py-1.5 border border-subtle hover:border-subtle-hover focus:border-blue-500 focus:outline-none transition-all truncate pr-8 cursor-pointer"
          >
            <option value="ALL">【全部配置文件】(聚合查看所有服务商)</option>
            {configs.map((c) => (
              <option key={c.path} value={c.path}>
                {c.label} ({c.provider_count}个服务商, {c.custom_count}个自定义) - {c.path}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={onAddCustom}
          className="flex items-center gap-1 text-xs text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white bg-surface-alt hover:bg-surface-hover px-2.5 py-1.5 rounded-lg border border-subtle transition-all active:scale-95 shrink-0"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>添加配置...</span>
        </button>

        <button
          onClick={onOpenFolder}
          className="flex items-center gap-1 text-xs text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white bg-surface-alt hover:bg-surface-hover px-2.5 py-1.5 rounded-lg border border-subtle transition-all active:scale-95 shrink-0"
          title="在系统文件管理器中打开"
        >
          <FolderOpen className="w-3.5 h-3.5 text-zinc-500 dark:text-zinc-400" />
          <span>打开目录</span>
        </button>
      </div>

      <div className="mt-2.5 pt-2.5 border-t border-subtle/60 flex items-center justify-between text-[11px] font-mono text-zinc-500 dark:text-zinc-400">
        <div className="flex items-center gap-2 truncate">
          <span className="w-1.5 h-1.5 rounded-full bg-sky-500 shrink-0" />
          {selectedPath === "ALL" ? (
            <span>
              已聚合扫描 <strong className="text-zinc-800 dark:text-zinc-200">{configs.length}</strong> 个物理配置文件
            </span>
          ) : (
            <span className="truncate">
              物理路径: <span className="text-zinc-700 dark:text-zinc-300 select-all">{currentConfig?.path}</span>
            </span>
          )}
        </div>

        {currentConfig && selectedPath !== "ALL" && (
          <div className="flex items-center gap-3 shrink-0 text-zinc-400 dark:text-zinc-500">
            <span>大小: {currentConfig.size_bytes} 字节</span>
            <span>更新于: {currentConfig.updated_at}</span>
          </div>
        )}
      </div>
    </div>
  );
};
