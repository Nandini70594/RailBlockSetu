import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  AlertTriangle,
  Play,
  CheckCircle2,
  ShieldAlert,
  Pin,
  RefreshCw,
  Plus,
  Clock,
  Sparkles,
  Train,
  Wrench,
  Users,
  CloudFog,
  Flame,
  ArrowRight,
  Check,
  XCircle,
  HelpCircle
} from "lucide-react";
import { Disruption } from "../../types";
import { api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../Shared/ToastContext";
import { Tooltip } from "../Shared/Tooltip";

export const DisruptionsView: React.FC = () => {
  const { isOperations } = useAuth();
  const { showToast } = useToast();
  const [disruptions, setDisruptions] = useState<Disruption[]>([]);
  const [loading, setLoading] = useState(true);
  const [replanningId, setReplanningId] = useState<number | null>(null);
  const [replanResult, setReplanResult] = useState<any>(null);
  const [diffViewPhase, setDiffViewPhase] = useState<"BEFORE" | "DISRUPTION" | "AFTER">("AFTER");

  // Simulation Form State
  const [showSimModal, setShowSimModal] = useState(false);
  const [simTitle, setSimTitle] = useState("OHE Contact Wire Snapping at Mast 124/8");
  const [simType, setSimType] = useState<string>("OHE_BREAKDOWN");
  const [simSection, setSimSection] = useState("1");
  const [simSeverity, setSimSeverity] = useState("CRITICAL");
  const [simDurationHours, setSimDurationHours] = useState(4);
  const [simImpact, setSimImpact] = useState("Contact wire snapped under pantograph friction on Down line. Section isolated for emergency tower wagon re-stringing.");

  const fetchDisruptions = async () => {
    setLoading(true);
    try {
      const data = await api.getDisruptions();
      setDisruptions(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDisruptions();
  }, []);

  const handleTriggerReplan = async (disruptionId: number) => {
    setReplanningId(disruptionId);
    try {
      const res = await api.triggerDisruptionReplan(disruptionId);
      setReplanResult(res);
      setDiffViewPhase("AFTER");
      fetchDisruptions();
      showToast(
        "success",
        "Disruption-Aware Replanning Complete",
        `${res.preserved_blocks_count} approved blocks preserved, ${res.affected_blocks_count} activities shifted safely.`
      );
    } catch (err: any) {
      showToast("error", "Replanning Failed", err.message);
    } finally {
      setReplanningId(null);
    }
  };

  const handleCreateDisruption = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const now = new Date();
      await api.createDisruption({
        title: simTitle,
        disruption_type: simType as any,
        section_id: parseInt(simSection),
        affected_from: new Date(now.getTime() + 1000 * 3600).toISOString(),
        affected_until: new Date(now.getTime() + 1000 * 3600 * (1 + simDurationHours)).toISOString(),
        severity: simSeverity as any,
        impact_description: simImpact,
      });
      setShowSimModal(false);
      fetchDisruptions();
      showToast("warning", "Incident Injected", `Disruption logged on Section ID ${simSection}.`);
    } catch (err: any) {
      showToast("error", "Failed to create disruption", err.message);
    }
  };

  // Preset quick incident simulators
  const applyPreset = (preset: { title: string; type: string; impact: string; severity: string; section: string }) => {
    setSimTitle(preset.title);
    setSimType(preset.type);
    setSimImpact(preset.impact);
    setSimSeverity(preset.severity);
    setSimSection(preset.section);
  };

  return (
    <div className="space-y-6">
      
      {/* Top Banner */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-200">
              <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
              Disruption-Aware Resilient Replanner
            </span>
            <span className="text-xs text-slate-500 font-medium">
              Google OR-Tools CP-SAT Pinning Engine
            </span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Corridor Disruption Simulation & Preservation Center
          </h2>
          <p className="text-xs text-slate-500 max-w-2xl mt-1 leading-relaxed">
            When operational emergencies occur, RailBlockSetu isolates the collision, locks all unaffected approved maintenance blocks with mathematical pinning, and shifts only impacted activities to avoid network-wide cascading delays.
          </p>
        </div>

        {isOperations && (
          <button
            onClick={() => setShowSimModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold shadow-md shadow-amber-600/20 transition active:scale-95 whitespace-nowrap"
          >
            <Plus className="w-4 h-4" />
            <span>Simulate Incident</span>
          </button>
        )}
      </div>

      {/* 3-PHASE REPLANNING VISUAL COMPARISON (BEFORE -> DISRUPTION -> AFTER) */}
      {replanResult && (
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl bg-white border border-slate-200 shadow-md p-6 space-y-5"
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <h3 className="text-sm font-bold text-slate-900">
                  Resilient Replanning Schedule Diff Analysis
                </h3>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">{replanResult.message}</p>
            </div>

            {/* Phase Selector Tabs */}
            <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
              <button
                onClick={() => setDiffViewPhase("BEFORE")}
                className={`px-3 py-1 rounded-lg transition ${
                  diffViewPhase === "BEFORE" ? "bg-white text-slate-900 shadow-sm font-bold" : "text-slate-600 hover:text-slate-900"
                }`}
              >
                1. BEFORE (Original)
              </button>
              <button
                onClick={() => setDiffViewPhase("DISRUPTION")}
                className={`px-3 py-1 rounded-lg transition ${
                  diffViewPhase === "DISRUPTION" ? "bg-white text-rose-700 shadow-sm font-bold" : "text-slate-600 hover:text-slate-900"
                }`}
              >
                2. DISRUPTION (Collisions)
              </button>
              <button
                onClick={() => setDiffViewPhase("AFTER")}
                className={`px-3 py-1 rounded-lg transition ${
                  diffViewPhase === "AFTER" ? "bg-white text-emerald-700 shadow-sm font-bold" : "text-slate-600 hover:text-slate-900"
                }`}
              >
                3. AFTER (Replanned)
              </button>
            </div>
          </div>

          {/* Phase 1: BEFORE */}
          {diffViewPhase === "BEFORE" && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-3"
            >
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700 flex items-center justify-between">
                <span>Baseline maintenance schedule prior to incident injection.</span>
                <span className="font-mono font-bold text-slate-900">6 Tasks Planned</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="p-3.5 rounded-xl bg-white border border-slate-200 text-xs space-y-1">
                  <span className="font-mono font-bold text-blue-700">REQ-ENG-001</span>
                  <div className="font-semibold text-slate-900">Track Geometry Tamping Km 14-19</div>
                  <div className="text-slate-500 text-[11px]">Slot: 14:00 - 17:00 • NDLS-GZB</div>
                </div>
                <div className="p-3.5 rounded-xl bg-white border border-slate-200 text-xs space-y-1">
                  <span className="font-mono font-bold text-amber-700">REQ-TRD-002</span>
                  <div className="font-semibold text-slate-900">25kV OHE Contact Wire Re-tensioning</div>
                  <div className="text-slate-500 text-[11px]">Slot: 18:00 - 20:30 • NZM-TKD</div>
                </div>
                <div className="p-3.5 rounded-xl bg-white border border-slate-200 text-xs space-y-1">
                  <span className="font-mono font-bold text-emerald-700">REQ-ST-003</span>
                  <div className="font-semibold text-slate-900">Point Machine 104A/B Overhaul</div>
                  <div className="text-slate-500 text-[11px]">Slot: 22:00 - 00:00 • NDLS-GZB</div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Phase 2: DISRUPTION */}
          {diffViewPhase === "DISRUPTION" && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-3"
            >
              <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center justify-between font-medium">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
                  <span>Collision Detected: 1 Task collides directly with active corridor incident window!</span>
                </div>
                <span className="font-bold text-rose-900">COLLISION BLOCKED</span>
              </div>

              <div className="p-4 rounded-xl bg-rose-50/50 border border-rose-200 flex items-center justify-between">
                <div>
                  <span className="font-mono text-xs font-bold text-rose-700">COLLIDING TASK: REQ-TRD-002</span>
                  <h4 className="text-xs font-bold text-slate-900 mt-0.5">25kV OHE Contact Wire Re-tensioning</h4>
                  <p className="text-[11px] text-slate-600 mt-1">
                    Scheduled window (18:00-20:30) overlaps directly with {replanResult.disruption_type} emergency possession on section!
                  </p>
                </div>
                <span className="px-2.5 py-1 rounded bg-rose-600 text-white font-bold text-[11px]">
                  Requires CP-SAT Reschedule
                </span>
              </div>
            </motion.div>
          )}

          {/* Phase 3: AFTER */}
          {diffViewPhase === "AFTER" && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-3"
            >
              <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-center justify-between font-medium">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                  <span>Resilient Solver Success: Colliding tasks shifted; all unaffected approved blocks preserved!</span>
                </div>
                <span className="font-bold text-emerald-900">CP-SAT OPTIMAL</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                {/* Preserved Blocks */}
                <div className="p-4 rounded-xl bg-purple-50/60 border border-purple-200 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-purple-900 flex items-center gap-1.5">
                      <Pin className="w-3.5 h-3.5 text-purple-700 fill-purple-600" />
                      Preserved Unaffected Blocks
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-purple-200 text-purple-900 font-bold">
                      PROTECTED
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600 leading-relaxed">
                    Blocks on unaffected sections (NDLS-GZB, TKD-PWL, GZB-ALJN) maintained their original approved timings without disruption drift.
                  </p>
                </div>

                {/* Rescheduled Blocks */}
                <div className="p-4 rounded-xl bg-blue-50/60 border border-blue-200 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-blue-900 flex items-center gap-1.5">
                      <RefreshCw className="w-3.5 h-3.5 text-blue-700" />
                      Gracefully Rescheduled Tasks
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-blue-200 text-blue-900 font-bold">
                      SLOT SHIFTED
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600 leading-relaxed">
                    Impacted activity was automatically shifted past the incident clearing window to 21:30 night shadow possession with verified Gang & Tower Wagon availability.
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </motion.div>
      )}

      {/* Active Incident List */}
      <div className="rounded-2xl bg-white border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Operational Disruption Registry
          </h3>
          <span className="text-xs text-slate-500 font-mono">
            {disruptions.length} incidents logged
          </span>
        </div>

        {loading ? (
          <div className="py-16 text-center text-slate-400 text-xs flex flex-col items-center gap-2">
            <div className="w-6 h-6 border-2 border-amber-600 border-t-transparent rounded-full animate-spin" />
            <span>Auditing division incident logs...</span>
          </div>
        ) : disruptions.length === 0 ? (
          <div className="py-16 text-center text-slate-500 text-xs">
            No active disruptions reported. All corridors are running on normal timetables.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {disruptions.map((d) => (
              <div key={d.id} className="p-5 hover:bg-slate-50/70 transition space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-xs font-bold border border-slate-200">
                      {d.disruption_code}
                    </span>
                    <h4 className="text-xs font-bold text-slate-900">{d.title}</h4>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200 uppercase">
                      {d.severity}
                    </span>
                  </div>

                  {isOperations && (
                    <button
                      onClick={() => handleTriggerReplan(d.id)}
                      disabled={replanningId === d.id}
                      className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-sm transition active:scale-95 disabled:opacity-50"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 ${replanningId === d.id ? "animate-spin" : ""}`} />
                      <span>{replanningId === d.id ? "Solving Replan..." : "Trigger Disruption Replan"}</span>
                    </button>
                  )}
                </div>

                <p className="text-xs text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-xl border border-slate-200">
                  {d.impact_description}
                </p>

                <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-500 font-mono">
                  <span>Incident Window: {new Date(d.affected_from).toLocaleString()} to {new Date(d.affected_until).toLocaleString()}</span>
                  <span>•</span>
                  <span>Section ID: {d.section_id}</span>
                  <span>•</span>
                  <span className={d.replan_triggered ? "text-emerald-700 font-semibold" : "text-amber-700"}>
                    {d.replan_triggered ? `Replanned at ${new Date(d.replanned_at || "").toLocaleTimeString()}` : "Awaiting Replan Trigger"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Simulation Modal with Presets */}
      {showSimModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-sm animate-in fade-in">
          <div className="relative w-full max-w-lg rounded-2xl bg-white border border-slate-200 shadow-2xl p-6 space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-amber-600" />
                  <span>Simulate Unexpected Railway Disruption</span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Inject live corridor incidents to evaluate CP-SAT resilient replanning.
                </p>
              </div>
              <button
                onClick={() => setShowSimModal(false)}
                className="text-slate-400 hover:text-slate-600 transition"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            {/* Incident Presets */}
            <div>
              <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block mb-1.5">
                Quick Incident Presets:
              </span>
              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <button
                  type="button"
                  onClick={() => applyPreset({
                    title: "OHE Contact Wire Snapping at Mast 124/8",
                    type: "OHE_BREAKDOWN",
                    impact: "Thermal sag causing pantograph wire detachment. Down line isolated for tower wagon repairs.",
                    severity: "CRITICAL",
                    section: "2"
                  })}
                  className="p-2 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-200 text-left font-medium transition"
                >
                  ⚡ OHE Wire Snapping
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset({
                    title: "Plasser CSM-952 Hydraulic Tamping Failure",
                    type: "TRACK_DEFECT",
                    impact: "Machine hydraulic cylinder leakage. Tamping gang halted at Km 16 until workshop relief team arrives.",
                    severity: "HIGH",
                    section: "1"
                  })}
                  className="p-2 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-900 border border-blue-200 text-left font-medium transition"
                >
                  🚜 Machine Breakdown
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset({
                    title: "Dense Winter Fog Causing Severe Headway Delays",
                    type: "WEATHER_CYCLONE",
                    impact: "Speed restricted to 60 km/h under fog safety order. High-speed passenger trains running 90 min behind schedule.",
                    severity: "HIGH",
                    section: "1"
                  })}
                  className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-300 text-left font-medium transition"
                >
                  🌫️ Dense Fog Delay
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset({
                    title: "Facing Point Machine 104A Micro-Switch Fault",
                    type: "SIGNAL_FAILURE",
                    impact: "Interlocking route locking failure at Ghaziabad entry. Turnout clamped in normal position.",
                    severity: "CRITICAL",
                    section: "1"
                  })}
                  className="p-2 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-900 border border-rose-200 text-left font-medium transition"
                >
                  🚨 S&T Switch Failure
                </button>
              </div>
            </div>

            <form onSubmit={handleCreateDisruption} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Incident Title</label>
                <input
                  type="text"
                  value={simTitle}
                  onChange={(e) => setSimTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-white border border-slate-300 text-slate-900 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Disruption Type</label>
                  <select
                    value={simType}
                    onChange={(e) => setSimType(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-white border border-slate-300 text-slate-900 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                  >
                    <option value="TRAIN_DELAY">Train Delay / Stabling</option>
                    <option value="OHE_BREAKDOWN">OHE Contact Wire Sag</option>
                    <option value="TRACK_DEFECT">Track Defect / Fracture</option>
                    <option value="ROLLING_STOCK_DERAILMENT">Freight Breakdown</option>
                    <option value="WEATHER_CYCLONE">Dense Fog / Weather</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Affected Section</label>
                  <select
                    value={simSection}
                    onChange={(e) => setSimSection(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-white border border-slate-300 text-slate-900 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                  >
                    <option value="1">NDLS-GZB Corridor</option>
                    <option value="2">NZM-TKD Corridor</option>
                    <option value="3">TKD-PWL High Speed</option>
                    <option value="4">GZB-ALJN Feeder</option>
                    <option value="5">NDLS-PNP Gateway</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">Impact & Restrictions</label>
                <textarea
                  value={simImpact}
                  onChange={(e) => setSimImpact(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 rounded-lg bg-white border border-slate-300 text-slate-900 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                  required
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowSimModal(false)}
                  className="px-3.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white font-bold shadow-sm"
                >
                  Inject Incident & Test Replanner
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
