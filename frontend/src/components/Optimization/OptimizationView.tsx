import React, { useState, useEffect } from "react";
import {
  Cpu,
  Play,
  CheckCircle2,
  XCircle,
  Pin,
  Clock,
  Shield,
  Layers,
  Sparkles,
  Zap,
  Radio,
  FileCheck2,
  Calendar,
  AlertCircle
} from "lucide-react";
import { MaintenanceBlock, WorkPackage } from "../../types";
import { api } from "../../api/client";
import { BlockReviewModal } from "./BlockReviewModal";
import { useAuth } from "../../context/AuthContext";

export const OptimizationView: React.FC = () => {
  const { isOperations } = useAuth();
  const [blocks, setBlocks] = useState<MaintenanceBlock[]>([]);
  const [workPackages, setWorkPackages] = useState<WorkPackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [solving, setSolving] = useState(false);
  const [solveStats, setSolveStats] = useState<any>(null);
  const [horizonHours, setHorizonHours] = useState(72);
  const [activeFilter, setActiveFilter] = useState("ALL");
  const [reviewingBlock, setReviewingBlock] = useState<MaintenanceBlock | null>(null);

  const fetchBlocks = async () => {
    setLoading(true);
    try {
      const [data, packages] = await Promise.all([
        api.getBlocks(activeFilter),
        api.getWorkPackages(),
      ]);
      setBlocks(data);
      setWorkPackages(packages);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBlocks();
  }, [activeFilter]);

  const handleRunOptimization = async () => {
    setSolving(true);
    try {
      const res = await api.runOptimization(horizonHours);
      setSolveStats(res);
      fetchBlocks();
    } catch (err) {
      console.error(err);
    } finally {
      setSolving(false);
    }
  };

  const handleReviewBlock = async (status: "APPROVED" | "REJECTED", notes?: string) => {
    if (!reviewingBlock) return;
    await api.reviewBlock(reviewingBlock.id, status, notes);
    fetchBlocks();
  };

  const handleTogglePin = async (id: number) => {
    await api.togglePinBlock(id);
    fetchBlocks();
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "APPROVED":
        return "bg-emerald-950 text-emerald-300 border-emerald-700";
      case "PROPOSED":
        return "bg-cyan-950 text-cyan-300 border-cyan-700";
      case "REJECTED":
        return "bg-rose-950 text-rose-300 border-rose-700";
      default:
        return "bg-slate-800 text-slate-400 border-slate-700";
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Top Banner & Control Deck */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-850 to-slate-900 border border-slate-800 shadow-2xl flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-cyan-950 text-cyan-300 border border-cyan-800">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" />
              OR-Tools CP-SAT Constraint Engine
            </span>
            <span className="text-xs text-amber-400 font-semibold flex items-center gap-1">
              <Shield className="w-3.5 h-3.5" />
              Railway Officer Human-in-the-Loop Authority
            </span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            Corridor Block Scheduling & Officer Approval
          </h2>
          <p className="text-xs text-slate-300 max-w-xl mt-1 leading-relaxed">
            Multi-objective constraint optimization resolves track possession clashes, respects corridor headway curfews, verifies Gang/Machine quotas, and delivers reviewable proposed blocks.
          </p>
        </div>

        {/* Solver Execution Box */}
        <div className="p-4 rounded-xl bg-slate-800/90 border border-slate-700 flex flex-col sm:flex-row items-center gap-3">
          <div>
            <label className="block text-[11px] font-semibold text-slate-300 mb-1">
              Planning Horizon
            </label>
            <select
              value={horizonHours}
              onChange={(e) => setHorizonHours(parseInt(e.target.value))}
              className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-cyan-500 font-medium"
            >
              <option value={24}>24 Hours (Immediate)</option>
              <option value={48}>48 Hours (Weekend)</option>
              <option value={72}>72 Hours (3-Day Trunk)</option>
              <option value={168}>7 Days (Weekly Horizon)</option>
            </select>
          </div>

          <button
            onClick={handleRunOptimization}
            disabled={solving}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-bold shadow-lg shadow-cyan-600/25 transition active:scale-95 disabled:opacity-50 mt-auto w-full sm:w-auto justify-center"
          >
            {solving ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Solving Constraints...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>Run CP-SAT Solver</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Solver Telemetry Stats (if solved) */}
      {solveStats && (
        <div className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-800/50 flex flex-wrap items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-2 text-emerald-300 font-semibold">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Optimization Completed: {solveStats.status} ({solveStats.solver_status_name})</span>
          </div>
          <div className="flex items-center gap-4 text-slate-300 font-mono text-[11px]">
            <span>Wall Time: {solveStats.wall_time_seconds}s</span>
            <span>•</span>
            <span>Blocks Scheduled: {solveStats.blocks_scheduled}</span>
            <span>•</span>
            <span>Penalty Objective: {solveStats.objective_value ? Math.round(solveStats.objective_value) : "0"}</span>
          </div>
        </div>
      )}
      {solveStats?.excluded?.length > 0 && (
        <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-800/50 space-y-3">
          <h3 className="text-xs font-bold text-rose-300">
            Requests excluded by readiness ({solveStats.excluded.length})
          </h3>
          {solveStats.excluded.map((item: any) => (
            <div key={item.request_id} className="text-xs text-slate-300">
              <span className="font-semibold text-white">{item.task_title}</span>
              <span className="text-rose-300"> — {item.failing_pillars.join(", ")}</span>
              <p className="mt-1 text-slate-400">{item.recommended_action}</p>
            </div>
          ))}
        </div>
      )}

      <section className="rounded-2xl bg-slate-900 border border-slate-800 p-5 shadow-xl">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm font-bold text-white">Work Packages</h3>
            <p className="text-[11px] text-slate-400 mt-1">
              Compatible cross-department tasks sharing a section window
            </p>
          </div>
          <Layers className="w-4 h-4 text-cyan-400" />
        </div>
        {workPackages.length === 0 ? (
          <p className="text-xs text-slate-500">No shared work packages in the current schedule.</p>
        ) : (
          <div className="grid gap-3 md:grid-cols-2">
            {workPackages.map((workPackage) => (
              <article
                key={workPackage.id}
                className="rounded-xl border border-slate-800 bg-slate-950/60 p-3"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs font-bold text-cyan-300">
                    WP-{workPackage.id}
                  </span>
                  <span className="text-[10px] text-emerald-300">
                    {workPackage.expected_utilization.toFixed(0)}% utilization
                  </span>
                </div>
                <p className="text-[11px] text-slate-300 mt-2">
                  {workPackage.section_code || `Section ${workPackage.section_id}`}
                  {" · "}
                  {workPackage.departments.join(", ")}
                </p>
                <p className="text-[11px] text-slate-400 mt-1">
                  {workPackage.tasks.map((task) => task.title).join(" + ")}
                </p>
                <p className="text-[10px] text-slate-500 font-mono mt-2">
                  {new Date(workPackage.shared_window_start).toLocaleString()}
                  {" – "}
                  {new Date(workPackage.shared_window_end).toLocaleString()}
                </p>
              </article>
            ))}
          </div>
        )}
      </section>

      {/* Filter Tabs */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {["ALL", "PROPOSED", "APPROVED", "REJECTED"].map((st) => (
            <button
              key={st}
              onClick={() => setActiveFilter(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                activeFilter === st
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                  : "text-slate-400 hover:text-white bg-slate-900 border border-slate-800"
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        <span className="text-xs text-slate-400 font-mono">
          Showing {blocks.length} scheduled maintenance blocks
        </span>
      </div>

      {/* Blocks Grid / Table */}
      <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden shadow-xl">
        {loading ? (
          <div className="py-16 text-center text-slate-400 text-xs flex flex-col items-center gap-2">
            <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
            <span>Loading scheduled maintenance blocks...</span>
          </div>
        ) : blocks.length === 0 ? (
          <div className="py-16 text-center text-slate-500 text-xs">
            No maintenance blocks scheduled. Click "Run CP-SAT Solver" to generate optimal blocks.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-850/60 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  <th className="py-3.5 px-4">Block Code</th>
                  <th className="py-3.5 px-4">Task & Corridor Section</th>
                  <th className="py-3.5 px-4">Scheduled Slot & Duration</th>
                  <th className="py-3.5 px-4">Track Possession</th>
                  <th className="py-3.5 px-4">Safety Isolations</th>
                  <th className="py-3.5 px-4">Pin Protection</th>
                  <th className="py-3.5 px-4">Approval Status</th>
                  <th className="py-3.5 px-4 text-right">Officer Authority</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70 text-xs">
                {blocks.map((b) => (
                  <tr key={b.id} className="hover:bg-slate-850/50 transition">
                    
                    {/* Block Code */}
                    <td className="py-3.5 px-4 font-mono font-bold text-cyan-400 whitespace-nowrap">
                      {b.block_code}
                    </td>

                    {/* Task Title & Section */}
                    <td className="py-3.5 px-4 max-w-sm">
                      <div className="font-semibold text-white truncate">{b.task_title}</div>
                      <div className="flex items-center gap-2 text-[11px] text-slate-400 mt-0.5">
                        <span className="font-mono text-cyan-300">{b.section_code}</span>
                        <span>•</span>
                        <span className="text-slate-300">{b.department}</span>
                      </div>
                    </td>

                    {/* Slot & Duration */}
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <div className="text-slate-200 font-mono text-[11px]">
                        {new Date(b.scheduled_start).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                      </div>
                      <div className="text-[10px] text-slate-400 mt-0.5">
                        Duration: <span className="font-semibold text-cyan-300">{b.duration_hours} hrs</span>
                      </div>
                    </td>

                    {/* Track Type */}
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium border border-slate-700">
                        {b.track_type.replace("_", " ")}
                      </span>
                    </td>

                    {/* Safety Isolation Clearance */}
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <div className="space-y-1">
                        {b.power_block_required && (
                          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-amber-950 text-amber-300 border border-amber-800">
                            <Zap className="w-3 h-3 text-amber-400" />
                            <span>25kV OHE Isolation</span>
                          </span>
                        )}
                        {b.signal_disconnection_required && (
                          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-emerald-950 text-emerald-300 border border-emerald-800 block">
                            <Radio className="w-3 h-3 text-emerald-400" />
                            <span>S&T Disconnection</span>
                          </span>
                        )}
                        {!b.power_block_required && !b.signal_disconnection_required && (
                          <span className="text-slate-500 text-[10px]">P-Way Lookout Flag</span>
                        )}
                      </div>
                    </td>

                    {/* Pin Status */}
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <button
                        onClick={() => handleTogglePin(b.id)}
                        title={b.is_pinned ? "Pinned (Protected from replan drift)" : "Click to pin"}
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border transition ${
                          b.is_pinned
                            ? "bg-purple-950 text-purple-300 border-purple-700 shadow-sm shadow-purple-950"
                            : "bg-slate-800 text-slate-400 border-slate-700 hover:text-white"
                        }`}
                      >
                        <Pin className={`w-3 h-3 ${b.is_pinned ? "fill-purple-400" : ""}`} />
                        <span>{b.is_pinned ? "PINNED" : "FLEXIBLE"}</span>
                      </button>
                    </td>

                    {/* Status */}
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wider ${getStatusBadge(b.status)}`}>
                        {b.status}
                      </span>
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 text-right whitespace-nowrap">
                      {isOperations ? (
                        <button
                          onClick={() => setReviewingBlock(b)}
                          className="px-3 py-1.5 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/40 text-[11px] font-bold transition flex items-center gap-1 ml-auto"
                        >
                          <FileCheck2 className="w-3.5 h-3.5 text-cyan-400" />
                          <span>Review & Decide</span>
                        </button>
                      ) : (
                        <span className="text-[11px] text-slate-500 italic">Operations Only</span>
                      )}
                    </td>

                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Review Modal */}
      {reviewingBlock && (
        <BlockReviewModal
          block={reviewingBlock}
          onConfirm={handleReviewBlock}
          onClose={() => setReviewingBlock(null)}
        />
      )}

    </div>
  );
};
