interface ErrorStateProps {
  title?: string
  description: string
}

export function ErrorState({ title = 'Monitoring data unavailable', description }: ErrorStateProps) {
  return (
    <div className="rounded-2xl border border-rose-200 bg-rose-50 px-6 py-10 text-center" role="alert">
      <div className="mx-auto mb-4 grid size-10 place-items-center rounded-full border border-rose-200 bg-white text-rose-700" aria-hidden="true">!</div>
      <h3 className="text-sm font-semibold text-rose-900">{title}</h3>
      <p className="mx-auto mt-2 max-w-2xl text-sm leading-6 text-rose-800">{description}</p>
    </div>
  )
}
