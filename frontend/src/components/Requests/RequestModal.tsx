import React, { useState } from "react";
import { X, Layers, Sparkles, Check, AlertCircle } from "lucide-react";
import { MaintenanceRequest } from "../../types";

interface RequestModalProps {
  initialData?: MaintenanceRequest | null;
  onSave: (data: Partial<MaintenanceRequest>) => Promise<void>;
  onClose: () => void;
}

export const RequestModal: React.FC<RequestModalProps> = ({
  initialData,
  onSave,
  onClose
}) => {
  const [formData, setFormData] = useState<Partial<MaintenanceRequest>>({
    task_title: initialData?.task_title || "",
    description: initialData?.description || "",
    department: initialData?.department || "Engineering",
    railway_division: initialData?.railway_division || "Delhi",
    railway_section: initialData?.railway_section || "NDLS-GZB",
    asset_id: initialData?.asset_id || "TRK-NDLS-GZB-KM16",
    asset_type: initialData?.asset_type || "Track",
    maintenance_type: initialData?.maintenance_type || "PREVENTIVE",
    required_start_date: initialData?.required_start_date ? initialData.required_start_date.slice(0, 16) : new Date().toISOString().slice(0, 16),
    deadline: initialData?.deadline ? initialData.deadline.slice(0, 16) : new Date(Date.now() + 86400000 * 3).toISOString().slice(0, 16),
    estimated_duration: initialData?.estimated_duration || 2.5,
    required_staff: initialData?.required_staff || 6,
    required_machinery: initialData?.required_machinery || "[\"CSM-952\"]",
    required_materials: initialData?.required_materials || "[\"PSC-60KG\"]",
    safety_requirements: initialData?.safety_requirements || "[\"Track possession memo\", \"Banner flag at 600m\"]",
    task_dependencies: initialData?.task_dependencies || "[]",
    asset_criticality: initialData?.asset_criticality || "HIGH",
    urgency_level: initialData?.urgency_level || "ROUTINE",
  });

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await onSave(formData);
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to save maintenance request");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in">
      <div className="relative w-full max-w-4xl rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        
        {/* Header */}
        <div className="px-6 py-4 bg-slate-850 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-cyan-950 text-cyan-400 border border-cyan-800">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">
                {initialData ? "Edit Railway Maintenance Request" : "New Cross-Department Maintenance Request"}
              </h2>
              <p className="text-xs text-slate-400">
                Departmental requisitions undergo ML priority assessment & CP-SAT corridor slotting.
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

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="p-3 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Section 1: Department & Core Identity */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Department <span className="text-rose-400">*</span>
              </label>
              <select
                value={formData.department}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs focus:ring-2 focus:ring-cyan-500 focus:outline-none"
              >
                <option value="Engineering">Engineering (Track & P-Way)</option>
                <option value="TRD">TRD (Traction & OHE Distribution)</option>
                <option value="S&T">S&T (Signals & Telecommunication)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Railway Division <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                value={formData.railway_division}
                onChange={(e) => setFormData({ ...formData, railway_division: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs focus:ring-2 focus:ring-cyan-500 focus:outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Railway Section Code <span className="text-rose-400">*</span>
              </label>
              <select
                value={formData.railway_section}
                onChange={(e) => setFormData({ ...formData, railway_section: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs focus:ring-2 focus:ring-cyan-500 focus:outline-none"
              >
                <option value="NDLS-GZB">NDLS-GZB (New Delhi - Ghaziabad Quad)</option>
                <option value="NZM-TKD">NZM-TKD (Nizamuddin - Tuglakabad Quad)</option>
                <option value="TKD-PWL">TKD-PWL (Tuglakabad - Palwal Semi-High)</option>
                <option value="GZB-ALJN">GZB-ALJN (Ghaziabad - Aligarh Feeder)</option>
                <option value="NDLS-PNP">NDLS-PNP (New Delhi - Panipat Gateway)</option>
              </select>
            </div>
          </div>

          {/* Section 2: Task Title & Description */}
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Task Title <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                value={formData.task_title}
                onChange={(e) => setFormData({ ...formData, task_title: e.target.value })}
                placeholder="e.g. Mechanized Tamping & Ballast Regulation (Km 18-22 UP Main)"
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs focus:ring-2 focus:ring-cyan-500 focus:outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Detailed Scope of Maintenance Work <span className="text-rose-400">*</span>
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                placeholder="Describe specific defect telemetry, speed restriction avoidance justification, and track possession parameters..."
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs focus:ring-2 focus:ring-cyan-500 focus:outline-none"
                required
              />
            </div>
          </div>

          {/* Section 3: Asset Details & Criticality */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Asset ID / Track Km <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                value={formData.asset_id}
                onChange={(e) => setFormData({ ...formData, asset_id: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs focus:ring-2 focus:ring-cyan-500 focus:outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Maintenance Type
              </label>
              <select
                value={formData.maintenance_type}
                onChange={(e) => setFormData({ ...formData, maintenance_type: e.target.value as any })}
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs focus:ring-2 focus:ring-cyan-500 focus:outline-none"
              >
                <option value="PREVENTIVE">PREVENTIVE (Cyclic)</option>
                <option value="CORRECTIVE">CORRECTIVE (Defect)</option>
                <option value="EMERGENCY">EMERGENCY (Safety Critical)</option>
                <option value="OVERHAUL">OVERHAUL (Rehabilitation)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Asset Criticality
              </label>
              <select
                value={formData.asset_criticality}
                onChange={(e) => setFormData({ ...formData, asset_criticality: e.target.value as any })}
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs focus:ring-2 focus:ring-cyan-500 focus:outline-none"
              >
                <option value="CRITICAL">CRITICAL (Main Trunk)</option>
                <option value="HIGH">HIGH (Branch Trunk)</option>
                <option value="MEDIUM">MEDIUM (Feeder Line)</option>
                <option value="LOW">LOW (Yard Siding)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Urgency Level
              </label>
              <select
                value={formData.urgency_level}
                onChange={(e) => setFormData({ ...formData, urgency_level: e.target.value as any })}
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs focus:ring-2 focus:ring-cyan-500 focus:outline-none"
              >
                <option value="EMERGENCY">EMERGENCY (Immediate)</option>
                <option value="URGENT">URGENT (&lt; 48 hours)</option>
                <option value="ROUTINE">ROUTINE (Standard)</option>
              </select>
            </div>
          </div>

          {/* Section 4: Timings & Duration */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Required Earliest Start
              </label>
              <input
                type="datetime-local"
                value={formData.required_start_date}
                onChange={(e) => setFormData({ ...formData, required_start_date: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs focus:ring-2 focus:ring-cyan-500 focus:outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Hard Execution Deadline
              </label>
              <input
                type="datetime-local"
                value={formData.deadline}
                onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs focus:ring-2 focus:ring-cyan-500 focus:outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Estimated Duration (Hours)
              </label>
              <input
                type="number"
                step="0.5"
                min="0.5"
                max="12"
                value={formData.estimated_duration}
                onChange={(e) => setFormData({ ...formData, estimated_duration: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs focus:ring-2 focus:ring-cyan-500 focus:outline-none"
                required
              />
            </div>
          </div>

          {/* Section 5: Resource Requisitions */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Required Gang Personnel (Staff Count)
              </label>
              <input
                type="number"
                min="1"
                max="50"
                value={formData.required_staff}
                onChange={(e) => setFormData({ ...formData, required_staff: parseInt(e.target.value) })}
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs focus:ring-2 focus:ring-cyan-500 focus:outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Required Machinery (JSON or code)
              </label>
              <input
                type="text"
                value={formData.required_machinery}
                onChange={(e) => setFormData({ ...formData, required_machinery: e.target.value })}
                placeholder='["CSM-952", "BCM-12", "TW-04"]'
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs font-mono focus:ring-2 focus:ring-cyan-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Required Materials (JSON or code)
              </label>
              <input
                type="text"
                value={formData.required_materials}
                onChange={(e) => setFormData({ ...formData, required_materials: e.target.value })}
                placeholder='["PSC-60KG", "CW-107", "PM-SIEMENS"]'
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs font-mono focus:ring-2 focus:ring-cyan-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Section 6: Safety Requirements & Task Dependencies */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Safety & Isolation Protocols (JSON list)
              </label>
              <input
                type="text"
                value={formData.safety_requirements}
                onChange={(e) => setFormData({ ...formData, safety_requirements: e.target.value })}
                placeholder='["Track possession memo", "25kV Power Block"]'
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs font-mono focus:ring-2 focus:ring-cyan-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Task Dependencies (e.g. ["1", "2"])
              </label>
              <input
                type="text"
                value={formData.task_dependencies}
                onChange={(e) => setFormData({ ...formData, task_dependencies: e.target.value })}
                placeholder='["REQ-ENG-2026-001"]'
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs font-mono focus:ring-2 focus:ring-cyan-500 focus:outline-none"
              />
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-850 border border-slate-800 flex items-center gap-2 text-xs text-slate-400">
            <Sparkles className="w-4 h-4 text-cyan-400 flex-shrink-0" />
            <span>
              Upon submission, the Scikit-Learn ML Model will evaluate criticality, traffic density, and degradation to synthesize an explainable Priority Score.
            </span>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-750 text-slate-300 text-xs font-semibold transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-2 px-5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold shadow-lg shadow-cyan-600/25 transition disabled:opacity-50"
            >
              <Check className="w-4 h-4" />
              <span>{saving ? "Evaluating & Submitting..." : initialData ? "Save Changes" : "Submit Maintenance Requisition"}</span>
            </button>
          </div>
        </form>

      </div>
    </div>
  );
};
