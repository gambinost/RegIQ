import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import type { ReportSummary } from '../types'
import { fetchAllReports } from '../api'
import StatusBadge from '../components/StatusBadge'

function formatDate(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

function EmptyState({ onTrigger }: { onTrigger: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-16 text-center">
      <div
        className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl"
        style={{ background: 'var(--color-accent-bg)', border: '1px solid var(--color-accent-muted)' }}
      >
        <svg className="h-8 w-8 text-[var(--color-accent)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <h2 className="text-lg font-semibold text-[var(--color-ink)]">No analyses yet</h2>
      <p className="mt-1.5 text-sm text-[var(--color-ink-muted)]" style={{ maxWidth: '40ch' }}>
        Start your first compliance analysis. RegIQ's 5-agent cascade will parse requirements, map them to your processes, and generate a remediation plan.
      </p>
      <button
        type="button"
        onClick={onTrigger}
        className="mt-5 flex items-center gap-2 rounded-lg bg-[var(--color-accent)] px-5 py-2.5 text-sm font-semibold text-white shadow-[0_0_20px_var(--color-accent-glow)] transition-all duration-150 hover:shadow-[0_0_30px_var(--color-accent-glow)] active:scale-[0.98]"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        Start New Analysis
      </button>
    </div>
  )
}

function ReportRow({ report, index, onClick }: { report: ReportSummary; index: number; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="animate-stagger flex w-full items-center gap-4 rounded-lg border border-[var(--color-surface-2)] px-4 py-3.5 text-left transition-all duration-150 hover:border-[var(--color-accent-muted)] hover:bg-[var(--color-surface-1)] active:scale-[0.99]"
      style={{
        '--i': index,
        background: 'var(--color-surface-1)',
      } as React.CSSProperties}
    >
      {/* Regulation info */}
      <div className="min-w-0 flex-1">
        <h3 className="truncate text-sm font-semibold text-[var(--color-ink)]">
          {report.regulation_name}
        </h3>
        <p className="mt-0.5 text-xs text-[var(--color-ink-dim)]" style={{ fontVariantNumeric: 'tabular-nums' }}>
          {report.regulation_id} · {formatDate(report.generated_at)}
        </p>
      </div>

      {/* Metrics */}
      <div className="hidden shrink-0 items-center gap-5 sm:flex">
        <div className="text-center">
          <div className="text-sm font-semibold text-[var(--color-ink-muted)]" style={{ fontVariantNumeric: 'tabular-nums' }}>
            {report.ticket_count}
          </div>
          <div className="text-[10px] font-medium uppercase tracking-wider text-[var(--color-ink-dim)]">
            Tickets
          </div>
        </div>
        <div className="text-center">
          <div className="text-sm font-semibold text-[var(--color-priority-critical)]" style={{ fontVariantNumeric: 'tabular-nums' }}>
            {report.critical_gaps}
          </div>
          <div className="text-[10px] font-medium uppercase tracking-wider text-[var(--color-ink-dim)]">
            Critical
          </div>
        </div>
        <div className="text-center">
          <div className="text-sm font-semibold text-[var(--color-ink-muted)]" style={{ fontVariantNumeric: 'tabular-nums' }}>
            {report.critical_path_weeks}wk
          </div>
          <div className="text-[10px] font-medium uppercase tracking-wider text-[var(--color-ink-dim)]">
            Critical Path
          </div>
        </div>
      </div>

      {/* Status badge */}
      <div className="shrink-0">
        <StatusBadge status={report.status} />
      </div>

      {/* Chevron */}
      <svg className="h-5 w-5 shrink-0 text-[var(--color-ink-dim)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
      </svg>
    </button>
  )
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const [reports, setReports] = useState<ReportSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    fetchAllReports()
      .then((data) => {
        if (!cancelled) {
          setReports(data)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load reports')
          setLoading(false)
        }
      })

    return () => { cancelled = true }
  }, [])

  const approvedCount = reports.filter((r) => r.status === 'approved').length
  const rejectedCount = reports.filter((r) => r.status === 'rejected').length
  const pendingCount = reports.filter((r) => r.status === 'pending_approval').length

  return (
    <div className="mx-auto min-h-screen max-w-3xl">
      {/* Header */}
      <header className="animate-header-reveal border-b border-[var(--color-surface-2)] px-6 py-8 sm:px-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-xl"
              style={{ background: 'var(--color-accent-bg)', border: '1px solid var(--color-accent-muted)' }}
            >
              <svg className="h-5 w-5 text-[var(--color-accent)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-semibold text-[var(--color-ink)]" style={{ letterSpacing: '-0.02em' }}>
                RegIQ
              </h1>
              <p className="text-sm text-[var(--color-ink-dim)]">Regulatory Compliance Intelligence</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => navigate('/trigger')}
            className="flex items-center gap-2 rounded-lg bg-[var(--color-accent)] px-4 py-2.5 text-sm font-semibold text-white shadow-[0_0_20px_var(--color-accent-glow)] transition-all duration-150 hover:shadow-[0_0_30px_var(--color-accent-glow)] active:scale-[0.98]"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            New Analysis
          </button>
        </div>

        {/* Stats bar */}
        {!loading && reports.length > 0 && (
          <div className="mt-5 flex gap-6">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-[var(--color-ink-muted)]" style={{ fontVariantNumeric: 'tabular-nums' }}>
                {reports.length}
              </span>
              <span className="text-xs text-[var(--color-ink-dim)]">Total</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-[var(--color-status-approved)]" style={{ fontVariantNumeric: 'tabular-nums' }}>
                {approvedCount}
              </span>
              <span className="text-xs text-[var(--color-ink-dim)]">Approved</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-[var(--color-status-rejected)]" style={{ fontVariantNumeric: 'tabular-nums' }}>
                {rejectedCount}
              </span>
              <span className="text-xs text-[var(--color-ink-dim)]">Rejected</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-[var(--color-status-pending)]" style={{ fontVariantNumeric: 'tabular-nums' }}>
                {pendingCount}
              </span>
              <span className="text-xs text-[var(--color-ink-dim)]">Pending</span>
            </div>
          </div>
        )}
      </header>

      {/* Body */}
      <div className="px-6 py-6 sm:px-8">
        {loading ? (
          <div className="flex flex-col gap-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="animate-pulse rounded-lg border border-[var(--color-surface-2)] px-4 py-4"
                style={{ background: 'var(--color-surface-1)' }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="h-5 w-3/4 rounded bg-[var(--color-surface-2)]" />
                    <div className="mt-2 h-3 w-1/2 rounded bg-[var(--color-surface-2)]" />
                  </div>
                  <div className="h-6 w-24 rounded-full bg-[var(--color-surface-2)]" />
                </div>
              </div>
            ))}
          </div>
        ) : error ? (
          <div
            className="rounded-lg border border-[var(--color-priority-critical)] bg-[var(--color-priority-critical-bg)] px-4 py-3 text-sm text-[var(--color-priority-critical)]"
            role="alert"
          >
            {error}
          </div>
        ) : reports.length === 0 ? (
          <EmptyState onTrigger={() => navigate('/trigger')} />
        ) : (
          <div className="flex flex-col gap-2.5" role="list">
            {reports.map((report, i) => (
              <ReportRow
                key={report.regulation_id}
                report={report}
                index={i}
                onClick={() => navigate(`/review/${report.regulation_id}`)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
