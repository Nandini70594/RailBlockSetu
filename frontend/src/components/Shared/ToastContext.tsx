import React, { createContext, useContext, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from "lucide-react";

export type ToastType = "success" | "error" | "warning" | "info";

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
}

interface ToastContextType {
  showToast: (type: ToastType, title: string, message?: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = (type: ToastType, title: string, message?: string) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, type, title, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const getToastIcon = (type: ToastType) => {
    switch (type) {
      case "success":
        return <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />;
      case "error":
        return <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />;
      case "warning":
        return <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />;
      default:
        return <Info className="w-5 h-5 text-blue-600 flex-shrink-0" />;
    }
  };

  const getToastStyle = (type: ToastType) => {
    switch (type) {
      case "success":
        return "bg-white border-emerald-200 text-slate-800 shadow-emerald-900/10";
      case "error":
        return "bg-white border-red-200 text-slate-800 shadow-red-900/10";
      case "warning":
        return "bg-white border-amber-200 text-slate-800 shadow-amber-900/10";
      default:
        return "bg-white border-blue-200 text-slate-800 shadow-blue-900/10";
    }
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className={`pointer-events-auto p-4 rounded-xl border shadow-lg flex items-start gap-3 ${getToastStyle(
                toast.type
              )}`}
            >
              {getToastIcon(toast.type)}
              <div className="flex-1 pr-2">
                <h4 className="text-xs font-bold text-slate-900">{toast.title}</h4>
                {toast.message && (
                  <p className="text-xs text-slate-600 mt-0.5 leading-snug">{toast.message}</p>
                )}
              </div>
              <button
                onClick={() => removeToast(toast.id)}
                className="text-slate-400 hover:text-slate-600 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
};
