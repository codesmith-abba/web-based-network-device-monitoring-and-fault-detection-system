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
  const buckets = new Map<
    string,
    {
      reachable: number
      total: number
      latencyTotal: number
      latencyCount: number
      lossTotal: number
      lossCount: number
    }
  >()

  for (const record of histories) {
    const date = new Date(record.timestamp)

    // Group measurements into the same minute.
    date.setSeconds(0, 0)
    const bucketKey = date.toISOString()

    const bucket = buckets.get(bucketKey) ?? {
      reachable: 0,
      total: 0,
      latencyTotal: 0,
      latencyCount: 0,
      lossTotal: 0,
      lossCount: 0,
    }

    if (record.reachable !== null) {
      bucket.total += 1

      if (record.reachable) {
        bucket.reachable += 1
      }
    }

    if (record.latencyMs !== null) {
      bucket.latencyTotal += record.latencyMs
      bucket.latencyCount += 1
    }

    if (record.packetLossPercent !== null) {
      bucket.lossTotal += record.packetLossPercent
      bucket.lossCount += 1
    }

    buckets.set(bucketKey, bucket)
  }

  return Array.from(buckets.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([timestamp, bucket]) => {
      const date = new Date(timestamp)

      return {
        label: date.toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
        availabilityPercent:
          bucket.total > 0
            ? (bucket.reachable / bucket.total) * 100
            : undefined,
        latencyMs:
          bucket.latencyCount > 0
            ? bucket.latencyTotal / bucket.latencyCount
            : undefined,
        packetLossPercent:
          bucket.lossCount > 0
            ? bucket.lossTotal / bucket.lossCount
            : undefined,
      }
    })
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