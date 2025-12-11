# 工作流系统开发方案 - 阶段3：React前端界面

**目标**: 实现工作流模板管理、执行监控、定时调度的React管理界面

**预估工作量**: 4-5天

**前置条件**:
- 阶段2完成（工作流管理API可用）
- React管理前端正常运行
- API服务器可访问

---

## 一、目录结构规划

```
apps/web-admin/src/
├── pages/
│   └── Workflows/                  # 工作流管理页面（新增）
│       ├── Templates.tsx           # 工作流模板管理
│       ├── Monitor.tsx             # 工作流执行监控
│       ├── Schedules.tsx           # 定时调度管理
│       └── components/             # 页面专用组件
│           ├── TemplateForm.tsx    # 模板表单
│           ├── ExecuteModal.tsx    # 执行工作流弹窗
│           └── ScheduleForm.tsx    # 调度表单
├── components/                     # 全局组件（新增）
│   └── CronEditor/                 # Cron表达式编辑器
│       ├── index.tsx
│       ├── presets.ts              # 预设模板
│       └── parser.ts               # Cron解析工具
├── services/
│   └── crawler.ts                  # API服务（扩展）
├── router/
│   └── index.tsx                   # 路由配置（扩展）
└── types/
    └── workflow.ts                 # 工作流类型定义（新增）
```

---

## 二、类型定义

**新建文件**: `apps/web-admin/src/types/workflow.ts`

```typescript
export interface WorkflowTemplate {
  id: number;
  name: string;
  description?: string;
  template_json: string;
  category?: string;
  is_system: boolean;
  created_by?: number;
  created_at: string;
  updated_at: string;
  usage_count: number;
}

export interface WorkflowExecution {
  workflow_id: string;
  workflow_name: string;
  status: 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED';
  total_steps: number;
  completed_steps: number;
  progress_percent: number;
  created_at: string;
  tasks?: WorkflowTask[];
}

export interface WorkflowTask {
  id: number;
  step_order: number;
  task_name: string;
  task_type: string;
  status: string;
  start_time?: string;
  end_time?: string;
  success_items: number;
  failed_items: number;
  error_message?: string;
}

export interface Schedule {
  id: number;
  name: string;
  template_id: number;
  template_name?: string;
  cron_expression: string;
  timezone: string;
  is_enabled: boolean;
  config?: string;
  next_run_time?: string;
  last_run_time?: string;
  last_task_id?: number;
  created_by?: number;
  created_at: string;
}
```

---

## 三、API Service扩展

**修改文件**: `apps/web-admin/src/services/crawler.ts`

```typescript
import request from '@/utils/request';

// ===== 工作流模板相关API =====

export async function getWorkflowTemplates(params?: {
  category?: string;
  search?: string;
  page?: number;
  page_size?: number;
}) {
  return request('/api/v1/admin/crawler/templates', {
    method: 'GET',
    params,
  });
}

export async function getWorkflowTemplateDetail(templateId: number) {
  return request(`/api/v1/admin/crawler/templates/${templateId}`, {
    method: 'GET',
  });
}

export async function createWorkflowTemplate(data: {
  name: string;
  description?: string;
  template_json: string;
  category?: string;
}) {
  return request('/api/v1/admin/crawler/templates', {
    method: 'POST',
    data,
  });
}

export async function updateWorkflowTemplate(templateId: number, data: any) {
  return request(`/api/v1/admin/crawler/templates/${templateId}`, {
    method: 'PUT',
    data,
  });
}

export async function deleteWorkflowTemplate(templateId: number) {
  return request(`/api/v1/admin/crawler/templates/${templateId}`, {
    method: 'DELETE',
  });
}

// ===== 工作流执行相关API =====

export async function executeWorkflow(data: {
  template_id: number;
  params: Record<string, any>;
}) {
  return request('/api/v1/admin/crawler/workflows/execute', {
    method: 'POST',
    data,
  });
}

export async function getWorkflowStatus(workflowId: string, includeTasks = true) {
  return request(`/api/v1/admin/crawler/workflows/${workflowId}`, {
    method: 'GET',
    params: { include_tasks: includeTasks },
  });
}

// ===== 定时调度相关API =====

export async function getSchedules(params?: {
  is_enabled?: boolean;
  page?: number;
  page_size?: number;
}) {
  return request('/api/v1/admin/crawler/schedules', {
    method: 'GET',
    params,
  });
}

export async function createSchedule(data: {
  name: string;
  template_id: number;
  cron_expression: string;
  timezone?: string;
  config?: Record<string, any>;
}) {
  return request('/api/v1/admin/crawler/schedules', {
    method: 'POST',
    data,
  });
}

export async function updateSchedule(scheduleId: number, data: {
  name?: string;
  cron_expression?: string;
  timezone?: string;
  is_enabled?: boolean;
  config?: Record<string, any>;
}) {
  return request(`/api/v1/admin/crawler/schedules/${scheduleId}`, {
    method: 'PUT',
    data,
  });
}

export async function deleteSchedule(scheduleId: number) {
  return request(`/api/v1/admin/crawler/schedules/${scheduleId}`, {
    method: 'DELETE',
  });
}
```

