export type NotificationSeverity = 'critical' | 'high' | 'medium' | 'low'
export type NotificationStatus = 'unread' | 'read'

export interface FaultNotification {
  id: string
  faultId: string
  deviceId: string
  deviceName: string
  faultType: string
  severity: NotificationSeverity
  detectedAt: string
  status: NotificationStatus
  description?: string
}

export interface NotificationListResult {
  notifications: FaultNotification[]
}

export interface NotificationService {
  list: () => Promise<NotificationListResult>
  markAsRead: (notificationId: string) => Promise<FaultNotification>
}

export type NotificationScenario = 'populated' | 'empty' | 'partial' | 'error' | 'loading'

export class NotificationServiceError extends Error {
  readonly code: 'NOTIFICATIONS_NOT_CONFIGURED' | 'NOTIFICATIONS_API_ERROR' | 'NOTIFICATION_NOT_FOUND'

  constructor(message: string, code: NotificationServiceError['code'] = 'NOTIFICATIONS_API_ERROR') {
    super(message)
    this.name = 'NotificationServiceError'
    this.code = code
  }
}
