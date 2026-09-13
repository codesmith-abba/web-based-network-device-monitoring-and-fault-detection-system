import type { FaultSeverity } from '../dashboard/types'

interface FaultSeverityBadgeProps {
  severity: FaultSeverity
}

const config: Record<FaultSeverity, { label: string; symbol: string; classes: string }> = {
  critical: { label: 'Critical', symbol: '!', classes: 'border-rose-200 bg-rose-50 text-rose-700' },
  high: { label: 'High', symbol: '↑', classes: 'border-orange-200 bg-orange-50 text-orange-700' },
  medium: { label: 'Medium', symbol: '•', classes: 'border-amber-200 bg-amber-50 text-amber-700' },
  low: { label: 'Low', symbol: '↓', classes: 'border-slate-200 bg-slate-50 text-slate-600' },
}

export function FaultSeverityBadge({ severity }: FaultSeverityBadgeProps) {
  const item = config[severity]
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold ${item.classes}`}>
      <span aria-hidden="true" className="font-bold">{item.symbol}</span>
      <span>{item.label}</span>
    </span>
  )
}
