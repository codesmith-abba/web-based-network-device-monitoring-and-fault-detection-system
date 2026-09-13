import type { DeviceStatus } from '../dashboard/types'

interface StatusBadgeProps {
  status: DeviceStatus
}

const config: Record<DeviceStatus, { label: string; symbol: string; classes: string }> = {
  online: { label: 'Online', symbol: '✓', classes: 'border-emerald-200 bg-emerald-50 text-emerald-700' },
  offline: { label: 'Offline', symbol: '×', classes: 'border-rose-200 bg-rose-50 text-rose-700' },
  unknown: { label: 'Unknown', symbol: '?', classes: 'border-slate-200 bg-slate-50 text-slate-600' },
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const item = config[status]
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold ${item.classes}`}>
      <span aria-hidden="true" className="font-bold">{item.symbol}</span>
      <span>{item.label}</span>
    </span>
  )
}
