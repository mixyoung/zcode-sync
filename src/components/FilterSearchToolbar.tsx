import React from "react";
import { Search, Sparkles, X } from "lucide-react";

interface FilterSearchToolbarProps {
  filterType: "all" | "custom" | "builtin";
  onFilterChange: (type: "all" | "custom" | "builtin") => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onOpenDuplicateModal: () => void;
  duplicateCount: number;
}

export const FilterSearchToolbar: React.FC<FilterSearchToolbarProps> = ({
  filterType,
  onFilterChange,
  searchQuery,
  onSearchChange,
  onOpenDuplicateModal,
  duplicateCount,
}) => {
  return (
    <div className="flex items-center justify-between gap-3">
      <div className="flex items-center gap-2">
        <span className="text-xs text-zinc-500 dark:text-zinc-400 font-medium">筛选:</span>
        <div className="flex items-center p-0.5 rounded-lg bg-surface border border-subtle shadow-sm">
          <button
            onClick={() => onFilterChange("all")}
            className={`px-2.5 py-1 text-xs rounded-md font-medium transition-all ${
              filterType === "all"
                ? "bg-surface-hover text-zinc-900 dark:text-white font-semibold shadow-sm"
                : "text-zinc-500 hover:text-zinc-800 dark:text-zinc-400 dark:hover:text-zinc-200"
            }`}
          >
            全部
          </button>
          <button
            onClick={() => onFilterChange("custom")}
            className={`px-2.5 py-1 text-xs rounded-md font-medium transition-all ${
              filterType === "custom"
                ? "bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20 font-semibold shadow-sm"
                : "text-zinc-500 hover:text-zinc-800 dark:text-zinc-400 dark:hover:text-zinc-200"
            }`}
          >
            仅自定义
          </button>
          <button
            onClick={() => onFilterChange("builtin")}
            className={`px-2.5 py-1 text-xs rounded-md font-medium transition-all ${
              filterType === "builtin"
                ? "bg-surface-hover text-zinc-900 dark:text-zinc-300 font-semibold shadow-sm"
                : "text-zinc-500 hover:text-zinc-800 dark:text-zinc-400 dark:hover:text-zinc-200"
            }`}
          >
            仅官方套餐
          </button>
        </div>

        {/* 搜索框 */}
        <div className="relative w-64 group ml-2">
          <Search className="w-3.5 h-3.5 text-zinc-400 group-focus-within:text-blue-500 absolute left-2.5 top-1/2 -translate-y-1/2 transition-colors" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="搜索服务商或模型..."
            className="w-full bg-input text-xs text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 dark:placeholder-zinc-500 rounded-lg pl-8 pr-12 py-1.5 border border-subtle focus:border-blue-500 focus:outline-none transition-all shadow-sm"
          />
          {searchQuery ? (
            <button
              onClick={() => onSearchChange("")}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          ) : (
            <kbd className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] font-mono text-zinc-400 dark:text-zinc-500 bg-surface px-1.5 py-0.5 rounded border border-subtle pointer-events-none">
              Ctrl+K
            </kbd>
          )}
        </div>
      </div>

      {/* 重复模型诊断按钮 */}
      <button
        onClick={onOpenDuplicateModal}
        className="flex items-center gap-1.5 text-xs text-zinc-700 dark:text-zinc-200 hover:text-zinc-900 dark:hover:text-white bg-surface hover:bg-surface-hover px-3 py-1.5 rounded-lg border border-subtle transition-all active:scale-95 group shadow-sm"
      >
        <Sparkles className="w-3.5 h-3.5 text-amber-500 group-hover:rotate-12 transition-transform" />
        <span>重复模型诊断</span>
        {duplicateCount > 0 && (
          <span className="ml-1 px-1.5 py-0.5 rounded-full text-[10px] font-mono bg-amber-500/10 dark:bg-amber-500/20 text-amber-600 dark:text-amber-300 border border-amber-500/30">
            {duplicateCount}
          </span>
        )}
      </button>
    </div>
  );
};
