import { apiRequest, ApiError } from '../api/client'
import { NotificationServiceError, type FaultNotification, type NotificationListResult, type NotificationService } from './types'

function handleError(error: unknown): never {
  if (error instanceof ApiError && (error.status === 401 || error.status === 403)) throw new NotificationServiceError('Your session is no longer authorized. Please sign in again.')
  throw new NotificationServiceError(error instanceof Error ? error.message : 'Notifications could not be loaded.')
}

const apiService: NotificationService = {
  async list(): Promise<NotificationListResult> {
    try { return { notifications: await apiRequest<FaultNotification[]>('/notifications/') } } catch (error) { return handleError(error) }
  },
  async markAsRead(notificationId) {
    try { return await apiRequest<FaultNotification>(`/notifications/${notificationId}/read/`, { method: 'POST' }) } catch (error) { return handleError(error) }
  },
}

export function getNotificationService(): NotificationService { return apiService }
