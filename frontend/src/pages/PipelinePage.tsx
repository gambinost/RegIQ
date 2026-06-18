import { useState, useEffect, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import type { PipelineStatus, AgentStatus } from '../types'
import { fetchPipelineStatus } from '../api'

interface AgentNode {
  key: string
  label: string
  description: string
  icon: React.ReactNode
}

const PIPELINE_AGENTS: AgentNode[] = [
  {
    key: 'monitor',
    label: 'Monitor',
    description: 'Assessing regulation urgency',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
  {
    key: 'legal_parser',
    label: 'Legal Parser',
    description: 'Extracting compliance requirements',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
      </svg>
    ),
  },
  {
    key: 'impact_mapper',
    label: 'Impact Mapper',
    description: 'Mapping to company processes (RAG)',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m-11.25 0V7.5m13.5 9V9M4.5 3.375l4.5 6 4.5-3 6 7.5" />
      </svg>
    ),
  },
  {
    key: 'gap_analyst',
    label: 'Gap Analyst',
    description: 'Identifying compliance gaps',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5" />
      </svg>
    ),
  },
  {
    key: 'remediation_planner',
    label: 'Remediation Planner',
    description: 'Generating remediation tickets',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.68.227-.815.503" />
      </svg>
    ),
  },
]

const POLL_INTERVAL = 3000

function getAgentStatus(status: PipelineStatus, agentKey: string): AgentStatus {
  const val = status[agentKey]
  if (val === 'complete') return 'complete'
  if (val === 'processing') return 'processing'
  return 'pending'
}

function getDuration(status: PipelineStatus, agentKey: string): string | null {
  const dur = status[`${agentKey}_duration`]
  if (!dur) return null
  const seconds = parseFloat(dur)
  if (isNaN(seconds)) return null
  return seconds < 60 ? `${seconds.toFixed(1)}s` : `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`
}

