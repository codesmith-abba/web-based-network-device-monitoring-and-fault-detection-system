import { AuthProvider } from './auth/AuthProvider'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { AppShell } from './layouts/AppShell'
import { DashboardPage } from './pages/DashboardPage'
import { DeviceDetailsPage } from './pages/DeviceDetailsPage'
import { DevicesPage } from './pages/DevicesPage'
import { FaultsPage } from './pages/FaultsPage'
import { LoginPage } from './pages/LoginPage'

function AppContent() {
  const path = window.location.pathname
  if (path === '/login') return <LoginPage />
  const deviceDetailsMatch = path.match(/^\/devices\/([^/]+)$/)
  const page = path === '/devices' ? <DevicesPage /> : path === '/faults' ? <FaultsPage /> : deviceDetailsMatch ? <DeviceDetailsPage deviceId={decodeURIComponent(deviceDetailsMatch[1])} /> : <DashboardPage />
  return <ProtectedRoute><AppShell>{page}</AppShell></ProtectedRoute>
}

function App() {
  return <AuthProvider><AppContent /></AuthProvider>
}

export default App
