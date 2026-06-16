import type { RemediationTicket } from '../types'

const PRIORITY_CONFIG: Record<
  RemediationTicket['priority'],
  { label: string; color: string; bg: string; border: string }
> = {
  P0: {
    label: 'Critical',
    color: 'var(--color-priority-critical)',
    bg: 'var(--color-priority-critical-bg)',
    border: 'oklch(60% 0.22 25 / 0.3)',
  },
  P1: {
    label: 'High',
    color: 'var(--color-priority-high)',
    bg: 'var(--color-priority-high-bg)',
    border: 'oklch(65% 0.18 55 / 0.2)',
  },
  P2: {
    label: 'Medium',
    color: 'var(--color-priority-medium)',
    bg: 'var(--color-priority-medium-bg)',
    border: 'oklch(70% 0.14 85 / 0.15)',
  },
}

export default function TicketCard({
  ticket,
  index,
}: {
  ticket: RemediationTicket
  index: number
}) {
  const priority = PRIORITY_CONFIG[ticket.priority]
  const isCritical = ticket.priority === 'P0'

  return (
    <article
      className="animate-stagger rounded-lg border px-4 py-4 transition-all duration-200 sm:px-5 hover:border-[var(--color-surface-3)] hover:bg-[var(--color-surface-2)] focus-within:border-[var(--color-accent-muted)]"
      style={{
        background: 'var(--color-surface-1)',
        borderColor: isCritical ? priority.border : 'var(--color-surface-2)',
        '--i': index,
      } as React.CSSProperties}
      aria-label={`${priority.label} priority ticket: ${ticket.title}`}
    >
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold"
            style={{ color: priority.color, background: priority.bg }}
          >
            {priority.label}
          </span>
          <span
            className="text-xs font-medium text-[var(--color-ink-dim)]"
            style={{ fontVariantNumeric: 'tabular-nums' }}
          >
            {ticket.ticket_id}
          </span>
          <span className="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium text-[var(--color-ink-dim)] bg-[var(--color-surface-2)] border border-[var(--color-surface-3)]">
            {ticket.gap_ref}
          </span>
        </div>
        <h3 className="mt-2 text-base font-semibold leading-snug text-[var(--color-ink)]">
          {ticket.title}
        </h3>

        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5">
          <dl className="flex items-center gap-1.5">
            <dt className="text-xs font-medium text-[var(--color-ink-dim)]">Owner</dt>
            <dd className="text-xs font-semibold text-[var(--color-ink-muted)]">{ticket.owner_team}</dd>
          </dl>
          <dl className="flex items-center gap-1.5">
            <dt className="text-xs font-medium text-[var(--color-ink-dim)]">Effort</dt>
            <dd className="text-xs font-semibold text-[var(--color-ink-muted)]" style={{ fontVariantNumeric: 'tabular-nums' }}>
              {ticket.effort_weeks}w
            </dd>
          </dl>
        </div>

        {ticket.depends_on.length > 0 && (
          <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
            <span className="text-[10px] font-medium uppercase tracking-wider text-[var(--color-ink-dim)]">
              Depends on
            </span>
            {ticket.depends_on.map((dep) => (
              <span
                key={dep}
                className="inline-flex items-center rounded border border-[var(--color-surface-3)] bg-[var(--color-surface-0)] px-1.5 py-0.5 text-[10px] font-mono font-medium text-[var(--color-accent)]"
              >
                {dep}
              </span>
            ))}
          </div>
        )}

        <div className="mt-3 border-t border-[var(--color-surface-2)] pt-3">
          <span className="text-[10px] font-medium uppercase tracking-wider text-[var(--color-ink-dim)]">
            Actions
          </span>
          <ol className="mt-1 space-y-1">
            {ticket.actions.map((action, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-[var(--color-ink-muted)]">
                <span
                  className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[10px] font-bold"
                  style={{
                    background: 'var(--color-surface-2)',
                    color: 'var(--color-ink-dim)',
                  }}
                >
                  {i + 1}
                </span>
                {action}
              </li>
            ))}
          </ol>
        </div>

        <div className="mt-2.5 flex items-start gap-1.5 rounded border border-[var(--color-surface-2)] bg-[var(--color-surface-0)] px-2.5 py-1.5">
          <svg
            className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[var(--color-status-approved)]"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          <div>
            <span className="text-[10px] font-medium uppercase tracking-wider text-[var(--color-ink-dim)]">
              Done when
            </span>
            <p className="text-sm text-[var(--color-ink-muted)]">{ticket.done_criteria}</p>
          </div>
        </div>
      </div>
    </article>
  )
}