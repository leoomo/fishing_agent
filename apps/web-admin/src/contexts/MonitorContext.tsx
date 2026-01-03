import React, { createContext, useContext, useState, useCallback, useMemo } from 'react'
import dayjs, { Dayjs } from 'dayjs'

export interface MonitorContextType {
  // 日期范围
  dateRange: [Dayjs, Dayjs]
  setDateRange: (range: [Dayjs, Dayjs]) => void

  // 格式化后的日期字符串（用于API调用）
  startDate: string
  endDate: string

  // 刷新控制
  refreshKey: number
  refresh: () => void

  // 最后更新时间
  lastUpdated: Date | null
  setLastUpdated: (date: Date) => void

  // Agent类型过滤（用于钻取功能）
  agentTypeFilter: string | null
  setAgentTypeFilter: (type: string | null) => void

  // 当前激活的标签页
  activeTab: string
  setActiveTab: (tab: string) => void
}

const MonitorContext = createContext<MonitorContextType | null>(null)

export interface MonitorProviderProps {
  children: React.ReactNode
  defaultDays?: number
}

export const MonitorProvider: React.FC<MonitorProviderProps> = ({
  children,
  defaultDays = 7,
}) => {
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs]>([
    dayjs().subtract(defaultDays, 'day'),
    dayjs(),
  ])
  const [refreshKey, setRefreshKey] = useState(0)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [agentTypeFilter, setAgentTypeFilter] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('overview')

  const refresh = useCallback(() => {
    setRefreshKey((prev) => prev + 1)
  }, [])

  // 格式化日期用于API调用
  const startDate = useMemo(
    () => dateRange[0].format('YYYY-MM-DD'),
    [dateRange]
  )
  const endDate = useMemo(
    () => dateRange[1].format('YYYY-MM-DD'),
    [dateRange]
  )

  const value = useMemo(
    () => ({
      dateRange,
      setDateRange,
      startDate,
      endDate,
      refreshKey,
      refresh,
      lastUpdated,
      setLastUpdated,
      agentTypeFilter,
      setAgentTypeFilter,
      activeTab,
      setActiveTab,
    }),
    [dateRange, startDate, endDate, refreshKey, refresh, lastUpdated, agentTypeFilter, activeTab]
  )

  return (
    <MonitorContext.Provider value={value}>{children}</MonitorContext.Provider>
  )
}

export const useMonitorContext = (): MonitorContextType => {
  const context = useContext(MonitorContext)
  if (!context) {
    throw new Error('useMonitorContext must be used within MonitorProvider')
  }
  return context
}

// 预设时间范围
export const DATE_RANGE_PRESETS = [
  { label: '最近24小时', value: () => [dayjs().subtract(1, 'day'), dayjs()] as [Dayjs, Dayjs] },
  { label: '最近7天', value: () => [dayjs().subtract(7, 'day'), dayjs()] as [Dayjs, Dayjs] },
  { label: '最近30天', value: () => [dayjs().subtract(30, 'day'), dayjs()] as [Dayjs, Dayjs] },
  { label: '最近90天', value: () => [dayjs().subtract(90, 'day'), dayjs()] as [Dayjs, Dayjs] },
]

export default MonitorContext
