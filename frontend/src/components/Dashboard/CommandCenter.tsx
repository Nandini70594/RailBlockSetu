import React from "react";
import { motion } from "framer-motion";
import {
  Layers,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Flame,
  Gauge,
  Sparkles,
  Train,
  ShieldAlert,
  ArrowUpRight,
  TrendingUp,
  Cpu,
  Zap,
  Wrench,
  Radio,
  FileCheck2,
  Calendar,
  HelpCircle,
  AlertCircle
} from "lucide-react";
import { DashboardMetrics, AuditLog } from "../../types";
import { Tooltip } from "../Shared/Tooltip";

interface CommandCenterProps {
  metrics: DashboardMetrics | null;
  activityLogs: AuditLog[];
  onNavigate: (tab: string) => void;
  onOpenOptimizationWorkflow: () => void;
}

export const CommandCenter: React.FC<CommandCenterProps> = ({
  metrics,
  activityLogs,
  onNavigate,
  onOpenOptimizationWorkflow
}) => {
  if (!metrics) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs font-semibold text-slate-500">
            Connecting to Delhi Division Real-Time Operational Database...
          </p>
        </div>
      </div>
    );
  }

  // 10 Core Prompt-Mandated Statistics
  const statCards = [
    {
      title: "Total Maintenance Requests",
      value: metrics.total_maintenance_requests,
      subtitle: "Multi-department pipeline",
      icon: Layers,
      color: "bg-blue-50 text-blue-700 border-blue-200",
      iconColor: "text-blue-600",
      tab: "requests",
      tooltip: "Unified requests logged from Engineering, TRD, and S&T."
    },
    {
      title: "Pending Requests",
      value: metrics.pending_requests,
      subtitle: "Awaiting CP-SAT solve",
      icon: Clock,
      color: "bg-amber-50 text-amber-800 border-amber-200",
      iconColor: "text-amber-600",
      tab: "requests",
      tooltip: "Requisitions submitted but not yet scheduled or approved."
    },
    {
      title: "Approved Blocks",
      value: metrics.approved_maintenance_blocks,
      subtitle: "Officer authorized",
      icon: CheckCircle2,
      color: "bg-emerald-50 text-emerald-800 border-emerald-200",
      iconColor: "text-emerald-600",
      tab: "optimization",
      tooltip: "Blocks approved by the Railway Operations Officer and locked with pin protection."
    },
    {
      title: "Completed Tasks",
      value: metrics.completed_maintenance_tasks,
      subtitle: "Executed safely",
      icon: FileCheck2,
      color: "bg-slate-50 text-slate-700 border-slate-200",
      iconColor: "text-slate-600",
      tab: "requests",
      tooltip: "Maintenance activities completed with fitness certificates submitted."
    },
    {
      title: "Critical Priority (P1)",
      value: metrics.critical_maintenance_tasks,
      subtitle: "Emergency track assets",
      icon: Flame,
      color: "bg-rose-50 text-rose-800 border-rose-200",
      iconColor: "text-rose-600",
      tab: "requests",
      tooltip: "Assets requiring immediate clearance before peak passenger movements."
    },
    {
      title: "Resource Readiness",
      value: metrics.resource_readiness_percentage === null
        ? "N/A"
        : `${metrics.resource_readiness_percentage}%`,
      subtitle: "Gangs, Machines & Spares",
      icon: Gauge,
      color: "bg-sky-50 text-sky-800 border-sky-200",
      iconColor: "text-blue-600",
      tab: "resources",
      tooltip: "Composite ratio of Gang staff, heavy machinery, and track fittings in depots."
    },
    {
      title: "Available Windows",
      value: metrics.available_maintenance_windows,
      subtitle: "Headway gaps identified",
      icon: Sparkles,
      color: "bg-indigo-50 text-indigo-800 border-indigo-200",
      iconColor: "text-indigo-600",
      tab: "timeline",
      tooltip: "Train-free gaps at least the minimum useful duration, after approved blocks."
    },
    {
      title: "Sections Under Work",
      value: metrics.railway_sections_under_maintenance,
      subtitle: "Active corridor work",
      icon: Train,
      color: "bg-purple-50 text-purple-800 border-purple-200",
      iconColor: "text-purple-600",
      tab: "topology",
      tooltip: "Corridors currently having active maintenance or speed restrictions."
    },
    {
      title: "Scheduling Conflicts",
      value: metrics.current_scheduling_conflicts,
      subtitle: metrics.current_scheduling_conflicts === 0 ? "Resolved by CP-SAT" : "Clash detected",
      icon: AlertTriangle,
      color: metrics.current_scheduling_conflicts === 0 ? "bg-emerald-50 text-emerald-800 border-emerald-200" : "bg-amber-50 text-amber-800 border-amber-200",
      iconColor: metrics.current_scheduling_conflicts === 0 ? "text-emerald-600" : "text-amber-600",
      tab: "optimization",
      tooltip: "Mathematical clashes on same track section without co-location."
    },
    {
      title: "Active Disruptions",
      value: metrics.upcoming_disruptions,
      subtitle: "Weather & track incidents",
      icon: ShieldAlert,
      color: "bg-orange-50 text-orange-800 border-orange-200",
      iconColor: "text-orange-600",
      tab: "disruptions",
      tooltip: "Current incidents requiring resilient replanning."
    }
  ];

  // Department distribution
  const depts = [
    { name: "Engineering (Track)", count: metrics.department_distribution["Engineering"] || 0, icon: Wrench, color: "text-blue-700", bg: "bg-blue-600" },
    { name: "TRD (Electrical OHE)", count: metrics.department_distribution["TRD"] || 0, icon: Zap, color: "text-amber-700", bg: "bg-amber-500" },
    { name: "S&T (Signals & ATP)", count: metrics.department_distribution["S&T"] || 0, icon: Radio, color: "text-emerald-700", bg: "bg-emerald-600" },
  ];
  const totalDeptTasks = Math.max(1, depts.reduce((acc, d) => acc + d.count, 0));

  return (
    <div className="space-y-6">
      
      {/* Executive Command Center Banner */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">
              <Cpu className="w-3.5 h-3.5 text-blue-600" />
              Google OR-Tools CP-SAT + Scikit-Learn Engine
            </span>
            <span className="text-xs text-slate-500 font-medium">
              Delhi Division (NDLS-GZB-PWL) Integrated Operations
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
            Railway Maintenance Planning & Decision-Support Command Center
          </h1>
          <p className="text-xs text-slate-600 max-w-2xl mt-1 leading-relaxed">
            Eliminating departmental scheduling conflicts between Engineering, TRD, and S&T. Validating resource availability, protecting high-speed train corridors, and providing disruption-resilient replanning.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onOpenOptimizationWorkflow}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-md shadow-blue-500/20 transition active:scale-95"
          >
            <Cpu className="w-4 h-4" />
            <span>Run CP-SAT Solver</span>
          </button>
          <button
            onClick={() => onNavigate("disruptions")}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-300 text-xs font-bold transition"
          >
            <ShieldAlert className="w-4 h-4 text-amber-600" />
            <span>Disruption Replanner</span>
          </button>
        </div>
      </div>

      {/* 10 Operational KPI Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
        {statCards.map((card, i) => {
          const Icon = card.icon;
          return (
            <motion.div
              key={i}
              whileHover={{ y: -2 }}
              transition={{ duration: 0.15 }}
              onClick={() => onNavigate(card.tab)}
              className="cursor-pointer rounded-2xl bg-white border border-slate-200 p-4 shadow-sm hover:shadow-md transition flex flex-col justify-between"
            >
              <div className="flex items-start justify-between">
                <span className="text-[11px] font-bold text-slate-600 leading-tight">
                  {card.title}
                </span>
                <div className={`p-1.5 rounded-lg border ${card.color}`}>
                  <Icon className={`w-3.5 h-3.5 ${card.iconColor}`} />
                </div>
              </div>

              <div className="my-2">
                <div className="text-2xl font-black text-slate-900 tracking-tight">
                  {card.value}
                </div>
                <p className="text-[10px] text-slate-500 mt-0.5 truncate">{card.subtitle}</p>
              </div>

              <div className="flex items-center justify-between text-[10px] text-slate-500 pt-2 border-t border-slate-100">
                <span className="font-semibold text-blue-600">Inspect Details</span>
                <ArrowUpRight className="w-3 h-3 text-slate-400" />
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Analytics Breakdown Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Department Workload Share */}
        <div className="rounded-2xl bg-white border border-slate-200 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Department Workload Share
                </h3>
                <p className="text-xs text-slate-500">Engineering, TRD, and S&T active demands</p>
              </div>
              <Wrench className="w-4 h-4 text-blue-600" />
            </div>

            <div className="space-y-4">
              {depts.map((d, idx) => {
                const Icon = d.icon;
                const pct = Math.round((d.count / totalDeptTasks) * 100);
                return (
                  <div key={idx} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <Icon className={`w-3.5 h-3.5 ${d.color}`} />
                        <span className="text-slate-800 font-semibold">{d.name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-500">{d.count} requests</span>
                        <span className="font-bold text-slate-900">{pct}%</span>
                      </div>
                    </div>
                    <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${d.bg} rounded-full transition-all duration-500`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>Co-located megablocks enabled</span>
            <button
              onClick={() => onNavigate("requests")}
              className="text-blue-600 hover:text-blue-800 font-semibold flex items-center gap-1"
            >
              <span>View all requests</span>
              <ArrowUpRight className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* Priority & AI Assessment Distribution */}
        <div className="rounded-2xl bg-white border border-slate-200 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  AI Priority & Risk Distribution
                </h3>
                <p className="text-xs text-slate-500">Scikit-Learn feature-weighted assessment</p>
              </div>
              <Flame className="w-4 h-4 text-rose-600" />
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200">
                <span className="text-[10px] font-bold text-rose-800 uppercase tracking-wider">
                  P1 Critical (85-100)
                </span>
                <div className="text-2xl font-black text-rose-900 mt-1">
                  {metrics.priority_distribution["P1_CRITICAL"] || 0}
                </div>
                <p className="text-[10px] text-slate-600 mt-0.5">Emergency track clearances</p>
              </div>

              <div className="p-3 rounded-xl bg-amber-50 border border-amber-200">
                <span className="text-[10px] font-bold text-amber-800 uppercase tracking-wider">
                  P2 High (70-84)
                </span>
                <div className="text-2xl font-black text-amber-900 mt-1">
                  {metrics.priority_distribution["P2_HIGH"] || 0}
                </div>
                <p className="text-[10px] text-slate-600 mt-0.5">Next daylight / night window</p>
              </div>

              <div className="p-3 rounded-xl bg-blue-50 border border-blue-200">
                <span className="text-[10px] font-bold text-blue-800 uppercase tracking-wider">
                  P3 Medium (50-69)
                </span>
                <div className="text-2xl font-black text-blue-900 mt-1">
                  {metrics.priority_distribution["P3_MEDIUM"] || 0}
                </div>
                <p className="text-[10px] text-slate-600 mt-0.5">Synchronized multi-dept</p>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                <span className="text-[10px] font-bold text-slate-700 uppercase tracking-wider">
                  P4 Routine (&lt;50)
                </span>
                <div className="text-2xl font-black text-slate-800 mt-1">
                  {metrics.priority_distribution["P4_ROUTINE"] || 0}
                </div>
                <p className="text-[10px] text-slate-600 mt-0.5">Standard cyclic maintenance</p>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>Features: Criticality, GMT, Age, Speed</span>
            <span className="text-emerald-700 font-bold">Trained Model</span>
          </div>
        </div>

        {/* Maintenance Window Utilization */}
        <div className="rounded-2xl bg-white border border-slate-200 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Corridor Block Utilization
                </h3>
                <p className="text-xs text-slate-500">
                  Scheduled maintenance vs train-free capacity
                </p>
              </div>
              <TrendingUp className="w-4 h-4 text-emerald-600" />
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-center">
              <div className="text-3xl font-black text-blue-700 tracking-tight">
                {metrics.block_utilization.hours_requested} hrs
              </div>
              <p className="text-xs text-slate-500 mt-1">Total Maintenance Demand</p>

              <div className="mt-4 grid grid-cols-2 gap-2 text-left text-xs">
                <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                  <span className="text-slate-500 text-[10px]">Granted Hours:</span>
                  <div className="font-bold text-emerald-700">{metrics.block_utilization.hours_granted} hrs</div>
                </div>
                <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                  <span className="text-slate-500 text-[10px]">Utilization Rate:</span>
                  <div className="font-bold text-blue-700">                  {metrics.block_utilization.utilization_percentage === null
                    ? "N/A"
                    : `${metrics.block_utilization.utilization_percentage}%`}</div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-100">
            <button
              onClick={() => onNavigate("timeline")}
              className="w-full py-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-blue-700 text-xs font-bold border border-slate-200 transition flex items-center justify-center gap-1.5"
            >
              <span>Explore Interactive Scheduling Timeline</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

      </div>

      {/* Live System Activity Feed */}
      <div className="rounded-2xl bg-white border border-slate-200 p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-600" />
            </span>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Operational Activity Feed & Audit Trail
            </h3>
          </div>
          <span className="text-xs text-slate-500 font-mono">
            {activityLogs.length} events logged
          </span>
        </div>

        <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
          {activityLogs.length === 0 ? (
            <p className="text-xs text-slate-500 py-4 text-center">No recent audit logs.</p>
          ) : (
            activityLogs.map((log) => {
              const getBadge = (b: string) => {
                switch (b) {
                  case "success":
                    return "bg-emerald-50 text-emerald-800 border-emerald-200";
                  case "danger":
                    return "bg-rose-50 text-rose-800 border-rose-200";
                  case "warning":
                    return "bg-amber-50 text-amber-800 border-amber-200";
                  default:
                    return "bg-blue-50 text-blue-800 border-blue-200";
                }
              };

              return (
                <div
                  key={log.id}
                  className="p-3 rounded-xl bg-slate-50/70 hover:bg-slate-50 border border-slate-200 transition flex items-start justify-between gap-3 text-xs"
                >
                  <div className="flex items-start gap-3">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase mt-0.5 ${getBadge(
                        log.badge_type
                      )}`}
                    >
                      {log.action.replace("_", " ")}
                    </span>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-900">{log.user_name}</span>
                        <span className="text-[10px] text-slate-500 font-mono">[{log.role}]</span>
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-white text-slate-600 border border-slate-200">
                          {log.department}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 mt-0.5 leading-snug">{log.details}</p>
                    </div>
                  </div>
                  <span className="text-[10px] text-slate-400 font-mono whitespace-nowrap">
                    {new Date(log.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                  </span>
                </div>
              );
            })
          )}
        </div>
      </div>

    </div>
  );
};
