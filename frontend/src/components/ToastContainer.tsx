import React, { useState, useEffect } from 'react';
import { CheckCircle2, AlertTriangle, Info, X } from 'lucide-react';

export interface ToastMessage {
  id: string;
  title: string;
  message: string;
  type: 'success' | 'warning' | 'info' | 'error';
}

export const ToastContainer: React.FC = () => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  useEffect(() => {
    const handleToastEvent = (e: Event) => {
      const customEvt = e as CustomEvent<{ title: string; message: string; type?: 'success' | 'warning' | 'info' | 'error' }>;
      if (!customEvt.detail) return;

      const { title, message, type = 'info' } = customEvt.detail;
      const id = `toast-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`;

      const newToast: ToastMessage = { id, title, message, type };
      setToasts((prev) => [...prev, newToast]);

      // Auto-remove after 4 seconds
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 4000);
    };

    window.addEventListener('astra-toast', handleToastEvent);
    return () => {
      window.removeEventListener('astra-toast', handleToastEvent);
    };
  }, []);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-6 right-6 z-50 flex flex-col space-y-2 max-w-sm w-full pointer-events-none">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`pointer-events-auto p-4 rounded-xl border backdrop-blur-md shadow-2xl transition-all animate-in fade-in slide-in-from-top-4 flex items-start gap-3 text-xs font-sans ${
            toast.type === 'success'
              ? 'bg-[#07130F]/95 border-emerald-500/50 text-emerald-100'
              : toast.type === 'warning'
              ? 'bg-[#1A1308]/95 border-amber-500/50 text-amber-100'
              : toast.type === 'error'
              ? 'bg-[#1A0A0A]/95 border-rose-500/50 text-rose-100'
              : 'bg-[#0A131A]/95 border-[#8FAFC2]/50 text-slate-100'
          }`}
        >
          <div className="shrink-0 mt-0.5">
            {toast.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            ) : toast.type === 'warning' ? (
              <AlertTriangle className="w-4 h-4 text-amber-400" />
            ) : toast.type === 'error' ? (
              <AlertTriangle className="w-4 h-4 text-rose-400" />
            ) : (
              <Info className="w-4 h-4 text-[#8FAFC2]" />
            )}
          </div>

          <div className="flex-1 space-y-0.5">
            <h4 className="font-mono text-xs font-bold uppercase tracking-wider">{toast.title}</h4>
            <p className="text-[11px] opacity-90 leading-relaxed">{toast.message}</p>
          </div>

          <button
            onClick={() => removeToast(toast.id)}
            className="text-slate-400 hover:text-white p-1 rounded hover:bg-white/10 transition-colors cursor-pointer shrink-0"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
};
