import { useEffect } from 'react'
import type { ReactNode } from 'react'
import { useAuth } from './useAuth'

interface ProtectedRouteProps {
  children: ReactNode
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      window.location.replace(`/login?next=${encodeURIComponent(window.location.pathname)}`)
    }
  }, [isAuthenticated, isLoading])

  if (isLoading || !isAuthenticated) {
    return (
      <main className="grid min-h-screen place-items-center bg-slate-50 px-6" aria-live="polite">
        <div className="text-center">
          <div className="mx-auto mb-4 size-8 animate-spin rounded-full border-2 border-slate-300 border-t-slate-950" aria-hidden="true" />
          <p className="text-sm font-medium text-slate-700">Checking your session…</p>
        </div>
      </main>
    )
  }

  return <>{children}</>
}
