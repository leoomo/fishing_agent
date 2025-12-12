import React, { useState } from 'react';
import { Tabs, Card, Typography, Space, Row, Col, Statistic } from 'antd';
import {
  BranchesOutlined,
  PlayCircleOutlined,
  HistoryOutlined,
  DashboardOutlined,
} from '@ant-design/icons';
import WorkflowTemplates from './WorkflowTemplates';
import WorkflowMonitor from './WorkflowMonitor';
import ScheduleManager from './ScheduleManager';
import { workflowApi } from '../../api/workflow';

const { Title } = Typography;
const { TabPane } = Tabs;

const Workflow: React.FC = () => {
  const [stats, setStats] = useState({
    templates: 0,
    activeWorkflows: 0,
    schedules: 0,
    completedToday: 0,
  });

  // Fetch statistics
  const fetchStats = async () => {
    try {
      // Get template count
      const templateResponse = await workflowApi.getTemplates({ page: 1, page_size: 1 });
      const templateCount = templateResponse.data.total;

      // Get schedule count
      const scheduleResponse = await workflowApi.getSchedules({ page: 1, page_size: 1 });
      const scheduleCount = scheduleResponse.data.total;

      // Get scheduler status
      const statusResponse = await workflowApi.getSchedulerStatus();
      const activeCount = statusResponse.data.schedule_jobs;

      setStats({
        templates: templateCount,
        activeWorkflows: activeCount,
        schedules: scheduleCount,
        completedToday: 0, // This would come from a separate API call
      });
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  React.useEffect(() => {
    fetchStats();
  }, []);

  return (
    <div>
      <Title level={2}>
        <DashboardOutlined /> 工作流管理
      </Title>

      {/* Statistics Cards */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="工作流模板"
              value={stats.templates}
              prefix={<BranchesOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="运行中的工作流"
              value={stats.activeWorkflows}
              prefix={<PlayCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="定时调度"
              value={stats.schedules}
              prefix={<HistoryOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="今日完成"
              value={stats.completedToday}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Main Content */}
      <Card>
        <Tabs defaultActiveKey="templates" size="large">
          <TabPane
            tab={
              <span>
                <BranchesOutlined />
                工作流模板
              </span>
            }
            key="templates"
          >
            <WorkflowTemplates />
          </TabPane>
          <TabPane
            tab={
              <span>
                <PlayCircleOutlined />
                执行监控
              </span>
            }
            key="monitor"
          >
            <WorkflowMonitor />
          </TabPane>
          <TabPane
            tab={
              <span>
                <HistoryOutlined />
                定时调度
              </span>
            }
            key="schedules"
          >
            <ScheduleManager />
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default Workflow;