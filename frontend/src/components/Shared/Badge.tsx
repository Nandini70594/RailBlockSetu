import React from "react";

interface BadgeProps {
  variant?: "navy" | "blue" | "emerald" | "amber" | "red" | "slate" | "sky";
  children: React.ReactNode;
  size?: "sm" | "md";
  className?: string;
  icon?: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = "slate",
  children,
  size = "sm",
  className = "",
  icon,
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case "navy":
        return "bg-slate-900 text-white border-slate-700";
      case "blue":
        return "bg-blue-50 text-blue-700 border-blue-200 font-semibold";
      case "emerald":
        return "bg-emerald-50 text-emerald-800 border-emerald-200 font-semibold";
      case "amber":
        return "bg-amber-50 text-amber-800 border-amber-200 font-semibold";
      case "red":
        return "bg-rose-50 text-rose-800 border-rose-200 font-semibold";
      case "sky":
        return "bg-sky-50 text-sky-800 border-sky-200 font-semibold";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  const getSizeStyles = () => {
    return size === "sm"
      ? "text-[11px] px-2 py-0.5"
      : "text-xs px-2.5 py-1";
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border font-medium tracking-tight ${getVariantStyles()} ${getSizeStyles()} ${className}`}
    >
      {icon && <span className="flex-shrink-0">{icon}</span>}
      <span>{children}</span>
    </span>
  );
};
