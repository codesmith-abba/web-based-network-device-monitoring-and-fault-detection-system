import { createContext } from 'react'
import type { AuthCredentials, AuthSession } from './types'

export interface AuthContextValue {
  session: AuthSession | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (credentials: AuthCredentials) => Promise<AuthSession>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)
