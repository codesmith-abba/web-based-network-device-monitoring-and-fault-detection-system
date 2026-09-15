import { apiRequest, ApiError } from '../api/client'
import { DashboardError, type DashboardData } from './types'

interface ApiDashboard {
  summary: DashboardData['summary']
  deviceHealth: DashboardData['deviceHealth']
  activeFaults: Array<{ id: string; deviceName: string; faultType: string; severity: DashboardData['activeFaults'][number]['severity']; detectedAt: string; description?: string }>
}

export async function getDashboardData(): Promise<DashboardData> {
  try {
    const data = await apiRequest<ApiDashboard>('/dashboard/')
    return {
      summary: data.summary,
      deviceHealth: data.deviceHealth,
      activeFaults: data.activeFaults.map((fault) => ({ ...fault, title: fault.faultType.replaceAll('_', ' ') })),
    }
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) throw new DashboardError('Your session is no longer authorized. Please sign in again.')
    throw new DashboardError(error instanceof Error ? error.message : 'Dashboard data could not be loaded.')
  }
}
