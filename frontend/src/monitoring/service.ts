import { getDeviceService } from '../devices/service'
import type { Device } from '../devices/types'
import { MonitoringServiceError, type DeviceMonitoringService, type DeviceMonitoringSnapshot, type MonitoringRecord, type MonitoringScenario } from './types'

function scenario(): MonitoringScenario {
  const value = import.meta.env.VITE_MONITORING_SCENARIO
  return value === 'empty' || value === 'partial' || value === 'error' || value === 'loading' ? value : 'populated'
}

const demoHistory: Record<string, MonitoringRecord[]> = {
  'rtr-01': [
    { id: 'rtr-01-1', deviceId: 'rtr-01', timestamp: '2026-09-13T20:00:00Z', reachable: true, latencyMs: 12, packetLossPercent: 0 },
    { id: 'rtr-01-2', deviceId: 'rtr-01', timestamp: '2026-09-13T20:15:00Z', reachable: true, latencyMs: 14, packetLossPercent: 0 },
    { id: 'rtr-01-3', deviceId: 'rtr-01', timestamp: '2026-09-13T20:30:00Z', reachable: true, latencyMs: 18, packetLossPercent: 1 },
    { id: 'rtr-01-4', deviceId: 'rtr-01', timestamp: '2026-09-13T20:45:00Z', reachable: true, latencyMs: 13, packetLossPercent: 0 },
  ],
  'sw-01': [
    { id: 'sw-01-1', deviceId: 'sw-01', timestamp: '2026-09-13T20:00:00Z', reachable: true, latencyMs: 7, packetLossPercent: 0 },
    { id: 'sw-01-2', deviceId: 'sw-01', timestamp: '2026-09-13T20:15:00Z', reachable: true, latencyMs: 9, packetLossPercent: 0 },
    { id: 'sw-01-3', deviceId: 'sw-01', timestamp: '2026-09-13T20:30:00Z', reachable: true, latencyMs: 8, packetLossPercent: 0 },
  ],
}

function buildSnapshot(device: Device): DeviceMonitoringSnapshot {
  const currentScenario = scenario()
  if (currentScenario === 'error') throw new MonitoringServiceError('The temporary monitoring adapter could not load monitoring data.')
  if (currentScenario === 'loading') return new Promise<DeviceMonitoringSnapshot>(() => undefined) as unknown as DeviceMonitoringSnapshot

  const history = currentScenario === 'empty' ? [] : (demoHistory[device.id] ?? [])
  const partialHistory = currentScenario === 'partial' ? history.slice(0, 1) : history
  const latest = partialHistory.at(-1) ?? null
  const snmpMetrics = device.type === 'server'
    ? [{ name: 'CPU utilization', value: null, unit: '%', available: false }, { name: 'Memory utilization', value: null, unit: '%', available: false }]
    : [
        { name: 'Interface traffic', value: null, unit: 'bps', available: false },
        { name: 'Uptime', value: null, unit: 's', available: false },
      ]

  return {
    device,
    latest,
    history: partialHistory,
    snmpMetrics,
    configuration: {
      enabled: device.monitoring === 'enabled',
      intervalSeconds: device.monitoring === 'enabled' ? 60 : null,
      snmpEnabled: false,
      snmpVersion: null,
      availableMetrics: [],
    },
  }
}

const mockService: DeviceMonitoringService = {
  async getSnapshot(deviceId) {
    const devices = await getDeviceService().list()
    const device = devices.find((item) => item.id === deviceId)
    if (!device) throw new MonitoringServiceError('The requested device could not be found.')
    return buildSnapshot(device)
  },
}

export function getMonitoringService(): DeviceMonitoringService {
  if (import.meta.env.VITE_MONITORING_ADAPTER === 'mock') return mockService
  return {
    async getSnapshot() {
      throw new MonitoringServiceError('Device monitoring is not connected yet. Configure the Django/DRF monitoring adapter when the backend contract is available.', 'MONITORING_NOT_CONFIGURED')
    },
  }
}
