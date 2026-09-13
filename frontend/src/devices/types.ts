export type DeviceStatus = 'online' | 'offline' | 'unknown'
export type MonitoringState = 'enabled' | 'disabled'
export type DeviceType = 'router' | 'switch' | 'server' | 'access-point' | 'firewall' | 'other'

export interface Device {
  id: string
  name: string
  ipAddress: string
  type: DeviceType
  status: DeviceStatus
  monitoring: MonitoringState
  createdAt: string
  updatedAt: string
}

export interface DeviceRegistrationInput {
  name: string
  ipAddress: string
  type: DeviceType | ''
  monitoring: MonitoringState
}

export type DeviceListScenario = 'populated' | 'empty' | 'partial' | 'error' | 'loading'

export class DeviceServiceError extends Error {
  readonly code: 'DEVICES_NOT_CONFIGURED' | 'DEVICES_API_ERROR' | 'DEVICE_VALIDATION_ERROR'

  constructor(message: string, code: DeviceServiceError['code'] = 'DEVICES_API_ERROR') {
    super(message)
    this.name = 'DeviceServiceError'
    this.code = code
  }
}

export interface DeviceService {
  list: () => Promise<Device[]>
  create: (input: DeviceRegistrationInput) => Promise<Device>
  update: (id: string, input: DeviceRegistrationInput) => Promise<Device>
  setMonitoring: (id: string, monitoring: MonitoringState) => Promise<Device>
}
