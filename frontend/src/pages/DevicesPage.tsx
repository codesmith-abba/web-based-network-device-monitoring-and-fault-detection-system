import { FormEvent, useEffect, useMemo, useState } from 'react'
import { AlertTriangleIcon, PlusIcon, RefreshIcon, SearchIcon, ServerIcon, XIcon } from '../components/icons'
import { DeviceStatusBadge } from '../components/DeviceStatusBadge'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import { getDeviceService, isValidIp } from '../devices/service'
import { DeviceServiceError, type Device, type DeviceRegistrationInput, type DeviceType, type MonitoringState } from '../devices/types'

const typeLabels: Record<DeviceType, string> = { router: 'Router', switch: 'Switch', server: 'Server', 'access-point': 'Access Point', firewall: 'Firewall', other: 'Other' }
const types = Object.entries(typeLabels) as [DeviceType, string][]
const pageSize = 5

const emptyForm: DeviceRegistrationInput = { name: '', ipAddress: '', type: '', monitoring: 'enabled' }

function DeviceForm({ device, onClose, onSaved }: { device: Device | null; onClose: () => void; onSaved: (device: Device) => void }) {
  const [form, setForm] = useState<DeviceRegistrationInput>(device ? { name: device.name, ipAddress: device.ipAddress, type: device.type, monitoring: device.monitoring } : emptyForm)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isSaving, setIsSaving] = useState(false)
  const [submitError, setSubmitError] = useState('')

  const validate = () => {
    const next: Record<string, string> = {}
    if (!form.name.trim()) next.name = 'Device name is required.'
    if (!form.ipAddress.trim()) next.ipAddress = 'IP address is required.'
    else if (!isValidIp(form.ipAddress)) next.ipAddress = 'Enter a valid IPv4 address.'
    if (!form.type) next.type = 'Device type is required.'
    if (!form.monitoring) next.monitoring = 'Monitoring configuration is required.'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setSubmitError('')
    if (!validate()) return
    setIsSaving(true)
    try {
      const service = getDeviceService()
      const saved = device ? await service.update(device.id, form) : await service.create(form)
      onSaved(saved)
    } catch (reason: unknown) {
      setSubmitError(reason instanceof DeviceServiceError ? reason.message : 'Unable to save the device.')
    } finally { setIsSaving(false) }
  }

  const fieldClass = (field: string) => `mt-1 w-full rounded-xl border bg-white px-3 py-2.5 text-sm outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200 ${errors[field] ? 'border-rose-400' : 'border-slate-200'}`
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/40 p-0 sm:items-center sm:p-4" role="dialog" aria-modal="true" aria-labelledby="device-form-title">
      <form onSubmit={submit} className="max-h-[95vh] w-full overflow-y-auto rounded-t-2xl bg-white p-5 shadow-xl sm:max-w-lg sm:rounded-2xl sm:p-6">
        <div className="flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Device management</p><h2 id="device-form-title" className="mt-1 text-xl font-semibold text-slate-950">{device ? 'Edit device' : 'Register device'}</h2><p className="mt-1 text-sm text-slate-500">Configure the device details and monitoring state.</p></div><button type="button" onClick={onClose} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100" aria-label="Close form"><XIcon className="size-5" /></button></div>
        {submitError && <div className="mt-5"><ErrorState description={submitError} /></div>}
        <div className="mt-6 space-y-4">
          <label className="block text-sm font-medium text-slate-700">Device name<input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className={fieldClass('name')} aria-invalid={Boolean(errors.name)} aria-describedby={errors.name ? 'device-name-error' : undefined} autoComplete="off" />{errors.name && <span id="device-name-error" className="mt-1 block text-xs text-rose-700">{errors.name}</span>}</label>
          <label className="block text-sm font-medium text-slate-700">IP address<input value={form.ipAddress} onChange={(e) => setForm({ ...form, ipAddress: e.target.value })} className={fieldClass('ipAddress')} inputMode="decimal" placeholder="192.168.1.1" aria-invalid={Boolean(errors.ipAddress)} aria-describedby={errors.ipAddress ? 'device-ip-error' : undefined} />{errors.ipAddress && <span id="device-ip-error" className="mt-1 block text-xs text-rose-700">{errors.ipAddress}</span>}</label>
          <label className="block text-sm font-medium text-slate-700">Device type<select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value as DeviceType })} className={fieldClass('type')} aria-invalid={Boolean(errors.type)}><option value="">Select device type</option>{types.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>{errors.type && <span className="mt-1 block text-xs text-rose-700">{errors.type}</span>}</label>
          <fieldset><legend className="text-sm font-medium text-slate-700">Monitoring configuration</legend><div className="mt-2 grid gap-2 sm:grid-cols-2"><label className="flex cursor-pointer items-center gap-2 rounded-xl border border-slate-200 p-3 text-sm"><input type="radio" name="monitoring" checked={form.monitoring === 'enabled'} onChange={() => setForm({ ...form, monitoring: 'enabled' })} />Enable monitoring</label><label className="flex cursor-pointer items-center gap-2 rounded-xl border border-slate-200 p-3 text-sm"><input type="radio" name="monitoring" checked={form.monitoring === 'disabled'} onChange={() => setForm({ ...form, monitoring: 'disabled' })} />Disable monitoring</label></div>{errors.monitoring && <span className="mt-1 block text-xs text-rose-700">{errors.monitoring}</span>}</fieldset>
        </div>
        <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end"><button type="button" onClick={onClose} className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50">Cancel</button><button type="submit" disabled={isSaving} className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60">{isSaving && <span className="size-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />} {isSaving ? 'Saving…' : device ? 'Save changes' : 'Register device'}</button></div>
      </form>
    </div>
  )
}