export default function PipelinePage() {
  const { roomId } = useParams<{ roomId: string }>()
  const navigate = useNavigate()
  const [status, setStatus] = useState<PipelineStatus>({})
  const [error, setError] = useState<string | null>(null)
  const [elapsed, setElapsed] = useState(0)
  const startTimeRef = useRef<number>(0)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const redirectedRef = useRef(false)

  useEffect(() => {
    if (!roomId) return
    startTimeRef.current = Date.now()

    const poll = async () => {
      try {
        const data = await fetchPipelineStatus(roomId)
        setStatus(data)
        setError(null)

        const plannerStatus = getAgentStatus(data, 'remediation_planner')
        if (plannerStatus === 'complete' && !redirectedRef.current) {
          redirectedRef.current = true
          if (pollRef.current) clearInterval(pollRef.current)
          if (timerRef.current) clearInterval(timerRef.current)
          setTimeout(() => navigate('/review'), 2000)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch status')
      }
    }

    poll()
    pollRef.current = setInterval(poll, POLL_INTERVAL)
    timerRef.current = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTimeRef.current) / 1000))
    }, 1000)

    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [roomId, navigate])

  const allComplete = PIPELINE_AGENTS.every((a) => getAgentStatus(status, a.key) === 'complete')
  const completedCount = PIPELINE_AGENTS.filter((a) => getAgentStatus(status, a.key) === 'complete').length
  const currentAgent = PIPELINE_AGENTS.find((a) => getAgentStatus(status, a.key) === 'processing')
  const elapsedStr = elapsed < 60 ? `${elapsed}s` : `${Math.floor(elapsed / 60)}m ${elapsed % 60}s`

  return (
    <div className="mx-auto min-h-screen max-w-3xl">
      {/* Header */}
      <header className="animate-header-reveal border-b border-[var(--color-surface-2)] px-6 py-6 sm:px-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-[var(--color-ink)]" style={{ letterSpacing: '-0.02em' }}>
              Pipeline Running
            </h1>
            <p className="mt-1 text-sm text-[var(--color-ink-dim)]" style={{ fontVariantNumeric: 'tabular-nums' }}>
              Room: <span className="font-mono text-xs">{roomId?.slice(0, 8)}...</span>
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-sm text-[var(--color-ink-muted)]" style={{ fontVariantNumeric: 'tabular-nums' }}>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {elapsedStr}
            </div>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-4">
          <div className="flex items-center justify-between text-xs text-[var(--color-ink-dim)]">
            <span>{completedCount}/{PIPELINE_AGENTS.length} agents complete</span>
            {currentAgent && <span className="text-[var(--color-accent)]">{currentAgent.label} processing...</span>}
          </div>
          <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-[var(--color-surface-2)]">
            <div
              className="h-full rounded-full bg-[var(--color-accent)] transition-all duration-500 ease-out"
              style={{ width: `${(completedCount / PIPELINE_AGENTS.length) * 100}%` }}
            />
          </div>
        </div>
      </header>

      {/* Agent nodes */}
      <div className="px-6 py-6 sm:px-8">
        <div className="flex flex-col gap-0">
          {PIPELINE_AGENTS.map((agent, i) => {
            const agentStatus = getAgentStatus(status, agent.key)
            const duration = getDuration(status, agent.key)
            const isLast = i === PIPELINE_AGENTS.length - 1

            return (
              <div key={agent.key} className="relative">
                {/* Connector line */}
                {!isLast && (
                  <div
                    className="absolute left-[26px] top-[52px] w-0.5 transition-colors duration-300"
                    style={{
                      height: '24px',
                      background: agentStatus === 'complete' ? 'var(--color-accent)' : 'var(--color-surface-2)',
                    }}
                  />
                )}

                <div
                  className="flex items-center gap-4 rounded-lg px-4 py-4 transition-all duration-300"
                  style={{
                    background: agentStatus === 'processing' ? 'var(--color-accent-bg)' : 'transparent',
                  }}
                >
                  {/* Status circle */}
                  <div
                    className={`relative flex h-[52px] w-[52px] shrink-0 items-center justify-center rounded-full border-2 transition-all duration-300 ${
                      agentStatus === 'processing' ? 'animate-status-pulse' : ''
                    }`}
                    style={{
                      borderColor:
                        agentStatus === 'complete'
                          ? 'var(--color-accent)'
                          : agentStatus === 'processing'
                          ? 'var(--color-accent)'
                          : 'var(--color-surface-3)',
                      background:
                        agentStatus === 'complete'
                          ? 'var(--color-accent)'
                          : agentStatus === 'processing'
                          ? 'var(--color-surface-1)'
                          : 'var(--color-surface-0)',
                    }}
                  >
                    {agentStatus === 'complete' ? (
                      <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    ) : agentStatus === 'processing' ? (
                      <svg className="animate-spinner h-5 w-5 text-[var(--color-accent)]" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                    ) : (
                      <div className="text-[var(--color-ink-dim)]">{agent.icon}</div>
                    )}
                  </div>

                  {/* Label + description */}
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <h3
                        className="text-sm font-semibold transition-colors duration-300"
                        style={{
                          color:
                            agentStatus === 'pending'
                              ? 'var(--color-ink-dim)'
                              : agentStatus === 'processing'
                              ? 'var(--color-accent)'
                              : 'var(--color-ink)',
                        }}
                      >
                        {agent.label}
                      </h3>
                      {duration && (
                        <span
                          className="text-xs font-medium text-[var(--color-ink-dim)]"
                          style={{ fontVariantNumeric: 'tabular-nums' }}
                        >
                          {duration}
                        </span>
                      )}
                    </div>
                    <p
                      className="mt-0.5 text-xs transition-colors duration-300"
                      style={{
                        color:
                          agentStatus === 'pending' ? 'var(--color-ink-dim)' : 'var(--color-ink-muted)',
                      }}
                    >
                      {agentStatus === 'processing' ? agent.description : agentStatus === 'complete' ? 'Complete' : 'Waiting...'}
                    </p>
                  </div>

                  {/* Step number */}
                  <span
                    className="shrink-0 text-xs font-medium text-[var(--color-ink-dim)]"
                    style={{ fontVariantNumeric: 'tabular-nums' }}
                  >
                    {String(i + 1).padStart(2, '0')}
                  </span>
                </div>
              </div>
            )
          })}
        </div>

        {/* Completion banner */}
        {allComplete && (
          <div
            className="animate-decision-reveal mt-6 flex items-center justify-center gap-2 rounded-lg px-4 py-3.5 text-sm font-medium"
            style={{
              background: 'var(--color-status-approved-bg)',
              color: 'var(--color-status-approved)',
              border: '1px solid var(--color-status-approved)',
            }}
            role="status"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Pipeline complete — redirecting to review...
          </div>
        )}

        {/* Error */}
        {error && (
          <div
            className="animate-fade-in-up mt-4 rounded-lg border border-[var(--color-priority-critical)] bg-[var(--color-priority-critical-bg)] px-4 py-3 text-sm text-[var(--color-priority-critical)]"
            role="alert"
          >
            {error}
          </div>
        )}

        {/* Back link */}
        <div className="mt-6 pb-8">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="text-xs font-medium text-[var(--color-ink-dim)] transition-colors duration-150 hover:text-[var(--color-ink-muted)]"
          >
            ← Back to trigger
          </button>
        </div>
      </div>
    </div>
  )
}
