export interface RemediationTicket {
  ticket_id: string
  gap_id: string
  title: string
  description: string
  priority: 'Low' | 'Medium' | 'High' | 'Critical'
  owner: string
  estimated_effort_days: number
  deadline: string
}

export interface ComplianceReport {
  regulation_id: string
  regulation_name: string
  executive_summary: string
  total_gaps: number
  critical_gaps: number
  status: 'pending_approval' | 'approved' | 'rejected'
  tickets: RemediationTicket[]
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
