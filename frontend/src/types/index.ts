export type UserRole = "ADMIN" | "DEPARTMENT_OFFICER" | "OPERATIONS_OFFICER";
export type DepartmentType = "Engineering" | "TRD" | "S&T" | "Operations" | "All";

export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
  role: UserRole;
  department: DepartmentType;
  is_active: boolean;
  created_at: string;
}

export type MaintenanceType = "PREVENTIVE" | "CORRECTIVE" | "EMERGENCY" | "OVERHAUL";
export type AssetCriticality = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
export type UrgencyLevel = "EMERGENCY" | "URGENT" | "ROUTINE";
export type RequestStatus = "DRAFT" | "SUBMITTED" | "VALIDATED" | "OPTIMIZED" | "APPROVED" | "IN_PROGRESS" | "COMPLETED" | "REJECTED";

export interface MaintenanceRequest {
  id: number;
  request_id: string;
  task_title: string;
  description: string;
  department: string;
  railway_division: string;
  railway_section: string;
  section_id?: number;
  asset_id: string;
  asset_type: string;
  maintenance_type: MaintenanceType;
  required_start_date: string;
  deadline: string;
  estimated_duration: number;
  required_staff: number;
  required_machinery?: string;
  required_materials?: string;
  safety_requirements?: string;
  obtained_safety_requirements?: string;
  task_dependencies?: string;
  asset_criticality: AssetCriticality;
  urgency_level: UrgencyLevel;
  current_status: RequestStatus;
  ai_priority_score: number;
  ai_risk_factor: string;
  ai_explanation?: string;
  readiness_score?: number;
  created_at: string;
  updated_at: string;
}

export type BlockStatus = "PROPOSED" | "APPROVED" | "REJECTED" | "IN_PROGRESS" | "COMPLETED" | "CANCELLED";
export type TrackType = "UP_LINE" | "DOWN_LINE" | "BOTH_LINES" | "YARD";

export interface MaintenanceBlock {
  id: number;
  block_code: string;
  request_id: number;
  section_id: number;
  work_package_id?: number | null;
  scheduled_start: string;
  scheduled_end: string;
  duration_hours: number;
  track_type: TrackType;
  power_block_required: boolean;
  signal_disconnection_required: boolean;
  status: BlockStatus;
  is_pinned: boolean;
  or_tools_score: number;
  approval_notes?: string;
  task_title?: string;
  department?: string;
  section_code?: string;
  readiness_verdict?: "READY" | "PARTIALLY_READY" | "NOT_READY";
  readiness_snapshot?: ReadinessReport | null;
}

export interface WorkPackage {
  id: number;
  section_id: number;
  section_code: string | null;
  departments: string[];
  included_task_ids: number[];
  shared_window_start: string;
  shared_window_end: string;
  expected_utilization: number;
  compatibility_status: string;
  compatibility_reasons: string[];
  tasks: { id: number; title: string }[];
}

export interface Resource {
  id: number;
  resource_type: "MACHINERY" | "STAFF" | "MATERIAL";
  name: string;
  code: string;
  department: string;
  total_quantity: number;
  available_quantity: number;
  allocated_quantity: number;
  unit: string;
  specifications?: string;
  base_station: string;
  operational_status: string;
  created_at: string;
}

export interface TrainSchedule {
  id: number;
  train_number: string;
  train_name: string;
  train_type: string;
  origin: string;
  destination: string;
  priority_level: number;
  section_id: number;
  section_code: string;
  entry_time: string;
  exit_time: string;
  typical_delay_minutes: number;
  current_status: string;
}

export interface Disruption {
  id: number;
  disruption_code: string;
  title: string;
  disruption_type: string;
  section_id: number;
  affected_from: string;
  affected_until: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  impact_description: string;
  is_active: boolean;
  replan_triggered: boolean;
  replanned_at?: string;
  affected_blocks_count: number;
  preserved_blocks_count: number;
  schedule_snapshot?: string | null;
  replan_diff?: string | null;
  created_at: string;
}

export interface ReplanDiff {
  retained: {
    task_id: number;
    task_title: string | null;
    block_id: number;
    start: string;
    end: string;
    status: string;
  }[];
  rescheduled: {
    task_id: number;
    task_title: string | null;
    block_id: number;
    old_start: string;
    new_start: string;
    old_end: string;
    new_end: string;
    delta_minutes: number;
    status: string;
  }[];
  newly_assigned: {
    task_id: number;
    task_title: string | null;
    block_id: number;
    new_start: string;
    new_end: string;
    status: string;
  }[];
  unschedulable: {
    task_id: number;
    task_title: string | null;
    reason: string;
  }[];
  resource_changes: {
    task_id: number;
    old_resources: Record<string, unknown>;
    new_resources: Record<string, unknown>;
  }[];
  summary: {
    retained_count: number;
    rescheduled_count: number;
    newly_assigned_count: number;
    unschedulable_count: number;
    resource_change_count: number;
    total_movement_minutes: number;
  };
}

export interface ReplanSnapshotItem {
  task_id: number;
  task_code: string | null;
  task_title: string | null;
  block_id: number;
  start: string;
  end: string;
  section_id: number;
  assigned_resources: Record<string, unknown>;
  status: string;
}

export interface AuditLog {
  id: number;
  user_name: string;
  role: string;
  action: string;
  department: string;
  details?: string;
  badge_type: string;
  created_at: string;
}

export interface DashboardMetrics {
  total_maintenance_requests: number;
  pending_requests: number;
  approved_maintenance_blocks: number;
  proposed_maintenance_blocks: number;
  completed_maintenance_tasks: number;
  critical_maintenance_tasks: number;
  resource_readiness_percentage: number | null;
  available_maintenance_windows: number;
  railway_sections_under_maintenance: number;
  current_scheduling_conflicts: number;
  upcoming_disruptions: number;
  department_distribution: Record<string, number>;
  priority_distribution: Record<string, number>;
  block_utilization: {
    hours_requested: number;
    hours_granted: number;
    utilization_percentage: number | null;
    scheduled_minutes: number;
    usable_window_minutes: number;
  };
}

export interface ReadinessPillar {
  score: number | null;
  status: string;
  notes?: string;
  reasons?: string[];
  [key: string]: any;
}

export interface ReadinessReport {
  request_id: string;
  overall_readiness_score: number | null;
  readiness_grade: "READY_FOR_EXECUTION" | "CONDITIONAL_APPROVAL" | "CRITICAL_DEFICIT";
  verdict: "READY" | "PARTIALLY_READY" | "NOT_READY";
  mandatory_pillars: string[];
  failing_pillars: string[];
  pillars: {
    staff: ReadinessPillar;
    machinery: ReadinessPillar;
    materials: ReadinessPillar;
    traffic_window: ReadinessPillar;
    safety_isolation: ReadinessPillar;
  };
  recommendation: string;
  recommended_action: string;
}

export interface TopologyNode {
  id: string;
  label: string;
  type: string;
  lat?: number;
  lng?: number;
}

export interface TopologyEdge {
  source: string;
  target: string;
  section_code: string;
  distance_km: number;
  tracks: number;
  density: string;
}

export interface NetworkTopology {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
}
