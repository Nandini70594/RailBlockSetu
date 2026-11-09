import React, { useState, useEffect } from "react";
import { Train, Clock, ArrowRight, ShieldCheck, AlertCircle } from "lucide-react";
import { TrainSchedule } from "../../types";
import { api } from "../../api/client";

export const TrainsView: React.FC = () => {
  const [trains, setTrains] = useState<TrainSchedule[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getTrains()
      .then((data) => setTrains(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const getPriorityColor = (p: number) => {
    switch (p) {
      case 1:
        return "bg-rose-950 text-rose-300 border-rose-800";
      case 2:
        return "bg-amber-950 text-amber-300 border-amber-800";
      default:
        return "bg-slate-800 text-slate-300 border-slate-700";
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <Train className="w-5 h-5 text-cyan-400" />
          <span>Train Operations & Corridor Timetables</span>
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          High-priority passenger & freight paths mapped for traffic window gap analysis and caution order mitigation.
        </p>
      </div>

      {/* Info Card */}
      <div className="p-4 rounded-xl bg-cyan-950/30 border border-cyan-800/40 text-xs text-slate-300 flex items-start gap-3">
        <ShieldCheck className="w-4 h-4 text-cyan-400 mt-0.5 flex-shrink-0" />
        <span>
          <strong className="text-cyan-300">CP-SAT Corridor Headway Guarantee:</strong> Maintenance blocks scheduled on main running lines (UP/DOWN) enforce strict headway clearance buffers around Priority 1 Vande Bharat and Rajdhani express trains to prevent transit delays.
        </span>
      </div>

      {/* Trains Table */}
      <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden shadow-xl">
        {loading ? (
          <div className="py-16 text-center text-slate-400 text-xs flex flex-col items-center gap-2">
            <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
            <span>Fetching train operations database...</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-850/60 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  <th className="py-3.5 px-4">Train Number</th>
                  <th className="py-3.5 px-4">Train Name & Route</th>
                  <th className="py-3.5 px-4">Category</th>
                  <th className="py-3.5 px-4">Corridor Section</th>
                  <th className="py-3.5 px-4">Section Window</th>
                  <th className="py-3.5 px-4">Priority Ranking</th>
                  <th className="py-3.5 px-4">Live Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {trains.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-850/50 transition">
                    <td className="py-3.5 px-4 font-mono font-bold text-cyan-400">
                      {t.train_number}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-white">{t.train_name}</div>
                      <div className="flex items-center gap-1.5 text-[11px] text-slate-400 mt-0.5">
                        <span>{t.origin}</span>
                        <ArrowRight className="w-3 h-3 text-slate-500" />
                        <span>{t.destination}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium">
                        {t.train_type.replace("_", " ")}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-cyan-300">
                      {t.section_code}
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap font-mono text-slate-200">
                      {t.entry_time} - {t.exit_time}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`px-2 py-0.5 rounded font-bold border ${getPriorityColor(t.priority_level)}`}>
                        Priority {t.priority_level}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-bold uppercase text-[10px]">
                        {t.current_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
};
