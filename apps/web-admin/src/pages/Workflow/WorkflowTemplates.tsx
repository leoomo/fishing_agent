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
  Divider,
  Tabs,
  List,
  Badge,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  CopyOutlined,
  EyeOutlined,
  BranchesOutlined,
} from '@ant-design/icons';
import { workflowApi } from '../../api/workflow';
import type { WorkflowTemplate, CreateWorkflowTemplateRequest } from '../../api/workflow';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { TabPane } = Tabs;

const WorkflowTemplates: React.FC = () => {
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [viewModalVisible, setViewModalVisible] = useState(false);
  const [currentTemplate, setCurrentTemplate] = useState<WorkflowTemplate | null>(null);
  const [form] = Form.useForm();
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(20);

  // Fetch templates
  const fetchTemplates = async (page = 1) => {
    setLoading(true);
    try {
      const response = await workflowApi.getTemplates({
        page,
        page_size: pageSize,
      });
      setTemplates(response.data.items);
      setTotal(response.data.total);
      setCurrentPage(response.data.page);
    } catch (error) {
      message.error('获取工作流模板失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

  // Handle create/update
  const handleSubmit = async (values: any) => {
    try {
      const data: CreateWorkflowTemplateRequest = {
        name: values.name,
        description: values.description,
        category: values.category || 'custom',
        version: values.version || '1.0',
        tags: values.tags || [],
        workflow_def: {
          name: values.name,
          description: values.description,
          version: values.version || '1.0',
          steps: values.steps || [],
        },
      };

      if (currentTemplate) {
        await workflowApi.updateTemplate(currentTemplate.id, data);
        message.success('更新成功');
      } else {
        await workflowApi.createTemplate(data);
        message.success('创建成功');
      }

      setModalVisible(false);
      form.resetFields();
      setCurrentTemplate(null);
      fetchTemplates(currentPage);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败');
    }
  };

  // Handle delete
  const handleDelete = async (id: number) => {
    try {
      await workflowApi.deleteTemplate(id);
      message.success('删除成功');
      fetchTemplates(currentPage);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败');
    }
  };

  // Handle execute
  const handleExecute = async (template: WorkflowTemplate) => {
    try {
      const result = await workflowApi.executeWorkflow({
        template_id: template.id,
      });
      message.success(`工作流已启动，ID: ${result.data.workflow_id}`);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '执行失败');
    }
  };

  // Handle duplicate
  const handleDuplicate = (template: WorkflowTemplate) => {
    setCurrentTemplate(null);
    form.setFieldsValue({
      name: `${template.name} - 副本`,
      description: template.description,
      category: template.category,
      version: '1.0',
      tags: template.tags,
      steps: template.workflow_def.steps,
    });
    setModalVisible(true);
  };

  // View template details
  const handleView = (template: WorkflowTemplate) => {
    setCurrentTemplate(template);
    setViewModalVisible(true);
  };

  // Columns for table
  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: WorkflowTemplate) => (
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
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => (
        <Tag color={category === 'system' ? 'red' : 'blue'}>
          {category || 'custom'}
        </Tag>
      ),
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
    },
    {
      title: '步骤数',
      key: 'steps',
      render: (record: WorkflowTemplate) => (
        <Badge count={record.workflow_def.steps.length} showZero />
      ),
    },
    {
      title: '使用次数',
      dataIndex: 'usage_count',
      key: 'usage_count',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Badge status={isActive ? 'success' : 'default'} text={isActive ? '启用' : '禁用'} />
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => new Date(text).toLocaleString(),
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: WorkflowTemplate) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleView(record)}
          >
            查看
          </Button>
          <Button
            type="link"
            icon={<PlayCircleOutlined />}
            onClick={() => handleExecute(record)}
          >
            执行
          </Button>
          <Button
            type="link"
            icon={<CopyOutlined />}
            onClick={() => handleDuplicate(record)}
          >
            复制
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => {
              setCurrentTemplate(record);
              form.setFieldsValue({
                name: record.name,
                description: record.description,
                category: record.category,
                version: record.version,
                tags: record.tags,
                steps: record.workflow_def.steps,
              });
              setModalVisible(true);
            }}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个模板吗？"
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
      <Card>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={3}>
              <BranchesOutlined /> 工作流模板
            </Title>
          </Col>
          <Col>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                setCurrentTemplate(null);
                form.resetFields();
                setModalVisible(true);
              }}
            >
              创建模板
            </Button>
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={templates}
          rowKey="id"
          loading={loading}
          pagination={{
            current: currentPage,
            total: total,
            pageSize: pageSize,
            onChange: fetchTemplates,
            showSizeChanger: false,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        title={currentTemplate ? '编辑工作流模板' : '创建工作流模板'}
        visible={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
          setCurrentTemplate(null);
        }}
        footer={null}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            category: 'custom',
            version: '1.0',
            steps: [],
          }}
        >
          <Form.Item
            label="模板名称"
            name="name"
            rules={[{ required: true, message: '请输入模板名称' }]}
          >
            <Input placeholder="输入模板名称" />
          </Form.Item>

          <Form.Item label="描述" name="description">
            <TextArea rows={3} placeholder="输入模板描述" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item label="分类" name="category">
                <Select>
                  <Select.Option value="custom">自定义</Select.Option>
                  <Select.Option value="system">系统</Select.Option>
                  <Select.Option value="test">测试</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="版本" name="version">
                <Input placeholder="1.0" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="标签" name="tags">
                <Select mode="tags" placeholder="添加标签">
                  <Select.Option value="数据采集">数据采集</Select.Option>
                  <Select.Option value="定时任务">定时任务</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider>工作流步骤</Divider>

          <Form.Item name="steps">
            <div style={{ textAlign: 'center', padding: '20px' }}>
              <Text type="secondary">
                工作流步骤编辑器将在后续版本中提供
              </Text>
              <br />
              <Text type="secondary" style={{ fontSize: 12 }}>
                目前可通过API直接创建复杂的工作流模板
              </Text>
            </div>
          </Form.Item>

          <Form.Item style={{ marginTop: 24, textAlign: 'right' }}>
            <Space>
              <Button
                onClick={() => {
                  setModalVisible(false);
                  form.resetFields();
                  setCurrentTemplate(null);
                }}
              >
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                {currentTemplate ? '更新' : '创建'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* View Modal */}
      <Modal
        title="工作流模板详情"
        visible={viewModalVisible}
        onCancel={() => {
          setViewModalVisible(false);
          setCurrentTemplate(null);
        }}
        footer={[
          <Button key="close" onClick={() => setViewModalVisible(false)}>
            关闭
          </Button>,
        ]}
        width={800}
      >
        {currentTemplate && (
          <Tabs defaultActiveKey="1">
            <TabPane tab="基本信息" key="1">
              <Row gutter={16}>
                <Col span={12}>
                  <Text strong>名称：</Text>
                  <Text>{currentTemplate.name}</Text>
                </Col>
                <Col span={12}>
                  <Text strong>版本：</Text>
                  <Text>{currentTemplate.version}</Text>
                </Col>
              </Row>
              <Row gutter={16} style={{ marginTop: 16 }}>
                <Col span={12}>
                  <Text strong>分类：</Text>
                  <Tag color={currentTemplate.category === 'system' ? 'red' : 'blue'}>
                    {currentTemplate.category}
                  </Tag>
                </Col>
                <Col span={12}>
                  <Text strong>状态：</Text>
                  <Badge
                    status={currentTemplate.is_active ? 'success' : 'default'}
                    text={currentTemplate.is_active ? '启用' : '禁用'}
                  />
                </Col>
              </Row>
              <Row style={{ marginTop: 16 }}>
                <Col span={24}>
                  <Text strong>描述：</Text>
                  <Paragraph>{currentTemplate.description || '无'}</Paragraph>
                </Col>
              </Row>
              <Row gutter={16} style={{ marginTop: 16 }}>
                <Col span={8}>
                  <Text strong>使用次数：</Text>
                  <Text>{currentTemplate.usage_count}</Text>
                </Col>
                <Col span={8}>
                  <Text strong>创建者：</Text>
                  <Text>{currentTemplate.created_by || '未知'}</Text>
                </Col>
                <Col span={8}>
                  <Text strong>创建时间：</Text>
                  <Text>{new Date(currentTemplate.created_at).toLocaleString()}</Text>
                </Col>
              </Row>
            </TabPane>
            <TabPane tab="工作流步骤" key="2">
              <List
                dataSource={currentTemplate.workflow_def.steps}
                renderItem={(step, index) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<Badge count={index + 1} />}
                      title={
                        <Space>
                          <Text strong>{step.name}</Text>
                          <Tag>{step.task_type}</Tag>
                        </Space>
                      }
                      description={
                        <Space direction="vertical" size="small">
                          <Text type="secondary">步骤ID: {step.id}</Text>
                          {step.depends_on.length > 0 && (
                            <Text type="secondary">
                              依赖: {step.depends_on.join(', ')}
                            </Text>
                          )}
                          {step.config && Object.keys(step.config).length > 0 && (
                            <Text code>{JSON.stringify(step.config, null, 2)}</Text>
                          )}
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            </TabPane>
          </Tabs>
        )}
      </Modal>
    </div>
  );
};

export default WorkflowTemplates;