export interface RemediationTicket {
  ticket_id: string
  title: string
  gap_ref: string
  priority: 'P0' | 'P1' | 'P2'
  owner_team: string
  effort_weeks: number
  depends_on: string[]
  actions: string[]
  done_criteria: string
}

export interface ComplianceReport {
  regulation_id: string
  regulation_name: string
  executive_summary: string
  generated_at: string
  compliance_deadline: string
  weeks_to_deadline: number
  critical_path_weeks: number
  total_gaps: number
  critical_gaps: number
  status: 'pending_approval' | 'approved' | 'rejected'
  sequencing_note: string
  tickets: RemediationTicket[]
  timing?: PipelineTiming | null
}

export interface PipelineTiming {
  monitor?: number
  legal_parser?: number
  impact_mapper?: number
  gap_analyst?: number
  remediation_planner?: number
  total?: number
}

export type Decision = 'APPROVED' | 'REJECTED'

export interface DecisionRequest {
  decision: Decision
  reason?: string
}

export interface DecisionResponse {
  status: string
  decision: string
}

export interface RegulationOption {
  regulation_id: string
  title: string
  jurisdiction: string
  summary: string
  industry_tags: string[]
}

export interface TriggerRequest {
  regulation_text: string
  regulation_title?: string
}

export interface TriggerResponse {
  status: string
  room_id: string
  regulation_title: string | null
}

export type AgentStatus = 'pending' | 'processing' | 'complete'

export interface PipelineStatus {
  [key: string]: string
}