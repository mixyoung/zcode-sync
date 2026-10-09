import React from "react";
import { X, Sparkles, Layers, Info } from "lucide-react";
import { DuplicateAnalysisResult } from "../types";

interface DuplicateModalProps {
  duplicates: DuplicateAnalysisResult;
  isOpen: boolean;
  onClose: () => void;
}

export const DuplicateModal: React.FC<DuplicateModalProps> = ({
  duplicates,
  isOpen,
  onClose,
}) => {
  if (!isOpen) return null;

  const entries = Object.entries(duplicates);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 dark:bg-black/75 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-surface w-full max-w-2xl rounded-2xl border border-subtle shadow-2xl flex flex-col max-h-[85vh] overflow-hidden">
        {/* 标题 */}
        <div className="p-4 border-b border-subtle flex items-center justify-between bg-surface-alt/50">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-zinc-900 dark:text-white">
                重复模型诊断报告
              </h3>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                检测到 <strong className="text-amber-600 dark:text-amber-400">{entries.length}</strong> 个在多个服务商或文件中同时声明的模型
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

        {/* 诊断列表 */}
        <div className="p-5 flex-1 overflow-y-auto space-y-3.5">
          {entries.length === 0 ? (
            <div className="py-12 text-center text-zinc-500 space-y-2">
              <Layers className="w-8 h-8 mx-auto text-emerald-500" />
              <p className="text-sm text-zinc-800 dark:text-zinc-300 font-medium">未发现重复模型</p>
              <p className="text-xs text-zinc-500">所有服务商声明的模型 ID 均唯一无重叠</p>
            </div>
          ) : (
            entries.map(([modelId, occurrences]) => (
              <div
                key={modelId}
                className="bg-surface-alt/50 rounded-xl p-3.5 border border-subtle space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                    <span className="text-xs font-mono font-bold text-zinc-900 dark:text-zinc-100">
                      {modelId}
                    </span>
                  </div>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-surface text-zinc-600 dark:text-zinc-400 border border-subtle">
                    共 {occurrences.length} 处引用
                  </span>
                </div>

                <div className="space-y-1 pl-3.5 border-l border-subtle/80">
                  {occurrences.map((occ, idx) => (
                    <div
                      key={idx}
                      className="text-xs flex items-center justify-between text-zinc-600 dark:text-zinc-400 py-0.5"
                    >
                      <div className="flex items-center gap-2">
                        {occ.is_custom ? (
                          <span className="text-[10px] font-medium px-1.5 py-0.2 rounded bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-500/20">
                            自定义
                          </span>
                        ) : (
                          <span className="text-[10px] font-medium px-1.5 py-0.2 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700">
                            官方内置
                          </span>
                        )}
                        <span className="text-zinc-800 dark:text-zinc-200 font-medium">{occ.provider}</span>
                        <span className="text-[11px] font-mono text-zinc-400 dark:text-zinc-500">
                          ({occ.provider_id})
                        </span>
                      </div>
                      <span className="text-[11px] font-mono text-zinc-400 dark:text-zinc-500 truncate max-w-[200px]" title={occ.file}>
                        {occ.file.split(/[/\\]/).pop()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>

        {/* 底部说明与关闭 */}
        <div className="p-3.5 border-t border-subtle bg-surface-alt/30 flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-[11px] text-zinc-500 dark:text-zinc-400">
            <Info className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
            <span>官方 BigModel / Z.ai 的各套餐默认自带同名模型，属于正常现象。</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-semibold text-zinc-700 dark:text-zinc-200 hover:text-zinc-900 dark:hover:text-white bg-surface hover:bg-surface-hover rounded-lg border border-subtle transition-all shrink-0 ml-4 shadow-sm"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  );
};
