import React from "react";
import { UnifiedProviderItem } from "../types";
import { Layers } from "lucide-react";

interface ProviderTableProps {
  items: UnifiedProviderItem[];
  selectedIds: string[];
  onToggleSelect: (id: string, shiftKey: boolean) => void;
  onSelectAll: () => void;
  onEdit: (item: UnifiedProviderItem) => void;
}

export const ProviderTable: React.FC<ProviderTableProps> = ({
  items,
  selectedIds,
  onToggleSelect,
  onSelectAll,
  onEdit,
}) => {
  const allSelected = items.length > 0 && selectedIds.length === items.length;

  return (
    <div className="flex-1 min-h-0 bg-surface rounded-xl border border-subtle overflow-hidden flex flex-col shadow-sm">
      <div className="overflow-y-auto flex-1 divide-y divide-subtle/50">
        <table className="w-full text-left border-collapse">
          <thead className="bg-surface-alt sticky top-0 z-10 text-[11px] font-semibold text-zinc-600 dark:text-zinc-300 border-b border-subtle">
            <tr>
              <th className="py-2.5 px-3 w-10 text-center">
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={onSelectAll}
                  className="rounded bg-input border-subtle text-blue-600 focus:ring-0 cursor-pointer"
                />
              </th>
              <th className="py-2.5 px-3 w-48">服务商名称 (Provider)</th>
              <th className="py-2.5 px-3 w-24 text-center">分类类型</th>
              <th className="py-2.5 px-3 w-32 text-center">协议类型</th>
              <th className="py-2.5 px-3 w-20 text-center">模型数</th>
              <th className="py-2.5 px-3 w-48">所属配置文件</th>
              <th className="py-2.5 px-3">模型清单预览</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-subtle/30 text-xs">
            {items.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-16 text-center text-zinc-400 dark:text-zinc-500">
                  <Layers className="w-8 h-8 mx-auto mb-2 text-zinc-400 dark:text-zinc-600" />
                  <p>未找到匹配的模型服务商配置</p>
                </td>
              </tr>
            ) : (
              items.map((it) => {
                const isSelected = selectedIds.includes(it.provider_id);
                return (
                  <tr
                    key={`${it.source_file}@@${it.provider_id}`}
                    onDoubleClick={() => onEdit(it)}
                    className={`group cursor-pointer transition-colors ${
                      isSelected
                        ? "bg-blue-50 dark:bg-blue-950/40 hover:bg-blue-100 dark:hover:bg-blue-950/60"
                        : "hover:bg-surface-hover/80"
                    }`}
                  >
                    <td
                      className="py-2 px-3 text-center"
                      onClick={(e) => {
                        e.stopPropagation();
                        onToggleSelect(it.provider_id, e.shiftKey);
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => {}}
                        className="rounded bg-input border-subtle text-blue-600 focus:ring-0 cursor-pointer"
                      />
                    </td>

                    <td className="py-2 px-3">
                      <div className="font-semibold text-zinc-900 dark:text-zinc-100 group-hover:text-blue-600 dark:group-hover:text-blue-300 transition-colors">
                        {it.name}
                      </div>
                      <div className="text-[10px] font-mono text-zinc-500 truncate max-w-[180px]">
                        ID: {it.provider_id}
                      </div>
                    </td>

                    <td className="py-2 px-3 text-center">
                      {it.is_custom ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-50 dark:bg-emerald-950/80 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-500/30">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                          自定义
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700">
                          官方内置
                        </span>
                      )}
                    </td>

                    <td className="py-2 px-3 text-center">
                      <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-surface-alt text-zinc-700 dark:text-zinc-300 border border-subtle">
                        {it.kind}
                      </span>
                    </td>

                    <td className="py-2 px-3 text-center">
                      <span className="font-mono font-semibold text-zinc-800 dark:text-zinc-200">
                        {it.models.length}
                      </span>
                    </td>

                    <td className="py-2 px-3 text-[11px] font-mono text-zinc-600 dark:text-zinc-400 truncate max-w-[180px]">
                      <span title={it.source_file}>
                        {it.source_file.split(/[/\\]/).pop()} ({it.source_label})
                      </span>
                    </td>

                    <td className="py-2 px-3">
                      <div className="flex flex-wrap gap-1 max-h-12 overflow-hidden">
                        {it.models.slice(0, 3).map((m) => (
                          <span
                            key={m}
                            className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface-alt text-zinc-700 dark:text-zinc-300 border border-subtle truncate max-w-[150px]"
                            title={m}
                          >
                            {m}
                          </span>
                        ))}
                        {it.models.length > 3 && (
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface-alt text-zinc-500 border border-subtle">
                            +{it.models.length - 3}
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <div className="px-3 py-1.5 bg-surface-alt/40 border-t border-subtle text-[11px] text-zinc-500 dark:text-zinc-400 flex justify-between items-center">
        <span>双击表格行直接打开可视化编辑</span>
        <span>
          已选中: <strong className="text-zinc-800 dark:text-zinc-200">{selectedIds.length}</strong> /{" "}
          {items.length} 项
        </span>
      </div>
    </div>
  );
};
