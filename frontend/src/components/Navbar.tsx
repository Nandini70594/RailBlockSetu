import React, { useState, useEffect } from "react";
import {
  Train,
  Shield,
  Layers,
  Cpu,
  Clock,
  Calendar,
  AlertTriangle,
  Wrench,
  Users,
  Activity,
  ChevronDown,
  CheckCircle2,
  RefreshCw
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onRefreshAll?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, onRefreshAll }) => {
  const { user, switchRole, demoCredentials } = useAuth();
  const [showRoleMenu, setShowRoleMenu] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const navItems = [
    { id: "dashboard", label: "Command Center", icon: Activity },
    { id: "requests", label: "Maintenance Requests", icon: Layers },
    { id: "optimization", label: "Block Optimization", icon: Cpu },
    { id: "timeline", label: "Weekly Timeline", icon: Calendar },
    { id: "trains", label: "Train Corridors", icon: Train },
    { id: "resources", label: "Resource Depots", icon: Wrench },
    { id: "disruptions", label: "Disruption Replanner", icon: AlertTriangle },
    { id: "topology", label: "Network Topology", icon: Shield },
  ];

  const getRoleBadgeColor = (role?: string) => {
    switch (role) {
      case "ADMIN":
        return "bg-purple-900/40 text-purple-300 border-purple-500/40";
      case "OPERATIONS_OFFICER":
        return "bg-amber-900/40 text-amber-300 border-amber-500/40";
      case "DEPARTMENT_OFFICER":
        return "bg-cyan-900/40 text-cyan-300 border-cyan-500/40";
      default:
        return "bg-slate-800 text-slate-300 border-slate-700";
    }
  };

  return (
    <header className="sticky top-0 z-50 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 shadow-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo & Platform Info */}
          <div className="flex items-center gap-3">
            <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-700 shadow-lg shadow-cyan-500/20 text-white font-bold">
              <Train className="w-6 h-6" />
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-500 rounded-full border-2 border-slate-900 signal-live" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-cyan-100 to-cyan-400 bg-clip-text text-transparent">
                  RailBlockSetu
                </span>
                <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-700/50">
                  NOVEX 2026
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                AI Railway Maintenance Planning & Optimization
              </p>
            </div>
          </div>

          {/* Quick Actions & Role Switcher */}
          <div className="flex items-center gap-4">
            
            {/* Live Clock & Train Controller Signal */}
            <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/70 text-xs text-slate-300 font-mono">
              <Clock className="w-3.5 h-3.5 text-cyan-400" />
              <span>{currentTime} IST</span>
              <span className="text-slate-500">|</span>
              <span className="text-emerald-400 flex items-center gap-1 font-sans font-medium text-[11px]">
                <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block animate-ping" />
                Live Control
              </span>
            </div>

            {/* Refresh Button */}
            {onRefreshAll && (
              <button
                onClick={onRefreshAll}
                title="Refresh Live Data"
                className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            )}

            {/* Role Switcher Dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowRoleMenu(!showRoleMenu)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-750 border border-slate-700 transition text-left"
              >
                <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-slate-700 to-slate-600 flex items-center justify-center text-xs font-semibold text-cyan-300 border border-slate-600">
                  {user?.full_name?.charAt(0) || "U"}
                </div>
                <div className="hidden sm:block">
                  <div className="text-xs font-semibold text-slate-200 truncate max-w-[140px]">
                    {user?.full_name?.split("(")[0] || "Railway Officer"}
                  </div>
                  <div className={`text-[10px] font-medium border px-1.5 rounded inline-block ${getRoleBadgeColor(user?.role)}`}>
                    {user?.role?.replace("_", " ")}
                  </div>
                </div>
                <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
              </button>

              {/* Role Switcher Menu */}
              {showRoleMenu && (
                <div className="absolute right-0 mt-2 w-80 rounded-xl bg-slate-900 border border-slate-700 shadow-2xl p-2 z-50 animate-in fade-in slide-in-from-top-2">
                  <div className="px-3 py-2 border-b border-slate-800">
                    <p className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                      Demo Role Switcher
                    </p>
                    <p className="text-[11px] text-slate-400">
                      Switch personas to test role-based authorities & approvals
                    </p>
                  </div>
                  <div className="mt-1 space-y-1">
                    {demoCredentials.map((cred) => {
                      const isActive = user?.username === cred.username;
                      return (
                        <button
                          key={cred.username}
                          onClick={() => {
                            switchRole(cred.username);
                            setShowRoleMenu(false);
                          }}
                          className={`w-full text-left px-3 py-2 rounded-lg transition flex items-start gap-2.5 ${
                            isActive
                              ? "bg-cyan-950/80 border border-cyan-800/80 text-white"
                              : "hover:bg-slate-800/80 text-slate-300"
                          }`}
                        >
                          <div className="mt-0.5">
                            {isActive ? (
                              <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                            ) : (
                              <Users className="w-4 h-4 text-slate-500" />
                            )}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-semibold text-slate-200">
                                {cred.title}
                              </span>
                              <span className="text-[10px] px-1 rounded bg-slate-800 text-slate-400 border border-slate-700">
                                {cred.department}
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-400 leading-tight mt-0.5">
                              {cred.name}
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
        </div>

        {/* Tab Navigation Row */}
        <div className="flex items-center space-x-1 overflow-x-auto py-2 scrollbar-none border-t border-slate-800/60">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
                  isActive
                    ? "bg-cyan-500/15 text-cyan-300 border border-cyan-500/40 shadow-sm shadow-cyan-500/10"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent"
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? "text-cyan-400" : "text-slate-400"}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

      </div>
    </header>
  );
};
