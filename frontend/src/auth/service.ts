import { apiRequest, clearStoredToken, setStoredToken } from '../api/client'
import { AuthError } from './types'
import type { AuthService, AuthSession } from './types'

interface LoginResponse {
  token: string
  user: { id: number; username: string; email: string }
}

interface MeResponse {
  id: number
  username: string
  email: string
}

const MOCK_SESSION_STORAGE_KEY = 'netwatch.auth.session.mock'
const MOCK_SESSION_DURATION_MS = 8 * 60 * 60 * 1000

function readMockSession(): AuthSession | null {
  const raw = sessionStorage.getItem(MOCK_SESSION_STORAGE_KEY)
  if (!raw) return null
  try {
    const session = JSON.parse(raw) as AuthSession
    if (!session.user?.id || !session.user?.username || session.expiresAt <= Date.now()) {
      sessionStorage.removeItem(MOCK_SESSION_STORAGE_KEY)
      return null
    }
    return session
  } catch {
    sessionStorage.removeItem(MOCK_SESSION_STORAGE_KEY)
    return null
  }
}

const mockAuthService: AuthService = {
  async login(credentials) {
    await new Promise((resolve) => window.setTimeout(resolve, 350))
    if (!credentials.identifier.trim() || !credentials.password) throw new AuthError('INVALID_CREDENTIALS', 'Enter a valid username or email and password.')
    const username = credentials.identifier.includes('@') ? credentials.identifier.split('@')[0] : credentials.identifier
    const session: AuthSession = { user: { id: 'mock-administrator', username, email: credentials.identifier.includes('@') ? credentials.identifier : undefined, role: 'administrator' }, expiresAt: Date.now() + MOCK_SESSION_DURATION_MS }
    sessionStorage.setItem(MOCK_SESSION_STORAGE_KEY, JSON.stringify(session))
    return session
  },
  async logout() { sessionStorage.removeItem(MOCK_SESSION_STORAGE_KEY) },
  async getSession() { return readMockSession() },
}

const apiAuthService: AuthService = {
  async login(credentials) {
    if (!credentials.identifier.trim() || !credentials.password) throw new AuthError('INVALID_CREDENTIALS', 'Enter a valid username or email and password.')
    try {
      const response = await apiRequest<LoginResponse>('/auth/login/', {
        method: 'POST',
        body: JSON.stringify({ username: credentials.identifier.trim(), password: credentials.password }),
      })
      setStoredToken(response.token)
      return {
        user: { id: String(response.user.id), username: response.user.username, email: response.user.email || undefined, role: 'administrator' },
        expiresAt: Date.now() + 8 * 60 * 60 * 1000,
      }
    } catch (error) {
      clearStoredToken()
      if (error instanceof Error && 'status' in error && (error as { status: number }).status === 400) throw new AuthError('INVALID_CREDENTIALS', 'The username or password is incorrect.')
      throw new AuthError('AUTH_SERVICE_UNAVAILABLE', error instanceof Error ? error.message : 'Authentication failed.')
    }
  },
  async logout() {
    if (!sessionStorage.getItem('netwatch.auth.token')) return
    try { await apiRequest('/auth/logout/', { method: 'POST' }) } finally { clearStoredToken() }
  },
  async getSession() {
    if (!sessionStorage.getItem('netwatch.auth.token')) return null
    try {
      const user = await apiRequest<MeResponse>('/auth/me/')
      return { user: { id: String(user.id), username: user.username, email: user.email || undefined, role: 'administrator' }, expiresAt: Date.now() + 8 * 60 * 60 * 1000 }
    } catch {
      clearStoredToken()
      return null
    }
  },
}

export function getAuthService(): AuthService {
  return import.meta.env.VITE_AUTH_ADAPTER === 'mock' ? mockAuthService : apiAuthService
}
