import React, { useCallback } from 'react'
import {
  Form,
  Select,
  DatePicker,
  Input,
  Button,
  Space,
  Row,
  Col,
} from 'antd'
import {
  SearchOutlined,
  ClearOutlined,
  FilterOutlined,
} from '@ant-design/icons'
import type { TaskFilters } from '../../types/crawler'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker
const { Option } = Select
const { Search } = Input

interface TaskFiltersProps {
  filters: TaskFilters
  onFilterChange: (filters: Partial<TaskFilters>) => void
  onClearFilters: () => void
}

const TaskFilters: React.FC<TaskFiltersProps> = ({
  filters,
  onFilterChange,
  onClearFilters,
}) => {
  const [form] = Form.useForm()

  // 处理表单值变化
  const handleValuesChange = useCallback((changedValues: any, allValues: any) => {
    const newFilters: Partial<TaskFilters> = {}

    // 处理搜索关键词
    if (allValues.keyword) {
      newFilters.keyword = allValues.keyword.trim()
    }

    // 处理状态筛选
    if (allValues.status) {
      newFilters.status = allValues.status
    }

    // 处理任务类型筛选
    if (allValues.task_type) {
      newFilters.task_type = allValues.task_type
    }

    // 处理平台筛选
    if (allValues.platform) {
      newFilters.platform = allValues.platform
    }

    // 处理优先级筛选
    if (allValues.priority) {
      newFilters.priority = allValues.priority
    }

    // 处理日期范围
    if (allValues.date_range && allValues.date_range.length === 2) {
      newFilters.date_range = [
        allValues.date_range[0].format('YYYY-MM-DD'),
        allValues.date_range[1].format('YYYY-MM-DD'),
      ] as [string, string]
    }

    onFilterChange(newFilters)
  }, [onFilterChange])

  // 清除筛选
  const handleClear = useCallback(() => {
    form.resetFields()
    onClearFilters()
  }, [form, onClearFilters])

  // 快速搜索（防抖处理）
  const handleSearch = useCallback((value: string) => {
    onFilterChange({ keyword: value.trim() })
  }, [onFilterChange])

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={filters}
      onValuesChange={handleValuesChange}
    >
      <Row gutter={16}>
        {/* 搜索关键词 */}
        <Col span={6}>
          <Form.Item label="搜索" name="keyword">
            <Search
              placeholder="搜索任务名称或描述"
              allowClear
              enterButton={<SearchOutlined />}
              onSearch={handleSearch}
              style={{ width: '100%' }}
            />
          </Form.Item>
        </Col>

        {/* 状态筛选 */}
        <Col span={4}>
          <Form.Item label="状态" name="status">
            <Select placeholder="选择状态" allowClear>
              <Option value="pending">等待中</Option>
              <Option value="running">运行中</Option>
              <Option value="success">成功</Option>
              <Option value="failed">失败</Option>
              <Option value="cancelled">已取消</Option>
              <Option value="paused">已暂停</Option>
            </Select>
          </Form.Item>
        </Col>

        {/* 任务类型 */}
        <Col span={4}>
          <Form.Item label="任务类型" name="task_type">
            <Select placeholder="选择类型" allowClear>
              <Option value="taobao">淘宝爬虫</Option>
              <Option value="jd">京东爬虫</Option>
              <Option value="pdd">拼多多爬虫</Option>
              <Option value="forum">论坛爬虫</Option>
              <Option value="workflow">工作流</Option>
            </Select>
          </Form.Item>
        </Col>

        {/* 平台筛选 */}
        <Col span={4}>
          <Form.Item label="平台" name="platform">
            <Select placeholder="选择平台" allowClear>
              <Option value="taobao">淘宝</Option>
              <Option value="tmall">天猫</Option>
              <Option value="jd">京东</Option>
              <Option value="pdd">拼多多</Option>
              <Option value="weibo">微博</Option>
              <Option value="zhihu">知乎</Option>
            </Select>
          </Form.Item>
        </Col>

        {/* 优先级 */}
        <Col span={4}>
          <Form.Item label="优先级" name="priority">
            <Select placeholder="选择优先级" allowClear>
              <Option value="high">高</Option>
              <Option value="medium">中</Option>
              <Option value="low">低</Option>
            </Select>
          </Form.Item>
        </Col>

        {/* 操作按钮 */}
        <Col span={2}>
          <Form.Item label=" ">
            <Space>
              <Button
                icon={<ClearOutlined />}
                onClick={handleClear}
                size="small"
              >
                清除
              </Button>
            </Space>
          </Form.Item>
        </Col>
      </Row>

      {/* 第二行：日期范围 */}
      <Row gutter={16}>
        <Col span={8}>
          <Form.Item label="创建时间" name="date_range">
            <RangePicker
              style={{ width: '100%' }}
              placeholder={['开始日期', '结束日期']}
              format="YYYY-MM-DD"
              disabledDate={(current) => {
                return current && current > dayjs().endOf('day')
              }}
            />
          </Form.Item>
        </Col>

        {/* 可以在这里添加更多筛选条件 */}
        <Col span={16}>
          {/* 预留给未来的筛选条件 */}
        </Col>
      </Row>
    </Form>
  )
}

export default TaskFilters