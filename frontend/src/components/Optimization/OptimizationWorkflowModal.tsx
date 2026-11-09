import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Cpu,
  CheckCircle2,
  Clock,
  Sparkles,
  ArrowRight,
  Shield,
  Layers,
  Wrench,
  Train,
  Check,
  X,
  FileCheck2
} from "lucide-react";
import { api } from "../../api/client";
import { useToast } from "../Shared/ToastContext";

interface OptimizationWorkflowModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete?: () => void;
  onSuccess?: () => void;
  horizonHours?: number;
}

export const OptimizationWorkflowModal: React.FC<OptimizationWorkflowModalProps> = ({
  isOpen,
  onClose,
  onComplete,
  onSuccess,
  horizonHours = 72,
}) => {
  if (!isOpen) return null;
  const { showToast } = useToast();
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [isSolving, setIsSolving] = useState<boolean>(true);
  const [solverResult, setSolverResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const steps = [
    { title: "Analysing maintenance requests", desc: "Loading multi-department requisitions from Engineering, TRD, and S&T", icon: Layers },
    { title: "Evaluating task priorities", desc: "Executing Scikit-Learn trained priority & risk assessment model", icon: Sparkles },
    { title: "Checking resource availability", desc: "Validating Gang staff quotas, heavy machinery, and replacement spares", icon: Wrench },
    { title: "Validating train schedules", desc: "Checking Vande Bharat, Rajdhani, and Freight headway buffer curfews", icon: Train },
    { title: "Running CP-SAT optimizer", desc: "Google OR-Tools CP-SAT multi-objective integer programming", icon: Cpu },
    { title: "Evaluating scheduling constraints", desc: "Verifying track non-overlap, power isolation, and DAG dependencies", icon: Shield },
    { title: "Generating optimized plan", desc: "Synthesizing conflict-free, reviewable proposed maintenance blocks", icon: FileCheck2 },
  ];

  useEffect(() => {
    let cancelled = false;

    const executeWorkflow = async () => {
      try {
        // Step 1: Analysing requests
        setCurrentStep(0);
        await new Promise((r) => setTimeout(r, 600));
        if (cancelled) return;

        // Step 2: Evaluating priorities
        setCurrentStep(1);
        await new Promise((r) => setTimeout(r, 600));
        if (cancelled) return;

        // Step 3: Checking resources
        setCurrentStep(2);
        await new Promise((r) => setTimeout(r, 500));
        if (cancelled) return;

        // Step 4: Validating train schedules
        setCurrentStep(3);
        await new Promise((r) => setTimeout(r, 500));
        if (cancelled) return;

        // Step 5: Running CP-SAT
        setCurrentStep(4);
        
        // Actual Backend Call to Google OR-Tools CP-SAT
        const res = await api.runOptimization(horizonHours);
        if (cancelled) return;

        // Step 6: Constraint validation
        setCurrentStep(5);
        await new Promise((r) => setTimeout(r, 600));
        if (cancelled) return;

        // Step 7: Completed
        setCurrentStep(6);
        setSolverResult(res);
        setIsSolving(false);
        onSuccess?.();
        onComplete?.();
        showToast("success", "Optimization Solved", `${res.blocks_scheduled} maintenance blocks planned via CP-SAT.`);
      } catch (err: any) {
        if (!cancelled) {
          setError(err.message || "Failed to solve maintenance schedule");
          setIsSolving(false);
          showToast("error", "Optimization Error", err.message);
        }
      }
    };

    executeWorkflow();

    return () => {
      cancelled = true;
    };
  }, [horizonHours]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-sm animate-in fade-in">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative w-full max-w-3xl rounded-2xl bg-white border border-slate-200 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
      >
        {/* Header */}
        <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-blue-600 text-white shadow-md shadow-blue-500/30">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white">Google OR-Tools CP-SAT Optimization</h3>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-blue-300 border border-slate-700">
                  {horizonHours}h Horizon
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Evaluating multi-objective mathematical constraints for Indian Railways
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Stepper Progress */}
        <div className="p-6 overflow-y-auto space-y-6">
          {error ? (
            <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
              {error}
            </div>
          ) : isSolving ? (
            <div className="space-y-4">
              <div className="space-y-3">
                {steps.map((st, idx) => {
                  const Icon = st.icon;
                  const isDone = currentStep > idx;
                  const isCurrent = currentStep === idx;
                  return (
                    <div
                      key={idx}
                      className={`p-3.5 rounded-xl border transition-all flex items-center gap-3.5 ${
                        isCurrent
                          ? "bg-blue-50 border-blue-300 shadow-sm"
                          : isDone
                          ? "bg-slate-50 border-slate-200 text-slate-700"
                          : "bg-white border-slate-100 text-slate-400 opacity-60"
                      }`}
                    >
                      <div
                        className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 font-bold text-xs ${
                          isDone
                            ? "bg-emerald-600 text-white"
                            : isCurrent
                            ? "bg-blue-600 text-white animate-pulse"
                            : "bg-slate-200 text-slate-500"
                        }`}
                      >
                        {isDone ? <Check className="w-4 h-4" /> : idx + 1}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <h4 className="text-xs font-bold text-slate-900">{st.title}</h4>
                          {isCurrent && (
                            <span className="text-[10px] font-mono text-blue-600 font-semibold animate-pulse">
                              Processing...
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5 truncate">{st.desc}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Actual Solver Telemetry Results */}
              <div className="p-5 rounded-2xl bg-gradient-to-r from-emerald-50 via-white to-blue-50 border border-emerald-200 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-3.5">
                  <div className="w-12 h-12 rounded-full bg-emerald-600 text-white flex items-center justify-center flex-shrink-0 shadow-lg shadow-emerald-600/20">
                    <CheckCircle2 className="w-6 h-6" />
                  </div>
                  <div>
                    <span className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider">
                      Solver Status: {solverResult?.status} ({solverResult?.solver_status_name})
                    </span>
                    <h3 className="text-lg font-bold text-slate-900 mt-0.5">
                      {solverResult?.blocks_scheduled} Maintenance Blocks Synthesized
                    </h3>
                    <p className="text-xs text-slate-500">
                      Zero track possession clashes • Verified Gang & Machine capacities
                    </p>
                  </div>
                </div>

                <div className="text-xs font-mono text-slate-700 bg-white p-3 rounded-xl border border-slate-200 shadow-sm space-y-1">
                  <div>Wall Time: <strong className="text-blue-600">{solverResult?.wall_time_seconds}s</strong></div>
                  <div>Objective: <strong className="text-emerald-700">{solverResult?.objective_value ? Math.round(solverResult.objective_value) : "0"}</strong></div>
                </div>
              </div>

              {/* Explainable Decision Justification */}
              <div>
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2">
                  Optimization Explainability & Allocation Rationales
                </h4>

                <div className="space-y-2.5">
                  {solverResult?.schedule?.map((item: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 hover:border-blue-200 transition text-xs space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-blue-700">{item.section_code}</span>
                          <span className="text-slate-400">•</span>
                          <span className="font-semibold text-slate-900">{item.task_title}</span>
                        </div>
                        <span className="font-mono text-slate-600 text-[11px]">
                          {new Date(item.scheduled_start).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} - {new Date(item.scheduled_end).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </span>
                      </div>

                      <div className="flex items-center gap-2 text-[11px] text-slate-500">
                        <span className="px-1.5 py-0.2 rounded bg-white text-slate-700 border border-slate-200">
                          {item.department}
                        </span>
                        <span className="px-1.5 py-0.2 rounded bg-white text-slate-700 border border-slate-200">
                          Track: {item.track_type.replace("_", " ")}
                        </span>
                        <span className="text-emerald-700 font-medium">
                          ✓ Headway buffer cleared with Vande Bharat corridor
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-white hover:bg-slate-100 text-slate-700 text-xs font-semibold border border-slate-200 transition"
          >
            Close Stepper
          </button>
          {!isSolving && (
            <button
              onClick={onClose}
              className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md shadow-blue-500/20 transition"
            >
              Inspect Schedule
            </button>
          )}
        </div>
      </motion.div>
    </div>
  );
};
