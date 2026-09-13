import type { ComponentType, SVGProps } from 'react'

type Icon = ComponentType<SVGProps<SVGSVGElement>>

interface StatCardProps {
  label: string
  value: number
  description: string
  icon: Icon
  tone?: 'neutral' | 'positive' | 'warning' | 'danger'
}

const toneClasses = {
  neutral: 'bg-slate-100 text-slate-700',
  positive: 'bg-emerald-50 text-emerald-700',
  warning: 'bg-amber-50 text-amber-700',
  danger: 'bg-rose-50 text-rose-700',
}

export function StatCard({ label, value, description, icon: Icon, tone = 'neutral' }: StatCardProps) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-950/[0.02]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">{label}</p>
          <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-950" aria-label={`${label}: ${value}`}>{value}</p>
        </div>
        <div className={`grid size-10 shrink-0 place-items-center rounded-xl ${toneClasses[tone]}`}>
          <Icon className="size-5" />
        </div>
      </div>
      <p className="mt-3 text-xs leading-5 text-slate-500">{description}</p>
    </article>
  )
}
