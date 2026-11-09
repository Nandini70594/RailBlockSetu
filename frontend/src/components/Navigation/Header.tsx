import React, { useState, useEffect } from "react";
import {
  Clock,
  RefreshCw,
  Search,
  ChevronDown,
  CheckCircle2,
  Users,
  Cpu,
  Shield,
  Layers,
  Sparkles,
  MapPin,
  Bell
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../Shared/ToastContext";

interface HeaderProps {
  collapsed: boolean;
  onRefreshAll?: () => void;
  onOpenOptimizationWorkflow?: () => void;
  activeDisruptionCount?: number;
}

export const Header: React.FC<HeaderProps> = ({
  collapsed,
  onRefreshAll,
  onOpenOptimizationWorkflow,
  activeDisruptionCount = 0,
}) => {
  const { user, switchRole, demoCredentials } = useAuth();
  const { showToast } = useToast();
  const [showRoleMenu, setShowRoleMenu] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const handleRoleSwitch = async (username: string) => {
    try {
      await switchRole(username);
      setShowRoleMenu(false);
      showToast("success", "Switched Persona", `Active authority updated to ${username}.`);
    } catch (err) {
      showToast("error", "Role switch failed");
    }
  };

  const getRoleBadgeStyle = (role?: string) => {
    switch (role) {
      case "ADMIN":
        return "bg-purple-100 text-purple-800 border-purple-300";
      case "OPERATIONS_OFFICER":
        return "bg-blue-100 text-blue-800 border-blue-300";
      case "DEPARTMENT_OFFICER":
        return "bg-cyan-100 text-cyan-800 border-cyan-300";
      default:
        return "bg-slate-100 text-slate-700 border-slate-300";
    }
  };

  return (
    <header
      className={`fixed top-0 right-0 h-16 bg-white/95 backdrop-blur-md border-b border-slate-200 z-30 transition-all duration-300 flex items-center justify-between px-6 shadow-sm ${
        collapsed ? "left-20" : "left-64"
      }`}
    >
      {/* Left: Division context & Search */}
      <div className="flex items-center gap-4">
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-100 border border-slate-200 text-xs text-slate-700 font-medium">
          <MapPin className="w-3.5 h-3.5 text-blue-600" />
          <span>Delhi Division</span>
          <span className="text-slate-300">•</span>
          <span className="text-slate-500 font-mono text-[11px]">NDLS-GZB Quad Line</span>
        </div>

        {activeDisruptionCount > 0 && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-50 text-red-700 border border-red-200 text-xs font-semibold animate-pulse">
            <span className="w-2 h-2 rounded-full bg-red-500" />
            <span>{activeDisruptionCount} Active Disruption Incident</span>
          </div>
        )}
      </div>

      {/* Right: Actions, Live IST Clock, Role Switcher */}
      <div className="flex items-center gap-3">
        
        {/* Live IST Clock */}
        <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 font-mono font-medium">
          <Clock className="w-3.5 h-3.5 text-blue-600" />
          <span>{currentTime} IST</span>
          <span className="text-emerald-600 font-sans font-bold flex items-center gap-1 text-[11px] ml-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block animate-ping" />
            Live
          </span>
        </div>

        {/* Quick Optimization Workflow Launcher */}
        {onOpenOptimizationWorkflow && (
          <button
            onClick={onOpenOptimizationWorkflow}
            className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-sm transition active:scale-95"
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>Optimization Stepper</span>
          </button>
        )}

        {/* Refresh */}
        {onRefreshAll && (
          <button
            onClick={() => {
              onRefreshAll();
              showToast("info", "Telemetry Refreshed", "Loaded latest requests, timetable slots and blocks.");
            }}
            title="Refresh All Data"
            className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 border border-slate-250 transition"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        )}

        {/* Role Switcher Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowRoleMenu(!showRoleMenu)}
            className="flex items-center gap-2.5 px-3 py-1.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 transition text-left"
          >
            <div className="w-7 h-7 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-xs shadow-sm">
              {user?.full_name?.charAt(0) || "U"}
            </div>
            <div className="hidden sm:block">
              <div className="text-xs font-bold text-slate-900 leading-tight truncate max-w-[150px]">
                {user?.full_name?.split("(")[0] || "Railway Official"}
              </div>
              <div
                className={`text-[10px] font-semibold border px-1.5 rounded-sm inline-block mt-0.5 ${getRoleBadgeStyle(
                  user?.role
                )}`}
              >
                {user?.role?.replace("_", " ")}
              </div>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>

          {/* Persona Menu */}
          {showRoleMenu && (
            <div className="absolute right-0 mt-2 w-84 rounded-2xl bg-white border border-slate-200 shadow-2xl p-3 z-50 animate-in fade-in zoom-in-95">
              <div className="px-3 py-2 border-b border-slate-100">
                <p className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Select Railway Official Persona
                </p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Test role authorities, request approvals & replanning
                </p>
              </div>

              <div className="mt-2 space-y-1">
                {demoCredentials.map((cred) => {
                  const isActive = user?.username === cred.username;
                  return (
                    <button
                      key={cred.username}
                      onClick={() => handleRoleSwitch(cred.username)}
                      className={`w-full text-left p-2.5 rounded-xl transition flex items-start gap-3 ${
                        isActive
                          ? "bg-blue-50 border border-blue-200 text-blue-950 font-medium"
                          : "hover:bg-slate-50 text-slate-700"
                      }`}
                    >
                      <div className="mt-0.5">
                        {isActive ? (
                          <CheckCircle2 className="w-4 h-4 text-blue-600" />
                        ) : (
                          <Users className="w-4 h-4 text-slate-400" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-slate-900 truncate">
                            {cred.title}
                          </span>
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 border border-slate-200">
                            {cred.department}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-600 leading-tight mt-0.5">
                          {cred.name}
                        </p>
                        <p className="text-[10px] text-slate-400 leading-tight mt-1 line-clamp-1">
                          {cred.description}
                        </p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

      </div>
    </header>
  );
};