---

## 四、Cron表达式编辑器

**新建文件**: `apps/web-admin/src/components/CronEditor/presets.ts`

```typescript
export const CRON_PRESETS = [
  { label: '每分钟', value: '* * * * *' },
  { label: '每小时', value: '0 * * * *' },
  { label: '每天凌晨2点', value: '0 2 * * *' },
  { label: '每天中午12点', value: '0 12 * * *' },
  { label: '每周一凌晨2点', value: '0 2 * * 1' },
  { label: '每月1号凌晨2点', value: '0 2 1 * *' },
];

export function parseCronToHuman(cronExpression: string): string {
  // 简单解析（可使用cronstrue库更精确）
  const preset = CRON_PRESETS.find((p) => p.value === cronExpression);
  if (preset) return preset.label;

  const parts = cronExpression.split(' ');
  if (parts.length !== 5) return '自定义表达式';

  const [minute, hour, day, month, weekday] = parts;

  if (minute === '*' && hour === '*') return '每分钟';
  if (minute === '0' && hour === '*') return '每小时';
  if (minute === '0' && hour !== '*' && day === '*') return `每天${hour}点`;

  return '自定义表达式';
}
```

**新建文件**: `apps/web-admin/src/components/CronEditor/index.tsx`

```typescript
import React, { useState } from 'react';
import { Select, Input, Space, Button, Tooltip } from 'antd';
import { QuestionCircleOutlined } from '@ant-design/icons';
import { CRON_PRESETS, parseCronToHuman } from './presets';

interface CronEditorProps {
  value?: string;
  onChange?: (value: string) => void;
}

const CronEditor: React.FC<CronEditorProps> = ({ value = '0 2 * * *', onChange }) => {
  const [mode, setMode] = useState<'preset' | 'custom'>('preset');
  const [customValue, setCustomValue] = useState(value);

  const handlePresetChange = (val: string) => {
    onChange?.(val);
  };

  const handleCustomChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setCustomValue(val);
    onChange?.(val);
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <Space>
        <Button
          type={mode === 'preset' ? 'primary' : 'default'}
          onClick={() => setMode('preset')}
          size="small"
        >
          预设模板
        </Button>
        <Button
          type={mode === 'custom' ? 'primary' : 'default'}
          onClick={() => setMode('custom')}
          size="small"
        >
          自定义
        </Button>
        <Tooltip title="Cron表达式格式: 分 时 日 月 星期">
          <QuestionCircleOutlined />
        </Tooltip>
      </Space>

      {mode === 'preset' ? (
        <Select
          value={value}
          onChange={handlePresetChange}
          style={{ width: '100%' }}
          options={CRON_PRESETS}
        />
      ) : (
        <Input
          value={customValue}
          onChange={handleCustomChange}
          placeholder="0 2 * * *"
          style={{ fontFamily: 'monospace' }}
        />
      )}

      <div style={{ color: '#999', fontSize: 12 }}>
        解析: {parseCronToHuman(value)}
      </div>
    </Space>
  );
};

export default CronEditor;
```

