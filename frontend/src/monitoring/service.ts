import { apiRequest, ApiError } from '../api/client'
import { MonitoringServiceError, type DeviceMonitoringService, type DeviceMonitoringSnapshot, type MonitoringRecord } from './types'

function handleError(error: unknown): never {
  if (error instanceof ApiError && (error.status === 401 || error.status === 403)) throw new MonitoringServiceError('Your session is no longer authorized. Please sign in again.')
  if (error instanceof ApiError && error.status === 400) throw new MonitoringServiceError(error.message, 'MONITORING_NOT_CONFIGURED')
  throw new MonitoringServiceError(error instanceof Error ? error.message : 'Monitoring data could not be loaded.')
}

const apiService: DeviceMonitoringService = {
  async getSnapshot(deviceId): Promise<DeviceMonitoringSnapshot> {
    try { return await apiRequest<DeviceMonitoringSnapshot>(`/devices/${deviceId}/monitoring-snapshot/`) } catch (error) { return handleError(error) }
  },
  async runCheck(deviceId): Promise<MonitoringRecord> {
    try { return await apiRequest<MonitoringRecord>(`/devices/${deviceId}/monitor/`, { method: 'POST', body: JSON.stringify({}) }) } catch (error) { return handleError(error) }
  },
}

export function getMonitoringService(): DeviceMonitoringService { return apiService }
