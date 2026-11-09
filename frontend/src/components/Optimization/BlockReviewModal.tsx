import React, { useState } from "react";
import { X, CheckCircle2, XCircle, Pin, Shield } from "lucide-react";
import { MaintenanceBlock } from "../../types";

interface BlockReviewModalProps {
  block: MaintenanceBlock;
  onConfirm: (status: "APPROVED" | "REJECTED", notes?: string) => Promise<void>;
  onClose: () => void;
}

export const BlockReviewModal: React.FC<BlockReviewModalProps> = ({
  block,
  onConfirm,
  onClose
}) => {
  const [decision, setDecision] = useState<"APPROVED" | "REJECTED">("APPROVED");
  const [notes, setNotes] = useState<string>(block.approval_notes || "Corridor slot authorized. Coordinate with Station Master for track possession flag and OHE permit.");
  const [loading, setLoading] = useState(false);

  const handleAction = async () => {
    setLoading(true);
    try {
      await onConfirm(decision, notes);
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
      <div className="relative w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl overflow-hidden flex flex-col">
        
        {/* Header */}
        <div className="px-6 py-4 bg-slate-850 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-amber-950 text-amber-400 border border-amber-800">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Operations Officer Authority Review</h2>
              <p className="text-xs text-slate-400 font-mono">Block Code: {block.block_code}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <div className="p-3.5 rounded-xl bg-slate-850 border border-slate-800 text-xs text-slate-300 space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-400">Corridor Section:</span>
              <span className="font-mono font-semibold text-cyan-300">{block.section_code}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Track Possession:</span>
              <span className="font-semibold text-white">{block.track_type.replace("_", " ")}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Scheduled Start:</span>
              <span className="font-mono text-slate-200">{new Date(block.scheduled_start).toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Duration:</span>
              <span className="font-semibold text-white">{block.duration_hours} hours</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">TRD Power Block Required:</span>
              <span className={`font-semibold ${block.power_block_required ? "text-amber-400" : "text-slate-500"}`}>
                {block.power_block_required ? "YES (25kV OHE Isolation)" : "NO"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">S&T Disconnection Notice:</span>
              <span className={`font-semibold ${block.signal_disconnection_required ? "text-amber-400" : "text-slate-500"}`}>
                {block.signal_disconnection_required ? "YES (Interlocking Disconnection)" : "NO"}
              </span>
            </div>
          </div>

          {block.readiness_snapshot && (
            <div className="p-3.5 rounded-xl bg-slate-850 border border-slate-800 text-xs text-slate-300 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white">Readiness: {block.readiness_verdict}</span>
                <span className="text-[10px] text-slate-400">
                  Mandatory: {block.readiness_snapshot.mandatory_pillars.join(", ")}
                </span>
              </div>
              {Object.entries(block.readiness_snapshot.pillars).map(([name, pillar]) => (
                <div key={name} className="flex items-start justify-between gap-3">
                  <span className="capitalize text-slate-400">{name.replaceAll("_", " ")}</span>
                  <span className="text-right">
                    <span className={pillar.status === "PASS" ? "text-emerald-300" : "text-amber-300"}>
                      {pillar.status}
                    </span>
                    {pillar.reasons?.length ? (
                      <span className="block text-[10px] text-slate-400">
                        {pillar.reasons.join("; ")}
                      </span>
                    ) : null}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Decision Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2">
              Official Decision
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setDecision("APPROVED")}
                className={`py-2.5 px-3 rounded-xl border flex items-center justify-center gap-2 text-xs font-bold transition ${
                  decision === "APPROVED"
                    ? "bg-emerald-950 text-emerald-300 border-emerald-600 shadow-md shadow-emerald-950/40"
                    : "bg-slate-800 text-slate-400 border-slate-700 hover:text-white"
                }`}
              >
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>APPROVE & PIN BLOCK</span>
              </button>
              <button
                type="button"
                onClick={() => setDecision("REJECTED")}
                className={`py-2.5 px-3 rounded-xl border flex items-center justify-center gap-2 text-xs font-bold transition ${
                  decision === "REJECTED"
                    ? "bg-rose-950 text-rose-300 border-rose-600 shadow-md shadow-rose-950/40"
                    : "bg-slate-800 text-slate-400 border-slate-700 hover:text-white"
                }`}
              >
                <XCircle className="w-4 h-4 text-rose-400" />
                <span>REJECT PROPOSAL</span>
              </button>
            </div>
          </div>

          {/* Approval Notes */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Controller Orders / Speed Restriction Memo
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs focus:ring-1 focus:ring-cyan-500 focus:outline-none"
              placeholder="Enter official Section Controller instructions..."
            />
          </div>

          <div className="p-3 rounded-xl bg-cyan-950/40 border border-cyan-800/50 flex items-start gap-2 text-[11px] text-cyan-300">
            <Pin className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
            <span>
              Approving this block automatically pins it in the CP-SAT engine. If unexpected traffic disruptions occur later, this block remains protected from schedule drift.
            </span>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 bg-slate-850 border-t border-slate-800 flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-750 text-slate-300 text-xs font-semibold transition"
          >
            Cancel
          </button>
          <button
            onClick={handleAction}
            disabled={loading}
            className={`px-5 py-2 rounded-lg text-xs font-bold text-white shadow-lg transition ${
              decision === "APPROVED"
                ? "bg-emerald-600 hover:bg-emerald-500 shadow-emerald-600/25"
                : "bg-rose-600 hover:bg-rose-500 shadow-rose-600/25"
            }`}
          >
            {loading ? "Recording Decision..." : `Submit ${decision} Order`}
          </button>
        </div>

      </div>
    </div>
  );
};