---

## 五、工作流模板管理页面

**新建文件**: `apps/web-admin/src/pages/Workflows/Templates.tsx`

```typescript
import React, { useState, useRef } from 'react';
import { ProTable, ActionType } from '@ant-design/pro-components';
import { Button, Modal, Form, Input, Select, message, Popconfirm, Space, Tag } from 'antd';
import { PlusOutlined, PlayCircleOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import {
  getWorkflowTemplates,
  createWorkflowTemplate,
  updateWorkflowTemplate,
  deleteWorkflowTemplate,
  executeWorkflow,
} from '@/services/crawler';
import type { WorkflowTemplate } from '@/types/workflow';

const WorkflowTemplates: React.FC = () => {
  const actionRef = useRef<ActionType>();
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [executeModalVisible, setExecuteModalVisible] = useState(false);
  const [currentTemplate, setCurrentTemplate] = useState<WorkflowTemplate | null>(null);
  const [form] = Form.useForm();
  const [executeForm] = Form.useForm();

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60, search: false },
    {
      title: '模板名称',
      dataIndex: 'name',
      ellipsis: true,
      copyable: true,
    },
    {
      title: '分类',
      dataIndex: 'category',
      width: 100,
      valueType: 'select',
      valueEnum: {
        shop: { text: '店铺抓取', status: 'Processing' },
        keyword: { text: '关键词搜索', status: 'Success' },
        sync: { text: '数据同步', status: 'Default' },
      },
    },
    {
      title: '使用次数',
      dataIndex: 'usage_count',
      width: 100,
      search: false,
      sorter: true,
    },
    {
      title: '系统模板',
      dataIndex: 'is_system',
      width: 100,
      search: false,
      render: (val: boolean) => (val ? <Tag color="blue">系统</Tag> : <Tag>自定义</Tag>),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      valueType: 'dateTime',
      width: 180,
      search: false,
    },
    {
      title: '操作',
      valueType: 'option',
      width: 200,
      render: (_, record: WorkflowTemplate) => [
        <Button
          key="execute"
          type="link"
          icon={<PlayCircleOutlined />}
          onClick={() => handleExecuteClick(record)}
        >
          执行
        </Button>,
        <Button
          key="edit"
          type="link"
          icon={<EditOutlined />}
          disabled={record.is_system}
          onClick={() => handleEditClick(record)}
        >
          编辑
        </Button>,
        <Popconfirm
          key="delete"
          title="确定删除此模板吗？"
          onConfirm={() => handleDelete(record.id)}
          disabled={record.is_system}
        >
          <Button type="link" danger icon={<DeleteOutlined />} disabled={record.is_system}>
            删除
          </Button>
        </Popconfirm>,
      ],
    },
  ];

  const handleCreate = async (values: any) => {
    try {
      await createWorkflowTemplate(values);
      message.success('创建成功');
      setCreateModalVisible(false);
      form.resetFields();
      actionRef.current?.reload();
    } catch (error: any) {
      message.error(error.message || '创建失败');
    }
  };

  const handleEditClick = (record: WorkflowTemplate) => {
    setCurrentTemplate(record);
    form.setFieldsValue({
      name: record.name,
      description: record.description,
      category: record.category,
      template_json: record.template_json,
    });
    setEditModalVisible(true);
  };

  const handleUpdate = async (values: any) => {
    if (!currentTemplate) return;

    try {
      await updateWorkflowTemplate(currentTemplate.id, values);
      message.success('更新成功');
      setEditModalVisible(false);
      form.resetFields();
      actionRef.current?.reload();
    } catch (error: any) {
      message.error(error.message || '更新失败');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteWorkflowTemplate(id);
      message.success('删除成功');
      actionRef.current?.reload();
    } catch (error: any) {
      message.error(error.message || '删除失败');
    }
  };

  const handleExecuteClick = (record: WorkflowTemplate) => {
    setCurrentTemplate(record);
    executeForm.resetFields();
    setExecuteModalVisible(true);
  };

  const handleExecute = async (values: any) => {
    if (!currentTemplate) return;

    try {
      const { params } = values;
      const paramsObj = JSON.parse(params);

      const result = await executeWorkflow({
        template_id: currentTemplate.id,
        params: paramsObj,
      });

      message.success(`工作流已提交执行，ID: ${result.data.workflow_id}`);
      setExecuteModalVisible(false);

      // 跳转到监控页面
      // history.push(`/workflows/monitor/${result.data.workflow_id}`);
    } catch (error: any) {
      message.error(error.message || '执行失败');
    }
  };

  return (
    <>
      <ProTable<WorkflowTemplate>
        actionRef={actionRef}
        columns={columns}
        request={async (params, sorter) => {
          const res = await getWorkflowTemplates({
            ...params,
            page: params.current,
            page_size: params.pageSize,
          });
          return {
            data: res.data.items,
            total: res.data.total,
            success: true,
          };
        }}
        rowKey="id"
        search={{ labelWidth: 'auto' }}
        pagination={{ defaultPageSize: 20 }}
        toolBarRender={() => [
          <Button
            key="create"
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalVisible(true)}
          >
            新建模板
          </Button>,
        ]}
      />

      {/* 创建模板弹窗 */}
      <Modal
        title="新建工作流模板"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        onOk={() => form.submit()}
        width={800}
      >
        <Form form={form} onFinish={handleCreate} layout="vertical">
          <Form.Item name="name" label="模板名称" rules={[{ required: true }]}>
            <Input placeholder="例如：淘宝店铺商品抓取" />
          </Form.Item>
          <Form.Item name="category" label="分类">
            <Select>
              <Select.Option value="shop">店铺抓取</Select.Option>
              <Select.Option value="keyword">关键词搜索</Select.Option>
              <Select.Option value="sync">数据同步</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="template_json" label="工作流定义" rules={[{ required: true }]}>
            <Input.TextArea
              rows={12}
              placeholder='{"steps": [...]}'
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑模板弹窗（类似创建） */}
      <Modal
        title="编辑工作流模板"
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        onOk={() => form.submit()}
        width={800}
      >
        <Form form={form} onFinish={handleUpdate} layout="vertical">
          {/* 同创建表单 */}
        </Form>
      </Modal>

      {/* 执行工作流弹窗 */}
      <Modal
        title={`执行工作流: ${currentTemplate?.name}`}
        open={executeModalVisible}
        onCancel={() => setExecuteModalVisible(false)}
        onOk={() => executeForm.submit()}
      >
        <Form form={executeForm} onFinish={handleExecute} layout="vertical">
          <Form.Item
            name="params"
            label="执行参数（JSON格式）"
            rules={[{ required: true }]}
          >
            <Input.TextArea
              rows={6}
              placeholder='{"shop_url": "https://...", "max_pages": 10}'
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default WorkflowTemplates;
```

