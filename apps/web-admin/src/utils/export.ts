/**
 * 数据导出工具函数
 */

interface ExportColumn {
  title: string
  dataIndex: string
  render?: (value: unknown, record: Record<string, unknown>) => string | number
}

/**
 * 导出数据为 CSV 格式
 * @param data 数据数组
 * @param columns 列配置
 * @param filename 文件名（不含扩展名）
 */
export function exportToCSV<T extends Record<string, unknown>>(
  data: T[],
  columns: ExportColumn[],
  filename: string
): void {
  if (data.length === 0) {
    console.warn('No data to export')
    return
  }

  // 生成 CSV 内容
  const headers = columns.map((col) => `"${col.title}"`).join(',')
  const rows = data.map((record) => {
    return columns
      .map((col) => {
        const value = record[col.dataIndex]
        // 使用自定义 render 函数或默认值
        const displayValue = col.render ? col.render(value, record) : value
        // 转义双引号并包装
        const stringValue = String(displayValue ?? '')
        return `"${stringValue.replace(/"/g, '""')}"`
      })
      .join(',')
  })

  const csvContent = [headers, ...rows].join('\n')

  // 添加 BOM 以支持中文
  const BOM = '\uFEFF'
  const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })

  // 触发下载
  downloadBlob(blob, `${filename}.csv`)
}

/**
 * 导出数据为 JSON 格式
 * @param data 数据
 * @param filename 文件名（不含扩展名）
 */
export function exportToJSON<T>(data: T, filename: string): void {
  const jsonContent = JSON.stringify(data, null, 2)
  const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' })
  downloadBlob(blob, `${filename}.json`)
}

/**
 * 下载 Blob 文件
 */
function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * 格式化日期时间用于文件名
 */
export function getExportFilename(prefix: string): string {
  const now = new Date()
  const dateStr = now.toISOString().slice(0, 10).replace(/-/g, '')
  const timeStr = now.toTimeString().slice(0, 5).replace(':', '')
  return `${prefix}_${dateStr}_${timeStr}`
}
