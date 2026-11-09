import React, { useState, useEffect } from "react";
import {
  Calendar,
  Clock,
  Pin,
  Zap,
  Radio,
  Train,
  Wrench,
  Layers,
  ChevronRight,
  Info,
  CheckCircle2,
  AlertTriangle,
  X,
  Filter
} from "lucide-react";
import { api } from "../../api/client";
import { Tooltip } from "../Shared/Tooltip";

export const WeeklyGanttTimeline: React.FC = () => {
  const [items, setItems] = useState<any[]>([]);
  const [trains, setTrains] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedBlock, setSelectedBlock] = useState<any | null>(null);
  const [selectedDept, setSelectedDept] = useState("All");
  const [selectedTrack, setSelectedTrack] = useState("ALL");

  useEffect(() => {
    Promise.all([api.getWeeklyTimeline(), api.getTrains()])
      .then(([timelineData, trainData]) => {
        setItems(timelineData);
        setTrains(trainData);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const sections = [
    { code: "NDLS-GZB", name: "New Delhi to Ghaziabad Quad Line", tracks: ["UP_LINE", "DOWN_LINE"] },
    { code: "NZM-TKD", name: "Nizamuddin to Tuglakabad Freight & Main", tracks: ["UP_LINE", "DOWN_LINE"] },
    { code: "TKD-PWL", name: "Tuglakabad to Palwal Semi-High Speed (160 km/h)", tracks: ["UP_LINE", "DOWN_LINE"] },
    { code: "GZB-ALJN", name: "Ghaziabad to Aligarh Double Line", tracks: ["UP_LINE", "DOWN_LINE"] },
    { code: "NDLS-PNP", name: "New Delhi to Panipat Northern Gateway", tracks: ["UP_LINE", "DOWN_LINE"] },
  ];

  const getDeptColor = (dept: string) => {
    switch (dept) {
      case "Engineering":
        return "bg-blue-600 border-blue-700 text-white shadow-blue-500/20";
      case "TRD":
        return "bg-amber-600 border-amber-700 text-white shadow-amber-500/20";
      case "S&T":
        return "bg-emerald-600 border-emerald-700 text-white shadow-emerald-500/20";
      default:
        return "bg-slate-700 border-slate-800 text-white";
    }
  };

  const filteredBlocks = items.filter((b) => {
    if (selectedDept !== "All" && b.department !== selectedDept) return false;
    if (selectedTrack !== "ALL" && b.track_type !== selectedTrack) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <Calendar className="w-5 h-5 text-blue-600" />
              <span>Interactive Corridor Block Scheduling Timeline</span>
            </h2>
            <Tooltip content="Visual scheduling map aligning multi-department track blocks with train movements to avoid traffic congestion." />
          </div>
          <p className="text-xs text-slate-500">
            Real-time projection of maintenance windows, scheduled blocks, train headway intervals, and track possession boundaries.
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Department Filter */}
          <div className="flex items-center gap-1 bg-white p-1 rounded-xl border border-slate-200 shadow-sm text-xs">
            {["All", "Engineering", "TRD", "S&T"].map((d) => (
              <button
                key={d}
                onClick={() => setSelectedDept(d)}
                className={`px-2.5 py-1 rounded-lg font-semibold transition ${
                  selectedDept === d
                    ? "bg-blue-600 text-white shadow-sm"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {d}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Legend & Telemetry Indicators */}
      <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-4 text-xs">
        <div className="flex flex-wrap items-center gap-4 text-slate-700 font-medium">
          <span className="text-slate-400 font-bold uppercase text-[10px] tracking-wider">Legend:</span>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-blue-600 inline-block" />
            <span>Engineering (Track)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-amber-600 inline-block" />
            <span>TRD (25kV OHE)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-emerald-600 inline-block" />
            <span>S&T (Signaling)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-slate-800 inline-block" />
            <span>Train Movement Slot</span>
          </div>
          <div className="flex items-center gap-1.5 text-purple-700">
            <Pin className="w-3 h-3 fill-purple-600" />
            <span>Pinned Block</span>
          </div>
        </div>

        <div className="text-[11px] text-slate-500 font-mono">
          Showing {filteredBlocks.length} maintenance blocks • Click to inspect
        </div>
      </div>

      {/* Timeline Schedule Canvas */}
      <div className="rounded-2xl bg-white border border-slate-200 shadow-sm overflow-hidden">
        
        {/* Hours Ribbon (00:00 to 24:00) */}
        <div className="grid grid-cols-12 bg-slate-50 border-b border-slate-200 text-center py-2 text-[11px] font-mono text-slate-500 font-semibold">
          {["00:00", "02:00", "04:00", "06:00", "08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00", "22:00"].map((h) => (
            <div key={h} className="border-r border-slate-200 last:border-r-0">
              {h}
            </div>
          ))}
        </div>

        {/* Corridor Tracks Lanes */}
        <div className="divide-y divide-slate-100">
          {sections.map((sec) => {
            const sectionBlocks = filteredBlocks.filter((b) => b.section_code === sec.code);
            const sectionTrains = trains.filter((t) => t.section_code === sec.code);

            return (
              <div key={sec.code} className="p-4 hover:bg-slate-50/50 transition">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-xs text-blue-700 px-2 py-0.5 rounded bg-blue-50 border border-blue-200">
                      {sec.code}
                    </span>
                    <span className="text-xs font-semibold text-slate-900">{sec.name}</span>
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono">
                    {sectionBlocks.length} blocks allocated
                  </span>
                </div>

                {/* Multi-track Lane */}
                <div className="relative min-h-[64px] bg-slate-50 rounded-xl border border-slate-200 p-2 overflow-hidden flex flex-col justify-center gap-2">
                  
                  {/* Train Slots Bar */}
                  {sectionTrains.length > 0 && (
                    <div className="flex items-center gap-2 overflow-x-auto pb-1">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex-shrink-0">
                        Trains:
                      </span>
                      {sectionTrains.map((tr) => (
                        <div
                          key={tr.id}
                          className="px-2 py-0.5 rounded bg-slate-800 text-white text-[10px] font-mono flex items-center gap-1.5 flex-shrink-0 shadow-sm"
                        >
                          <Train className="w-3 h-3 text-cyan-400" />
                          <span>{tr.train_name}</span>
                          <span className="text-slate-400">({tr.entry_time}-{tr.exit_time})</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Scheduled Maintenance Blocks */}
                  <div className="flex flex-wrap items-center gap-2">
                    {sectionBlocks.length === 0 ? (
                      <span className="text-[11px] text-slate-400 italic">
                        Corridor clear — available for planned night shadow possession.
                      </span>
                    ) : (
                      sectionBlocks.map((b) => (
                        <div
                          key={b.block_id}
                          onClick={() => setSelectedBlock(b)}
                          className={`cursor-pointer px-3 py-1.5 rounded-lg border text-xs font-medium shadow-sm transition transform hover:scale-[1.02] flex items-center gap-2 ${getDeptColor(
                            b.department
                          )}`}
                        >
                          {b.is_pinned && <Pin className="w-3 h-3 fill-white" />}
                          <span className="font-bold">{b.block_code}:</span>
                          <span className="truncate max-w-[200px]">{b.task_title}</span>
                          <span className="text-[11px] opacity-90 font-mono">
                            ({b.duration_hours}h)
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Block Detail Inspector Modal */}
      {selectedBlock && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-sm animate-in fade-in">
          <div className="relative w-full max-w-lg rounded-2xl bg-white border border-slate-200 shadow-2xl p-6 space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[11px] font-bold font-mono text-blue-700 px-2 py-0.5 rounded bg-blue-50 border border-blue-200">
                  {selectedBlock.block_code}
                </span>
                <h3 className="text-sm font-bold text-slate-900 mt-1">
                  {selectedBlock.task_title}
                </h3>
                <p className="text-xs text-slate-500">
                  Corridor: {selectedBlock.section_code} • {selectedBlock.department}
                </p>
              </div>
              <button
                onClick={() => setSelectedBlock(null)}
                className="text-slate-400 hover:text-slate-600 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-500">Scheduled Window:</span>
                <span className="font-mono font-semibold text-slate-900">
                  {new Date(selectedBlock.start).toLocaleString()} to {new Date(selectedBlock.end).toLocaleTimeString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Duration:</span>
                <span className="font-bold text-blue-700">{selectedBlock.duration_hours} hours</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Track Possession:</span>
                <span className="font-semibold text-slate-800">{selectedBlock.track_type.replace("_", " ")}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Power Block (25kV OHE):</span>
                <span className={selectedBlock.power_block ? "text-amber-700 font-bold" : "text-slate-400"}>
                  {selectedBlock.power_block ? "Required (OHE Permit Issued)" : "Not Required"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Signal Disconnection (S&T):</span>
                <span className={selectedBlock.signal_disconnection ? "text-emerald-700 font-bold" : "text-slate-400"}>
                  {selectedBlock.signal_disconnection ? "Required (Notice T-351 Signed)" : "Not Required"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Pin Protection:</span>
                <span className={selectedBlock.is_pinned ? "text-purple-700 font-bold flex items-center gap-1" : "text-slate-400"}>
                  {selectedBlock.is_pinned ? "PINNED (Protected from replanning drift)" : "FLEXIBLE"}
                </span>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedBlock(null)}
                className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold transition"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