---

## 六、工作流监控页面（简化）

**新建文件**: `apps/web-admin/src/pages/Workflows/Monitor.tsx`

```typescript
import React, { useEffect, useState } from 'react';
import { Card, Steps, Progress, Table, Tag, Descriptions } from 'antd';
import { useParams } from 'react-router-dom';
import { getWorkflowStatus } from '@/services/crawler';
import type { WorkflowExecution } from '@/types/workflow';

const WorkflowMonitor: React.FC = () => {
  const { workflowId } = useParams<{ workflowId: string }>();
  const [workflowData, setWorkflowData] = useState<WorkflowExecution | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadWorkflowData();
    const interval = setInterval(loadWorkflowData, 5000); // 5秒刷新
    return () => clearInterval(interval);
  }, [workflowId]);

  const loadWorkflowData = async () => {
    try {
      const res = await getWorkflowStatus(workflowId!, true);
      setWorkflowData(res.data);
    } catch (error) {
      console.error('加载工作流状态失败:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>加载中...</div>;
  if (!workflowData) return <div>工作流不存在</div>;

  const statusColors = {
    SUCCESS: 'success',
    RUNNING: 'processing',
    FAILED: 'error',
    PENDING: 'default',
  };

  return (
    <div>
      <Card title="工作流执行进度" style={{ marginBottom: 16 }}>
        <Descriptions column={2}>
          <Descriptions.Item label="工作流ID">{workflowData.workflow_id}</Descriptions.Item>
          <Descriptions.Item label="名称">{workflowData.workflow_name}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={statusColors[workflowData.status]}>{workflowData.status}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">{workflowData.created_at}</Descriptions.Item>
        </Descriptions>

        <Progress
          percent={workflowData.progress_percent}
          status={workflowData.status === 'FAILED' ? 'exception' : 'active'}
          style={{ marginTop: 16 }}
        />
      </Card>

      <Card title="任务详情">
        <Table
          dataSource={workflowData.tasks}
          rowKey="id"
          columns={[
            { title: '步骤', dataIndex: 'step_order', width: 60 },
            { title: '任务名称', dataIndex: 'task_name' },
            {
              title: '状态',
              dataIndex: 'status',
              render: (status) => <Tag color={statusColors[status]}>{status}</Tag>,
            },
            { title: '成功数', dataIndex: 'success_items', width: 80 },
            { title: '失败数', dataIndex: 'failed_items', width: 80 },
            { title: '开始时间', dataIndex: 'start_time', valueType: 'dateTime', width: 180 },
          ]}
          pagination={false}
        />
      </Card>
    </div>
  );
};

export default WorkflowMonitor;
```

