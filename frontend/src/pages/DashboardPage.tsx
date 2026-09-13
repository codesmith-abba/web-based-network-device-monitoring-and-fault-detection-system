import { ActivityIcon, AlertTriangleIcon, ServerIcon } from '../components/icons'

const sections = [
  {
    title: 'Device visibility',
    description: 'Device totals and online/offline status will appear here once monitoring data is connected.',
    icon: ServerIcon,
  },
  {
    title: 'Fault visibility',
    description: 'Active fault summaries and severity information will be surfaced here in the monitoring phases.',
    icon: AlertTriangleIcon,
  },
  {
    title: 'Monitoring health',
    description: 'Latency, packet loss, availability, and supported SNMP metrics will be added without fabricating live data.',
    icon: ActivityIcon,
  },
]

export function DashboardPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 lg:py-10">
      <section className="mb-8">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Dashboard</p>
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl">Network overview</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">Your monitoring workspace is ready. Live device and fault information will be connected in later phases.</p>
          </div>
          <div className="inline-flex w-fit items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-600 shadow-sm">
            <span className="size-2 rounded-full bg-emerald-500" /> Foundation ready
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3" aria-label="Dashboard modules">
        {sections.map(({ title, description, icon: Icon }) => (
          <article key={title} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-950/[0.02]">
            <div className="mb-5 grid size-10 place-items-center rounded-xl bg-slate-100 text-slate-700"><Icon className="size-5" /></div>
            <h2 className="text-sm font-semibold text-slate-950">{title}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">{description}</p>
          </article>
        ))}
      </section>

      <section className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-white p-6 sm:p-8">
        <div className="max-w-2xl">
          <p className="text-sm font-semibold text-slate-900">Monitoring data not connected yet</p>
          <p className="mt-2 text-sm leading-6 text-slate-500">Phase 1 intentionally contains no fake device counts, monitoring measurements, or fault events. The dashboard is structured to receive real Django REST API data in the integration phases.</p>
        </div>
      </section>
    </div>
  )
}
