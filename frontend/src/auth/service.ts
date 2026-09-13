import { AuthError } from './types'
import type { AuthCredentials, AuthService, AuthSession } from './types'

const SESSION_STORAGE_KEY = 'netwatch.auth.session'
const MOCK_SESSION_DURATION_MS = 8 * 60 * 60 * 1000

function readStoredSession(): AuthSession | null {
  const raw = sessionStorage.getItem(SESSION_STORAGE_KEY)
  if (!raw) return null

  try {
    const session = JSON.parse(raw) as AuthSession
    if (!session.user?.id || !session.user?.username || session.expiresAt <= Date.now()) {
      sessionStorage.removeItem(SESSION_STORAGE_KEY)
      return null
    }
    return session
  } catch {
    sessionStorage.removeItem(SESSION_STORAGE_KEY)
    return null
  }
}

function storeSession(session: AuthSession) {
  sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session))
}

const mockAuthService: AuthService = {
  async login(credentials) {
    // Development-only adapter. It deliberately does not represent a backend contract.
    await new Promise((resolve) => window.setTimeout(resolve, 350))
    if (!credentials.identifier.trim() || !credentials.password) {
      throw new AuthError('INVALID_CREDENTIALS', 'Enter a valid username or email and password.')
    }

    const username = credentials.identifier.includes('@')
      ? credentials.identifier.split('@')[0]
      : credentials.identifier

    const session: AuthSession = {
      user: {
        id: 'mock-administrator',
        username,
        email: credentials.identifier.includes('@') ? credentials.identifier : undefined,
        role: 'administrator',
      },
      expiresAt: Date.now() + MOCK_SESSION_DURATION_MS,
    }
    storeSession(session)
    return session
  },

  async logout() {
    sessionStorage.removeItem(SESSION_STORAGE_KEY)
  },

  async getSession() {
    return readStoredSession()
  },
}

const unconfiguredAuthService: AuthService = {
  async login() {
    throw new AuthError(
      'AUTH_NOT_CONFIGURED',
      'Authentication is not connected to the backend yet. Configure the production authentication adapter before deployment.',
    )
  },
  async logout() {
    sessionStorage.removeItem(SESSION_STORAGE_KEY)
  },
  async getSession() {
    return readStoredSession()
  },
}

export function getAuthService(): AuthService {
  return import.meta.env.VITE_AUTH_ADAPTER === 'mock'
    ? mockAuthService
    : unconfiguredAuthService
}
