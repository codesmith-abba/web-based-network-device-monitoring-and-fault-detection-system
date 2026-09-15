import { getFaultService } from '../faults/service'
import { NotificationServiceError, type FaultNotification, type NotificationScenario, type NotificationService } from './types'

function scenario(): NotificationScenario {
  const value = import.meta.env.VITE_NOTIFICATIONS_SCENARIO
  return value === 'empty' || value === 'partial' || value === 'error' || value === 'loading' ? value : 'populated'
}

let store: FaultNotification[] = []

async function loadFromFaults(): Promise<FaultNotification[]> {
  const result = await getFaultService().list()
  return result.faults.map((fault) => ({
    id: `notification-${fault.id}`,
    faultId: fault.id,
    deviceId: fault.deviceId,
    deviceName: fault.deviceName,
    faultType: fault.faultType,
    severity: fault.severity,
    detectedAt: fault.detectedAt,
    status: 'unread',
    description: fault.description,
  }))
}

const mockService: NotificationService = {
  async list() {
    const currentScenario = scenario()
    if (currentScenario === 'error') throw new NotificationServiceError('The temporary notification adapter could not load fault notifications.')
    if (currentScenario === 'loading') return new Promise(() => undefined)
    if (store.length === 0) store = await loadFromFaults()
    const notifications = currentScenario === 'empty' ? [] : currentScenario === 'partial' ? store.slice(0, 1) : store
    return { notifications }
  },
  async markAsRead(notificationId) {
    if (store.length === 0) store = await loadFromFaults()
    const index = store.findIndex((item) => item.id === notificationId)
    if (index < 0) throw new NotificationServiceError('The requested notification could not be found.', 'NOTIFICATION_NOT_FOUND')
    store = store.map((item, itemIndex) => itemIndex === index ? { ...item, status: 'read' } : item)
    return store[index]
  },
}

export function getNotificationService(): NotificationService {
  if (import.meta.env.VITE_NOTIFICATIONS_ADAPTER === 'mock') return mockService
  return {
    async list() {
      throw new NotificationServiceError('Notifications are not connected yet. Configure the Django/DRF notification adapter when the backend contract is available.', 'NOTIFICATIONS_NOT_CONFIGURED')
    },
    async markAsRead() {
      throw new NotificationServiceError('Notification read-state updates are not supported until the backend contract is available.', 'NOTIFICATIONS_NOT_CONFIGURED')
    },
  }
}
