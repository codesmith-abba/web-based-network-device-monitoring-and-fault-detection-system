interface LoadingStateProps {
  label?: string
}

export function LoadingState({ label = 'Loading monitoring data…' }: LoadingStateProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white px-6 py-12 text-center" role="status" aria-live="polite">
      <div className="mx-auto mb-4 size-8 animate-spin rounded-full border-2 border-slate-200 border-t-slate-900" aria-hidden="true" />
      <p className="text-sm font-medium text-slate-700">{label}</p>
    </div>
  )
}
