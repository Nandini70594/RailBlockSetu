import React from "react";
import { ChevronRight, Home } from "lucide-react";

interface BreadcrumbsProps {
  items: { label: string; onClick?: () => void }[];
}

export const Breadcrumbs: React.FC<BreadcrumbsProps> = ({ items }) => {
  return (
    <nav className="flex items-center space-x-2 text-xs text-slate-500 mb-4">
      <div className="flex items-center gap-1.5 font-medium text-slate-700">
        <Home className="w-3.5 h-3.5 text-blue-600" />
        <span>RailBlockSetu</span>
      </div>
      {items.map((item, idx) => (
        <React.Fragment key={idx}>
          <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
          {item.onClick ? (
            <button
              onClick={item.onClick}
              className="text-slate-600 hover:text-blue-600 font-medium transition"
            >
              {item.label}
            </button>
          ) : (
            <span className="text-slate-900 font-semibold">{item.label}</span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
};
