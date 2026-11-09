import React, { useEffect, useState } from "react";
import {
  X,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Users,
  Wrench,
  Package,
  Clock,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { ReadinessReport } from "../../types";
import { api } from "../../api/client";

interface ReadinessAuditModalProps {
  requestId: number;
  taskTitle: string;
  onClose: () => void;
}

export const ReadinessAuditModal: React.FC<ReadinessAuditModalProps> = ({
  requestId,
  taskTitle,
  onClose
}) => {
  const [report, setReport] = useState<ReadinessReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    api.getReadinessReport(requestId)
      .then((data) => setReport(data))
      .catch((err) => console.error("Failed to load readiness report", err))
      .finally(() => setLoading(false));
  }, [requestId]);

  const getGradeBadge = (grade?: string) => {
    switch (grade) {
      case "READY_FOR_EXECUTION":
        return {
          bg: "bg-emerald-950/80 border-emerald-500/50 text-emerald-300",
          icon: CheckCircle2,
          text: "READY FOR EXECUTION"
        };
      case "CONDITIONAL_APPROVAL":
        return {
          bg: "bg-amber-950/80 border-amber-500/50 text-amber-300",
          icon: AlertTriangle,
          text: "CONDITIONAL APPROVAL (REMEDIATE DEFICIT)"
        };
      default:
        return {
          bg: "bg-rose-950/80 border-rose-500/50 text-rose-300",
          icon: XCircle,
          text: "CRITICAL DEFICIT BLOCKED"
        };
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in">
      <div className="relative w-full max-w-3xl rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="px-6 py-4 bg-slate-850 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-cyan-950 text-cyan-400 border border-cyan-800">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white">Explainable Block Readiness Audit</h2>
                <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-cyan-300 font-mono border border-slate-700">
                  ID: #{requestId}
                </span>
              </div>
              <p className="text-xs text-slate-400 truncate max-w-lg mt-0.5">{taskTitle}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center gap-3">
              <div className="w-8 h-8 border-3 border-cyan-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-xs text-slate-400">Verifying staff rosters, depot machinery, and power permits...</p>
            </div>
          ) : !report ? (
            <div className="py-12 text-center text-rose-400 text-sm">Failed to generate readiness audit.</div>
          ) : (
            <>
              {/* Composite Readiness Score Card */}
              <div className="p-5 rounded-2xl bg-gradient-to-r from-slate-850 via-slate-800 to-slate-850 border border-slate-700 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className="relative flex items-center justify-center w-20 h-20 rounded-full bg-slate-900 border-4 border-cyan-500/80 shadow-lg text-white font-extrabold text-2xl font-mono">
                    {report.overall_readiness_score == null ? "—" : `${report.overall_readiness_score}%`}
                  </div>
                  <div>
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Composite Readiness Score
                    </span>
                    <div className="mt-1">
                      {(() => {
                        const badge = getGradeBadge(report.readiness_grade);
                        const Icon = badge.icon;
                        return (
                          <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${badge.bg}`}>
                            <Icon className="w-3.5 h-3.5" />
                            <span>{badge.text}</span>
                          </div>
                        );
                      })()}
                    </div>
                  </div>
                </div>

                <div className="text-xs text-slate-300 max-w-xs bg-slate-900/60 p-3 rounded-xl border border-slate-800 leading-relaxed">
                  <span className="font-semibold text-cyan-300 block mb-1">Decision Support Recommendation:</span>
                  {report.recommendation}
                </div>
              </div>

              {/* 5-Pillar Detailed Explainability Audit */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  5-Pillar Verification Breakdown
                </h3>

                {/* Pillar 1: Staff */}
                <div className="p-4 rounded-xl bg-slate-850 border border-slate-800 flex items-start gap-3.5">
                  <div className="p-2 rounded-lg bg-blue-950 text-blue-400 border border-blue-800 mt-0.5">
                    <Users className="w-4 h-4" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white">1. Gang & Skilled Crew Readiness</span>
                      <span className="text-xs font-mono font-bold text-cyan-400">
                        {report.pillars.staff.score == null
                          ? report.pillars.staff.status
                          : `${report.pillars.staff.score}% ${report.pillars.staff.status}`}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">{report.pillars.staff.notes}</p>
                  </div>
                </div>

                {/* Pillar 2: Machinery */}
                <div className="p-4 rounded-xl bg-slate-850 border border-slate-800 flex items-start gap-3.5">
                  <div className="p-2 rounded-lg bg-amber-950 text-amber-400 border border-amber-800 mt-0.5">
                    <Wrench className="w-4 h-4" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white">2. Heavy Machinery & Equipment Allocation</span>
                      <span className="text-xs font-mono font-bold text-cyan-400">
                        {report.pillars.machinery.score == null
                          ? report.pillars.machinery.status
                          : `${report.pillars.machinery.score}% ${report.pillars.machinery.status}`}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">{report.pillars.machinery.notes}</p>
                  </div>
                </div>

                {/* Pillar 3: Materials & Permanent-Way Spares */}
                <div className="p-4 rounded-xl bg-slate-850 border border-slate-800 flex items-start gap-3.5">
                  <div className="p-2 rounded-lg bg-emerald-950 text-emerald-400 border border-emerald-800 mt-0.5">
                    <Package className="w-4 h-4" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white">3. Materials & Replacement Stock</span>
                      <span className="text-xs font-mono font-bold text-cyan-400">
                        {report.pillars.materials.score == null
                          ? report.pillars.materials.status
                          : `${report.pillars.materials.score}% ${report.pillars.materials.status}`}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">{report.pillars.materials.notes}</p>
                  </div>
                </div>

                {/* Pillar 4: Traffic Window Feasibility */}
                <div className="p-4 rounded-xl bg-slate-850 border border-slate-800 flex items-start gap-3.5">
                  <div className="p-2 rounded-lg bg-indigo-950 text-indigo-400 border border-indigo-800 mt-0.5">
                    <Clock className="w-4 h-4" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white">4. Corridor Traffic Window & Headway Gap</span>
                      <span className="text-xs font-mono font-bold text-cyan-400">
                        {report.pillars.traffic_window.score == null
                          ? report.pillars.traffic_window.status
                          : `${report.pillars.traffic_window.score}% ${report.pillars.traffic_window.status}`}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">{report.pillars.traffic_window.notes}</p>
                  </div>
                </div>

                {/* Pillar 5: Safety Isolation Clearance */}
                <div className="p-4 rounded-xl bg-slate-850 border border-slate-800 flex items-start gap-3.5">
                  <div className="p-2 rounded-lg bg-purple-950 text-purple-400 border border-purple-800 mt-0.5">
                    <ShieldCheck className="w-4 h-4" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white">5. Department Safety Protocols & Isolation Memo</span>
                      <span className="text-xs font-mono font-bold text-cyan-400">
                        {report.pillars.safety_isolation.score == null
                          ? report.pillars.safety_isolation.status
                          : `${report.pillars.safety_isolation.score}% ${report.pillars.safety_isolation.status}`}
                      </span>
                    </div>
                    <div className="mt-2 space-y-1">
                      {report.pillars.safety_isolation.protocol_checks?.map((check: string, idx: number) => (
                        <div key={idx} className="flex items-center gap-2 text-xs text-slate-300">
                          {report.pillars.safety_isolation.obtained?.includes(check)
                            ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                            : <AlertTriangle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />}
                          <span>{check}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 bg-slate-850 border-t border-slate-800 flex items-center justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-750 text-white text-xs font-semibold transition"
          >
            Close Audit
          </button>
        </div>

      </div>
    </div>
  );
};
