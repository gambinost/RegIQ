import { useNavigate } from 'react-router-dom'

interface ActionBarProps {
  onApprove: () => void
  onReject: () => void
  disabled: boolean
  loading: boolean
  loadingAction: 'approve' | 'reject' | null
  submitted: boolean
  decision: string | null
}

export default function ActionBar({
  onApprove,
  onReject,
  disabled,
  loading,
  loadingAction,
  submitted,
  decision,
}: ActionBarProps) {
  const navigate = useNavigate()

  if (submitted) {
    const isApproved = decision === 'APPROVED'
    return (
      <div
        className="fixed bottom-0 left-0 right-0 z-40 border-t border-[var(--color-surface-2)] bg-[var(--color-surface-0)]/90 backdrop-blur-md px-6 py-4 sm:px-8"
      >
        <div className="mx-auto flex max-w-3xl flex-col gap-2.5">
          <div
            className="animate-decision-reveal flex items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-medium"
            style={{
              background: isApproved ? 'var(--color-status-approved-bg)' : 'var(--color-status-rejected-bg)',
              color: isApproved ? 'var(--color-status-approved)' : 'var(--color-status-rejected)',
              border: `1px solid ${isApproved ? 'var(--color-status-approved)' : 'var(--color-status-rejected)'}`,
            }}
            role="status"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              {isApproved ? (
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              )}
            </svg>
            {isApproved ? 'Remediation plan approved' : 'Remediation plan rejected'}
          </div>
          <div className="flex gap-2.5">
            <button
              type="button"
              onClick={() => navigate('/trigger')}
              className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-[var(--color-surface-2)] bg-[var(--color-surface-1)] px-4 py-2.5 text-sm font-semibold text-[var(--color-ink-muted)] transition-all duration-150 hover:border-[var(--color-accent-muted)] hover:text-[var(--color-ink)] active:scale-[0.98]"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Run Another
            </button>
            <button
              type="button"
              onClick={() => navigate('/')}
              className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-[var(--color-surface-2)] bg-[var(--color-surface-1)] px-4 py-2.5 text-sm font-semibold text-[var(--color-ink-muted)] transition-all duration-150 hover:border-[var(--color-accent-muted)] hover:text-[var(--color-ink)] active:scale-[0.98]"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
              </svg>
              Dashboard
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div
      className="fixed bottom-0 left-0 right-0 z-40 border-t border-[var(--color-surface-2)] bg-[var(--color-surface-0)]/90 backdrop-blur-md px-6 py-4 sm:px-8"
      role="toolbar"
      aria-label="Review actions"
    >
      <div className="mx-auto flex max-w-3xl gap-3">
        <button
          type="button"
          onClick={onReject}
          disabled={disabled || loading}
          className="flex-1 rounded-lg border border-[var(--color-danger-muted)] px-4 py-3 text-sm font-semibold text-[var(--color-danger)] transition-all duration-150 hover:bg-[var(--color-danger-bg)] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Reject remediation plan"
        >
          <span className="flex items-center justify-center gap-2">
            {loading && loadingAction === 'reject' ? (
              <svg className="animate-spinner h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            ) : (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            )}
            Reject
          </span>
        </button>

        <button
          type="button"
          onClick={onApprove}
          disabled={disabled || loading}
          className="flex-1 rounded-lg bg-[var(--color-accent)] px-4 py-3 text-sm font-semibold text-white shadow-[0_0_20px_var(--color-accent-glow)] transition-all duration-150 hover:shadow-[0_0_30px_var(--color-accent-glow)] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Approve remediation plan"
        >
          <span className="flex items-center justify-center gap-2">
            {loading && loadingAction === 'approve' ? (
              <svg className="animate-spinner h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            ) : (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            )}
            Approve
          </span>
        </button>
      </div>
    </div>
  )
}
