import type {
  ComplianceReport,
  DecisionRequest,
  DecisionResponse,
  RegulationOption,
  TriggerRequest,
  TriggerResponse,
  PipelineStatus,
} from './types'

const API_BASE = '/api/v1'

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`HTTP ${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

export async function fetchReport(regulationId?: string): Promise<ComplianceReport> {
  const url = regulationId
    ? `${API_BASE}/hitl/report/${regulationId}`
    : `${API_BASE}/hitl/latest`
  const res = await fetch(url, {
    headers: { Accept: 'application/json' },
  })
  return handleResponse<ComplianceReport>(res)
}

export async function submitDecision(request: DecisionRequest): Promise<DecisionResponse> {
  const res = await fetch(`${API_BASE}/hitl/respond`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(request),
  })
  return handleResponse<DecisionResponse>(res)
}

export async function fetchRegulations(): Promise<RegulationOption[]> {
  const res = await fetch(`${API_BASE}/trigger/regulations`, {
    headers: { Accept: 'application/json' },
  })
  return handleResponse<RegulationOption[]>(res)
}

export async function triggerCascade(request: TriggerRequest): Promise<TriggerResponse> {
  const res = await fetch(`${API_BASE}/trigger`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(request),
  })
  return handleResponse<TriggerResponse>(res)
}

export async function fetchPipelineStatus(roomId: string): Promise<PipelineStatus> {
  const res = await fetch(`${API_BASE}/hitl/pipeline/status/${roomId}`, {
    headers: { Accept: 'application/json' },
  })
  return handleResponse<PipelineStatus>(res)
}
