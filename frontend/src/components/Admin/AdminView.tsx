import React, { useState } from "react";
import { Shield, RefreshCw, Users, Server, CheckCircle2, AlertTriangle } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../api/client";

export const AdminView: React.FC = () => {
  const { demoCredentials } = useAuth();
  const [resetting, setResetting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleResetData = async () => {
    if (confirm("Reset database to clean initial Indian Railways demo dataset?")) {
      setResetting(true);
      setMessage(null);
      try {
        const res = await api.resetDemoData();
        setMessage(res.message);
      } catch (err) {
        console.error(err);
      } finally {
        setResetting(false);
      }
    }
  };

  return (
    <div className="space-y-6">
      
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <Shield className="w-5 h-5 text-purple-400" />
          <span>System Administration & System Telemetry</span>
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Role-Based Access Control, CP-SAT solver parameters, and database state management.
        </p>
      </div>

      {message && (
        <div className="p-4 rounded-xl bg-emerald-950/60 border border-emerald-800 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <span>{message}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* User Roles */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Users className="w-4 h-4 text-cyan-400" />
            <span>Configured Demo Roles & Personas</span>
          </h3>

          <div className="space-y-2">
            {demoCredentials.map((c) => (
              <div
                key={c.username}
                className="p-3 rounded-xl bg-slate-850 border border-slate-800 flex items-center justify-between text-xs"
              >
                <div>
                  <div className="font-semibold text-slate-200">{c.name}</div>
                  <div className="text-[11px] text-slate-400">{c.title} ({c.username})</div>
                </div>
                <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-slate-800 text-cyan-300 border border-slate-700">
                  {c.role}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* System Reset & Engine Parameters */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl flex flex-col justify-between space-y-4">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-2">
              <Server className="w-4 h-4 text-emerald-400" />
              <span>Optimization & DB Engine Controls</span>
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Resetting will clear transient solver state and re-seed all 6 realistic Indian Railways requests, resources, and timetable slots.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-850 border border-slate-800 space-y-2 text-xs">
            <div className="flex justify-between text-slate-300">
              <span className="text-slate-400">Solver Engine:</span>
              <span className="font-mono text-cyan-300 font-semibold">Google OR-Tools CP-SAT v9.15</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span className="text-slate-400">ML Priority Model:</span>
              <span className="font-mono text-emerald-300 font-semibold">RandomForest + GradientBoosting</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span className="text-slate-400">Network Topology:</span>
              <span className="font-mono text-purple-300 font-semibold">NetworkX DiGraph Analyzer</span>
            </div>
          </div>

          <button
            onClick={handleResetData}
            disabled={resetting}
            className="w-full py-2.5 rounded-xl bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/40 text-xs font-bold transition flex items-center justify-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${resetting ? "animate-spin" : ""}`} />
            <span>{resetting ? "Re-seeding Database..." : "Reset Demo Database & Re-seed"}</span>
          </button>
        </div>

      </div>

    </div>
  );
};
