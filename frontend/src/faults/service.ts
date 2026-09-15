import { getDeviceService } from '../devices/service'
import { FaultServiceError, type FaultEvent, type FaultListResult, type FaultService, type FaultScenario } from './types'

function scenario(): FaultScenario {
  const value = import.meta.env.VITE_FAULTS_SCENARIO
  return value === 'empty' || value === 'partial' || value === 'error' || value === 'loading' ? value : 'populated'
}

const fixtures: FaultEvent[] = [
  {
    id: 'fault-fixture-01', deviceId: 'rtr-01', deviceName: 'Core Router', faultType: 'HIGH_LATENCY', severity: 'high',
    detectedAt: '2026-09-15T01:15:00Z', status: 'active', description: 'Latency exceeded the configured monitoring threshold.',
  },
  {
    id: 'fault-fixture-02', deviceId: 'sw-01', deviceName: 'Access Switch', faultType: 'HIGH_PACKET_LOSS', severity: 'medium',
    detectedAt: '2026-09-15T00:45:00Z', status: 'acknowledged', description: 'Packet loss exceeded the configured monitoring threshold.',
  },
  {
    id: 'fault-fixture-03', deviceId: 'srv-01', deviceName: 'Application Server', faultType: 'DEVICE_UNREACHABLE', severity: 'critical',
    detectedAt: '2026-09-14T23:30:00Z', status: 'resolved', resolvedAt: '2026-09-15T00:05:00Z', description: 'The monitoring probe could not reach the device after repeated attempts.',
  },
]

let store = fixtures.map((fault) => ({ ...fault }))

async function validateDeviceIds(faults: FaultEvent[]): Promise<FaultEvent[]> {
  const devices = await getDeviceService().list()
  return faults.map((fault) => {
    const device = devices.find((item) => item.id === fault.deviceId)
    return device ? { ...fault, deviceName: device.name } : fault
  })
}

const mockService: FaultService = {
  async list(): Promise<FaultListResult> {
    const currentScenario = scenario()
    if (currentScenario === 'error') throw new FaultServiceError('The temporary fault adapter could not load fault events.')
    if (currentScenario === 'loading') return new Promise<FaultListResult>(() => undefined)
    const source = currentScenario === 'empty' ? [] : currentScenario === 'partial' ? store.slice(0, 1) : store
    return { faults: await validateDeviceIds(source) }
  },
  async get(faultId) {
    const fault = store.find((item) => item.id === faultId)
    if (!fault) throw new FaultServiceError('The requested fault could not be found.', 'FAULT_NOT_FOUND')
    return (await validateDeviceIds([fault]))[0]
  },
  async acknowledge(faultId) {
    return this.updateStatus(faultId, 'acknowledged')
  },
  async updateStatus(faultId, status) {
    const index = store.findIndex((item) => item.id === faultId)
    if (index < 0) throw new FaultServiceError('The requested fault could not be found.', 'FAULT_NOT_FOUND')
    store = store.map((item, itemIndex) => itemIndex === index ? { ...item, status, resolvedAt: status === 'resolved' ? new Date().toISOString() : item.resolvedAt } : item)
    return store[index]
  },
  async resolve(faultId) {
    return this.updateStatus(faultId, 'resolved')
  },
}

export function getFaultService(): FaultService {
  if (import.meta.env.VITE_FAULTS_ADAPTER === 'mock') return mockService
  return {
    async list() { throw new FaultServiceError('Fault management is not connected yet. Configure the Django/DRF fault adapter when the backend contract is available.', 'FAULTS_NOT_CONFIGURED') },
    async get() { throw new FaultServiceError('Fault management is not connected yet.', 'FAULTS_NOT_CONFIGURED') },
    async acknowledge() { throw new FaultServiceError('Fault acknowledgement is not supported until the backend contract is available.', 'FAULT_ACTION_UNSUPPORTED') },
    async updateStatus(..._args: Parameters<FaultService['updateStatus']>) { throw new FaultServiceError('Fault status updates are not supported until the backend contract is available.', 'FAULT_ACTION_UNSUPPORTED') },
    async resolve() { throw new FaultServiceError('Fault resolution is not supported until the backend contract is available.', 'FAULT_ACTION_UNSUPPORTED') },
  }
}
