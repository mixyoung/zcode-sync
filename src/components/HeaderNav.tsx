import React from "react";
import { RefreshCw, Cpu, Laptop, Sun, Moon, Cloud } from "lucide-react";
import { ThemeMode } from "../services/theme";

interface HeaderNavProps {
  onRefresh: () => void;
  isRefreshing: boolean;
  totalProviders: number;
  themeMode: ThemeMode;
  onThemeModeChange: (mode: ThemeMode) => void;
  onOpenCloudModal: () => void;
}

export const HeaderNav: React.FC<HeaderNavProps> = ({
  onRefresh,
  isRefreshing,
  totalProviders,
  themeMode,
  onThemeModeChange,
  onOpenCloudModal,
}) => {
  return (
    <header className="flex items-center justify-between pb-3 border-b border-subtle">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <Cpu className="w-4 h-4 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-base font-bold tracking-tight text-zinc-900 dark:text-white">
              ZCode 模型服务商配置管理
            </h1>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
              Tauri v2
            </span>
          </div>
          <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
            共载入 <span className="text-zinc-800 dark:text-zinc-200 font-semibold">{totalProviders}</span> 个服务商配置 • 极速原生同步
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2.5">
        {/* 云端同步与备份入口 */}
        <button
          onClick={onOpenCloudModal}
          className="flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-lg bg-blue-50 dark:bg-blue-950/50 hover:bg-blue-100 dark:hover:bg-blue-900/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-500/30 transition-all active:scale-95 shadow-sm"
          title="打开 S3 / R2 / WebDAV 云端备份与多端同步"
        >
          <Cloud className="w-3.5 h-3.5 text-blue-500" />
          <span>云端备份同步</span>
        </button>

        {/* 三段式黑白双主题与系统跟随切换胶囊 */}
        <div className="flex items-center p-0.5 rounded-lg bg-surface border border-subtle shadow-sm">
          <button
            onClick={() => onThemeModeChange("system")}
            className={`flex items-center gap-1 px-2.5 py-1 text-xs rounded-md transition-all ${
              themeMode === "system"
                ? "bg-surface-hover text-blue-600 dark:text-blue-400 font-semibold shadow-sm"
                : "text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
            }`}
            title="跟随系统 (自动响应 Windows 浅色/深色主题)"
          >
            <Laptop className="w-3.5 h-3.5" />
            <span>系统</span>
          </button>

          <button
            onClick={() => onThemeModeChange("light")}
            className={`flex items-center gap-1 px-2.5 py-1 text-xs rounded-md transition-all ${
              themeMode === "light"
                ? "bg-surface-hover text-amber-600 dark:text-amber-400 font-semibold shadow-sm"
                : "text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
            }`}
            title="浅色模式 (高对比洁白界面)"
          >
            <Sun className="w-3.5 h-3.5" />
            <span>浅色</span>
          </button>

          <button
            onClick={() => onThemeModeChange("dark")}
            className={`flex items-center gap-1 px-2.5 py-1 text-xs rounded-md transition-all ${
              themeMode === "dark"
                ? "bg-surface-hover text-indigo-600 dark:text-indigo-400 font-semibold shadow-sm"
                : "text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
            }`}
            title="深色模式 (Zinc 工业暗黑界面)"
          >
            <Moon className="w-3.5 h-3.5" />
            <span>深色</span>
          </button>
        </div>

        <div className="flex items-center gap-1.5 text-xs text-zinc-600 dark:text-zinc-400 bg-surface px-2.5 py-1 rounded-md border border-subtle">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>Windows 10 x64</span>
        </div>

        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="flex items-center gap-1.5 text-xs text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white bg-surface hover:bg-surface-hover px-2.5 py-1 rounded-md border border-subtle transition-all active:scale-95 disabled:opacity-50"
          title="刷新全量配置文件"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
          <span>刷新</span>
        </button>
      </div>
    </header>
  );
};
