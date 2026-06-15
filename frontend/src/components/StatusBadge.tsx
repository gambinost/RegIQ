type Status = 'pending_approval' | 'approved' | 'rejected'

const STATUS_MAP: Record<Status, { label: string; color: string; bg: string }> = {
  pending_approval: {
    label: 'Pending Approval',
    color: 'var(--color-status-pending)',
    bg: 'var(--color-status-pending-bg)',
  },
  approved: {
    label: 'Approved',
    color: 'var(--color-status-approved)',
    bg: 'var(--color-status-approved-bg)',
  },
  rejected: {
    label: 'Rejected',
    color: 'var(--color-status-rejected)',
    bg: 'var(--color-status-rejected-bg)',
  },
}

export default function StatusBadge({ status, animate }: { status: Status; animate?: boolean }) {
  const config = STATUS_MAP[status] ?? STATUS_MAP.pending_approval

  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium tracking-wide ${animate ? 'animate-status-pulse' : ''}`}
      style={{
        color: config.color,
        background: config.bg,
        border: `1px solid ${config.color}`,
        fontVariantNumeric: 'tabular-nums',
      }}
    >
      <span
        className="mr-2 inline-block h-2 w-2 rounded-full"
        style={{ background: config.color }}
      />
      {config.label}
    </span>
  )
}
