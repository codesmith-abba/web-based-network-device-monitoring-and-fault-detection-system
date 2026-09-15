import { getDeviceService } from '../devices/service'
import { getFaultService } from '../faults/service'
import { getMonitoringService } from '../monitoring/service'
import { HistoryServiceError, type FaultHistoryService, type HistoryScenario, type MonitoringHistoryService, type MonitoringHistoryResult, type FaultHistoryResult } from './types'

function scenario(): HistoryScenario {
  const value = import.meta.env.VITE_HISTORY_SCENARIO
  return value === 'empty' || value === 'partial' || value === 'error' || value === 'loading' ? value : 'populated'
}

const monitoringHistoryService: MonitoringHistoryService = {
  async list(): Promise<MonitoringHistoryResult> {
    const currentScenario = scenario()
    if (currentScenario === 'error') throw new HistoryServiceError('Historical monitoring data could not be loaded.')
    if (currentScenario === 'loading') return new Promise<MonitoringHistoryResult>(() => undefined)

    const devices = await getDeviceService().list()
    const monitoredDevices = devices.filter((device) => device.monitoring === 'enabled')
    const snapshots = await Promise.all(monitoredDevices.map((device) => getMonitoringService().getSnapshot(device.id)))
    let records = snapshots.flatMap((snapshot) => snapshot.history.map((record) => ({ ...record, deviceName: snapshot.device.name })))
    if (currentScenario === 'empty') records = []
    if (currentScenario === 'partial') records = records.slice(0, 1)
    return { records }
  },
}

const faultHistoryService: FaultHistoryService = {
  async list(): Promise<FaultHistoryResult> {
    const currentScenario = scenario()
    if (currentScenario === 'error') throw new HistoryServiceError('Fault history could not be loaded.')
    if (currentScenario === 'loading') return new Promise<FaultHistoryResult>(() => undefined)
    const result = await getFaultService().list()
    const faults = currentScenario === 'empty' ? [] : currentScenario === 'partial' ? result.faults.slice(0, 1) : result.faults
    return { faults }
  },
}

export function getMonitoringHistoryService(): MonitoringHistoryService {
  if (import.meta.env.VITE_MONITORING_ADAPTER === 'mock') return monitoringHistoryService
  return { async list() { throw new HistoryServiceError('Monitoring history is not connected yet. Configure the Django/DRF historical monitoring adapter when the backend contract is available.', 'HISTORY_NOT_CONFIGURED') } }
}

export function getFaultHistoryService(): FaultHistoryService {
  if (import.meta.env.VITE_FAULTS_ADAPTER === 'mock') return faultHistoryService
  return { async list() { throw new HistoryServiceError('Fault history is not connected yet. Configure the Django/DRF historical fault adapter when the backend contract is available.', 'HISTORY_NOT_CONFIGURED') } }
}
