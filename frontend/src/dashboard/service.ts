import { apiRequest, ApiError } from '../api/client'
import { getMonitoringService } from '../monitoring/service'
import { DashboardError, type DashboardData, type MonitoringTrendPoint } from './types'

interface ApiDashboard {
  summary: DashboardData['summary']
  deviceHealth: DashboardData['deviceHealth']
  activeFaults: Array<{
    id: string
    deviceName: string
    title: string
    faultType: string
    severity: DashboardData['activeFaults'][number]['severity']
    detectedAt: string
    description?: string
  }>
}

function buildMonitoringTrend(
  histories: Array<{
    timestamp: string
    reachable: boolean | null
    latencyMs: number | null
    packetLossPercent: number | null
  }>,
): MonitoringTrendPoint[] {
  return histories
    .slice()
    .sort((a, b) => a.timestamp.localeCompare(b.timestamp))
    .map((record) => ({
      label: new Date(record.timestamp).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      }),
      availabilityPercent:
        record.reachable === null ? undefined : record.reachable ? 100 : 0,
      latencyMs: record.latencyMs ?? undefined,
      packetLossPercent: record.packetLossPercent ?? undefined,
    }))
}

export async function getDashboardData(): Promise<DashboardData> {
  try {
    const data = await apiRequest<ApiDashboard>('/dashboard/')

    const snapshots = await Promise.all(
      data.deviceHealth.map(async (device) => {
        try {
          return await getMonitoringService().getSnapshot(device.id)
        } catch {
          return null
        }
      }),
    )

    const history = snapshots
      .filter((snapshot): snapshot is NonNullable<typeof snapshot> => snapshot !== null)
      .flatMap((snapshot) => snapshot.history)

    return {
      summary: data.summary,
      deviceHealth: data.deviceHealth,
      activeFaults: data.activeFaults.map((fault) => ({
        ...fault,
        title: fault.title,
      })),
      monitoringTrend: buildMonitoringTrend(history),
    }
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      throw new DashboardError('Your session is no longer authorized. Please sign in again.')
    }

    throw new DashboardError(
      error instanceof Error ? error.message : 'Dashboard data could not be loaded.',
    )
  }
}