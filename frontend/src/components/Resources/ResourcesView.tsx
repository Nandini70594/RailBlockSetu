import React, { useState, useEffect } from "react";
import { Wrench, Users, Package, Gauge, Plus, CheckCircle2, AlertCircle } from "lucide-react";
import { Resource } from "../../types";
import { api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";

export const ResourcesView: React.FC = () => {
  const { isAdmin } = useAuth();
  const [resources, setResources] = useState<Resource[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeType, setActiveType] = useState<string>("ALL");
  const [activeDept, setActiveDept] = useState<string>("All");

  const fetchResources = async () => {
    setLoading(true);
    try {
      const data = await api.getResources(activeDept, activeType);
      setResources(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResources();
  }, [activeType, activeDept]);

  const getResourceTypeIcon = (type: string) => {
    switch (type) {
      case "MACHINERY":
        return Wrench;
      case "STAFF":
        return Users;
      default:
        return Package;
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Wrench className="w-5 h-5 text-cyan-400" />
            <span>Resource Depots & Infrastructure Inventory</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Heavy track machines, skilled Gang personnel, and critical permanent-way spares across Delhi Division.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        
        {/* Resource Type Filter */}
        <div className="flex items-center gap-1.5">
          {[
            { id: "ALL", label: "All Resources" },
            { id: "MACHINERY", label: "Heavy Machinery", icon: Wrench },
            { id: "STAFF", label: "Gang Personnel", icon: Users },
            { id: "MATERIAL", label: "Materials & Spares", icon: Package },
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveType(t.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 ${
                activeType === t.id
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {t.icon && <t.icon className="w-3.5 h-3.5" />}
              <span>{t.label}</span>
            </button>
          ))}
        </div>

        {/* Department Filter */}
        <div className="flex items-center gap-1.5">
          {["All", "Engineering", "TRD", "S&T"].map((d) => (
            <button
              key={d}
              onClick={() => setActiveDept(d)}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                activeDept === d
                  ? "bg-slate-800 text-white border border-slate-600"
                  : "text-slate-500 hover:text-slate-300"
              }`}
            >
              {d}
            </button>
          ))}
        </div>

      </div>

      {/* Resources Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-3 py-16 text-center text-slate-400 text-xs flex flex-col items-center gap-2">
            <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
            <span>Auditing depot stock and machinery telemetry...</span>
          </div>
        ) : resources.length === 0 ? (
          <div className="col-span-3 py-16 text-center text-slate-500 text-xs">
            No resources found for the selected category.
          </div>
        ) : (
          resources.map((r) => {
            const Icon = getResourceTypeIcon(r.resource_type);
            const availPct = Math.round((r.available_quantity / Math.max(1, r.total_quantity)) * 100);

            return (
              <div
                key={r.id}
                className="p-5 rounded-2xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition shadow-xl flex flex-col justify-between space-y-4"
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 rounded-xl bg-slate-800 text-cyan-400 border border-slate-700">
                        <Icon className="w-4 h-4" />
                      </div>
                      <div>
                        <span className="font-mono text-[10px] font-bold text-cyan-400 block">
                          {r.code}
                        </span>
                        <h4 className="text-xs font-bold text-white line-clamp-1">{r.name}</h4>
                      </div>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-bold">
                      {r.operational_status}
                    </span>
                  </div>

                  {r.specifications && (
                    <p className="text-[11px] text-slate-400 mt-2.5 line-clamp-2 leading-relaxed">
                      {r.specifications}
                    </p>
                  )}
                </div>

                {/* Progress bar */}
                <div className="space-y-1.5 pt-2 border-t border-slate-800/80">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Availability:</span>
                    <span className="font-mono font-bold text-white">
                      {r.available_quantity} / {r.total_quantity} {r.unit}
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        availPct >= 70 ? "bg-emerald-500" : availPct >= 30 ? "bg-amber-500" : "bg-rose-500"
                      }`}
                      style={{ width: `${availPct}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-slate-500 mt-1">
                    <span>Depot: {r.base_station}</span>
                    <span className="font-semibold text-slate-400">{r.department}</span>
                  </div>
                </div>

              </div>
            );
          })
        )}
      </div>

    </div>
  );
};
