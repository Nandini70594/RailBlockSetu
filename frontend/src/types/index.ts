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
  created_at: string;
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
  resource_readiness_percentage: number;
  available_maintenance_windows: number;
  railway_sections_under_maintenance: number;
  current_scheduling_conflicts: number;
  upcoming_disruptions: number;
  department_distribution: Record<string, number>;
  priority_distribution: Record<string, number>;
  block_utilization: {
    hours_requested: number;
    hours_granted: number;
    utilization_percentage: number;
  };
}

export interface ReadinessPillar {
  score: number;
  status: string;
  notes?: string;
  [key: string]: any;
}

export interface ReadinessReport {
  request_id: string;
  overall_readiness_score: number;
  readiness_grade: "READY_FOR_EXECUTION" | "CONDITIONAL_APPROVAL" | "CRITICAL_DEFICIT";
  pillars: {
    staff: ReadinessPillar;
    machinery: ReadinessPillar;
    materials: ReadinessPillar;
    traffic_window: ReadinessPillar;
    safety_isolation: ReadinessPillar;
  };
  recommendation: string;
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