---

## 七、定时调度管理页面（简化）

**新建文件**: `apps/web-admin/src/pages/Workflows/Schedules.tsx`

```typescript
import React, { useRef, useState } from 'react';
import { ProTable, ActionType } from '@ant-design/pro-components';
import { Button, Modal, Form, Input, Switch, message, Popconfirm, Tag } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import {
  getSchedules,
  createSchedule,
  updateSchedule,
  deleteSchedule,
  getWorkflowTemplates,
} from '@/services/crawler';
import CronEditor from '@/components/CronEditor';
import type { Schedule } from '@/types/workflow';

const WorkflowSchedules: React.FC = () => {
  const actionRef = useRef<ActionType>();
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [form] = Form.useForm();

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60, search: false },
    { title: '调度名称', dataIndex: 'name' },
    { title: '工作流模板', dataIndex: 'template_name', search: false },
    {
      title: 'Cron表达式',
      dataIndex: 'cron_expression',
      width: 150,
      search: false,
      copyable: true,
      render: (val: string) => <code>{val}</code>,
    },
    {
      title: '状态',
      dataIndex: 'is_enabled',
      width: 80,
      valueType: 'select',
      valueEnum: {
        true: { text: '启用', status: 'Success' },
        false: { text: '禁用', status: 'Default' },
      },
      render: (_, record: Schedule) => (
        <Switch
          checked={record.is_enabled}
          onChange={(checked) => handleToggle(record.id, checked)}
        />
      ),
    },
    {
      title: '下次执行',
      dataIndex: 'next_run_time',
      valueType: 'dateTime',
      width: 180,
      search: false,
    },
    {
      title: '操作',
      valueType: 'option',
      width: 100,
      render: (_, record: Schedule) => [
        <Popconfirm key="delete" title="确定删除？" onConfirm={() => handleDelete(record.id)}>
          <Button type="link" danger>
            删除
          </Button>
        </Popconfirm>,
      ],
    },
  ];

  const handleToggle = async (id: number, enabled: boolean) => {
    try {
      await updateSchedule(id, { is_enabled: enabled });
      message.success('更新成功');
      actionRef.current?.reload();
    } catch (error: any) {
      message.error(error.message || '更新失败');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteSchedule(id);
      message.success('删除成功');
      actionRef.current?.reload();
    } catch (error: any) {
      message.error(error.message || '删除失败');
    }
  };

  const handleCreate = async (values: any) => {
    try {
      const config = values.config ? JSON.parse(values.config) : undefined;
      await createSchedule({ ...values, config });
      message.success('创建成功');
      setCreateModalVisible(false);
      form.resetFields();
      actionRef.current?.reload();
    } catch (error: any) {
      message.error(error.message || '创建失败');
    }
  };

  return (
    <>
      <ProTable<Schedule>
        actionRef={actionRef}
        columns={columns}
        request={async (params) => {
          const res = await getSchedules({
            ...params,
            page: params.current,
            page_size: params.pageSize,
          });
          return { data: res.data.items, total: res.data.total, success: true };
        }}
        rowKey="id"
        toolBarRender={() => [
          <Button
            key="create"
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalVisible(true)}
          >
            新建调度
          </Button>,
        ]}
      />

      <Modal
        title="新建定时调度"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form form={form} onFinish={handleCreate} layout="vertical">
          <Form.Item name="name" label="调度名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="template_id" label="工作流模板" rules={[{ required: true }]}>
            {/* 这里应该是Select，从API加载模板列表 */}
            <Input type="number" placeholder="模板ID" />
          </Form.Item>
          <Form.Item name="cron_expression" label="Cron表达式" rules={[{ required: true }]}>
            <CronEditor />
          </Form.Item>
          <Form.Item name="config" label="执行参数（JSON）">
            <Input.TextArea rows={4} placeholder='{"param1": "value1"}' />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default WorkflowSchedules;
```

