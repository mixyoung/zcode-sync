import React from "react";
import {
  Upload,
  Download,
  Copy,
  ClipboardCheck,
  Edit3,
  Trash2,
  Shield,
} from "lucide-react";

interface ActionConsoleProps {
  selectedCount: number;
  maskApiKey: boolean;
  onToggleMaskKey: () => void;
  onEditSelected: () => void;
  onDeleteSelected: () => void;
  onExportFile: () => void;
  onImportFile: () => void;
  onCopyClipboard: () => void;
  onImportClipboard: () => void;
}

export const ActionConsole: React.FC<ActionConsoleProps> = ({
  selectedCount,
  maskApiKey,
  onToggleMaskKey,
  onEditSelected,
  onDeleteSelected,
  onExportFile,
  onImportFile,
  onCopyClipboard,
  onImportClipboard,
}) => {
  return (
    <div className="space-y-2.5">
      {/* 选中项管理工具条 */}
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2.5">
          <button
            onClick={onEditSelected}
            disabled={selectedCount === 0}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-surface hover:bg-surface-hover text-zinc-800 dark:text-zinc-200 hover:text-zinc-900 dark:hover:text-white border border-subtle transition-all active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
          >
            <Edit3 className="w-3.5 h-3.5 text-blue-500 dark:text-blue-400" />
            <span>编辑选中配置</span>
          </button>

          <button
            onClick={onDeleteSelected}
            disabled={selectedCount === 0}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-rose-50 dark:bg-rose-950/40 hover:bg-rose-100 dark:hover:bg-rose-950/70 text-rose-700 dark:text-rose-300 border border-rose-300 dark:border-rose-500/30 transition-all active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>删除选中配置</span>
          </button>

          <label className="flex items-center gap-2 text-xs text-zinc-600 dark:text-zinc-400 cursor-pointer hover:text-zinc-900 dark:hover:text-zinc-200 select-none ml-2">
            <input
              type="checkbox"
              checked={maskApiKey}
              onChange={onToggleMaskKey}
              className="rounded bg-input border-subtle text-blue-600 focus:ring-0 cursor-pointer"
            />
            <span>导出时抹除 API Key (安全脱敏)</span>
          </label>
        </div>

        <div className="text-[11px] text-zinc-500 dark:text-zinc-400">
          {selectedCount > 0
            ? `已选择 ${selectedCount} 项，导出将仅包含选定服务商`
            : "未勾选服务商时，默认导出当前视图全部配置"}
        </div>
      </div>

      {/* 2x2 对称现代化操作控制台 */}
      <div className="grid grid-cols-2 gap-2.5">
        <button
          onClick={onExportFile}
          className="flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl font-bold text-xs bg-primary hover:bg-primary-hover text-white shadow-lg shadow-blue-600/20 border border-blue-400/20 transition-all active:scale-[0.99]"
        >
          <Upload className="w-4 h-4" />
          <span>导出为 JSON 文件 (主要操作)</span>
        </button>

        <button
          onClick={onImportFile}
          className="flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl font-semibold text-xs bg-surface hover:bg-surface-hover text-zinc-800 dark:text-zinc-200 hover:text-zinc-900 dark:hover:text-white border border-subtle transition-all active:scale-[0.99] shadow-sm"
        >
          <Download className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
          <span>从文件导入配置</span>
        </button>

        <button
          onClick={onCopyClipboard}
          className="flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl font-semibold text-xs bg-surface hover:bg-surface-hover text-zinc-800 dark:text-zinc-200 hover:text-zinc-900 dark:hover:text-white border border-subtle transition-all active:scale-[0.99] shadow-sm"
        >
          <Copy className="w-4 h-4 text-sky-600 dark:text-sky-400" />
          <span>复制到系统剪贴板</span>
        </button>

        <button
          onClick={onImportClipboard}
          className="flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl font-semibold text-xs bg-surface hover:bg-surface-hover text-zinc-800 dark:text-zinc-200 hover:text-zinc-900 dark:hover:text-white border border-subtle transition-all active:scale-[0.99] shadow-sm"
        >
          <ClipboardCheck className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
          <span>从系统剪贴板导入</span>
        </button>
      </div>

      {/* 底部安全状态保障行 */}
      <div className="flex items-center justify-between text-[11px] text-zinc-500 dark:text-zinc-400 px-1 pt-1">
        <div className="flex items-center gap-1.5">
          <Shield className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
          <span>
            安全保障：写入前自动创建 .bak 历史双重备份 | 原子替换防损坏 | 增量合并绝不冲掉已有未冲突项
          </span>
        </div>
        <span>修改后重启 ZCode 客户端生效</span>
      </div>
    </div>
  );
};
