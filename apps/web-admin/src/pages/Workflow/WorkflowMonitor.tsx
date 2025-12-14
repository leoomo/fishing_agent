import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Progress,
  Modal,
  Descriptions,
  Timeline,
  Badge,
  Statistic,
  Row,
  Col,
  Typography,
  message,
  Tooltip,
  Popconfirm,
  Input,
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  ReloadOutlined,
  SearchOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { workflowApi } from '../../api/workflow';
import type { WorkflowStatus, WorkflowTaskStatus } from '../../api/workflow';
import { formatDateTime } from '../../utils/date';

const { Title, Text } = Typography;
const { Search } = Input;

const WorkflowMonitor: React.FC = () => {
  const [workflows, setWorkflows] = useState<WorkflowStatus[]>([]);
  const [loading, setLoading] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [currentWorkflow, setCurrentWorkflow] = useState<WorkflowStatus | null>(null);
  const [searchText, setSearchText] = useState('');
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);

  // Fetch workflow statuses
  const fetchWorkflows = async () => {
    setLoading(true);
    try {
      // Note: This would typically be an API call to list active workflows
      // For now, we'll simulate with some test data
      // const response = await workflowApi.getActiveWorkflows();
      // setWorkflows(response.data);

      // Simulated data
      setWorkflows([
        {
          workflow_id: 'workflow-12345',
          template_name: '电商数据采集流程',
          status: 'running',
          created_at: new Date().toISOString(),
          started_at: new Date(Date.now() - 5 * 60000).toISOString(),
          completed_at: undefined,
          tasks: [
            {
              task_id: 1001,
              step_id: 'step_1',
              step_name: '初始化',
              status: 'success',
              created_at: new Date(Date.now() - 5 * 60000).toISOString(),
              start_time: new Date(Date.now() - 5 * 60000).toISOString(),
              end_time: new Date(Date.now() - 4 * 60000).toISOString(),
              total_items: 0,
              success_items: 0,
              failed_items: 0,
            },
            {
              task_id: 1002,
              step_id: 'step_2',
              step_name: '淘宝数据抓取',
              status: 'running',
              created_at: new Date(Date.now() - 4 * 60000).toISOString(),
              start_time: new Date(Date.now() - 4 * 60000).toISOString(),
              end_time: undefined,
              total_items: 100,
              success_items: 45,
              failed_items: 2,
            },
            {
              task_id: 1003,
              step_id: 'step_3',
              step_name: '数据清洗',
              status: 'pending',
              created_at: new Date(Date.now() - 3 * 60000).toISOString(),
              total_items: 0,
              success_items: 0,
              failed_items: 0,
            },
          ],
          progress_percentage: 30,
        },
        {
          workflow_id: 'workflow-67890',
          template_name: '定时监控任务',
          status: 'success',
          created_at: new Date(Date.now() - 30 * 60000).toISOString(),
          started_at: new Date(Date.now() - 30 * 60000).toISOString(),
          completed_at: new Date(Date.now() - 5 * 60000).toISOString(),
          tasks: [
            {
              task_id: 2001,
              step_id: 'step_1',
              step_name: '系统检查',
              status: 'success',
              created_at: new Date(Date.now() - 30 * 60000).toISOString(),
              start_time: new Date(Date.now() - 30 * 60000).toISOString(),
              end_time: new Date(Date.now() - 28 * 60000).toISOString(),
              total_items: 10,
              success_items: 10,
              failed_items: 0,
            },
            {
              task_id: 2002,
              step_id: 'step_2',
              step_name: '发送报告',
              status: 'success',
              created_at: new Date(Date.now() - 28 * 60000).toISOString(),
              start_time: new Date(Date.now() - 28 * 60000).toISOString(),
              end_time: new Date(Date.now() - 5 * 60000).toISOString(),
              total_items: 1,
              success_items: 1,
              failed_items: 0,
            },
          ],
          progress_percentage: 100,
        },
      ]);
    } catch (error) {
      message.error('获取工作流状态失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkflows();

    // Set up auto-refresh
    const interval = setInterval(() => {
      fetchWorkflows();
    }, 5000);

    setRefreshInterval(interval);

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, []);

  // Handle pause workflow
  const handlePause = async (workflowId: string) => {
    try {
      await workflowApi.pauseWorkflow(workflowId);
      message.success('工作流已暂停');
      fetchWorkflows();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '暂停失败');
    }
  };

  // Handle resume workflow
  const handleResume = async (workflowId: string) => {
    try {
      await workflowApi.resumeWorkflow(workflowId);
      message.success('工作流已恢复');
      fetchWorkflows();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '恢复失败');
    }
  };

  // Handle cancel workflow
  const handleCancel = async (workflowId: string) => {
    try {
      await workflowApi.cancelWorkflow(workflowId);
      message.success('工作流已取消');
      fetchWorkflows();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '取消失败');
    }
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'processing';
      case 'success':
        return 'success';
      case 'failed':
        return 'error';
      case 'pending':
        return 'default';
      default:
        return 'default';
    }
  };

  // Get status text
  const getStatusText = (status: string) => {
    switch (status) {
      case 'running':
        return '运行中';
      case 'success':
        return '已完成';
      case 'failed':
        return '失败';
      case 'pending':
        return '等待中';
      default:
        return status;
    }
  };

  // Filter workflows
  const filteredWorkflows = workflows.filter(workflow =>
    workflow.template_name.toLowerCase().includes(searchText.toLowerCase()) ||
    workflow.workflow_id.toLowerCase().includes(searchText.toLowerCase())
  );

  // Calculate statistics
  const stats = {
    total: workflows.length,
    running: workflows.filter(w => w.status === 'running').length,
    success: workflows.filter(w => w.status === 'success').length,
    failed: workflows.filter(w => w.status === 'failed').length,
    pending: workflows.filter(w => w.status === 'pending').length,
  };

  const columns = [
    {
      title: '工作流ID',
      dataIndex: 'workflow_id',
      key: 'workflow_id',
      width: 200,
      render: (text: string) => (
        <Text code copyable>{text}</Text>
      ),
    },
    {
      title: '模板名称',
      dataIndex: 'template_name',
      key: 'template_name',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Badge status={getStatusColor(status) as any} text={getStatusText(status)} />
      ),
    },
    {
      title: '进度',
      dataIndex: 'progress_percentage',
      key: 'progress',
      render: (progress: number, record: WorkflowStatus) => (
        <Tooltip title={`${record.tasks.filter(t => t.status === 'success').length}/${record.tasks.length} 任务完成`}>
          <Progress
            percent={progress}
            size="small"
            status={record.status === 'failed' ? 'exception' : undefined}
          />
        </Tooltip>
      ),
    },
    {
      title: '任务统计',
      key: 'taskStats',
      render: (record: WorkflowStatus) => (
        <Space>
          <Tag color="green">成功: {record.tasks.filter(t => t.status === 'success').length}</Tag>
          <Tag color="blue">运行: {record.tasks.filter(t => t.status === 'running').length}</Tag>
          <Tag color="orange">等待: {record.tasks.filter(t => t.status === 'pending').length}</Tag>
          <Tag color="red">失败: {record.tasks.filter(t => t.status === 'failed').length}</Tag>
        </Space>
      ),
    },
    {
      title: '开始时间',
      dataIndex: 'started_at',
      key: 'started_at',
      render: (text: string) => text ? formatDateTime(text) : '-',
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: WorkflowStatus) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => {
              setCurrentWorkflow(record);
              setDetailModalVisible(true);
            }}
          >
            详情
          </Button>
          {record.status === 'running' && (
            <Button
              type="link"
              icon={<PauseCircleOutlined />}
              onClick={() => handlePause(record.workflow_id)}
            >
              暂停
            </Button>
          )}
          {record.status === 'pending' && (
            <Popconfirm
              title="确定要取消这个工作流吗？"
              onConfirm={() => handleCancel(record.workflow_id)}
            >
              <Button type="link" danger icon={<StopOutlined />}>
                取消
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* Statistics Cards */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总工作流数"
              value={stats.total}
              prefix={<PlayCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="运行中"
              value={stats.running}
              valueStyle={{ color: '#1890ff' }}
              prefix={<ReloadOutlined spin />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已完成"
              value={stats.success}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="失败"
              value={stats.failed}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      <Card>
        <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
          <Col>
            <Title level={3}>工作流监控</Title>
          </Col>
          <Col>
            <Space>
              <Search
                placeholder="搜索工作流ID或模板名称"
                allowClear
                style={{ width: 300 }}
                onSearch={setSearchText}
                onChange={(e) => setSearchText(e.target.value)}
              />
              <Button
                icon={<ReloadOutlined />}
                onClick={fetchWorkflows}
                loading={loading}
              >
                刷新
              </Button>
            </Space>
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={filteredWorkflows}
          rowKey="workflow_id"
          loading={loading}
          pagination={{
            showSizeChanger: false,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>

      {/* Detail Modal */}
      <Modal
        title="工作流详情"
        visible={detailModalVisible}
        onCancel={() => {
          setDetailModalVisible(false);
          setCurrentWorkflow(null);
        }}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>,
        ]}
        width={800}
      >
        {currentWorkflow && (
          <Tabs defaultActiveKey="1">
            <TabPane tab="基本信息" key="1">
              <Descriptions column={2} bordered>
                <Descriptions.Item label="工作流ID">
                  <Text code>{currentWorkflow.workflow_id}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="模板名称">
                  {currentWorkflow.template_name}
                </Descriptions.Item>
                <Descriptions.Item label="状态">
                  <Badge
                    status={getStatusColor(currentWorkflow.status) as any}
                    text={getStatusText(currentWorkflow.status)}
                  />
                </Descriptions.Item>
                <Descriptions.Item label="进度">
                  <Progress
                    percent={currentWorkflow.progress_percentage}
                    status={currentWorkflow.status === 'failed' ? 'exception' : undefined}
                  />
                </Descriptions.Item>
                <Descriptions.Item label="创建时间">
                  {formatDateTime(currentWorkflow.created_at)}
                </Descriptions.Item>
                <Descriptions.Item label="开始时间">
                  {currentWorkflow.started_at ? formatDateTime(currentWorkflow.started_at) : '-'}
                </Descriptions.Item>
                <Descriptions.Item label="完成时间" span={2}>
                  {currentWorkflow.completed_at ? formatDateTime(currentWorkflow.completed_at) : '-'}
                </Descriptions.Item>
              </Descriptions>
            </TabPane>
            <TabPane tab="任务详情" key="2">
              <Timeline mode="left">
                {currentWorkflow.tasks.map((task, index) => (
                  <Timeline.Item
                    key={task.task_id}
                    color={
                      task.status === 'success' ? 'green' :
                      task.status === 'failed' ? 'red' :
                      task.status === 'running' ? 'blue' : 'gray'
                    }
                    dot={
                      task.status === 'running' ? <ReloadOutlined spin /> : undefined
                    }
                  >
                    <Card size="small" style={{ marginBottom: 8 }}>
                      <Row justify="space-between">
                        <Col>
                          <Text strong>{task.step_name}</Text>
                          <Text type="secondary" style={{ marginLeft: 8 }}>
                            (ID: {task.step_id})
                          </Text>
                        </Col>
                        <Col>
                          <Tag color={
                            task.status === 'success' ? 'green' :
                            task.status === 'failed' ? 'red' :
                            task.status === 'running' ? 'blue' : 'default'
                          }>
                            {getStatusText(task.status)}
                          </Tag>
                        </Col>
                      </Row>
                      {task.start_time && (
                        <Row style={{ marginTop: 8 }}>
                          <Col span={12}>
                            <Text type="secondary">
                              开始: {formatDateTime(task.start_time)}
                            </Text>
                          </Col>
                          {task.end_time && (
                            <Col span={12}>
                              <Text type="secondary">
                                结束: {formatDateTime(task.end_time)}
                              </Text>
                            </Col>
                          )}
                        </Row>
                      )}
                      {(task.total_items > 0 || task.success_items > 0 || task.failed_items > 0) && (
                        <Row style={{ marginTop: 8 }}>
                          <Col span={24}>
                            <Space>
                              <Text type="secondary">处理项数:</Text>
                              <Tag color="green">成功: {task.success_items}</Tag>
                              {task.failed_items > 0 && (
                                <Tag color="red">失败: {task.failed_items}</Tag>
                              )}
                              <Text type="secondary">
                                总计: {task.total_items}
                              </Text>
                            </Space>
                          </Col>
                        </Row>
                      )}
                      {task.error_message && (
                        <Row style={{ marginTop: 8 }}>
                          <Col span={24}>
                            <Text type="danger">{task.error_message}</Text>
                          </Col>
                        </Row>
                      )}
                    </Card>
                  </Timeline.Item>
                ))}
              </Timeline>
            </TabPane>
          </Tabs>
        )}
      </Modal>
    </div>
  );
};

export default WorkflowMonitor;