'use client';

import React, { createContext, useCallback, useContext, useState } from 'react';

type ToastKind = 'success' | 'error' | 'info';
type Toast = { id: number; message: string; kind: ToastKind };

const ToastContext = createContext<(message: string, kind?: ToastKind) => void>(() => undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const notify = useCallback((message: string, kind: ToastKind = 'info') => {
    const id = Date.now() + Math.random();
    setToasts(current => [...current, { id, message, kind }]);
    window.setTimeout(
      () => setToasts(current => current.filter(toast => toast.id !== id)),
      4500
    );
  }, []);

  return (
    <ToastContext.Provider value={notify}>
      {children}
      <div className="fixed right-4 top-4 z-[100] flex w-[min(24rem,calc(100vw-2rem))] flex-col gap-2">
        {toasts.map(toast => (
          <div
            key={toast.id}
            role="status"
            className={`rounded-lg px-4 py-3 text-sm font-medium text-white shadow-lg ${
              toast.kind === 'success'
                ? 'bg-emerald-600'
                : toast.kind === 'error'
                  ? 'bg-red-600'
                  : 'bg-slate-800'
            }`}
          >
            {toast.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export const useToast = () => useContext(ToastContext);