---

## 八、路由配置

**修改文件**: `apps/web-admin/src/router/index.tsx`

```typescript
import { lazy } from 'react';
import { ClusterOutlined } from '@ant-design/icons';

// ... 现有路由 ...

// 新增工作流管理路由
{
  path: '/workflows',
  name: '工作流管理',
  icon: <ClusterOutlined />,
  routes: [
    {
      path: '/workflows/templates',
      name: '工作流模板',
      component: lazy(() => import('@/pages/Workflows/Templates')),
    },
    {
      path: '/workflows/monitor/:workflowId',
      name: '执行监控',
      component: lazy(() => import('@/pages/Workflows/Monitor')),
      hideInMenu: true,
    },
    {
      path: '/workflows/schedules',
      name: '定时调度',
      component: lazy(() => import('@/pages/Workflows/Schedules')),
    },
  ],
}
```

---

## 九、验收标准

### 9.1 功能验收

- [ ] 工作流模板列表正常显示
- [ ] 可创建/编辑/删除模板（系统模板不可操作）
- [ ] 执行工作流弹窗可正常提交
- [ ] 工作流监控页面实时刷新状态
- [ ] Progress和Steps组件展示正确
- [ ] 定时调度列表正常显示
- [ ] 可创建/删除调度
- [ ] Switch开关可启用/禁用调度
- [ ] Cron编辑器预设模板可用

### 9.2 UI/UX验收

- [ ] 页面布局美观，符合Ant Design规范
- [ ] 表格分页、筛选、排序正常
- [ ] 弹窗表单验证提示友好
- [ ] 操作成功/失败有明确提示
- [ ] 响应式布局适配移动端

### 9.3 性能验收

- [ ] 页面加载时间 < 2秒
- [ ] 列表滚动流畅，无卡顿
- [ ] WebSocket连接稳定（监控页面）
- [ ] 前端路由切换无闪烁

---

## 十、交付清单

### 代码文件
- [x] 类型定义（workflow.ts）
- [x] API Service扩展（crawler.ts）
- [x] Cron编辑器（CronEditor/）
- [x] 工作流模板管理（Templates.tsx）
- [x] 工作流监控（Monitor.tsx）
- [x] 定时调度管理（Schedules.tsx）
- [x] 路由配置（index.tsx）

### 文档
- [ ] 前端组件使用文档
- [ ] 工作流JSON格式示例
- [ ] 用户操作手册

### 测试
- [ ] 前端单元测试
- [ ] E2E测试（Playwright）

---

**至此，工作流系统3个阶段全部完成！**

## 总结

- **阶段1（5-6天）**: 工作流核心引擎、任务队列、平台抽象
- **阶段2（3-4天）**: 工作流管理API、定时调度服务
- **阶段3（4-5天）**: React管理前端界面

**总工作量**: 12-15天

**成果**: 完整的工作流管理系统，从后端引擎到前端界面，实现企业级爬虫任务编排和调度。
