import { apiRequest, ApiError } from '../api/client'
import { DeviceServiceError, type Device, type DeviceRegistrationInput, type DeviceService, type MonitoringState } from './types'

interface ApiDevice {
  id: string
  name: string
  ipAddress: string
  type: Device['type']
  status: Device['status']
  monitoring: MonitoringState
  createdAt: string
  updatedAt: string
}

function mapDevice(device: ApiDevice): Device { return device }
function toPayload(input: DeviceRegistrationInput) { return { name: input.name.trim(), ipAddress: input.ipAddress.trim(), type: input.type, monitoring: input.monitoring } }
function handleError(error: unknown, fallback: string): never {
  if (error instanceof ApiError && (error.status === 400 || error.status === 401 || error.status === 403)) throw new DeviceServiceError(error.message, 'DEVICE_VALIDATION_ERROR')
  throw new DeviceServiceError(error instanceof Error ? error.message : fallback)
}

const apiService: DeviceService = {
  async list() { try { const data = await apiRequest<ApiDevice[]>('/devices/'); return data.map(mapDevice) } catch (error) { return handleError(error, 'Devices could not be loaded.') } },
  async create(input) { try { return mapDevice(await apiRequest<ApiDevice>('/devices/', { method: 'POST', body: JSON.stringify(toPayload(input)) })) } catch (error) { return handleError(error, 'Device could not be registered.') } },
  async update(id, input) { try { return mapDevice(await apiRequest<ApiDevice>(`/devices/${id}/`, { method: 'PATCH', body: JSON.stringify(toPayload(input)) })) } catch (error) { return handleError(error, 'Device could not be updated.') } },
  async setMonitoring(id, monitoring) { try { return mapDevice(await apiRequest<ApiDevice>(`/devices/${id}/monitoring/`, { method: 'PATCH', body: JSON.stringify({ monitoring }) })) } catch (error) { return handleError(error, 'Monitoring state could not be updated.') } },
}

export function getDeviceService(): DeviceService { return apiService }
