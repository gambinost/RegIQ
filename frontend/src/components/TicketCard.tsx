import type { RemediationTicket } from '../types'

const PRIORITY_CONFIG: Record<
  RemediationTicket['priority'],
  { color: string; bg: string; border: string; label: string }
> = {
  Critical: {
    color: 'var(--color-priority-critical)',
    bg: 'var(--color-priority-critical-bg)',
    border: 'oklch(60% 0.22 25 / 0.3)',
    label: 'Critical',
  },
  High: {
    color: 'var(--color-priority-high)',
    bg: 'var(--color-priority-high-bg)',
    border: 'oklch(65% 0.18 55 / 0.2)',
    label: 'High',
  },
  Medium: {
    color: 'var(--color-priority-medium)',
    bg: 'var(--color-priority-medium-bg)',
    border: 'oklch(70% 0.14 85 / 0.15)',
    label: 'Medium',
  },
  Low: {
    color: 'var(--color-priority-low)',
    bg: 'var(--color-priority-low-bg)',
    border: 'oklch(65% 0.12 150 / 0.15)',
    label: 'Low',
  },
}

const METADATA = [
  { key: 'owner', label: 'Owner', value: (t: RemediationTicket) => t.owner || '\u2014' },
  { key: 'effort', label: 'Effort', value: (t: RemediationTicket) => `${t.estimated_effort_days}d` },
  { key: 'deadline', label: 'Deadline', value: (t: RemediationTicket) => t.deadline || '\u2014' },
] as const

export default function TicketCard({
  ticket,
  index,
}: {
  ticket: RemediationTicket
  index: number
}) {
  const priority = PRIORITY_CONFIG[ticket.priority]
  const isCritical = ticket.priority === 'Critical'

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
        <div className="flex items-center gap-2.5">
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
        </div>
        <h3 className="mt-2 text-base font-semibold leading-snug text-[var(--color-ink)]">
          {ticket.title}
        </h3>
        <p className="mt-1.5 text-sm leading-relaxed text-[var(--color-ink-muted)]">
          {ticket.description}
        </p>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 border-t border-[var(--color-surface-2)] pt-3">
        {METADATA.map((m) => (
          <dl key={m.key} className="flex items-center gap-1.5">
            <dt className="text-xs font-medium text-[var(--color-ink-dim)]">{m.label}</dt>
            <dd
              className="text-xs font-semibold text-[var(--color-ink-muted)]"
              style={{ fontVariantNumeric: 'tabular-nums' }}
            >
              {m.value(ticket)}
            </dd>
          </dl>
        ))}
      </div>
    </article>
  )
}
