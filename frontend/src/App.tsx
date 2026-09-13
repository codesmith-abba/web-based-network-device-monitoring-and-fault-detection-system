import { AuthProvider } from './auth/AuthProvider'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { AppShell } from './layouts/AppShell'
import { DashboardPage } from './pages/DashboardPage'
import { LoginPage } from './pages/LoginPage'

function AppContent() {
  const isLoginRoute = window.location.pathname === '/login'

  if (isLoginRoute) return <LoginPage />

  return (
    <ProtectedRoute>
      <AppShell>
        <DashboardPage />
      </AppShell>
    </ProtectedRoute>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App
