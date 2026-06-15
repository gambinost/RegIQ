import type { ComplianceReport } from '../types'

export default function SummaryBar({ report }: { report: ComplianceReport }) {
  const hasCritical = report.critical_gaps > 0

  return (
    <div className="grid grid-cols-2 gap-3 px-6 py-4 sm:px-8" role="region" aria-label="Gap summary">
      <div
        className="animate-counter-reveal rounded-lg border border-[var(--color-surface-2)] px-4 py-3 text-center"
        style={{ background: 'var(--color-surface-1)' }}
      >
        <p
          className="text-2xl font-semibold text-[var(--color-ink)]"
          style={{ fontVariantNumeric: 'tabular-nums' }}
        >
          {report.total_gaps}
        </p>
        <p className="mt-0.5 text-xs font-medium uppercase tracking-wider text-[var(--color-ink-dim)]">
          Total Gaps
        </p>
      </div>
      <div
        className={`animate-counter-reveal rounded-lg border px-4 py-3 text-center ${hasCritical ? 'animate-critical-breathe' : ''}`}
        style={{
          background: 'var(--color-priority-critical-bg)',
          borderColor: hasCritical ? 'oklch(60% 0.22 25 / 0.35)' : 'var(--color-surface-2)',
        }}
      >
        <p
          className="text-2xl font-semibold"
          style={{
            color: hasCritical ? 'var(--color-priority-critical)' : 'var(--color-ink-muted)',
            fontVariantNumeric: 'tabular-nums',
          }}
        >
          {report.critical_gaps}
        </p>
        <p
          className="mt-0.5 text-xs font-medium uppercase tracking-wider"
          style={{ color: hasCritical ? 'oklch(65% 0.16 25)' : 'var(--color-ink-dim)' }}
        >
          Critical Gaps
        </p>
      </div>
    </div>
  )
}
