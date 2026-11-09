import React, { useState, useEffect } from "react";
import { AuthProvider } from "./context/AuthContext";
import { ToastProvider } from "./components/Shared/ToastContext";
import { Sidebar } from "./components/Navigation/Sidebar";
import { Header } from "./components/Navigation/Header";
import { CommandCenter } from "./components/Dashboard/CommandCenter";
import { MaintenanceRequestsView } from "./components/Requests/MaintenanceRequestsView";
import { OptimizationView } from "./components/Optimization/OptimizationView";
import { OptimizationWorkflowModal } from "./components/Optimization/OptimizationWorkflowModal";
import { WeeklyGanttTimeline } from "./components/Dashboard/WeeklyGanttTimeline";
import { TrainsView } from "./components/Trains/TrainsView";
import { ResourcesView } from "./components/Resources/ResourcesView";
import { DisruptionsView } from "./components/Disruptions/DisruptionsView";
import { NetworkTopologyView } from "./components/Dashboard/NetworkTopologyView";
import { AdminView } from "./components/Admin/AdminView";
import { DashboardMetrics, AuditLog } from "./types";
import { api } from "./api/client";
import { motion, AnimatePresence, Variants } from "framer-motion";

function AppContent() {
  const [activeTab, setActiveTab] = useState<string>("dashboard");
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [activityLogs, setActivityLogs] = useState<AuditLog[]>([]);
  const [showOptimizationWorkflow, setShowOptimizationWorkflow] = useState(false);

  const refreshDashboardData = () => {
    api
      .getMetrics()
      .then(setMetrics)
      .catch((err) => console.error("Metrics load err", err));
    api
      .getActivityFeed()
      .then(setActivityLogs)
      .catch((err) => console.error("Logs load err", err));
  };

  useEffect(() => {
    refreshDashboardData();
    const interval = setInterval(refreshDashboardData, 15000);
    return () => clearInterval(interval);
  }, []);

  // Derive badge counts from metrics
  const pendingCount = metrics?.pending_requests ?? 0;
  const disruptionCount = metrics?.upcoming_disruptions ?? 0;

  // Sidebar width classes
  const sidebarWidth = sidebarCollapsed ? "w-20" : "w-64";
  const mainMargin = sidebarCollapsed ? "ml-20" : "ml-64";

  const pageVariants: Variants = {
    initial: { opacity: 0, y: 12 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.22, ease: "easeOut" } },
    exit: { opacity: 0, y: -8, transition: { duration: 0.15 } },
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 font-sans flex">
      {/* Sidebar — fixed position */}
      <div
        className={`fixed left-0 top-0 h-full z-40 ${sidebarWidth} transition-all duration-300 ease-in-out`}
      >
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          collapsed={sidebarCollapsed}
          setCollapsed={setSidebarCollapsed}
          pendingCount={pendingCount}
          disruptionCount={disruptionCount}
        />
      </div>

      {/* Main content area */}
      <div className={`flex-1 flex flex-col min-h-screen ${mainMargin} transition-all duration-300 ease-in-out`}>
        {/* Fixed top header */}
        <div className="fixed top-0 right-0 z-30 bg-white/95 backdrop-blur-sm border-b border-slate-200/80 shadow-sm"
          style={{ left: sidebarCollapsed ? "5rem" : "16rem", transition: "left 0.3s ease" }}
        >
          <Header
            collapsed={sidebarCollapsed}
            onRefreshAll={refreshDashboardData}
            onOpenOptimizationWorkflow={() => setShowOptimizationWorkflow(true)}
            activeDisruptionCount={disruptionCount}
          />
        </div>

        {/* Page content — padded below header */}
        <main className="flex-1 pt-16 min-h-0">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              className="h-full"
            >
              {activeTab === "dashboard" && (
                <CommandCenter
                  metrics={metrics}
                  activityLogs={activityLogs}
                  onNavigate={setActiveTab}
                  onOpenOptimizationWorkflow={() => setShowOptimizationWorkflow(true)}
                />
              )}
              {activeTab === "requests" && <MaintenanceRequestsView />}
              {activeTab === "optimization" && <OptimizationView />}
              {activeTab === "timeline" && <WeeklyGanttTimeline />}
              {activeTab === "trains" && <TrainsView />}
              {activeTab === "resources" && <ResourcesView />}
              {activeTab === "disruptions" && <DisruptionsView />}
              {activeTab === "topology" && <NetworkTopologyView />}
              {activeTab === "admin" && <AdminView />}
            </motion.div>
          </AnimatePresence>
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-200 bg-white/80 py-3 mt-auto">
          <div className="max-w-full px-6 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded bg-[#0f172a] flex items-center justify-center">
                <span className="text-white text-[8px] font-bold">RB</span>
              </div>
              <span className="font-semibold text-slate-600">RailBlockSetu</span>
              <span className="text-slate-300">•</span>
              <span>NOVEX 2026 Hackathon — AI / Smart Infrastructure</span>
            </div>
            <div className="text-[11px] text-slate-400">
              Decision-Support Platform · Indian Railways, Delhi Division · Officials Retain Full Approval Authority
            </div>
          </div>
        </footer>
      </div>

      {/* Optimization Workflow Modal — rendered at app root so it overlays everything */}
      <OptimizationWorkflowModal
        isOpen={showOptimizationWorkflow}
        onClose={() => setShowOptimizationWorkflow(false)}
        onComplete={() => {
          setShowOptimizationWorkflow(false);
          setActiveTab("optimization");
          refreshDashboardData();
        }}
      />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <AppContent />
      </ToastProvider>
    </AuthProvider>
  );
}
