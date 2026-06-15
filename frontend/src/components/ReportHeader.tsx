import type { ComplianceReport } from '../types'
import StatusBadge from './StatusBadge'

export default function ReportHeader({ report }: { report: ComplianceReport }) {
  return (
    <header className="animate-header-reveal border-b border-[var(--color-surface-2)] px-6 py-6 sm:px-8">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h1
            className="text-balance text-xl font-semibold leading-tight text-[var(--color-ink)] sm:text-2xl"
            style={{ letterSpacing: '-0.02em' }}
          >
            {report.regulation_name}
          </h1>
          <p
            className="mt-1.5 text-sm font-medium text-[var(--color-ink-dim)]"
            style={{ fontVariantNumeric: 'tabular-nums' }}
          >
            {report.regulation_id}
          </p>
        </div>
        <div className="shrink-0 sm:mt-0.5">
          <StatusBadge status={report.status} animate={report.status === 'pending_approval'} />
        </div>
      </div>
    </header>
  )
}
