import { useState, useCallback } from 'react'
import type { ComplianceReport, Decision } from '../types'
import { submitDecision } from '../api'
import ReportHeader from './ReportHeader'
import SummaryBar from './SummaryBar'
import TicketCard from './TicketCard'
import ActionBar from './ActionBar'
import ConfirmModal from './ConfirmModal'

export default function HITLReview({ report: initialReport }: { report: ComplianceReport }) {
  const [report, setReport] = useState<ComplianceReport>(initialReport)
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [decision, setDecision] = useState<Decision | null>(null)
  const [confirmType, setConfirmType] = useState<'approve' | 'reject' | null>(null)
  const [loadingAction, setLoadingAction] = useState<'approve' | 'reject' | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleConfirm = useCallback(
    async (type: 'approve' | 'reject', reason?: string) => {
      setConfirmType(null)
      setLoadingAction(type)
      setSubmitting(true)
      setError(null)

      try {
        const decisionValue: Decision = type === 'approve' ? 'APPROVED' : 'REJECTED'
        await submitDecision({ decision: decisionValue, reason })
        setDecision(decisionValue)
        setSubmitted(true)
        setReport((r) => ({
          ...r,
          status: type === 'approve' ? 'approved' : 'rejected',
        }))
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to submit decision')
      } finally {
        setSubmitting(false)
        setLoadingAction(null)
      }
    },
    []
  )

  const handleCancel = useCallback(() => {
    setConfirmType(null)
  }, [])

  const sortedTickets = [...report.tickets].sort((a, b) => {
    const order = { Critical: 0, High: 1, Medium: 2, Low: 3 }
    return order[a.priority] - order[b.priority]
  })

  const totalEffort = sortedTickets.reduce((sum, t) => sum + t.estimated_effort_days, 0)
  const earliestDeadline = sortedTickets
    .filter((t) => t.deadline)
    .sort((a, b) => a.deadline.localeCompare(b.deadline))[0]?.deadline

  return (
    <div className="relative mx-auto min-h-screen max-w-3xl">
      <ReportHeader report={report} />
      <SummaryBar report={report} />

      <section className="animate-fade-in px-6 pb-5 sm:px-8" aria-labelledby="summary-heading">
        <h2 id="summary-heading" className="text-sm font-semibold uppercase tracking-wider text-[var(--color-ink-dim)]">
          Executive Summary
        </h2>
        <p
          className="mt-2 text-sm leading-relaxed text-[var(--color-ink-muted)]"
          style={{ maxWidth: '70ch' }}
        >
          {report.executive_summary}
        </p>
        <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1.5">
          <dl className="flex items-center gap-1.5">
            <dt className="text-xs font-medium text-[var(--color-ink-dim)]">Total effort</dt>
            <dd className="text-xs font-semibold text-[var(--color-ink-muted)]" style={{ fontVariantNumeric: 'tabular-nums' }}>
              {totalEffort} engineer-days
            </dd>
          </dl>
          {earliestDeadline && (
            <dl className="flex items-center gap-1.5">
              <dt className="text-xs font-medium text-[var(--color-ink-dim)]">Earliest deadline</dt>
              <dd className="text-xs font-semibold text-[var(--color-ink-muted)]" style={{ fontVariantNumeric: 'tabular-nums' }}>
                {earliestDeadline}
              </dd>
            </dl>
          )}
        </div>
      </section>

      <section className="px-6 pb-24 sm:px-8" aria-labelledby="tickets-heading">
        <div className="mb-3 flex items-center justify-between">
          <h2 id="tickets-heading" className="text-sm font-semibold uppercase tracking-wider text-[var(--color-ink-dim)]">
            Remediation Tickets
          </h2>
          <span className="text-xs text-[var(--color-ink-dim)]" style={{ fontVariantNumeric: 'tabular-nums' }}>
            {sortedTickets.length} tickets
          </span>
        </div>

        <div className="flex flex-col gap-3" role="list">
          {sortedTickets.map((ticket, i) => (
            <TicketCard key={ticket.ticket_id} ticket={ticket} index={i} />
          ))}
        </div>
      </section>

      {error && (
        <div
          className="animate-fade-in-up fixed bottom-24 left-6 right-6 z-30 mx-auto max-w-3xl rounded-lg border border-[var(--color-priority-critical)] bg-[var(--color-priority-critical-bg)] px-4 py-3 text-sm text-[var(--color-priority-critical)] sm:left-8 sm:right-8"
          role="alert"
        >
          <div className="flex items-center gap-2">
            <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
            {error}
          </div>
        </div>
      )}

      <ActionBar
        onApprove={() => setConfirmType('approve')}
        onReject={() => setConfirmType('reject')}
        disabled={submitted}
        loading={submitting}
        loadingAction={loadingAction}
        submitted={submitted}
        decision={decision}
      />

      <ConfirmModal
        type={confirmType}
        onConfirm={(reason) => handleConfirm(confirmType!, reason)}
        onCancel={handleCancel}
      />
    </div>
  )
}
