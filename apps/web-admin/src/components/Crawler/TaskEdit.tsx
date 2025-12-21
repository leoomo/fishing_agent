import React, { useEffect } from 'react'
import {
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  Switch,
  Button,
  message,
  Divider,
} from 'antd'
import type { CrawlerTask } from '../../types/crawler'

const { Option } = Select
const { TextArea } = Input

interface TaskEditProps {
  visible: boolean
  task: CrawlerTask | null
  onClose: () => void
  onSave: (taskData: Partial<CrawlerTask>) => Promise<void>
  loading?: boolean
}

const TaskEdit: React.FC<TaskEditProps> = ({
  visible,
  task,
  onClose,
  onSave,
  loading = false,
}) => {
  const [form] = Form.useForm()

  // 重置表单数据
  useEffect(() => {
    if (visible && task) {
      form.setFieldsValue({
        task_name: task.task_name,
        task_type: task.task_type,
        priority: task.priority || 'medium',
        description: task.description || '',
        max_pages: task.max_pages || 5,
        delay_range: task.delay_range || [1, 3],
        timeout: task.timeout || 300,
        retry_count: task.retry_count || 3,
        extract_images: task.extract_images || false,
        use_proxy: task.use_proxy || false,
        random_ua: task.random_ua || false,
      })
    } else {
      form.resetFields()
    }
  }, [visible, task, form])

  // 处理保存
  const handleSubmit = async (values: any) => {
    if (!task) return

    try {
      await onSave({
        ...values,
        // 确保只更新允许的字段
        task_id: task.task_id,
      })
      message.success('任务更新成功')
      onClose()
    } catch (error) {
      console.error('更新任务失败:', error)
      // 错误处理已在父组件中完成
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
      width={600}
      destroyOnHidden
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          priority: 'medium',
          max_pages: 5,
          delay_range: [1, 3],
          timeout: 300,
          retry_count: 3,
          extract_images: false,
          use_proxy: false,
          random_ua: false,
        }}
      >
        {/* 基本信息 */}
        <Divider>基本信息</Divider>

        <Form.Item
          name="task_name"
          label="任务名称"
          rules={[
            { required: true, message: '请输入任务名称' },
            { max: 200, message: '任务名称不能超过200个字符' },
          ]}
        >
          <Input placeholder="请输入任务名称" />
        </Form.Item>

        <Form.Item
          name="task_type"
          label="任务类型"
          rules={[{ required: true, message: '请选择任务类型' }]}
        >
          <Select placeholder="请选择任务类型">
            <Option value="taobao">淘宝爬虫</Option>
            <Option value="jd">京东爬虫</Option>
            <Option value="pdd">拼多多爬虫</Option>
            <Option value="forum">论坛爬虫</Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="priority"
          label="优先级"
        >
          <Select placeholder="请选择优先级">
            <Option value="high">高优先级</Option>
            <Option value="medium">中优先级</Option>
            <Option value="low">低优先级</Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="description"
          label="任务描述"
        >
          <TextArea
            rows={3}
            placeholder="请输入任务描述（可选）"
            maxLength={500}
            showCount
          />
        </Form.Item>

        {/* 爬取配置 */}
        <Divider>爬取配置</Divider>

        <Form.Item
          name="max_pages"
          label="最大爬取页数"
          rules={[
            { required: true, message: '请输入最大爬取页数' },
            { type: 'number', min: 1, max: 50, message: '页数必须在1-50之间' },
          ]}
        >
          <InputNumber
            min={1}
            max={50}
            placeholder="请输入最大爬取页数"
            style={{ width: '100%' }}
          />
        </Form.Item>

        <Form.Item
          label="请求延迟范围（秒）"
          help="设置每次请求之间的延迟时间，避免被反爬虫系统检测"
        >
          <div style={{ display: 'flex', gap: '10px' }}>
            <Form.Item
              name={['delay_range', 0]}
              rules={[{ required: true, message: '请输入最小延迟' }]}
              style={{ flex: 1, marginBottom: 0 }}
            >
              <InputNumber
                min={0}
                max={10}
                placeholder="最小延迟"
                style={{ width: '100%' }}
              />
            </Form.Item>
            <Form.Item
              name={['delay_range', 1]}
              rules={[{ required: true, message: '请输入最大延迟' }]}
              style={{ flex: 1, marginBottom: 0 }}
            >
              <InputNumber
                min={0}
                max={10}
                placeholder="最大延迟"
                style={{ width: '100%' }}
              />
            </Form.Item>
          </div>
        </Form.Item>

        {/* 高级设置 */}
        <Divider>高级设置</Divider>

        <Form.Item
          name="timeout"
          label="超时时间（秒）"
          rules={[
            { required: true, message: '请输入超时时间' },
            { type: 'number', min: 10, max: 3600, message: '超时时间必须在10-3600秒之间' },
          ]}
        >
          <InputNumber
            min={10}
            max={3600}
            placeholder="请输入超时时间"
            style={{ width: '100%' }}
          />
        </Form.Item>

        <Form.Item
          name="retry_count"
          label="重试次数"
          rules={[
            { required: true, message: '请输入重试次数' },
            { type: 'number', min: 0, max: 10, message: '重试次数必须在0-10之间' },
          ]}
        >
          <InputNumber
            min={0}
            max={10}
            placeholder="请输入重试次数"
            style={{ width: '100%' }}
          />
        </Form.Item>

        {/* 开关选项 */}
        <Form.Item name="extract_images" valuePropName="checked">
          <Switch /> 提取图片
        </Form.Item>

        <Form.Item name="use_proxy" valuePropName="checked">
          <Switch /> 使用代理
        </Form.Item>

        <Form.Item name="random_ua" valuePropName="checked">
          <Switch /> 随机User-Agent
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default TaskEdit