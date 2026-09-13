export interface AuthCredentials {
  identifier: string
  password: string
}

export interface AuthUser {
  id: string
  username: string
  email?: string
  role: 'administrator'
}

export interface AuthSession {
  user: AuthUser
  expiresAt: number
}

export type AuthErrorCode =
  | 'INVALID_CREDENTIALS'
  | 'AUTH_SERVICE_UNAVAILABLE'
  | 'AUTH_NOT_CONFIGURED'
  | 'SESSION_EXPIRED'
  | 'SESSION_INVALID'

export class AuthError extends Error {
  readonly code: AuthErrorCode

  constructor(code: AuthErrorCode, message: string) {
    super(message)
    this.name = 'AuthError'
    this.code = code
  }
}

export interface AuthService {
  login(credentials: AuthCredentials): Promise<AuthSession>
  logout(): Promise<void>
  getSession(): Promise<AuthSession | null>
}
