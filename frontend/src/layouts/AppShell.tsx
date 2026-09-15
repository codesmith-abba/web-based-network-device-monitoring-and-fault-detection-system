import { useState } from 'react'
import type { ReactNode } from 'react'
import { useAuth } from '../auth/useAuth'
import { ActivityIcon, AlertTriangleIcon, BellIcon, ChevronRightIcon, HistoryIcon, LayoutDashboardIcon, MenuIcon, ServerIcon, SettingsIcon, ShieldIcon, XIcon } from '../components/icons'
import type { NavigationItem } from '../types/navigation'

interface AppShellProps { children: ReactNode }
const navigation: NavigationItem[] = [
  { key: 'dashboard', label: 'Dashboard', description: 'Network overview', available: true },
  { key: 'devices', label: 'Devices', description: 'Manage network devices', available: true },
  { key: 'faults', label: 'Faults', description: 'Active and resolved faults', available: true },
  { key: 'monitoring', label: 'Monitoring History', description: 'Historical measurements', available: false },
  { key: 'notifications', label: 'Notifications', description: 'Monitoring alerts', available: false },
  { key: 'settings', label: 'Settings', description: 'System configuration', available: false },
]
const icons = { dashboard: LayoutDashboardIcon, devices: ServerIcon, faults: AlertTriangleIcon, monitoring: HistoryIcon, notifications: BellIcon, settings: SettingsIcon }

export function AppShell({ children }: AppShellProps) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const { session, logout } = useAuth()
  const handleLogout = async () => { await logout(); window.location.replace('/login') }
  const username = session?.user.username ?? 'Administrator'
  const initials = username.slice(0, 2).toUpperCase()
  const currentPath = window.location.pathname
  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      {mobileOpen && <button className="fixed inset-0 z-40 bg-slate-950/40 lg:hidden" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />}
      <aside className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-slate-200 bg-white transition-transform lg:translate-x-0 ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex h-20 items-center justify-between border-b border-slate-200 px-6"><div className="flex items-center gap-3"><div className="grid size-10 place-items-center rounded-xl bg-slate-950 text-white shadow-sm"><ActivityIcon className="size-5" /></div><div><p className="text-sm font-semibold tracking-tight text-slate-950">NetWatch</p><p className="text-xs text-slate-500">Network Monitoring</p></div></div><button className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 lg:hidden" onClick={() => setMobileOpen(false)} aria-label="Close navigation"><XIcon className="size-5" /></button></div>
        <nav className="flex-1 space-y-1 px-3 py-5" aria-label="Main navigation"><p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400">Workspace</p>{navigation.map((item) => { const Icon = icons[item.key]; const active = item.key === 'dashboard' ? currentPath === '/' : item.key === 'devices' ? currentPath === '/devices' : item.key === 'faults' ? currentPath === '/faults' : false; return <button key={item.key} type="button" disabled={!item.available} title={item.available ? item.description : `${item.label} will be implemented in a later phase`} className={`group flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left transition ${active ? 'bg-slate-950 text-white shadow-sm' : item.available ? 'text-slate-600 hover:bg-slate-100' : 'cursor-not-allowed text-slate-400'}`} onClick={() => { if (item.available) { window.location.replace(item.key === 'devices' ? '/devices' : item.key === 'faults' ? '/faults' : '/'); setMobileOpen(false) } }}><Icon className="size-[18px] shrink-0" /><span className="min-w-0 flex-1"><span className="block text-sm font-medium">{item.label}</span>{!item.available && <span className="mt-0.5 block text-[10px] text-slate-400">Coming soon</span>}</span>{active && <ChevronRightIcon className="size-4 opacity-60" />}</button> })}</nav>
        <div className="border-t border-slate-200 p-4"><div className="flex items-center gap-3 rounded-xl bg-slate-50 p-3"><div className="grid size-9 place-items-center rounded-lg bg-white text-slate-700 ring-1 ring-slate-200"><ShieldIcon className="size-4" /></div><div className="min-w-0 flex-1"><p className="truncate text-xs font-semibold text-slate-800">{username}</p><p className="truncate text-[11px] text-slate-500">Administrator</p></div><button type="button" onClick={handleLogout} className="rounded-lg px-2 py-1.5 text-[11px] font-medium text-slate-500 hover:bg-white hover:text-slate-900" aria-label="Sign out">Sign out</button></div></div>
      </aside>
      <div className="lg:pl-72"><header className="sticky top-0 z-30 flex h-20 items-center justify-between border-b border-slate-200 bg-white/95 px-4 backdrop-blur sm:px-6 lg:px-8"><div className="flex items-center gap-3"><button className="rounded-xl p-2 text-slate-600 hover:bg-slate-100 lg:hidden" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><MenuIcon className="size-5" /></button><div><p className="text-sm font-semibold text-slate-950">Network Operations</p><p className="hidden text-xs text-slate-500 sm:block">Centralized monitoring and fault visibility</p></div></div><div className="flex items-center gap-2"><div className="hidden items-center gap-2 rounded-full border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 sm:flex"><span className="size-1.5 rounded-full bg-emerald-500" /> System ready</div><button className="relative rounded-xl p-2.5 text-slate-500 hover:bg-slate-100" aria-label="Notifications"><BellIcon className="size-5" /></button><div className="ml-1 grid size-9 place-items-center rounded-full bg-slate-200 text-xs font-semibold text-slate-700" aria-label={`${username} profile`}>{initials}</div></div></header><main className="min-h-[calc(100vh-5rem)]">{children}</main></div>
    </div>
  )
}
