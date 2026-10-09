import React, { useState, useEffect, useMemo, useCallback } from "react";
import {
  ConfigFileMeta,
  UnifiedProviderItem,
  DuplicateAnalysisResult,
  ToastMessage,
} from "./types";
import { ApiService } from "./services/api";
import { useTheme } from "./services/theme";
import { HeaderNav } from "./components/HeaderNav";
import { ConfigSelectorCard } from "./components/ConfigSelectorCard";
import { FilterSearchToolbar } from "./components/FilterSearchToolbar";
import { ProviderTable } from "./components/ProviderTable";
import { ProviderEditModal } from "./components/ProviderEditModal";
import { DuplicateModal } from "./components/DuplicateModal";
import { CloudSyncModal } from "./components/CloudSyncModal";
import { ActionConsole } from "./components/ActionConsole";
import { Toast } from "./components/Toast";

export const App: React.FC = () => {
  const { themeMode, setThemeMode } = useTheme();

  const [configs, setConfigs] = useState<ConfigFileMeta[]>([]);
  const [selectedConfigPath, setSelectedConfigPath] = useState<string>("ALL");
  const [providers, setProviders] = useState<UnifiedProviderItem[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [filterType, setFilterType] = useState<"all" | "custom" | "builtin">("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [maskApiKey, setMaskApiKey] = useState<boolean>(false);

  // 弹窗状态
  const [editingItem, setEditingItem] = useState<UnifiedProviderItem | null>(null);
  const [isDuplicateModalOpen, setIsDuplicateModalOpen] = useState<boolean>(false);
  const [isCloudModalOpen, setIsCloudModalOpen] = useState<boolean>(false);
  const [duplicates, setDuplicates] = useState<DuplicateAnalysisResult>({});

  // 浮动 Toast 状态
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addToast = useCallback(
    (type: "success" | "error" | "info", title: string, message?: string) => {
      const id = Date.now().toString() + Math.random().toString();
      setToasts((prev) => [...prev, { id, type, title, message }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 3500);
    },
    []
  );

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // 载入全部配置
  const loadData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const foundConfigs = await ApiService.discoverConfigs();
      setConfigs(foundConfigs);

      const targetFiles =
        selectedConfigPath === "ALL"
          ? foundConfigs.map((c) => c.path)
          : [selectedConfigPath];

      const loaded = await ApiService.loadAllProviders(targetFiles);
      setProviders(loaded);

      // 计算重复模型
      const dups = await ApiService.analyzeDuplicates(loaded);
      setDuplicates(dups);
    } catch (e: any) {
      addToast("error", "加载配置失败", e.message);
    } finally {
      setIsRefreshing(false);
    }
  }, [selectedConfigPath, addToast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // 视觉自动化测试与截图辅助：允许通过 URL 参数预置弹窗视图
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const view = params.get("view");
    if (view === "duplicate") {
      setIsDuplicateModalOpen(true);
    } else if (view === "cloud") {
      setIsCloudModalOpen(true);
    } else if (view === "edit" && providers.length > 0) {
      setEditingItem(providers[0]);
    }
  }, [providers]);

  // 全局快捷键 Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        const input = document.querySelector<HTMLInputElement>(
          'input[placeholder*="搜索服务商"]'
        );
        input?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // 过滤后的服务商列表
  const filteredProviders = useMemo(() => {
    return providers.filter((p) => {
      if (selectedConfigPath !== "ALL" && p.source_file !== selectedConfigPath) {
        return false;
      }
      if (filterType === "custom" && !p.is_custom) return false;
      if (filterType === "builtin" && p.is_custom) return false;

      if (searchQuery.trim()) {
        const kw = searchQuery.toLowerCase().trim();
        const mName = p.name.toLowerCase().includes(kw);
        const mId = p.provider_id.toLowerCase().includes(kw);
        const mModel = p.models.some((m) => m.toLowerCase().includes(kw));
        return mName || mId || mModel;
      }
      return true;
    });
  }, [providers, selectedConfigPath, filterType, searchQuery]);

  const handleToggleSelect = (id: string, shiftKey: boolean) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    if (selectedIds.length === filteredProviders.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filteredProviders.map((p) => p.provider_id));
    }
  };

  const handleAddCustomFile = () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".json";
    input.onchange = async (e: any) => {
      const file = e.target.files?.[0];
      if (file) {
        addToast("info", "已添加配置文件", file.name);
        loadData();
      }
    };
    input.click();
  };

  const handleOpenFolder = async () => {
    const target =
      selectedConfigPath === "ALL" && configs.length > 0
        ? configs[0].path
        : selectedConfigPath;
    if (target && target !== "ALL") {
      await ApiService.openFolder(target);
      addToast("info", "正在打开所在目录", target);
    }
  };

  const handleSaveProvider = async (updatedItem: UnifiedProviderItem) => {
    const msg = await ApiService.saveSingleProvider(
      updatedItem.source_file,
      updatedItem.provider_id,
      updatedItem.raw_data
    );
    addToast("success", "保存成功", msg);
    await loadData();
  };

  const handleDeleteSelected = async () => {
    if (selectedIds.length === 0) return;
    if (
      !confirm(
        `确定要从配置文件中删除选中的 ${selectedIds.length} 项服务商吗？系统将自动创建 .bak 历史安全备份。`
      )
    ) {
      return;
    }

    try {
      for (const id of selectedIds) {
        const item = providers.find((p) => p.provider_id === id);
        if (item) {
          await ApiService.deleteSingleProvider(item.source_file, item.provider_id);
        }
      }
      addToast("success", "删除成功", `已安全移除 ${selectedIds.length} 项配置`);
      setSelectedIds([]);
      await loadData();
    } catch (e: any) {
      addToast("error", "删除失败", e.message);
    }
  };

  // 获取待导出的服务商字典
  const getExportProviders = (maskKey: boolean = maskApiKey) => {
    const targetItems =
      selectedIds.length > 0
        ? providers.filter((p) => selectedIds.includes(p.provider_id))
        : filteredProviders;

    const out: Record<string, any> = {};
    for (const it of targetItems) {
      const copyData = JSON.parse(JSON.stringify(it.raw_data));
      if (maskKey && copyData.options && copyData.options.apiKey) {
        copyData.options.apiKey = "YOUR_API_KEY_HERE";
      }
      out[it.provider_id] = copyData;
    }
    return { provider: out };
  };

  const handleExportFile = () => {
    const data = getExportProviders();
    const count = Object.keys(data.provider).length;
    if (count === 0) {
      addToast("error", "导出失败", "当前视图无任何可导出的服务商配置");
      return;
    }

    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `zcode-models-export-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);

    addToast(
      "success",
      "导出成功",
      `已导出 ${count} 个模型服务商配置${maskApiKey ? " (已安全脱敏 API Key)" : ""}`
    );
  };

  const handleCopyClipboard = async () => {
    const data = getExportProviders();
    const count = Object.keys(data.provider).length;
    if (count === 0) {
      addToast("error", "复制失败", "当前视图无任何可导出的服务商配置");
      return;
    }

    const text = JSON.stringify(data, null, 2);
    await navigator.clipboard.writeText(text);
    addToast(
      "success",
      "已复制到剪贴板",
      `成功将 ${count} 个模型配置${maskApiKey ? " (已脱敏)" : ""}复制到系统剪贴板，可在目标电脑直接导入`
    );
  };

  // 执行增量导入
  const executeImport = async (parsedData: any, sourceName: string) => {
    let newProviders: Record<string, any> = {};
    if (parsedData.provider && typeof parsedData.provider === "object") {
      newProviders = parsedData.provider;
    } else if (typeof parsedData === "object") {
      newProviders = parsedData;
    }

    const count = Object.keys(newProviders).length;
    if (count === 0) {
      addToast("error", "导入失败", "导入数据中未检测到有效模型服务商节点");
      return;
    }

    const targetFile =
      selectedConfigPath === "ALL" && configs.length > 0
        ? configs[0].path
        : selectedConfigPath;

    for (const [pid, pdata] of Object.entries(newProviders)) {
      await ApiService.saveSingleProvider(targetFile, pid, pdata);
    }

    addToast(
      "success",
      "导入完成",
      `成功从 [${sourceName}] 增量合并 ${count} 个服务商至 ${targetFile.split(/[/\\]/).pop()}，已自动备份原文件！`
    );
    await loadData();
  };

  const handleImportFile = () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".json";
    input.onchange = async (e: any) => {
      const file = e.target.files?.[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = async (ev) => {
          try {
            const parsed = JSON.parse(ev.target?.result as string);
            await executeImport(parsed, file.name);
          } catch (err: any) {
            addToast("error", "文件解析错误", err.message);
          }
        };
        reader.readAsText(file);
      }
    };
    input.click();
  };

  const handleImportClipboard = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (!text || !text.trim()) {
        addToast("error", "剪贴板为空", "未在系统剪贴板中检测到有效文本内容");
        return;
      }
      const parsed = JSON.parse(text);
      await executeImport(parsed, "系统剪贴板");
    } catch (err: any) {
      addToast("error", "剪贴板解析失败", err.message);
    }
  };

  // 云端备份执行器
  const handleCloudBackupNow = async (maskKey: boolean) => {
    const payload = getExportProviders(maskKey);
    const msg = await ApiService.uploadCloudBackup(payload);
    addToast("success", "云端备份成功", msg);
  };

  // 云端备份恢复执行器
  const handleRestoreFromCloud = async (backupData: any, fileName: string) => {
    await executeImport(backupData, fileName);
    setIsCloudModalOpen(false);
  };

  return (
    <div className="h-screen w-screen flex flex-col p-4 bg-canvas text-zinc-900 dark:text-zinc-100 overflow-hidden space-y-3 transition-colors duration-150">
      {/* 1. 顶部状态栏与主题切换器 */}
      <HeaderNav
        onRefresh={loadData}
        isRefreshing={isRefreshing}
        totalProviders={providers.length}
        themeMode={themeMode}
        onThemeModeChange={setThemeMode}
        onOpenCloudModal={() => setIsCloudModalOpen(true)}
      />

      {/* 2. 配置文件选择卡片 */}
      <ConfigSelectorCard
        configs={configs}
        selectedPath={selectedConfigPath}
        onSelect={setSelectedConfigPath}
        onAddCustom={handleAddCustomFile}
        onOpenFolder={handleOpenFolder}
      />

      {/* 3. 搜索与筛选工具条 */}
      <FilterSearchToolbar
        filterType={filterType}
        onFilterChange={setFilterType}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onOpenDuplicateModal={() => setIsDuplicateModalOpen(true)}
        duplicateCount={Object.keys(duplicates).length}
      />

      {/* 4. 精密数据表格 */}
      <ProviderTable
        items={filteredProviders}
        selectedIds={selectedIds}
        onToggleSelect={handleToggleSelect}
        onSelectAll={handleSelectAll}
        onEdit={(it) => setEditingItem(it)}
      />

      {/* 5. 核心操作控制台 */}
      <ActionConsole
        selectedCount={selectedIds.length}
        maskApiKey={maskApiKey}
        onToggleMaskKey={() => setMaskApiKey(!maskApiKey)}
        onEditSelected={() => {
          const first = providers.find((p) => selectedIds.includes(p.provider_id));
          if (first) setEditingItem(first);
        }}
        onDeleteSelected={handleDeleteSelected}
        onExportFile={handleExportFile}
        onImportFile={handleImportFile}
        onCopyClipboard={handleCopyClipboard}
        onImportClipboard={handleImportClipboard}
      />

      {/* 模态框 */}
      {editingItem && (
        <ProviderEditModal
          item={editingItem}
          isOpen={!!editingItem}
          onClose={() => setEditingItem(null)}
          onSave={handleSaveProvider}
        />
      )}

      <DuplicateModal
        duplicates={duplicates}
        isOpen={isDuplicateModalOpen}
        onClose={() => setIsDuplicateModalOpen(false)}
      />

      <CloudSyncModal
        isOpen={isCloudModalOpen}
        onClose={() => setIsCloudModalOpen(false)}
        onBackupNow={handleCloudBackupNow}
        onRestoreFromCloud={handleRestoreFromCloud}
        onShowToast={addToast}
      />

      {/* 浮动通知 */}
      <Toast toasts={toasts} onDismiss={removeToast} />
    </div>
  );
};
