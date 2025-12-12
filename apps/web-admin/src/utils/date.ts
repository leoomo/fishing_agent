import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import relativeTime from 'dayjs/plugin/relativeTime';
import utc from 'dayjs/plugin/utc';

dayjs.extend(relativeTime);
dayjs.extend(utc);
dayjs.locale('zh-cn');

/**
 * 格式化日期时间
 */
export const formatDateTime = (date: string | Date | undefined | null): string => {
  if (!date) return '-';
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss');
};

/**
 * 格式化日期
 */
export const formatDate = (date: string | Date | undefined | null): string => {
  if (!date) return '-';
  return dayjs(date).format('YYYY-MM-DD');
};

/**
 * 格式化时间
 */
export const formatTime = (date: string | Date | undefined | null): string => {
  if (!date) return '-';
  return dayjs(date).format('HH:mm:ss');
};

/**
 * 相对时间
 */
export const formatRelativeTime = (date: string | Date | undefined | null): string => {
  if (!date) return '-';
  return dayjs(date).fromNow();
};

/**
 * 是否为今天
 */
export const isToday = (date: string | Date | undefined | null): boolean => {
  if (!date) return false;
  return dayjs(date).isSame(dayjs(), 'day');
};

/**
 * 是否为昨天
 */
export const isYesterday = (date: string | Date | undefined | null): boolean => {
  if (!date) return false;
  return dayjs(date).isSame(dayjs().subtract(1, 'day'), 'day');
};

/**
 * 获取日期范围
 */
export const getDateRange = (type: 'today' | 'yesterday' | 'week' | 'month' | 'year'): [Date, Date] => {
  const now = dayjs();

  switch (type) {
    case 'today':
      return [now.startOf('day').toDate(), now.endOf('day').toDate()];
    case 'yesterday':
      return [
        now.subtract(1, 'day').startOf('day').toDate(),
        now.subtract(1, 'day').endOf('day').toDate()
      ];
    case 'week':
      return [now.startOf('week').toDate(), now.endOf('week').toDate()];
    case 'month':
      return [now.startOf('month').toDate(), now.endOf('month').toDate()];
    case 'year':
      return [now.startOf('year').toDate(), now.endOf('year').toDate()];
    default:
      return [now.startOf('day').toDate(), now.endOf('day').toDate()];
  }
};

/**
 * 计算持续时间
 */
export const getDuration = (startTime: string | Date, endTime?: string | Date | null): string => {
  const start = dayjs(startTime);
  const end = endTime ? dayjs(endTime) : dayjs();
  const diff = end.diff(start, 'second');

  if (diff < 60) {
    return `${diff}秒`;
  } else if (diff < 3600) {
    return `${Math.floor(diff / 60)}分钟`;
  } else if (diff < 86400) {
    return `${Math.floor(diff / 3600)}小时`;
  } else {
    return `${Math.floor(diff / 86400)}天`;
  }
};

/**
 * 格式化持续时间（HH:mm:ss）
 */
export const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  return [hours, minutes, secs]
    .map(v => v.toString().padStart(2, '0'))
    .join(':');
};