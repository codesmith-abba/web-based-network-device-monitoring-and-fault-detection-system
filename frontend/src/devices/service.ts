import { DeviceServiceError, type Device, type DeviceRegistrationInput, type DeviceService, type DeviceListScenario, type MonitoringState } from './types'

const initialDevices: Device[] = [
  { id: 'rtr-01', name: 'Core Router', ipAddress: '10.0.0.1', type: 'router', status: 'online', monitoring: 'enabled', createdAt: '2026-09-01', updatedAt: '2026-09-13' },
  { id: 'sw-01', name: 'Main Switch', ipAddress: '10.0.0.10', type: 'switch', status: 'online', monitoring: 'enabled', createdAt: '2026-09-02', updatedAt: '2026-09-13' },
  { id: 'srv-01', name: 'Application Server', ipAddress: '10.0.0.20', type: 'server', status: 'offline', monitoring: 'enabled', createdAt: '2026-09-03', updatedAt: '2026-09-13' },
  { id: 'ap-01', name: 'Office Access Point', ipAddress: '10.0.0.30', type: 'access-point', status: 'online', monitoring: 'enabled', createdAt: '2026-09-04', updatedAt: '2026-09-13' },
  { id: 'fw-01', name: 'Perimeter Firewall', ipAddress: '10.0.0.254', type: 'firewall', status: 'unknown', monitoring: 'disabled', createdAt: '2026-09-05', updatedAt: '2026-09-12' },
]

function scenario(): DeviceListScenario {
  const value = import.meta.env.VITE_DEVICES_SCENARIO
  return value === 'empty' || value === 'partial' || value === 'error' || value === 'loading' ? value : 'populated'
}

function cloneDevices(): Device[] { return initialDevices.map((device) => ({ ...device })) }

function validate(input: DeviceRegistrationInput) {
  if (!input.name.trim()) throw new DeviceServiceError('Device name is required.', 'DEVICE_VALIDATION_ERROR')
  if (!input.ipAddress.trim()) throw new DeviceServiceError('IP address is required.', 'DEVICE_VALIDATION_ERROR')
  if (!isValidIp(input.ipAddress)) throw new DeviceServiceError('Enter a valid IPv4 address.', 'DEVICE_VALIDATION_ERROR')
  if (!input.type) throw new DeviceServiceError('Device type is required.', 'DEVICE_VALIDATION_ERROR')
}

export function isValidIp(value: string): boolean {
  const parts = value.trim().split('.')
  return parts.length === 4 && parts.every((part) => /^\d+$/.test(part) && Number(part) >= 0 && Number(part) <= 255)
}

function mockService(): DeviceService {
  const store = cloneDevices()
  return {
    async list() {
      const currentScenario = scenario()
      if (currentScenario === 'loading') return new Promise<Device[]>(() => undefined)
      if (currentScenario === 'error') throw new DeviceServiceError('The temporary device adapter could not load devices.')
      if (currentScenario === 'empty') return []
      if (currentScenario === 'partial') return store.slice(0, 2)
      return [...store]
    },
    async create(input) {
      validate(input)
      const now = new Date().toISOString().slice(0, 10)
      const device: Device = { id: `device-${Date.now()}`, name: input.name.trim(), ipAddress: input.ipAddress.trim(), type: input.type as Device['type'], status: 'unknown', monitoring: input.monitoring, createdAt: now, updatedAt: now }
      store.unshift(device)
      return { ...device }
    },
    async update(id, input) {
      validate(input)
      const index = store.findIndex((device) => device.id === id)
      if (index < 0) throw new DeviceServiceError('The requested device could not be found.')
      const updated = { ...store[index], name: input.name.trim(), ipAddress: input.ipAddress.trim(), type: input.type as Device['type'], monitoring: input.monitoring, updatedAt: new Date().toISOString().slice(0, 10) }
      store[index] = updated
      return { ...updated }
    },
    async setMonitoring(id, monitoring: MonitoringState) {
      const index = store.findIndex((device) => device.id === id)
      if (index < 0) throw new DeviceServiceError('The requested device could not be found.')
      store[index] = { ...store[index], monitoring, updatedAt: new Date().toISOString().slice(0, 10) }
      return { ...store[index] }
    },
  }
}

const service: DeviceService = {
  async list() {
    if (import.meta.env.VITE_DEVICES_ADAPTER === 'mock') return mockService().list()
    throw new DeviceServiceError('Device management is not connected yet. Configure the Django/DRF device adapter when the backend contract is available.', 'DEVICES_NOT_CONFIGURED')
  },
  async create(input) {
    if (import.meta.env.VITE_DEVICES_ADAPTER === 'mock') return mockService().create(input)
    throw new DeviceServiceError('Device registration is not connected yet. No backend endpoint has been assumed.', 'DEVICES_NOT_CONFIGURED')
  },
  async update(id, input) {
    if (import.meta.env.VITE_DEVICES_ADAPTER === 'mock') return mockService().update(id, input)
    throw new DeviceServiceError('Device editing is not connected yet. No backend endpoint has been assumed.', 'DEVICES_NOT_CONFIGURED')
  },
  async setMonitoring(id, monitoring) {
    if (import.meta.env.VITE_DEVICES_ADAPTER === 'mock') return mockService().setMonitoring(id, monitoring)
    throw new DeviceServiceError('Monitoring controls are not connected yet. No backend endpoint has been assumed.', 'DEVICES_NOT_CONFIGURED')
  },
}

export function getDeviceService(): DeviceService { return service }
