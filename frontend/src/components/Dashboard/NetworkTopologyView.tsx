import React, { useEffect, useState } from "react";
import { Shield, Train, Zap, Radio, CheckCircle2, ArrowRight } from "lucide-react";
import { NetworkTopology } from "../../types";
import { api } from "../../api/client";

export const NetworkTopologyView: React.FC = () => {
  const [topology, setTopology] = useState<NetworkTopology | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<string | null>("NDLS");

  useEffect(() => {
    api.getNetworkTopology()
      .then((data) => setTopology(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <Shield className="w-5 h-5 text-cyan-400" />
          <span>NetworkX Delhi Division Corridor Topology & Routing Graph</span>
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Mathematical graph representation of track corridors, junction interconnections, and detour route calculations.
        </p>
      </div>

      {/* Interactive Topology Visual Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Graph Visual Canvas */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl relative min-h-[420px] flex flex-col justify-between overflow-hidden">
          <div className="flex items-center justify-between z-10">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              Delhi Division Network Corridors
            </span>
            <span className="text-[11px] text-slate-400 font-mono">
              ABS • KAVACH ATP • 25kV AC OHE
            </span>
          </div>

          {loading ? (
            <div className="py-24 text-center text-slate-400 text-xs flex flex-col items-center gap-2">
              <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
              <span>Synthesizing NetworkX corridor graph...</span>
            </div>
          ) : (
            <div className="py-8 grid grid-cols-2 sm:grid-cols-3 gap-3.5 my-auto">
              {topology?.nodes.map((node) => {
                const isSelected = selectedNode === node.id;
                return (
                  <div
                    key={node.id}
                    onClick={() => setSelectedNode(node.id)}
                    className={`cursor-pointer p-4 rounded-xl border transition-all duration-200 ${
                      isSelected
                        ? "bg-cyan-950/70 border-cyan-500 shadow-lg shadow-cyan-950 text-white"
                        : "bg-slate-850/70 border-slate-750 hover:border-slate-600 text-slate-300"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-base font-extrabold font-mono text-cyan-400">
                        {node.id}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                        {node.type}
                      </span>
                    </div>
                    <div className="text-xs font-semibold text-slate-200 mt-1 truncate">
                      {node.label}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <div className="z-10 pt-3 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-400 font-mono">
            <span>Vertices: {topology?.nodes.length || 0} Junctions</span>
            <span>•</span>
            <span>Edges: {topology?.edges.length || 0} Track Corridors</span>
            <span>•</span>
            <span className="text-emerald-400">Max Speed: 160 km/h</span>
          </div>
        </div>

        {/* Section Links & Specifications */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl space-y-4">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            Connected Corridors (NetworkX Edges)
          </h3>

          <div className="space-y-2.5 max-h-[340px] overflow-y-auto pr-1">
            {topology?.edges.map((e, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl bg-slate-850 border border-slate-800 space-y-1 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-cyan-300">{e.section_code}</span>
                  <span className="text-slate-400 font-mono text-[11px]">{e.distance_km} km</span>
                </div>
                <div className="flex items-center gap-2 text-[11px] text-slate-400">
                  <span>{e.source}</span>
                  <ArrowRight className="w-3 h-3 text-slate-600" />
                  <span>{e.target}</span>
                  <span>•</span>
                  <span className="text-slate-300">{e.tracks} Tracks</span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

    </div>
  );
};
