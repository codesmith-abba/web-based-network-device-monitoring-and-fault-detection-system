import type { DeviceStatus } from '../devices/types'

const labels: Record<DeviceStatus, string> = { online: 'Online', offline: 'Offline', unknown: 'Unknown' }

export function DeviceStatusBadge({ status }: { status: DeviceStatus }) {
  const styles: Record<DeviceStatus, string> = {
    online: 'border-emerald-200 bg-emerald-50 text-emerald-800',
    offline: 'border-rose-200 bg-rose-50 text-rose-800',
    unknown: 'border-slate-200 bg-slate-100 text-slate-700',
  }
  const symbols: Record<DeviceStatus, string> = { online: '✓', offline: '×', unknown: '?' }
  return <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold ${styles[status]}`}><span aria-hidden="true">{symbols[status]}</span>{labels[status]}</span>
}
