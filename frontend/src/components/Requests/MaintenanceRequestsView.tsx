import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Layers,
  Plus,
  Search,
  Filter,
  Sparkles,
  ShieldCheck,
  Edit2,
  Trash2,
  Clock,
  Wrench,
  Zap,
  Radio,
  Gauge,
  CheckCircle2,
  AlertTriangle,
  Flame,
  ArrowRight
} from "lucide-react";
import { MaintenanceRequest } from "../../types";
import { api } from "../../api/client";
import { RequestModal } from "./RequestModal";
import { ReadinessAuditModal } from "./ReadinessAuditModal";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../Shared/ToastContext";

export const MaintenanceRequestsView: React.FC = () => {
  const { isDepartmentOfficer } = useAuth();
  const { showToast } = useToast();
  const [requests, setRequests] = useState<MaintenanceRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeDept, setActiveDept] = useState("All");
  const [activeStatus, setActiveStatus] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  
  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingRequest, setEditingRequest] = useState<MaintenanceRequest | null>(null);
  const [auditTarget, setAuditTarget] = useState<MaintenanceRequest | null>(null);

  const fetchRequests = async () => {
    setLoading(true);
    try {
      const data = await api.getRequests(activeDept, activeStatus);
      setRequests(data);
    } catch (err) {
      console.error("Failed to load requests", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, [activeDept, activeStatus]);

  const handleSaveRequest = async (formData: Partial<MaintenanceRequest>) => {
    if (editingRequest) {
      await api.updateRequest(editingRequest.id, formData);
      showToast("success", "Request Updated", "Changes saved successfully.");
    } else {
      await api.createRequest(formData);
      showToast("success", "Requisition Submitted", "ML priority score evaluated.");
    }
    fetchRequests();
  };

  const handleDeleteRequest = async (id: number) => {
    if (confirm("Are you sure you want to delete this maintenance request?")) {
      await api.deleteRequest(id);
      showToast("info", "Request Deleted", "Requisition removed from queue.");
      fetchRequests();
    }
  };

  const filteredRequests = requests.filter((r) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      r.task_title.toLowerCase().includes(query) ||
      r.request_id.toLowerCase().includes(query) ||
      r.railway_section.toLowerCase().includes(query) ||
      r.asset_id.toLowerCase().includes(query)
    );
  });

  const getDeptBadge = (dept: string) => {
    switch (dept) {
      case "Engineering":
        return { icon: Wrench, color: "text-blue-700 bg-blue-50 border-blue-200" };
      case "TRD":
        return { icon: Zap, color: "text-amber-700 bg-amber-50 border-amber-200" };
      case "S&T":
        return { icon: Radio, color: "text-emerald-700 bg-emerald-50 border-emerald-200" };
      default:
        return { icon: Layers, color: "text-slate-700 bg-slate-100 border-slate-200" };
    }
  };

  const getPriorityBadge = (score: number) => {
    if (score >= 85) return "text-rose-800 bg-rose-50 border-rose-200 font-bold";
    if (score >= 70) return "text-amber-800 bg-amber-50 border-amber-200 font-bold";
    if (score >= 50) return "text-blue-800 bg-blue-50 border-blue-200 font-bold";
    return "text-slate-700 bg-slate-100 border-slate-200";
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "APPROVED":
        return "text-emerald-800 bg-emerald-50 border-emerald-200";
      case "OPTIMIZED":
        return "text-blue-800 bg-blue-50 border-blue-200";
      case "SUBMITTED":
        return "text-amber-800 bg-amber-50 border-amber-200";
      case "REJECTED":
        return "text-rose-800 bg-rose-50 border-rose-200";
      default:
        return "text-slate-700 bg-slate-100 border-slate-200";
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Layers className="w-5 h-5 text-blue-600" />
            <span>Multi-Department Maintenance Requisitions</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Cross-department pipeline: Engineering (P-Way), TRD (25kV OHE), and S&T (Signals & ATP).
          </p>
        </div>

        {isDepartmentOfficer && (
          <button
            onClick={() => {
              setEditingRequest(null);
              setShowCreateModal(true);
            }}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md shadow-blue-500/20 transition active:scale-95"
          >
            <Plus className="w-4 h-4" />
            <span>New Maintenance Requisition</span>
          </button>
        )}
      </div>

      {/* Filter Ribbon */}
      <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
        
        {/* Department Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto">
          {["All", "Engineering", "TRD", "S&T"].map((dept) => (
            <button
              key={dept}
              onClick={() => setActiveDept(dept)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition ${
                activeDept === dept
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              }`}
            >
              {dept === "All" ? "All Departments" : dept}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative w-full md:w-72">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search request, corridor, or asset..."
            className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-slate-50 border border-slate-300 text-slate-900 text-xs placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

      </div>

      {/* Table Container */}
      <div className="rounded-2xl bg-white border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-slate-400 text-xs flex flex-col items-center gap-2">
            <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            <span>Loading department requisitions...</span>
          </div>
        ) : filteredRequests.length === 0 ? (
          <div className="py-16 text-center text-slate-500 text-xs">
            No maintenance requests matching current criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                  <th className="py-3.5 px-4">Request Code</th>
                  <th className="py-3.5 px-4">Task & Corridor Section</th>
                  <th className="py-3.5 px-4">Department</th>
                  <th className="py-3.5 px-4">Duration</th>
                  <th className="py-3.5 px-4">ML Priority Score</th>
                  <th className="py-3.5 px-4">Readiness Audit</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredRequests.map((req) => {
                  const deptStyle = getDeptBadge(req.department);
                  const DeptIcon = deptStyle.icon;
                  return (
                    <tr key={req.id} className="hover:bg-slate-50/70 transition">
                      
                      {/* Code */}
                      <td className="py-3.5 px-4 font-mono font-bold text-blue-700 whitespace-nowrap">
                        {req.request_id}
                      </td>

                      {/* Title & Section */}
                      <td className="py-3.5 px-4 max-w-sm">
                        <div className="font-bold text-slate-900 truncate">{req.task_title}</div>
                        <div className="flex items-center gap-2 text-[11px] text-slate-500 mt-0.5">
                          <span className="font-mono text-blue-700 font-semibold">{req.railway_section}</span>
                          <span>•</span>
                          <span>Asset: {req.asset_id}</span>
                          <span>•</span>
                          <span>{req.maintenance_type}</span>
                        </div>
                      </td>

                      {/* Department */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-semibold border ${deptStyle.color}`}>
                          <DeptIcon className="w-3 h-3" />
                          <span>{req.department}</span>
                        </div>
                      </td>

                      {/* Duration */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <div className="flex items-center gap-1.5 text-slate-700 font-medium">
                          <Clock className="w-3.5 h-3.5 text-slate-400" />
                          <span>{req.estimated_duration} hrs</span>
                        </div>
                      </td>

                      {/* AI Priority */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded text-[11px] font-mono border ${getPriorityBadge(req.ai_priority_score)}`}>
                            {req.ai_priority_score}
                          </span>
                          <span className="text-[10px] text-slate-500 font-bold uppercase">
                            {req.ai_risk_factor}
                          </span>
                        </div>
                      </td>

                      {/* Readiness Audit Button */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <button
                          onClick={() => setAuditTarget(req)}
                          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-blue-50 hover:text-blue-700 border border-slate-200 text-slate-700 text-[11px] font-semibold transition"
                        >
                          <Gauge className="w-3.5 h-3.5 text-blue-600" />
                          <span>Audit 5 Pillars</span>
                        </button>
                      </td>

                      {/* Status */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wider ${getStatusBadge(req.current_status)}`}>
                          {req.current_status}
                        </span>
                      </td>

                      {/* Actions */}
                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1.5">
                          {isDepartmentOfficer && (
                            <>
                              <button
                                onClick={() => {
                                  setEditingRequest(req);
                                  setShowCreateModal(true);
                                }}
                                title="Edit Request"
                                className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition"
                              >
                                <Edit2 className="w-3.5 h-3.5" />
                              </button>
                              <button
                                onClick={() => handleDeleteRequest(req.id)}
                                title="Delete Request"
                                className="p-1.5 rounded-lg bg-slate-100 hover:bg-rose-50 text-slate-500 hover:text-rose-600 transition"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </>
                          )}
                        </div>
                      </td>

                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modals */}
      {showCreateModal && (
        <RequestModal
          initialData={editingRequest}
          onSave={handleSaveRequest}
          onClose={() => {
            setShowCreateModal(false);
            setEditingRequest(null);
          }}
        />
      )}

      {auditTarget && (
        <ReadinessAuditModal
          requestId={auditTarget.id}
          taskTitle={auditTarget.task_title}
          onClose={() => setAuditTarget(null)}
        />
      )}

    </div>
  );
};
