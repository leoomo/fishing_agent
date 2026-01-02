import React, { useState } from 'react'
import {
  Form,
  Input,
  Select,
  InputNumber,
  Button,
  Space,
  Row,
  Col,
  Card,
  Divider,
  Alert,
  Tooltip,
  Switch,
} from 'antd'
import {
  InfoCircleOutlined,
} from '@ant-design/icons'
import type { FormInstance } from 'antd'

const { Option } = Select

interface TaskFormProps {
  form: FormInstance
  onSubmit: (values: any) => void
  onCancel: () => void
  loading?: boolean
  initialValues?: any
}

const TaskForm: React.FC<TaskFormProps> = ({
  form,
  onSubmit,
  onCancel,
  loading = false,
  initialValues,
}) => {
  const [taskType, setTaskType] = useState<string>('taobao')
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false)

  // 任务类型配置
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

  // 当前任务类型配置
  const currentConfig = taskTypeConfigs[taskType as keyof typeof taskTypeConfigs]

  // 处理任务类型变化
  const handleTaskTypeChange = (value: string) => {
    setTaskType(value)
    const config = taskTypeConfigs[value as keyof typeof taskTypeConfigs]

    // 设置默认值
    form.setFieldsValue({
      platform: config.platforms[0],
      priority: config.defaultPriority,
    })
  }

  // 预设模板
  const templates = [
    {
      name: '商品信息采集',
      type: 'taobao',
      config: {
        max_pages: 5,
        keywords: ['路亚竿', '渔轮'],
      },
    },
    {
      name: '价格监控',
      type: 'taobao',
      config: {
        max_pages: 1,
        keywords: ['路亚装备'],
      },
    },
    {
      name: '全站爬取',
      type: 'taobao',
      config: {
        max_pages: 50,
        keywords: ['路亚', '钓鱼装备', '渔具'],
      },
    },
  ]

  // 应用模板
  const handleApplyTemplate = (template: any) => {
    const { type, config } = template
    form.setFieldsValue({
      task_type: type,
      max_pages: config.max_pages,
      keywords: config.keywords?.join(', ') || '',
      shop_url: config.shop_url || '',
    })
    handleTaskTypeChange(type)
  }

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={onSubmit}
      initialValues={{
        task_type: 'taobao',
        platform: 'taobao',
        priority: 'medium',
        max_pages: 5,
        shop_url: '',
        keywords: '',
        ...initialValues,
      }}
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
          <Col span={8}>
            <Form.Item
              label="目标平台"
              name="platform"
              rules={[{ required: true, message: '请选择目标平台' }]}
            >
              <Select placeholder="选择平台">
                {currentConfig.platforms.map(platform => (
                  <Option key={platform} value={platform}>
                    {platform === 'taobao' ? '淘宝' :
                     platform === 'tmall' ? '天猫' :
                     platform === 'jd' ? '京东' :
                     platform === 'pdd' ? '拼多多' :
                     platform === 'zhihu' ? '知乎' :
                     platform === 'weibo' ? '微博' :
                     platform === 'tieba' ? '贴吧' : platform}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          <Col span={8}>
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
          <Col span={8}>
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
          rules={[
            { required: true, message: '请输入店铺URL' },
            {
              pattern: /^https?:\/\/.+/,
              message: '请输入有效的URL地址',
            }
          ]}
        >
          <Input
            placeholder="例如: https://shop123456.taobao.com 或 https://mall.jd.com/xxx"
          />
        </Form.Item>

        <Form.Item
          label="搜索关键词"
          name="keywords"
          tooltip="多个关键词用逗号分隔（可选）"
        >
          <Input
            placeholder="多个关键词用逗号分隔，例如: 路亚竿, 渔轮, 钓鱼装备"
          />
        </Form.Item>

      </Card>

      {/* 快速模板 */}
      <Card size="small" title="快速模板" style={{ marginTop: 16 }}>
        <Space wrap>
          {templates.map((template, index) => (
            <Button
              key={index}
              size="small"
              onClick={() => handleApplyTemplate(template)}
            >
              {template.name}
            </Button>
          ))}
        </Space>
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
                  label={
                    <Space>
                      延迟范围(秒)
                      <Tooltip title="每次请求之间的延迟时间范围">
                        <InfoCircleOutlined />
                      </Tooltip>
                    </Space>
                  }
                  name="delay_range"
                >
                  <Input.Group compact>
                    <InputNumber
                      style={{ width: '45%' }}
                      min={0}
                      max={60}
                      placeholder="最小"
                    />
                    <Input
                      style={{
                        width: '10%',
                        borderLeft: 0,
                        borderRight: 0,
                        pointerEvents: 'none',
                      }}
                      placeholder="~"
                      disabled
                    />
                    <InputNumber
                      style={{ width: '45%' }}
                      min={0}
                      max={60}
                      placeholder="最大"
                    />
                  </Input.Group>
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
            </Row>

            <Divider />

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

      {/* 提示信息 */}
      <Alert
        message="提示"
        description={
          <ul>
            <li>任务创建后将进入等待队列，可以随时启动或删除</li>
            <li>不同平台的爬取规则和限制可能不同</li>
            <li>请确保遵守相关平台的使用条款</li>
          </ul>
        }
        type="info"
        showIcon
        style={{ marginTop: 16 }}
      />

      {/* 操作按钮 */}
      <div style={{ marginTop: 24, textAlign: 'right' }}>
        <Space>
          <Button onClick={onCancel}>
            取消
          </Button>
          <Button type="primary" htmlType="submit" loading={loading}>
            创建任务
          </Button>
        </Space>
      </div>
    </Form>
  )
}

export default TaskForm