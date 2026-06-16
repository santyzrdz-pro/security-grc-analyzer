export interface Role {
  id: number;
  name: string;
  description?: string | null;
}

export interface CurrentUser {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  role: Role;
  permissions: string[];
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface Asset {
  id: number;
  name: string;
  owner?: string | null;
  business_unit?: string | null;
  asset_type: string;
  criticality: string;
  operating_system?: string | null;
  ip_address?: string | null;
  environment: string;
  status: string;
}

export interface Control {
  id: number;
  control_id: string;
  family: string;
  family_name?: string | null;
  title: string;
  description: string;
  implementation_status: string;
}

export interface MappedControl {
  control: Control;
  confidence: number;
  method?: string | null;
  rationale?: string | null;
}

export interface AIAnalysis {
  executive_summary?: string | null;
  business_impact?: string | null;
  technical_explanation?: string | null;
  recommended_remediation?: string | null;
}

export interface Finding {
  id: number;
  title: string;
  description?: string | null;
  severity: string;
  status: string;
  detection_date?: string | null;
  source?: string | null;
  evidence?: string | null;
  cve?: string | null;
  asset_id?: number | null;
  asset_name?: string | null;
  mapped_controls: MappedControl[];
  ai_analysis?: AIAnalysis | null;
}

export interface Risk {
  id: number;
  title: string;
  description?: string | null;
  likelihood: number;
  impact: number;
  risk_score: number;
  risk_level: string;
  mitigation_plan?: string | null;
  owner?: string | null;
  due_date?: string | null;
  asset_id?: number | null;
  asset_name?: string | null;
  finding_id?: number | null;
}

export interface Remediation {
  id: number;
  task: string;
  description?: string | null;
  owner?: string | null;
  status: string;
  priority: string;
  due_date?: string | null;
  finding_id?: number | null;
  risk_id?: number | null;
}

export interface NameValue {
  name: string;
  value: number;
}

export interface TrendPoint {
  month: string;
  count: number;
}

export interface DashboardResponse {
  stats: {
    total_assets: number;
    open_findings: number;
    critical_findings: number;
    total_risks: number;
    high_risks: number;
    compliance_score: number;
  };
  risk_distribution: NameValue[];
  findings_by_severity: NameValue[];
  controls_by_family: NameValue[];
  remediation_progress: NameValue[];
  monthly_findings_trend: TrendPoint[];
}

export interface ComplianceResponse {
  total_controls: number;
  implemented_controls: number;
  partially_implemented: number;
  not_implemented: number;
  not_applicable: number;
  compliance_percentage: number;
  grade: string;
  by_family: NameValue[];
}

export interface MappingResponse {
  finding: string;
  controls: string[];
  confidence: number;
  matches: {
    control_id: string;
    confidence: number;
    method: string;
    rationale: string;
  }[];
}

export interface ReportMeta {
  id: number;
  title: string;
  report_type: string;
  summary?: string | null;
  compliance_score?: number | null;
  created_at: string;
}
