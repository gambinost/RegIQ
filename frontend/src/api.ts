import type { ComplianceReport, DecisionRequest, DecisionResponse } from './types'

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
