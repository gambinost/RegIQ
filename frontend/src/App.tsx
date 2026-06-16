import { useState, useEffect } from 'react'
import type { ComplianceReport } from './types'
import { fetchReport } from './api'
import HITLReview from './components/HITLReview'

function SkeletonCard() {
  return (
    <div className="rounded-lg border border-[var(--color-surface-2)] px-4 py-4 sm:px-5" style={{ background: 'var(--color-surface-1)' }}>
      <div className="flex items-center gap-2.5">
        <div className="h-5 w-16 rounded-full bg-[var(--color-surface-2)]" />
        <div className="h-4 w-20 rounded bg-[var(--color-surface-2)]" />
      </div>
      <div className="mt-2 h-5 w-3/4 rounded bg-[var(--color-surface-2)]" />
      <div className="mt-1.5 h-4 w-full rounded bg-[var(--color-surface-2)]" />
      <div className="mt-1 h-4 w-2/3 rounded bg-[var(--color-surface-2)]" />
      <div className="mt-3 flex gap-5 border-t border-[var(--color-surface-2)] pt-3">
        <div className="h-4 w-24 rounded bg-[var(--color-surface-2)]" />
        <div className="h-4 w-16 rounded bg-[var(--color-surface-2)]" />
        <div className="h-4 w-20 rounded bg-[var(--color-surface-2)]" />
      </div>
    </div>
  )
}

function LoadingState() {
  return (
    <div className="relative mx-auto min-h-screen max-w-3xl animate-pulse">
      {/* Header skeleton */}
      <div className="border-b border-[var(--color-surface-2)] px-6 py-5 sm:px-8">
        <div className="flex items-center justify-between">
          <div className="min-w-0">
            <div className="h-7 w-3/4 rounded bg-[var(--color-surface-2)]" />
            <div className="mt-1 h-4 w-32 rounded bg-[var(--color-surface-2)]" />
          </div>
          <div className="h-7 w-32 rounded-full bg-[var(--color-surface-2)]" />
        </div>
      </div>

      {/* Summary bar skeleton */}
      <div className="grid grid-cols-2 gap-3 px-6 py-4 sm:px-8">
        <div className="rounded-lg border border-[var(--color-surface-2)] px-4 py-3" style={{ background: 'var(--color-surface-1)' }}>
          <div className="mx-auto h-8 w-8 rounded bg-[var(--color-surface-2)]" />
          <div className="mx-auto mt-1 h-3 w-20 rounded bg-[var(--color-surface-2)]" />
        </div>
        <div className="rounded-lg border border-[var(--color-surface-2)] px-4 py-3" style={{ background: 'var(--color-surface-1)' }}>
          <div className="mx-auto h-8 w-8 rounded bg-[var(--color-surface-2)]" />
          <div className="mx-auto mt-1 h-3 w-20 rounded bg-[var(--color-surface-2)]" />
        </div>
      </div>

      {/* Executive summary skeleton */}
      <div className="px-6 pb-5 sm:px-8">
        <div className="h-4 w-32 rounded bg-[var(--color-surface-2)]" />
        <div className="mt-2 h-4 w-full rounded bg-[var(--color-surface-2)]" />
        <div className="mt-1 h-4 w-5/6 rounded bg-[var(--color-surface-2)]" />
        <div className="mt-1 h-4 w-4/5 rounded bg-[var(--color-surface-2)]" />
      </div>

      {/* Tickets skeleton */}
      <div className="px-6 pb-24 sm:px-8">
        <div className="mb-3 flex items-center justify-between">
          <div className="h-4 w-32 rounded bg-[var(--color-surface-2)]" />
          <div className="h-3 w-16 rounded bg-[var(--color-surface-2)]" />
        </div>
        <div className="flex flex-col gap-3">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    </div>
  )
}

function ErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <div className="flex min-h-screen items-center justify-center px-6">
      <div className="max-w-md text-center">
        <div
          className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full"
          style={{ background: 'var(--color-priority-critical-bg)' }}
        >
          <svg className="h-6 w-6 text-[var(--color-priority-critical)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
          </svg>
        </div>
        <h2 className="text-lg font-semibold text-[var(--color-ink)]">Failed to load report</h2>
        <p className="mt-2 text-sm text-[var(--color-ink-muted)]">{error}</p>
        <button
          onClick={onRetry}
          className="mt-4 rounded-lg px-4 py-2.5 text-sm font-semibold text-white transition-all duration-200"
          style={{ background: 'var(--color-accent)' }}
        >
          Retry
        </button>
      </div>
    </div>
  )
}

export default function App() {
  const [report, setReport] = useState<ComplianceReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadReport = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchReport('GDPR-2026-003')
      setReport(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadReport()
  }, [])

  if (loading) return <LoadingState />
  if (error) return <ErrorState error={error} onRetry={loadReport} />
  if (!report) return <ErrorState error="No report data available" onRetry={loadReport} />

  return <HITLReview report={report} />
}
