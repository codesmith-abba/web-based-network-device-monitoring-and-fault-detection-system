export type DeviceStatus = 'online' | 'offline' | 'unknown'

export type FaultSeverity = 'critical' | 'high' | 'medium' | 'low'

export interface DashboardSummary {
  totalDevices: number
  onlineDevices: number
  offlineDevices: number
  activeFaults: number
}

export interface DeviceHealthItem {
  id: string
  name: string
  address: string
  type: string
  status: DeviceStatus
  availability?: number
  latencyMs?: number
  packetLossPercent?: number
}

export interface ActiveFaultItem {
  id: string
  deviceName: string
  title: string
  severity: FaultSeverity
  detectedAt: string
  description?: string
}

export interface MonitoringTrendPoint {
  label: string
  availabilityPercent?: number
  latencyMs?: number
  packetLossPercent?: number
}

export interface DashboardData {
  summary: DashboardSummary
  deviceHealth: DeviceHealthItem[]
  activeFaults: ActiveFaultItem[]
  monitoringTrend?: MonitoringTrendPoint[]
}

export type DashboardScenario = 'populated' | 'empty' | 'partial' | 'error' | 'loading'

export class DashboardError extends Error {
  readonly code: 'DASHBOARD_NOT_CONFIGURED' | 'DASHBOARD_API_ERROR'

  constructor(message: string, code: DashboardError['code'] = 'DASHBOARD_API_ERROR') {
    super(message)
    this.name = 'DashboardError'
    this.code = code
  }
}