export function DevicesPage() {
  const [devices, setDevices] = useState<Device[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState<'all' | Device['status']>('all')
  const [monitoring, setMonitoring] = useState<'all' | MonitoringState>('all')
  const [sort, setSort] = useState<'name' | 'status' | 'type'>('name')
  const [page, setPage] = useState(1)
  const [formDevice, setFormDevice] = useState<Device | null | undefined>(undefined)
  const [actionError, setActionError] = useState('')

  const load = async () => {
    setIsLoading(true); setError(''); setActionError('')
    try { setDevices(await getDeviceService().list()) } catch (reason: unknown) { setError(reason instanceof DeviceServiceError ? reason.message : 'Unable to load devices.') } finally { setIsLoading(false) }
  }
  useEffect(() => { void load() }, [])

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    return devices.filter((device) => (!normalized || [device.name, device.ipAddress, typeLabels[device.type]].some((value) => value.toLowerCase().includes(normalized))) && (status === 'all' || device.status === status) && (monitoring === 'all' || device.monitoring === monitoring)).sort((a, b) => sort === 'name' ? a.name.localeCompare(b.name) : sort === 'type' ? typeLabels[a.type].localeCompare(typeLabels[b.type]) : a.status.localeCompare(b.status))
  }, [devices, query, status, monitoring, sort])
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize))
  const visible = filtered.slice((page - 1) * pageSize, page * pageSize)
  useEffect(() => { if (page > totalPages) setPage(totalPages) }, [page, totalPages])

  const toggleMonitoring = async (device: Device) => {
    setActionError('')
    try { const updated = await getDeviceService().setMonitoring(device.id, device.monitoring === 'enabled' ? 'disabled' : 'enabled'); setDevices((current) => current.map((item) => item.id === updated.id ? updated : item)) } catch (reason: unknown) { setActionError(reason instanceof DeviceServiceError ? reason.message : 'Unable to change monitoring state.') }
  }

  const handleSaved = (saved: Device) => { setDevices((current) => current.some((item) => item.id === saved.id) ? current.map((item) => item.id === saved.id ? saved : item) : [saved, ...current]); setFormDevice(undefined); setActionError('') }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 lg:py-10">
      <section className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-end"><div><p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Devices</p><h1 className="text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl">Network devices</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">Register devices, manage their monitoring configuration, and review current status.</p></div><button type="button" onClick={() => setFormDevice(null)} className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800 sm:w-auto"><PlusIcon className="size-4" />Register device</button></section>

      <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5" aria-label="Device filters">
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_repeat(3,auto)_auto]"><label className="relative block"><span className="sr-only">Search devices</span><SearchIcon className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" /><input value={query} onChange={(e) => { setQuery(e.target.value); setPage(1) }} placeholder="Search by name, IP, or type" className="w-full rounded-xl border border-slate-200 py-2.5 pl-9 pr-3 text-sm outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200" /></label><select value={status} onChange={(e) => { setStatus(e.target.value as typeof status); setPage(1) }} className="rounded-xl border border-slate-200 px-3 py-2.5 text-sm"><option value="all">All statuses</option><option value="online">Online</option><option value="offline">Offline</option><option value="unknown">Unknown</option></select><select value={monitoring} onChange={(e) => { setMonitoring(e.target.value as typeof monitoring); setPage(1) }} className="rounded-xl border border-slate-200 px-3 py-2.5 text-sm"><option value="all">All monitoring</option><option value="enabled">Monitoring enabled</option><option value="disabled">Monitoring disabled</option></select><select value={sort} onChange={(e) => setSort(e.target.value as typeof sort)} className="rounded-xl border border-slate-200 px-3 py-2.5 text-sm"><option value="name">Sort: Name</option><option value="status">Sort: Status</option><option value="type">Sort: Type</option></select><button type="button" onClick={() => void load()} className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 px-3 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50" title="Refresh devices"><RefreshIcon className="size-4" />Refresh</button></div>
      </section>

      {actionError && <div className="mt-4"><ErrorState description={actionError} /></div>}
      <section className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        {isLoading ? <LoadingState /> : error ? <div className="p-5"><ErrorState description={error} /></div> : devices.length === 0 ? <div className="p-5"><EmptyState title="No devices registered" description="Register your first network device to begin managing its monitoring configuration." icon={<ServerIcon className="size-5" />} action={<button type="button" onClick={() => setFormDevice(null)} className="rounded-xl bg-slate-950 px-4 py-2 text-sm font-semibold text-white">Register device</button>} /></div> : visible.length === 0 ? <div className="p-5"><EmptyState title="No matching devices" description="Try changing the search or filters." icon={<SearchIcon className="size-5" />} /></div> : <>
          <div className="overflow-x-auto"><table className="w-full min-w-[780px] text-left text-sm"><thead className="border-b border-slate-200 bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500"><tr><th className="px-5 py-3">Device</th><th className="px-5 py-3">IP address</th><th className="px-5 py-3">Type</th><th className="px-5 py-3">Status</th><th className="px-5 py-3">Monitoring</th><th className="px-5 py-3 text-right">Actions</th></tr></thead><tbody className="divide-y divide-slate-100">{visible.map((device) => <tr key={device.id} className="hover:bg-slate-50"><td className="px-5 py-4"><p className="font-semibold text-slate-900">{device.name}</p><p className="mt-1 text-xs text-slate-500">Updated {device.updatedAt}</p></td><td className="px-5 py-4 font-mono text-xs text-slate-700">{device.ipAddress}</td><td className="px-5 py-4 text-slate-700">{typeLabels[device.type]}</td><td className="px-5 py-4"><DeviceStatusBadge status={device.status} /></td><td className="px-5 py-4"><button type="button" onClick={() => void toggleMonitoring(device)} className="rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100" aria-label={`${device.monitoring === 'enabled' ? 'Disable' : 'Enable'} monitoring for ${device.name}`}>{device.monitoring === 'enabled' ? 'Enabled' : 'Disabled'}</button></td><td className="px-5 py-4 text-right"><button type="button" onClick={() => setFormDevice(device)} className="rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100">Edit</button></td></tr>)}</tbody></table></div>
          <div className="flex flex-col gap-3 border-t border-slate-200 px-5 py-4 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between"><span>Showing {filtered.length === 0 ? 0 : (page - 1) * pageSize + 1}–{Math.min(page * pageSize, filtered.length)} of {filtered.length}</span><div className="flex items-center gap-2"><button type="button" disabled={page === 1} onClick={() => setPage((value) => value - 1)} className="rounded-lg border border-slate-200 px-3 py-1.5 font-semibold disabled:cursor-not-allowed disabled:opacity-40">Previous</button><span>Page {page} of {totalPages}</span><button type="button" disabled={page === totalPages} onClick={() => setPage((value) => value + 1)} className="rounded-lg border border-slate-200 px-3 py-1.5 font-semibold disabled:cursor-not-allowed disabled:opacity-40">Next</button></div></div>
        </>}
      </section>
      {formDevice !== undefined && <DeviceForm device={formDevice} onClose={() => setFormDevice(undefined)} onSaved={handleSaved} />}
      <p className="mt-4 flex items-start gap-2 text-xs text-slate-500"><AlertTriangleIcon className="mt-0.5 size-3.5 shrink-0" />Deletion is intentionally unavailable until the Django/DRF contract explicitly supports device deletion.</p>
    </div>
  )
}
