import { apiRequest, ApiError } from '../api/client'
import { DeviceServiceError, type Device, type DeviceRegistrationInput, type DeviceService } from './types'

interface ApiDevice {
  id: string
  name: string
  ipAddress: string
  type: Device['type']
  status: Device['status']
  monitoring: boolean
  createdAt: string
  updatedAt: string
}

function mapDevice(device: ApiDevice): Device {
  return {
    ...device,
    monitoring: device.monitoring ? 'enabled' : 'disabled',
  }
}

function toPayload(input: DeviceRegistrationInput) {
  return {
    name: input.name.trim(),
    ipAddress: input.ipAddress.trim(),
    type: input.type,
    monitoring: Boolean(input.monitoring),
  }
}

function handleError(error: unknown, fallback: string): never {
  if (error instanceof ApiError && (error.status === 400 || error.status === 401 || error.status === 403)) throw new DeviceServiceError(error.message, 'DEVICE_VALIDATION_ERROR')
  throw new DeviceServiceError(error instanceof Error ? error.message : fallback)
}

export function isValidIp(value: string): boolean {
  const parts = value.trim().split('.')

  if (parts.length !== 4) return false

  return parts.every((part) => {
    if (!/^\d+$/.test(part)) return false

    const number = Number(part)
    return number >= 0 && number <= 255
  })
}

const apiService: DeviceService = {
  async list() { try { const data = await apiRequest<ApiDevice[]>('/devices/'); return data.map(mapDevice) } catch (error) { return handleError(error, 'Devices could not be loaded.') } },
  async create(input) { try { return mapDevice(await apiRequest<ApiDevice>('/devices/', { method: 'POST', body: JSON.stringify(toPayload(input)) })) } catch (error) { return handleError(error, 'Device could not be registered.') } },
  async update(id, input) { try { return mapDevice(await apiRequest<ApiDevice>(`/devices/${id}/`, { method: 'PATCH', body: JSON.stringify(toPayload(input)) })) } catch (error) { return handleError(error, 'Device could not be updated.') } },
  async setMonitoring(id, monitoring) {
    try {
      return mapDevice(await apiRequest<ApiDevice>(`/devices/${id}/monitoring/`, {
        method: 'PATCH',
        body: JSON.stringify({ monitoring: Boolean(monitoring) }),
      }))
    } catch (error) {
      return handleError(error, 'Monitoring state could not be updated.')
    }
  },
}

export function getDeviceService(): DeviceService { return apiService }
