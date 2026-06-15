import { useState, useEffect, useRef } from 'react'

type DecisionType = 'approve' | 'reject'

interface ConfirmModalProps {
  type: DecisionType | null
  onConfirm: (reason?: string) => void
  onCancel: () => void
}

export default function ConfirmModal({ type, onConfirm, onCancel }: ConfirmModalProps) {
  const [reason, setReason] = useState('')
  const dialogRef = useRef<HTMLDivElement>(null)
  const confirmBtnRef = useRef<HTMLButtonElement>(null)
  const isReject = type === 'reject'

  // Focus trap + Escape key
  useEffect(() => {
    if (!type) return

    confirmBtnRef.current?.focus()

    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { onCancel(); return }
      if (e.key !== 'Tab' || !dialogRef.current) return

      const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
        'button, textarea, [tabindex]:not([tabindex="-1"])'
      )
      const first = focusable[0]
      const last = focusable[focusable.length - 1]

      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault(); last.focus()
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault(); first.focus()
      }
    }

    document.addEventListener('keydown', handleKey)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handleKey)
      document.body.style.overflow = ''
    }
  }, [type, onCancel])

  if (!type) return null

  return (
    <div
      className="animate-backdrop-fade fixed inset-0 z-50 flex items-end justify-center bg-black/60 backdrop-blur-sm sm:items-center sm:p-4"
      onClick={onCancel}
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-title"
    >
      <div
        ref={dialogRef}
        className="animate-modal-slide-up w-full max-w-md rounded-t-xl border border-[var(--color-surface-2)] p-6 sm:rounded-xl"
        style={{ background: 'var(--color-surface-1)' }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2
          id="confirm-title"
          className="text-lg font-semibold text-[var(--color-ink)]"
        >
          {isReject ? 'Reject Remediation Plan' : 'Approve Remediation Plan'}
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-[var(--color-ink-muted)]">
          {isReject
            ? 'Are you sure you want to reject this plan? The remediation planner will need to regenerate the report.'
            : 'Are you sure you want to approve this plan? The remediation planner will finalize the report and post it to the Band room.'}
        </p>

        {isReject && (
          <div className="mt-4">
            <label
              htmlFor="reject-reason"
              className="mb-1.5 block text-xs font-medium text-[var(--color-ink-dim)]"
            >
              Reason for rejection{' '}
              <span className="opacity-60">(optional)</span>
            </label>
            <textarea
              id="reject-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Describe what needs to change..."
              rows={3}
              className="w-full rounded-lg border border-[var(--color-surface-2)] bg-[var(--color-surface-0)] px-3 py-2 text-sm text-[var(--color-ink)] placeholder-[var(--color-ink-dim)] transition-colors duration-200 focus:border-[var(--color-accent)] focus:outline-none"
            />
          </div>
        )}

        <div className="mt-5 flex gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 rounded-lg border border-[var(--color-surface-2)] px-4 py-2.5 text-sm font-medium text-[var(--color-ink-muted)] transition-all duration-200 hover:border-[var(--color-surface-3)] hover:bg-[var(--color-surface-2)] hover:text-[var(--color-ink)] focus-visible:outline-2 focus-visible:outline-[var(--color-accent)]"
          >
            Cancel
          </button>
          <button
            ref={confirmBtnRef}
            type="button"
            onClick={() => onConfirm(isReject ? reason : undefined)}
            className={`flex-1 rounded-lg px-4 py-2.5 text-sm font-semibold text-white transition-all duration-200 hover:scale-[1.02] focus-visible:outline-2 focus-visible:outline-white ${
              isReject
                ? 'bg-[var(--color-danger)] shadow-[0_0_20px_var(--color-danger-glow)] hover:shadow-[0_0_30px_var(--color-danger-glow)]'
                : 'bg-[var(--color-accent)] shadow-[0_0_20px_var(--color-accent-glow)] hover:shadow-[0_0_30px_var(--color-accent-glow)]'
            }`}
          >
            {isReject ? 'Reject' : 'Approve'}
          </button>
        </div>
      </div>
    </div>
  )
}
