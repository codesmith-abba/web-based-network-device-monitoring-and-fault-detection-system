import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { AuthContext } from './auth-context'
import { getAuthService } from './service'
import type { AuthCredentials, AuthSession } from './types'

const authService = getAuthService()

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let active = true

    authService.getSession()
      .then((storedSession) => {
        if (active) setSession(storedSession)
      })
      .finally(() => {
        if (active) setIsLoading(false)
      })

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    if (!session) return

    const remainingMs = session.expiresAt - Date.now()
    if (remainingMs <= 0) {
      void authService.logout().finally(() => setSession(null))
      return
    }

    const timer = window.setTimeout(() => {
      void authService.logout().finally(() => setSession(null))
    }, remainingMs)

    return () => window.clearTimeout(timer)
  }, [session])

  const login = useCallback(async (credentials: AuthCredentials) => {
    const nextSession = await authService.login(credentials)
    setSession(nextSession)
    return nextSession
  }, [])

  const logout = useCallback(async () => {
    await authService.logout()
    setSession(null)
  }, [])

  const value = useMemo(() => ({
    session,
    isLoading,
    isAuthenticated: session !== null,
    login,
    logout,
  }), [isLoading, login, logout, session])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
