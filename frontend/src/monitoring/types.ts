import type { Device } from '../devices/types'

export interface MonitoringRecord {
  id: string
  deviceId: string
  timestamp: string
  reachable: boolean | null
  latencyMs: number | null
  packetLossPercent: number | null
}

export interface SnmpMetric {
  name: string
  value: string | number | null
  unit?: string
  available: boolean
}

export interface MonitoringConfiguration {
  enabled: boolean
  intervalSeconds: number | null
  snmpEnabled: boolean
  snmpVersion: string | null
  availableMetrics: string[]
}

export interface DeviceMonitoringSnapshot {
  device: Device
  latest: MonitoringRecord | null
  history: MonitoringRecord[]
  snmpMetrics: SnmpMetric[]
  configuration: MonitoringConfiguration
}

export type MonitoringScenario = 'populated' | 'empty' | 'partial' | 'error' | 'loading'

export class MonitoringServiceError extends Error {
  readonly code: 'MONITORING_NOT_CONFIGURED' | 'MONITORING_API_ERROR'

  constructor(message: string, code: MonitoringServiceError['code'] = 'MONITORING_API_ERROR') {
    super(message)
    this.name = 'MonitoringServiceError'
    this.code = code
  }
}

export interface DeviceMonitoringService {
  getSnapshot: (deviceId: string) => Promise<DeviceMonitoringSnapshot>
}
