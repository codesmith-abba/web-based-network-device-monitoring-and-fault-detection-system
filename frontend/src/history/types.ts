import type { FaultEvent, FaultService } from '../faults/types'
import type { Device } from '../devices/types'
import type { MonitoringRecord } from '../monitoring/types'

export interface HistoricalMonitoringRecord extends MonitoringRecord {
  deviceName: string
}

export interface MonitoringHistoryResult {
  records: HistoricalMonitoringRecord[]
}

export interface MonitoringHistoryFilters {
  deviceId: string | 'all'
  from: string
  to: string
}

export interface MonitoringHistoryService {
  list: () => Promise<MonitoringHistoryResult>
}

export interface FaultHistoryResult {
  faults: FaultEvent[]
}

export interface FaultHistoryService {
  list: () => Promise<FaultHistoryResult>
}

export type HistoryScenario = 'populated' | 'empty' | 'partial' | 'error' | 'loading'

export class HistoryServiceError extends Error {
  readonly code: 'HISTORY_NOT_CONFIGURED' | 'HISTORY_API_ERROR'

  constructor(message: string, code: HistoryServiceError['code'] = 'HISTORY_API_ERROR') {
    super(message)
    this.name = 'HistoryServiceError'
    this.code = code
  }
}

export interface HistoryDependencies {
  devices: Device[]
  faultService: FaultService
}
