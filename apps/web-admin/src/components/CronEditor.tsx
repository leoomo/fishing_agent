import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Select,
  InputNumber,
  Input,
  TimePicker,
  Button,
  Space,
  Row,
  Col,
  Typography,
  Divider,
  Alert,
  Tag,
} from 'antd';
import {
  ClockCircleOutlined,
} from '@ant-design/icons';
import { workflowApi } from '../api/workflow';
import type { CronExpressionRequest } from '../api/workflow';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;

interface CronEditorProps {
  value?: string;
  onChange?: (cronExpression: string) => void;
  timezone?: string;
}

const CronEditor: React.FC<CronEditorProps> = ({ value, onChange, timezone = 'Asia/Shanghai' }) => {
  const [form] = Form.useForm();
  const [mode, setMode] = useState<'simple' | 'advanced'>('simple');
  const [generatedCron, setGeneratedCron] = useState<string>('');
  const [nextRuns, setNextRuns] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (value) {
      // Parse existing cron expression
      setMode('advanced');
      form.setFieldsValue({
        cronExpression: value,
      });
      setGeneratedCron(value);
    }
  }, [value, form]);

  // Generate cron from simple form
  const generateCron = async (values: any) => {
    setLoading(true);
    try {
      const request: CronExpressionRequest = {
        frequency: values.frequency,
        interval: values.interval || 1,
        specific_times: values.specific_times,
        days_of_month: values.days_of_month,
        days_of_week: values.days_of_week,
        months: values.months,
        timezone: timezone,
      };

      const response = await workflowApi.generateCronExpression(request);
      const cron = response.data.cron_expression;
      setGeneratedCron(cron);
      setNextRuns(response.data.next_runs);
      onChange?.(cron);

      // Also set the advanced form value
      form.setFieldsValue({ cronExpression: cron });
    } catch (error) {
      console.error('Failed to generate cron expression:', error);
    } finally {
      setLoading(false);
    }
  };

  // Handle direct cron input
  const handleCronChange = (cron: string) => {
    setGeneratedCron(cron);
    onChange?.(cron);
  };

  // Frequency options
  const frequencyOptions = [
    { label: '每分钟', value: 'minutely' },
    { label: '每小时', value: 'hourly' },
    { label: '每天', value: 'daily' },
    { label: '每周', value: 'weekly' },
    { label: '每月', value: 'monthly' },
    { label: '每年', value: 'yearly' },
    { label: '自定义', value: 'custom' },
  ];

  const weekDays = [
    { label: '周一', value: '1' },
    { label: '周二', value: '2' },
    { label: '周三', value: '3' },
    { label: '周四', value: '4' },
    { label: '周五', value: '5' },
    { label: '周六', value: '6' },
    { label: '周日', value: '0' },
  ];

  return (
    <Card>
      <Row justify="space-between" align="middle">
        <Col>
          <Title level={4}>
            <ClockCircleOutlined /> Cron 表达式
          </Title>
        </Col>
        <Col>
          <Space>
            <Button
              type={mode === 'simple' ? 'primary' : 'default'}
              onClick={() => setMode('simple')}
            >
              简单模式
            </Button>
            <Button
              type={mode === 'advanced' ? 'primary' : 'default'}
              onClick={() => setMode('advanced')}
            >
              高级模式
            </Button>
          </Space>
        </Col>
      </Row>

      {mode === 'simple' ? (
        <Form
          form={form}
          layout="vertical"
          onFinish={generateCron}
          initialValues={{
            frequency: 'daily',
            interval: 1,
          }}
        >
          <Form.Item
            label="频率"
            name="frequency"
            rules={[{ required: true, message: '请选择执行频率' }]}
          >
            <Select onChange={() => setNextRuns([])}>
              {frequencyOptions.map(option => (
                <Option key={option.value} value={option.value}>
                  {option.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item noStyle shouldUpdate={(prevValues, currentValues) => prevValues.frequency !== currentValues.frequency}>
            {({ getFieldValue }) => {
              const frequency = getFieldValue('frequency');

              return (
                <>
                  {frequency === 'hourly' && (
                    <Form.Item label="每 N 小时执行一次" name="interval">
                      <InputNumber min={1} max={23} />
                    </Form.Item>
                  )}

                  {frequency === 'daily' && (
                    <>
                      <Form.Item label="每 N 天执行一次" name="interval">
                        <InputNumber min={1} max={365} />
                      </Form.Item>
                      <Form.Item label="执行时间" name="specific_times">
                        <TimePicker
                          format="HH:mm"
                          defaultValue={dayjs('09:00', 'HH:mm')}
                        />
                      </Form.Item>
                    </>
                  )}

                  {frequency === 'weekly' && (
                    <>
                      <Form.Item label="每 N 周执行一次" name="interval">
                        <InputNumber min={1} max={52} />
                      </Form.Item>
                      <Form.Item label="星期几" name="days_of_week">
                        <Select mode="multiple" placeholder="选择星期几">
                          {weekDays.map(day => (
                            <Option key={day.value} value={day.value}>
                              {day.label}
                            </Option>
                          ))}
                        </Select>
                      </Form.Item>
                      <Form.Item label="执行时间" name="specific_times">
                        <TimePicker
                          format="HH:mm"
                          defaultValue={dayjs('09:00', 'HH:mm')}
                        />
                      </Form.Item>
                    </>
                  )}

                  {frequency === 'monthly' && (
                    <>
                      <Form.Item label="每 N 月执行一次" name="interval">
                        <InputNumber min={1} max={12} />
                      </Form.Item>
                      <Form.Item label="日期" name="days_of_month">
                        <Select mode="multiple" placeholder="选择日期">
                          {Array.from({ length: 31 }, (_, i) => i + 1).map(day => (
                            <Option key={day} value={day}>
                              {day}日
                            </Option>
                          ))}
                        </Select>
                      </Form.Item>
                      <Form.Item label="执行时间" name="specific_times">
                        <TimePicker
                          format="HH:mm"
                          defaultValue={dayjs('09:00', 'HH:mm')}
                        />
                      </Form.Item>
                    </>
                  )}
                </>
              );
            }}
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                生成表达式
              </Button>
            </Space>
          </Form.Item>
        </Form>
      ) : (
        <Form form={form} layout="vertical">
          <Form.Item
            label="Cron 表达式"
            name="cronExpression"
            extra="格式: 分 时 日 月 周 (例如: 0 9 * * * 表示每天上午9点)"
          >
            <Input
              placeholder="0 9 * * *"
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleCronChange(e.target.value)}
            />
          </Form.Item>

          <Alert
            message="Cron 表达式格式说明"
            description={
              <div>
                <p><strong>字段说明（从左到右）：</strong></p>
                <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
                  <li><strong>分</strong>：0-59</li>
                  <li><strong>时</strong>：0-23</li>
                  <li><strong>日</strong>：1-31</li>
                  <li><strong>月</strong>：1-12 或 JAN-DEC</li>
                  <li><strong>周</strong>：0-6 (0=周日) 或 MON-SUN</li>
                </ul>
                <p><strong>特殊字符：</strong></p>
                <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
                  <li><code>*</code>：任意值</li>
                  <li><code>,</code>：多个值 (如: 1,3,5)</li>
                  <li><code>-</code>：范围 (如: 1-5)</li>
                  <li><code>/</code>：步长 (如: */5 表示每5个单位)</li>
                </ul>
              </div>
            }
            type="info"
            showIcon
            style={{ marginTop: 16 }}
          />
        </Form>
      )}

      {generatedCron && (
        <>
          <Divider />
          <Row gutter={16}>
            <Col span={12}>
              <Card size="small" title="生成的表达式">
                <Text code copyable>{generatedCron}</Text>
              </Card>
            </Col>
            <Col span={12}>
              <Card size="small" title="时区">
                <Text>{timezone}</Text>
              </Card>
            </Col>
          </Row>

          {nextRuns.length > 0 && (
            <Card size="small" title="下次执行时间" style={{ marginTop: 16 }}>
              <Space wrap>
                {nextRuns.slice(0, 10).map((run, index) => (
                  <Tag key={index} color="blue">
                    {dayjs(run).format('YYYY-MM-DD HH:mm:ss')}
                  </Tag>
                ))}
              </Space>
              {nextRuns.length > 10 && (
                <Text type="secondary">... 还有更多</Text>
              )}
            </Card>
          )}
        </>
      )}
    </Card>
  );
};

export default CronEditor;