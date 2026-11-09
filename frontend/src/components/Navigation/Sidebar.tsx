import React from "react";
import {
  Activity,
  Layers,
  Cpu,
  Calendar,
  Train,
  Wrench,
  AlertTriangle,
  Shield,
  Settings,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Users
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  collapsed: boolean;
  setCollapsed: (collapsed: boolean) => void;
  pendingCount?: number;
  disruptionCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  collapsed,
  setCollapsed,
  pendingCount = 0,
  disruptionCount = 0,
}) => {
  const { user } = useAuth();

  const navItems = [
    {
      id: "dashboard",
      label: "Command Center",
      icon: Activity,
      description: "Mission Control Overview",
    },
    {
      id: "requests",
      label: "Maintenance Requests",
      icon: Layers,
      description: "Multi-Department Requisitions",
      badge: pendingCount > 0 ? pendingCount : undefined,
      badgeColor: "bg-amber-500 text-slate-950 font-bold",
    },
    {
      id: "optimization",
      label: "Block Optimization",
      icon: Cpu,
      description: "CP-SAT Constraint Engine",
    },
    {
      id: "timeline",
      label: "Interactive Timeline",
      icon: Calendar,
      description: "Corridor Scheduling & Gaps",
    },
    {
      id: "trains",
      label: "Train Corridors",
      icon: Train,
      description: "Vande Bharat & Freight Timetables",
    },
    {
      id: "resources",
      label: "Resource Depots",
      icon: Wrench,
      description: "Machinery, Gangs & Spares",
    },
    {
      id: "disruptions",
      label: "Disruption Replanner",
      icon: AlertTriangle,
      description: "Resilient Re-Optimization",
      badge: disruptionCount > 0 ? disruptionCount : undefined,
      badgeColor: "bg-red-500 text-white font-bold",
    },
    {
      id: "topology",
      label: "Network Topology",
      icon: Shield,
      description: "Delhi Division Corridor Graph",
    },
    {
      id: "admin",
      label: "System Settings",
      icon: Settings,
      description: "Administration & Telemetry",
    },
  ];

  return (
    <aside
      className={`fixed top-0 left-0 h-screen bg-[#0f172a] text-slate-200 border-r border-slate-800 z-40 transition-all duration-300 flex flex-col justify-between ${
        collapsed ? "w-20" : "w-64"
      }`}
    >
      {/* Top Branding Section */}
      <div>
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="relative flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-xl bg-blue-600 text-white font-bold shadow-md shadow-blue-500/30">
              <Train className="w-5 h-5" />
              <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-[#0f172a] signal-live" />
            </div>
            {!collapsed && (
              <div className="min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="font-extrabold text-base tracking-tight text-white truncate">
                    RailBlockSetu
                  </span>
                </div>
                <span className="text-[10px] font-semibold text-blue-400 uppercase tracking-wider block">
                  NOVEX 2026 • AI Rail
                </span>
              </div>
            )}
          </div>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            title={collapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Section Label */}
        {!collapsed && (
          <div className="px-5 pt-4 pb-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            Operational Navigation
          </div>
        )}

        {/* Navigation Items */}
        <nav className="px-3 space-y-1 mt-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all group relative ${
                  isActive
                    ? "bg-blue-600 text-white shadow-md shadow-blue-600/30 font-semibold"
                    : "text-slate-300 hover:bg-slate-800 hover:text-white"
                } ${collapsed ? "justify-center px-2" : ""}`}
                title={collapsed ? item.label : undefined}
              >
                <Icon
                  className={`w-4 h-4 flex-shrink-0 transition-transform ${
                    isActive ? "text-white scale-110" : "text-slate-400 group-hover:text-slate-200"
                  }`}
                />
                {!collapsed && (
                  <div className="flex-1 text-left min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="truncate">{item.label}</span>
                      {item.badge && (
                        <span
                          className={`text-[10px] px-1.5 py-0.2 rounded-full ${item.badgeColor}`}
                        >
                          {item.badge}
                        </span>
                      )}
                    </div>
                  </div>
                )}
                {collapsed && item.badge && (
                  <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-amber-400" />
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* User Persona & Role Footer */}
      <div className="p-3 border-t border-slate-800 bg-[#0b1329]">
        <div className={`flex items-center gap-3 ${collapsed ? "justify-center" : ""}`}>
          <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-blue-400 flex-shrink-0">
            {user?.full_name?.charAt(0) || "O"}
          </div>
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <div className="text-xs font-bold text-white truncate">
                {user?.full_name?.split("(")[0] || "Railway Official"}
              </div>
              <div className="text-[10px] text-blue-300 font-mono flex items-center gap-1 mt-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
                <span>{user?.role?.replace("_", " ")}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};
