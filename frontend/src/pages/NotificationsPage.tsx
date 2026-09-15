import { useCallback, useEffect, useMemo, useState } from 'react'
import { BellIcon, RefreshIcon } from '../components/icons'
import { getNotificationService } from '../notifications/service'
import type { FaultNotification, NotificationSeverity } from '../notifications/types'

const severityLabel: Record<NotificationSeverity, string> = { critical: 'Critical', high: 'High', medium: 'Medium', low: 'Low' }
const faultTypeLabel = (value: string) => value.replaceAll('_', ' ').toLowerCase().replace(/(^| )\S/g, (letter) => letter.toUpperCase())

function SeverityBadge({ severity }: { severity: NotificationSeverity }) {
  const symbol = severity === 'critical' ? '!!' : severity === 'high' ? '!' : severity === 'medium' ? '•' : '·'
  return <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700"><span aria-hidden="true">{symbol}</span>{severityLabel[severity]}</span>
}

export function NotificationsPage() {
  const service = useMemo(() => getNotificationService(), [])
  const [notifications, setNotifications] = useState<FaultNotification[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [selected, setSelected] = useState<FaultNotification | null>(null)

  const load = useCallback(async (refresh = false) => {
    if (refresh) setLoading(true)
    setError(null)
    try {
      const result = await service.list()
      setNotifications(result.notifications)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Notifications could not be loaded.')
    } finally {
      setLoading(false)
    }
  }, [service])

  useEffect(() => {
    let cancelled = false
    const run = async () => {
      try {
        const result = await service.list()
        if (!cancelled) setNotifications(result.notifications)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Notifications could not be loaded.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void run()
    return () => { cancelled = true }
  }, [service])

  const unreadCount = notifications.filter((notification) => notification.status === 'unread').length
  const mockEnabled = import.meta.env.VITE_NOTIFICATIONS_ADAPTER === 'mock'

  const markRead = async (notification: FaultNotification) => {
    setActionError(null)
    try {
      const updated = await service.markAsRead(notification.id)
      setNotifications((items) => items.map((item) => item.id === updated.id ? updated : item))
      setSelected(updated)
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'The notification could not be marked as read.')
    }
  }

  return <section className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 lg:px-8">
    <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
      <div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Notifications</p><h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">Detected fault alerts</h1><p className="mt-1 max-w-2xl text-sm text-slate-500">Review fault notifications generated from the monitoring system. External email, SMS, and push delivery are not assumed here.</p></div>
      <button type="button" onClick={() => void load(true)} disabled={loading} className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"><RefreshIcon className="size-4" />Refresh</button>
    </div>

    {mockEnabled && <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-900">Development adapter active: notifications are derived from existing fault fixtures and are not live backend notifications.</div>}
    {actionError && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{actionError}</div>}

    <div className="grid gap-4 sm:grid-cols-2"><div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Total notifications</p><p className="mt-2 text-2xl font-semibold text-slate-950">{loading ? '—' : notifications.length}</p></div><div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Unread</p><p className="mt-2 text-2xl font-semibold text-slate-950">{loading ? '—' : unreadCount}</p></div></div>

    {loading ? <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-sm text-slate-500">Loading notifications…</div> : error ? <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-8 text-center"><p className="text-sm font-semibold text-red-900">Notifications unavailable</p><p className="mt-1 text-sm text-red-700">{error}</p><button type="button" onClick={() => void load(true)} className="mt-4 rounded-xl bg-slate-950 px-4 py-2 text-sm font-medium text-white">Try again</button></div> : notifications.length === 0 ? <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center"><BellIcon className="mx-auto size-8 text-slate-400" /><p className="mt-3 text-sm font-semibold text-slate-900">No notifications</p><p className="mt-1 text-sm text-slate-500">There are no detected fault notifications to review.</p></div> : <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"><div className="overflow-x-auto"><table className="min-w-[760px] w-full text-left"><thead className="border-b border-slate-200 bg-slate-50"><tr>{['Fault', 'Device', 'Severity', 'Detected', 'Status', ''].map((heading) => <th key={heading} className="px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">{heading}</th>)}</tr></thead><tbody className="divide-y divide-slate-100">{notifications.map((notification) => <tr key={notification.id} className={notification.status === 'unread' ? 'bg-slate-50/60' : ''}><td className="px-5 py-4"><p className="text-sm font-semibold text-slate-900">{faultTypeLabel(notification.faultType)}</p><p className="mt-0.5 text-xs text-slate-500">{notification.description ?? 'Detected network fault'}</p></td><td className="px-5 py-4 text-sm text-slate-700">{notification.deviceName}</td><td className="px-5 py-4"><SeverityBadge severity={notification.severity} /></td><td className="px-5 py-4 text-sm text-slate-600">{new Date(notification.detectedAt).toLocaleString()}</td><td className="px-5 py-4 text-sm font-medium text-slate-700">{notification.status === 'unread' ? 'Unread' : 'Read'}</td><td className="px-5 py-4 text-right"><button type="button" onClick={() => setSelected(notification)} className="rounded-lg px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100">Details</button></td></tr>)}</tbody></table></div></div>}

    {selected && <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/40 p-4" role="dialog" aria-modal="true" aria-labelledby="notification-title"><div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Fault notification</p><h2 id="notification-title" className="mt-1 text-lg font-semibold text-slate-950">{faultTypeLabel(selected.faultType)}</h2></div><SeverityBadge severity={selected.severity} /></div><dl className="mt-6 grid gap-4 sm:grid-cols-2"><div><dt className="text-xs text-slate-500">Affected device</dt><dd className="mt-1 text-sm font-medium text-slate-900">{selected.deviceName}</dd></div><div><dt className="text-xs text-slate-500">Detected</dt><dd className="mt-1 text-sm font-medium text-slate-900">{new Date(selected.detectedAt).toLocaleString()}</dd></div><div><dt className="text-xs text-slate-500">Notification status</dt><dd className="mt-1 text-sm font-medium text-slate-900">{selected.status === 'unread' ? 'Unread' : 'Read'}</dd></div></dl><p className="mt-5 rounded-xl bg-slate-50 p-4 text-sm text-slate-600">{selected.description ?? 'No additional fault description is available.'}</p><div className="mt-6 flex justify-end gap-2"><button type="button" onClick={() => setSelected(null)} className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700">Close</button>{selected.status === 'unread' && <button type="button" onClick={() => void markRead(selected)} className="rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white">Mark as read</button>}</div></div></div>}
  </section>
}
