import { AuthProvider } from './auth/AuthProvider'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { AppShell } from './layouts/AppShell'
import { DashboardPage } from './pages/DashboardPage'
import { DevicesPage } from './pages/DevicesPage'
import { LoginPage } from './pages/LoginPage'

function AppContent() {
  const path = window.location.pathname
  if (path === '/login') return <LoginPage />
  const page = path === '/devices' ? <DevicesPage /> : <DashboardPage />
  return <ProtectedRoute><AppShell>{page}</AppShell></ProtectedRoute>
}

function App() {
  return <AuthProvider><AppContent /></AuthProvider>
}

export default App
