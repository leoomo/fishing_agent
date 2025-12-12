import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Card,
  Typography,
  Row,
  Col,
  Switch,
  Descriptions,
  Divider,
  Timeline,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  EyeOutlined,
  HistoryOutlined,
} from '@ant-design/icons';
import { workflowApi, Schedule, CreateScheduleRequest, WorkflowTemplate } from '../../api/workflow';
import CronEditor from '../../components/CronEditor';
import { formatDateTime } from '../../utils/date';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const ScheduleManager: React.FC = () => {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [viewModalVisible, setViewModalVisible] = useState(false);
  const [currentSchedule, setCurrentSchedule] = useState<Schedule | null>(null);
  const [form] = Form.useForm();
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(20);
  const [schedulerStatus, setSchedulerStatus] = useState<any>(null);

  // Fetch schedules
  const fetchSchedules = async (page = 1) => {
    setLoading(true);
    try {
      const response = await workflowApi.getSchedules({
        page,
        page_size: pageSize,
      });
      setSchedules(response.data.items);
      setTotal(response.data.total);
      setCurrentPage(response.data.page);
    } catch (error) {
      message.error('获取调度列表失败');
    } finally {
      setLoading(false);
    }
  };

  // Fetch templates
  const fetchTemplates = async () => {
    try {
      const response = await workflowApi.getTemplates({
        page: 1,
        page_size: 1000,
      });
      setTemplates(response.data.items);
    } catch (error) {
      message.error('获取模板列表失败');
    }
  };

  // Fetch scheduler status
  const fetchSchedulerStatus = async () => {
    try {
      const response = await workflowApi.getSchedulerStatus();
      setSchedulerStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch scheduler status:', error);
    }
  };

  useEffect(() => {
    fetchSchedules();
    fetchTemplates();
    fetchSchedulerStatus();

    // Set up interval to refresh scheduler status
    const interval = setInterval(() => {
      fetchSchedulerStatus();
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  // Handle create/update
  const handleSubmit = async (values: any) => {
    try {
      const data: CreateScheduleRequest = {
        name: values.name,
        template_id: values.template_id,
        cron_expression: values.cron_expression,
        timezone: values.timezone || 'Asia/Shanghai',
        params: values.params ? JSON.parse(values.params) : {},
        is_enabled: values.is_enabled !== false,
        max_instances: values.max_instances || 1,
        timeout_seconds: values.timeout_seconds || 3600,
        description: values.description,
      };

      if (currentSchedule) {
        await workflowApi.updateSchedule(currentSchedule.id, data);
        message.success('更新成功');
      } else {
        await workflowApi.createSchedule(data);
        message.success('创建成功');
      }

      setModalVisible(false);
      form.resetFields();
      setCurrentSchedule(null);
      fetchSchedules(currentPage);
      fetchSchedulerStatus();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败');
    }
  };

  // Handle delete
  const handleDelete = async (id: number) => {
    try {
      await workflowApi.deleteSchedule(id);
      message.success('删除成功');
      fetchSchedules(currentPage);
      fetchSchedulerStatus();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败');
    }
  };

  // Handle enable/disable
  const handleToggleEnabled = async (schedule: Schedule) => {
    try {
      if (schedule.is_enabled) {
        await workflowApi.disableSchedule(schedule.id);
        message.success('调度已禁用');
      } else {
        await workflowApi.enableSchedule(schedule.id);
        message.success('调度已启用');
      }
      fetchSchedules(currentPage);
      fetchSchedulerStatus();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败');
    }
  };

  // View schedule details
  const handleView = (schedule: Schedule) => {
    setCurrentSchedule(schedule);
    setViewModalVisible(true);
  };

  // Get template name
  const getTemplateName = (templateId: number) => {
    const template = templates.find(t => t.id === templateId);
    return template ? template.name : '未知模板';
  };

  // Columns for table
  const columns = [
    {
      title: '调度名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Schedule) => (
        <Space direction="vertical" size="small">
          <Text strong>{text}</Text>
          {record.description && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {record.description}
            </Text>
          )}
        </Space>
      ),
    },
    {
      title: '关联模板',
      dataIndex: 'template_id',
      key: 'template_id',
      render: (templateId: number) => (
        <Text>{getTemplateName(templateId)}</Text>
      ),
    },
    {
      title: 'Cron表达式',
      dataIndex: 'cron_expression',
      key: 'cron_expression',
      render: (text: string) => (
        <Text code copyable>{text}</Text>
      ),
    },
    {
      title: '时区',
      dataIndex: 'timezone',
      key: 'timezone',
    },
    {
      title: '状态',
      dataIndex: 'is_enabled',
      key: 'is_enabled',
      render: (isEnabled: boolean, record: Schedule) => (
        <Space>
          <Switch
            checked={isEnabled}
            onChange={() => handleToggleEnabled(record)}
            loading={loading}
          />
          <Tag color={isEnabled ? 'green' : 'default'}>
            {isEnabled ? '启用' : '禁用'}
          </Tag>
        </Space>
      ),
    },
    {
      title: '运行统计',
      key: 'stats',
      render: (record: Schedule) => (
        <Space>
          <Tag color="blue">总计: {record.run_count}</Tag>
          <Tag color="green">成功: {record.success_count}</Tag>
          {record.failure_count > 0 && (
            <Tag color="red">失败: {record.failure_count}</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '上次运行',
      dataIndex: 'last_run_at',
      key: 'last_run_at',
      render: (text: string) => text ? formatDateTime(text) : '从未运行',
    },
    {
      title: '下次运行',
      dataIndex: 'next_run_at',
      key: 'next_run_at',
      render: (text: string) => text ? formatDateTime(text) : '-',
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: Schedule) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleView(record)}
          >
            详情
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => {
              setCurrentSchedule(record);
              form.setFieldsValue({
                name: record.name,
                template_id: record.template_id,
                cron_expression: record.cron_expression,
                timezone: record.timezone,
                params: JSON.stringify(record.params, null, 2),
                is_enabled: record.is_enabled,
                max_instances: record.max_instances,
                timeout_seconds: record.timeout_seconds,
                description: record.description,
              });
              setModalVisible(true);
            }}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个调度吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* Scheduler Status Card */}
      {schedulerStatus && (
        <Card style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col span={6}>
              <Card size="small">
                <Text type="secondary">调度器状态</Text>
                <div style={{ marginTop: 8 }}>
                  <Tag color={schedulerStatus.scheduler_state === 0 ? 'green' : 'red'}>
                    {schedulerStatus.scheduler_state === 0 ? '运行中' : '已停止'}
                  </Tag>
                </div>
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Text type="secondary">总任务数</Text>
                <div style={{ marginTop: 8 }}>
                  <Text strong style={{ fontSize: 18 }}>{schedulerStatus.total_jobs}</Text>
                </div>
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Text type="secondary">活跃调度</Text>
                <div style={{ marginTop: 8 }}>
                  <Text strong style={{ fontSize: 18 }}>{schedulerStatus.schedule_jobs}</Text>
                </div>
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Text type="secondary">已加载</Text>
                <div style={{ marginTop: 8 }}>
                  <Text strong style={{ fontSize: 18 }}>{schedulerStatus.loaded_schedules}</Text>
                </div>
              </Card>
            </Col>
          </Row>
        </Card>
      )}

      <Card>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={3}>
              <HistoryOutlined /> 定时调度管理
            </Title>
          </Col>
          <Col>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                setCurrentSchedule(null);
                form.resetFields();
                setModalVisible(true);
              }}
            >
              创建调度
            </Button>
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={schedules}
          rowKey="id"
          loading={loading}
          pagination={{
            current: currentPage,
            total: total,
            pageSize: pageSize,
            onChange: fetchSchedules,
            showSizeChanger: false,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        title={currentSchedule ? '编辑调度' : '创建调度'}
        visible={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
          setCurrentSchedule(null);
        }}
        footer={null}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            timezone: 'Asia/Shanghai',
            is_enabled: true,
            max_instances: 1,
            timeout_seconds: 3600,
          }}
        >
          <Form.Item
            label="调度名称"
            name="name"
            rules={[{ required: true, message: '请输入调度名称' }]}
          >
            <Input placeholder="输入调度名称" />
          </Form.Item>

          <Form.Item
            label="关联模板"
            name="template_id"
            rules={[{ required: true, message: '请选择工作流模板' }]}
          >
            <Select placeholder="选择工作流模板">
              {templates.map(template => (
                <Select.Option key={template.id} value={template.id}>
                  {template.name} (v{template.version})
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item label="描述" name="description">
            <TextArea rows={2} placeholder="输入调度描述（可选）" />
          </Form.Item>

          <Form.Item
            label="Cron表达式"
            name="cron_expression"
            rules={[{ required: true, message: '请设置执行时间' }]}
          >
            <CronEditor
              onChange={(value) => {
                form.setFieldsValue({ cron_expression: value });
              }}
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item label="最大并发实例" name="max_instances">
                <InputNumber min={1} max={10} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="超时时间（秒）" name="timeout_seconds">
                <InputNumber min={60} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="启用状态" name="is_enabled" valuePropName="checked">
                <Switch checkedChildren="启用" unCheckedChildren="禁用" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="执行参数" name="params">
            <TextArea
              rows={3}
              placeholder='{"key": "value"}'
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>

          <Form.Item style={{ marginTop: 24, textAlign: 'right' }}>
            <Space>
              <Button
                onClick={() => {
                  setModalVisible(false);
                  form.resetFields();
                  setCurrentSchedule(null);
                }}
              >
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                {currentSchedule ? '更新' : '创建'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* View Modal */}
      <Modal
        title="调度详情"
        visible={viewModalVisible}
        onCancel={() => {
          setViewModalVisible(false);
          setCurrentSchedule(null);
        }}
        footer={[
          <Button key="close" onClick={() => setViewModalVisible(false)}>
            关闭
          </Button>,
        ]}
        width={800}
      >
        {currentSchedule && (
          <Tabs defaultActiveKey="1">
            <TabPane tab="基本信息" key="1">
              <Descriptions column={2} bordered>
                <Descriptions.Item label="调度名称">
                  {currentSchedule.name}
                </Descriptions.Item>
                <Descriptions.Item label="关联模板">
                  {getTemplateName(currentSchedule.template_id)}
                </Descriptions.Item>
                <Descriptions.Item label="Cron表达式">
                  <Text code copyable>{currentSchedule.cron_expression}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="时区">
                  {currentSchedule.timezone}
                </Descriptions.Item>
                <Descriptions.Item label="状态">
                  <Tag color={currentSchedule.is_enabled ? 'green' : 'default'}>
                    {currentSchedule.is_enabled ? '启用' : '禁用'}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="最大并发实例">
                  {currentSchedule.max_instances}
                </Descriptions.Item>
                <Descriptions.Item label="超时时间">
                  {currentSchedule.timeout_seconds} 秒
                </Descriptions.Item>
                <Descriptions.Item label="创建者">
                  {currentSchedule.created_by || '未知'}
                </Descriptions.Item>
                <Descriptions.Item label="创建时间">
                  {formatDateTime(currentSchedule.created_at)}
                </Descriptions.Item>
                <Descriptions.Item label="上次运行">
                  {currentSchedule.last_run_at ? formatDateTime(currentSchedule.last_run_at) : '从未运行'}
                </Descriptions.Item>
                <Descriptions.Item label="下次运行">
                  {currentSchedule.next_run_at ? formatDateTime(currentSchedule.next_run_at) : '-'}
                </Descriptions.Item>
              </Descriptions>
            </TabPane>
            <TabPane tab="执行统计" key="2">
              <Row gutter={16}>
                <Col span={8}>
                  <Card size="small">
                    <Statistic
                      title="总执行次数"
                      value={currentSchedule.run_count}
                      prefix={<PlayCircleOutlined />}
                    />
                  </Card>
                </Col>
                <Col span={8}>
                  <Card size="small">
                    <Statistic
                      title="成功次数"
                      value={currentSchedule.success_count}
                      valueStyle={{ color: '#52c41a' }}
                    />
                  </Card>
                </Col>
                <Col span={8}>
                  <Card size="small">
                    <Statistic
                      title="失败次数"
                      value={currentSchedule.failure_count}
                      valueStyle={{ color: '#ff4d4f' }}
                    />
                  </Card>
                </Col>
              </Row>
            </TabPane>
            <TabPane tab="执行参数" key="3">
              <Card>
                <pre style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
                  {JSON.stringify(currentSchedule.params, null, 2)}
                </pre>
              </Card>
            </TabPane>
          </Tabs>
        )}
      </Modal>
    </div>
  );
};

export default ScheduleManager;