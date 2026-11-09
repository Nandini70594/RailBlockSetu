import {
  User,
  DashboardMetrics,
  MaintenanceRequest,
  MaintenanceBlock,
  Resource,
  TrainSchedule,
  Disruption,
  AuditLog,
  ReadinessReport,
  NetworkTopology
} from "../types";

const API_BASE = "/api/v1";

function getHeaders(): HeadersInit {
  const token = localStorage.getItem("railblocksetu_token");
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export const api = {
  // Auth
  async login(username: string, password: string):Promise<{ access_token: string; user: User }> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Login failed");
    }
    return res.json();
  },

  async getDemoCredentials() {
    const res = await fetch(`${API_BASE}/auth/demo-credentials`);
    return res.json();
  },

  async getMe(): Promise<User> {
    const res = await fetch(`${API_BASE}/auth/me`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Unauthorized");
    return res.json();
  },

  // Dashboard
  async getMetrics(): Promise<DashboardMetrics> {
    const res = await fetch(`${API_BASE}/dashboard/metrics`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to load dashboard metrics");
    return res.json();
  },

  async getActivityFeed(): Promise<AuditLog[]> {
    const res = await fetch(`${API_BASE}/dashboard/activity-feed`, { headers: getHeaders() });
    return res.json();
  },

  async getNetworkTopology(): Promise<NetworkTopology> {
    const res = await fetch(`${API_BASE}/dashboard/network-topology`, { headers: getHeaders() });
    return res.json();
  },

  async getWeeklyTimeline(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/dashboard/weekly-timeline`, { headers: getHeaders() });
    return res.json();
  },

  // Requests
  async getRequests(department?: string, status?: string): Promise<MaintenanceRequest[]> {
    const params = new URLSearchParams();
    if (department && department !== "All") params.append("department", department);
    if (status && status !== "ALL") params.append("status", status);
    const res = await fetch(`${API_BASE}/requests?${params.toString()}`, { headers: getHeaders() });
    return res.json();
  },

  async createRequest(data: Partial<MaintenanceRequest>): Promise<MaintenanceRequest> {
    const res = await fetch(`${API_BASE}/requests`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to create request");
    }
    return res.json();
  },

  async updateRequest(id: number, data: Partial<MaintenanceRequest>): Promise<MaintenanceRequest> {
    const res = await fetch(`${API_BASE}/requests/${id}`, {
      method: "PUT",
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    return res.json();
  },

  async deleteRequest(id: number): Promise<void> {
    await fetch(`${API_BASE}/requests/${id}`, {
      method: "DELETE",
      headers: getHeaders(),
    });
  },

  async getReadinessReport(id: number): Promise<ReadinessReport> {
    const res = await fetch(`${API_BASE}/requests/${id}/readiness`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to load readiness report");
    return res.json();
  },

  // Optimization
  async runOptimization(horizonHours: number = 72, pinnedIds?: number[]) {
    const res = await fetch(`${API_BASE}/optimization/run`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ horizon_hours: horizonHours, pinned_block_ids: pinnedIds }),
    });
    return res.json();
  },

  async getBlocks(status?: string): Promise<MaintenanceBlock[]> {
    const params = new URLSearchParams();
    if (status && status !== "ALL") params.append("status", status);
    const res = await fetch(`${API_BASE}/optimization/blocks?${params.toString()}`, { headers: getHeaders() });
    return res.json();
  },

  async reviewBlock(blockId: number, status: "APPROVED" | "REJECTED", notes?: string) {
    const res = await fetch(`${API_BASE}/optimization/blocks/${blockId}/review`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ status, approval_notes: notes }),
    });
    return res.json();
  },

  async togglePinBlock(blockId: number) {
    const res = await fetch(`${API_BASE}/optimization/blocks/${blockId}/toggle-pin`, {
      method: "POST",
      headers: getHeaders(),
    });
    return res.json();
  },

  // Resources
  async getResources(department?: string, resourceType?: string): Promise<Resource[]> {
    const params = new URLSearchParams();
    if (department && department !== "All") params.append("department", department);
    if (resourceType && resourceType !== "ALL") params.append("resource_type", resourceType);
    const res = await fetch(`${API_BASE}/resources?${params.toString()}`, { headers: getHeaders() });
    return res.json();
  },

  async createResource(data: Partial<Resource>): Promise<Resource> {
    const res = await fetch(`${API_BASE}/resources`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    return res.json();
  },

  // Trains
  async getTrains(): Promise<TrainSchedule[]> {
    const res = await fetch(`${API_BASE}/trains`, { headers: getHeaders() });
    return res.json();
  },

  // Sections
  async getSections() {
    const res = await fetch(`${API_BASE}/sections`, { headers: getHeaders() });
    return res.json();
  },

  // Disruptions
  async getDisruptions(): Promise<Disruption[]> {
    const res = await fetch(`${API_BASE}/disruptions`, { headers: getHeaders() });
    return res.json();
  },

  async createDisruption(data: Partial<Disruption>): Promise<Disruption> {
    const res = await fetch(`${API_BASE}/disruptions`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    return res.json();
  },

  async triggerDisruptionReplan(disruptionId: number) {
    const res = await fetch(`${API_BASE}/disruptions/${disruptionId}/replan`, {
      method: "POST",
      headers: getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Replanning failed");
    }
    return res.json();
  },

  // Admin
  async resetDemoData() {
    const res = await fetch(`${API_BASE}/admin/reset-demo-data`, {
      method: "POST",
      headers: getHeaders(),
    });
    return res.json();
  },
};
