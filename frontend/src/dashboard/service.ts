import { DashboardError, type DashboardData, type DashboardScenario } from './types'

const mockData: DashboardData = {
  summary: { totalDevices: 12, onlineDevices: 9, offlineDevices: 3, activeFaults: 4 },
  deviceHealth: [
    { id: 'rtr-01', name: 'Core Router', address: '10.0.0.1', type: 'Router', status: 'online', availability: 99.98, latencyMs: 8, packetLossPercent: 0 },
    { id: 'sw-01', name: 'Main Switch', address: '10.0.0.10', type: 'Switch', status: 'online', availability: 99.91, latencyMs: 4, packetLossPercent: 0.2 },
    { id: 'srv-01', name: 'Application Server', address: '10.0.0.20', type: 'Server', status: 'offline' },
    { id: 'ap-01', name: 'Office Access Point', address: '10.0.0.30', type: 'Access Point', status: 'online', availability: 99.7, latencyMs: 12, packetLossPercent: 0.4 },
    { id: 'sw-02', name: 'Branch Switch', address: '10.0.1.10', type: 'Switch', status: 'offline' },
  ],
  activeFaults: [
    { id: 'fault-01', deviceName: 'Application Server', title: 'Device unreachable', severity: 'critical', detectedAt: 'Today, 21:42' },
    { id: 'fault-02', deviceName: 'Branch Switch', title: 'Repeated connection failures', severity: 'high', detectedAt: 'Today, 21:18' },
    { id: 'fault-03', deviceName: 'Office Access Point', title: 'High packet loss', severity: 'medium', detectedAt: 'Today, 20:55' },
    { id: 'fault-04', deviceName: 'Main Switch', title: 'Elevated latency', severity: 'low', detectedAt: 'Today, 20:31' },
  ],
  monitoringTrend: [
    { label: '08:00', availabilityPercent: 99.2, latencyMs: 11, packetLossPercent: 0.4 },
    { label: '10:00', availabilityPercent: 99.4, latencyMs: 9, packetLossPercent: 0.3 },
    { label: '12:00', availabilityPercent: 99.1, latencyMs: 13, packetLossPercent: 0.6 },
    { label: '14:00', availabilityPercent: 98.9, latencyMs: 16, packetLossPercent: 0.8 },
    { label: '16:00', availabilityPercent: 99.3, latencyMs: 12, packetLossPercent: 0.4 },
    { label: '18:00', availabilityPercent: 99.5, latencyMs: 10, packetLossPercent: 0.2 },
  ],
}

const emptyData: DashboardData = {
  summary: { totalDevices: 0, onlineDevices: 0, offlineDevices: 0, activeFaults: 0 },
  deviceHealth: [],
  activeFaults: [],
}

const partialData: DashboardData = {
  summary: { totalDevices: 12, onlineDevices: 9, offlineDevices: 3, activeFaults: 4 },
  deviceHealth: mockData.deviceHealth.slice(0, 3),
  activeFaults: [],
}

function getScenario(): DashboardScenario {
  const value = import.meta.env.VITE_DASHBOARD_SCENARIO
  if (value === 'empty' || value === 'partial' || value === 'error' || value === 'loading') return value
  return 'populated'
}

function getMockDashboardData(): Promise<DashboardData> {
  const scenario = getScenario()

  if (scenario === 'loading') return new Promise(() => undefined)
  if (scenario === 'error') return Promise.reject(new DashboardError('The temporary monitoring adapter could not load dashboard data.'))
  if (scenario === 'empty') return Promise.resolve(emptyData)
  if (scenario === 'partial') return Promise.resolve(partialData)
  return Promise.resolve(mockData)
}

export async function getDashboardData(): Promise<DashboardData> {
  if (import.meta.env.VITE_DASHBOARD_ADAPTER === 'mock') return getMockDashboardData()

  throw new DashboardError(
    'Dashboard monitoring data is not connected yet. Configure a Django/DRF dashboard adapter when the backend contract is available.',
    'DASHBOARD_NOT_CONFIGURED',
  )
}
