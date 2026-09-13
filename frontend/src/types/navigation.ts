export type NavigationKey =
  | 'dashboard'
  | 'devices'
  | 'faults'
  | 'monitoring'
  | 'notifications'
  | 'settings'

export interface NavigationItem {
  key: NavigationKey
  label: string
  description: string
  available: boolean
}
