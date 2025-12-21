import React, { useEffect, useState } from 'react'
import {
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  Switch,
  Button,
  message,
  Row,
  Col,
  Card,
  Space,
  Tooltip,
  Divider,
} from 'antd'
import {
  InfoCircleOutlined,
} from '@ant-design/icons'
import type { CrawlerTask } from '../../types/crawler'

const { Option } = Select

interface TaskEditProps {
  visible: boolean
  task: CrawlerTask | null
  onClose: () => void
  onSave: (taskData: Partial<CrawlerTask>) => Promise<void>
  loading?: boolean
}

// 任务类型配置（与 TaskForm 保持一致）
const taskTypeConfigs = {
  taobao: {
    name: '淘宝数据采集',
    platforms: ['taobao', 'tmall'],
    defaultPriority: 'medium',
    description: '爬取淘宝商品信息',
  },
  jd: {
    name: '京东数据采集',
    platforms: ['jd'],
    defaultPriority: 'medium',
    description: '爬取京东商品信息',
  },
  pdd: {
    name: '拼多多数据采集',
    platforms: ['pdd'],
    defaultPriority: 'medium',
    description: '爬取拼多多商品信息',
  },
  forum: {
    name: '论坛数据采集',
    platforms: ['zhihu', 'weibo', 'tieba'],
    defaultPriority: 'low',
    description: '爬取论坛帖子信息',
  },
  workflow: {
    name: '工作流',
    platforms: ['custom'],
    defaultPriority: 'high',
    description: '执行预定义的工作流',
  },
}

const TaskEdit: React.FC<TaskEditProps> = ({
  visible,
  task,
  onClose,
  onSave,
  loading = false,
}) => {
  const [form] = Form.useForm()
  const [taskType, setTaskType] = useState<string>('taobao')
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false)

  // 当前任务类型配置
  const currentConfig = taskTypeConfigs[taskType as keyof typeof taskTypeConfigs] || taskTypeConfigs.taobao

  // 解析任务配置
  const parseTaskConfig = (task: CrawlerTask) => {
    try {
      const config = task.config ? JSON.parse(task.config) : {}
      return {
        keywords: config.keywords?.join(', ') || '',
        shop_url: config.shop_url || task.shop_url || '',
        max_pages: config.max_pages || 5,
        proxy: config.proxy || '',
      }
    } catch {
      return {
        keywords: '',
        shop_url: task.shop_url || '',
        max_pages: 5,
        proxy: '',
      }
    }
  }

  // 重置表单数据
  useEffect(() => {
    if (visible && task) {
      const parsedConfig = parseTaskConfig(task)
      setTaskType(task.task_type || 'taobao')

      form.setFieldsValue({
        task_name: task.task_name,
        task_type: task.task_type,
        priority: task.priority || 'medium',
        description: task.description || '',
        shop_url: parsedConfig.shop_url,
        keywords: parsedConfig.keywords,
        max_pages: parsedConfig.max_pages,
        delay_range: task.delay_range || [1, 3],
        timeout: task.timeout || 300,
        retry_count: task.retry_count || 3,
        extract_images: task.extract_images || false,
        use_proxy: task.use_proxy || false,
        random_ua: task.random_ua !== false, // 默认为 true
      })
    } else {
      form.resetFields()
    }
  }, [visible, task, form])

  // 处理任务类型变化
  const handleTaskTypeChange = (value: string) => {
    setTaskType(value)
  }

  // 处理保存
  const handleSubmit = async (values: any) => {
    if (!task) return

    try {
      await onSave({
        ...values,
        task_id: task.task_id,
      })
      message.success('任务更新成功')
      onClose()
    } catch (error) {
      console.error('更新任务失败:', error)
    }
  }

  return (
    <Modal
      title={`编辑任务 - ${task?.task_name || ''}`}
      open={visible}
      onCancel={onClose}
      footer={[
        <Button key="cancel" onClick={onClose}>
          取消
        </Button>,
        <Button
          key="save"
          type="primary"
          loading={loading}
          onClick={() => form.submit()}
        >
          保存更改
        </Button>,
      ]}
      width={700}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
      >
        {/* 基本信息 */}
        <Card size="small" title="基本信息">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="任务名称"
                name="task_name"
                rules={[{ required: true, message: '请输入任务名称' }]}
              >
                <Input placeholder="请输入任务名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="任务类型"
                name="task_type"
                rules={[{ required: true, message: '请选择任务类型' }]}
              >
                <Select
                  placeholder="选择任务类型"
                  onChange={handleTaskTypeChange}
                >
                  {Object.entries(taskTypeConfigs).map(([key, config]) => (
                    <Option key={key} value={key}>
                      {config.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="优先级"
                name="priority"
              >
                <Select placeholder="选择优先级">
                  <Option value="high">高</Option>
                  <Option value="medium">中</Option>
                  <Option value="low">低</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="任务描述"
                name="description"
              >
                <Input placeholder="任务描述（可选）" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="店铺URL"
            name="shop_url"
            tooltip="输入店铺首页URL，将爬取该店铺的所有商品"
          >
            <Input placeholder="例如: https://shop123456.taobao.com 或 https://mall.jd.com/xxx" />
          </Form.Item>

          <Form.Item
            label="搜索关键词"
            name="keywords"
            tooltip="多个关键词用逗号分隔"
          >
            <Input placeholder="多个关键词用逗号分隔，例如: 路亚竿, 渔轮, 钓鱼装备" />
          </Form.Item>
        </Card>

        {/* 高级设置 */}
        <Card
          size="small"
          title={
            <Space>
              高级设置
              <Switch
                size="small"
                checked={showAdvanced}
                onChange={setShowAdvanced}
              />
            </Space>
          }
          style={{ marginTop: 16 }}
        >
          {showAdvanced && (
            <>
              <Row gutter={16}>
                <Col span={6}>
                  <Form.Item
                    label={
                      <Space>
                        最大页数
                        <Tooltip title="最多爬取的页面数量">
                          <InfoCircleOutlined />
                        </Tooltip>
                      </Space>
                    }
                    name="max_pages"
                  >
                    <InputNumber
                      min={1}
                      max={1000}
                      placeholder="10"
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item
                    label="重试次数"
                    name="retry_count"
                  >
                    <InputNumber
                      min={0}
                      max={10}
                      placeholder="3"
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item
                    label="超时时间(秒)"
                    name="timeout"
                  >
                    <InputNumber
                      min={30}
                      max={3600}
                      placeholder="300"
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item
                    label={
                      <Space>
                        延迟范围(秒)
                        <Tooltip title="每次请求之间的延迟时间">
                          <InfoCircleOutlined />
                        </Tooltip>
                      </Space>
                    }
                    name="delay_range"
                  >
                    <InputNumber
                      min={0}
                      max={60}
                      placeholder="1-3"
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Divider style={{ margin: '12px 0' }} />

              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item
                    label="提取图片"
                    name="extract_images"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    label="使用代理"
                    name="use_proxy"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    label="随机User-Agent"
                    name="random_ua"
                    valuePropName="checked"
                  >
                    <Switch defaultChecked />
                  </Form.Item>
                </Col>
              </Row>
            </>
          )}
        </Card>
      </Form>
    </Modal>
  )
}

export default TaskEdit
