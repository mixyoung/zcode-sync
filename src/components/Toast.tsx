import React from "react";
import { CheckCircle2, AlertCircle, Info, X } from "lucide-react";
import { ToastMessage } from "../types";

interface ToastProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

export const Toast: React.FC<ToastProps> = ({ toasts, onDismiss }) => {
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map((t) => (
        <div
          key={t.id}
          className="pointer-events-auto flex items-start gap-3 w-80 p-3.5 rounded-lg bg-surface/95 border border-subtle shadow-2xl backdrop-blur-md transition-all animate-in slide-in-from-top-2 duration-200"
        >
          {t.type === "success" && (
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
          )}
          {t.type === "error" && (
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          )}
          {t.type === "info" && (
            <Info className="w-5 h-5 text-sky-400 shrink-0 mt-0.5" />
          )}

          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-semibold text-zinc-100">{t.title}</h4>
            {t.message && (
              <p className="text-xs text-zinc-400 mt-0.5 leading-relaxed break-words">
                {t.message}
              </p>
            )}
          </div>

          <button
            onClick={() => onDismiss(t.id)}
            className="text-zinc-500 hover:text-zinc-300 transition-colors p-0.5"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  );
};
