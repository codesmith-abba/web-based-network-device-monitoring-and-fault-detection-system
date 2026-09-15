import { apiRequest, ApiError } from '../api/client'
import { HistoryServiceError, type FaultHistoryService, type MonitoringHistoryService, type MonitoringHistoryResult, type FaultHistoryResult } from './types'

function handleError(error: unknown): never {
  if (error instanceof ApiError && (error.status === 401 || error.status === 403)) throw new HistoryServiceError('Your session is no longer authorized. Please sign in again.')
  throw new HistoryServiceError(error instanceof Error ? error.message : 'History data could not be loaded.')
}

export const monitoringHistoryService: MonitoringHistoryService = {
  async list(): Promise<MonitoringHistoryResult> {
    try { return await apiRequest<MonitoringHistoryResult>('/monitoring-history/') } catch (error) { return handleError(error) }
  },
}

export const faultHistoryService: FaultHistoryService = {
  async list(): Promise<FaultHistoryResult> {
    try { return await apiRequest<FaultHistoryResult>('/fault-history/') } catch (error) { return handleError(error) }
  },
}

export function getMonitoringHistoryService(): MonitoringHistoryService { return monitoringHistoryService }
export function getFaultHistoryService(): FaultHistoryService { return faultHistoryService }
