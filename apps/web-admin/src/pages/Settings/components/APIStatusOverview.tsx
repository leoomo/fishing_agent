import { Card, Row, Col, Statistic } from 'antd'
import {
  SettingOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons'
// import type { APIKeyStatus } from '../constants'

interface StatusCounts {
  total: number
  configured: number
  verified: number
  pending: number
  invalid: number
}

interface APIStatusOverviewProps {
  counts: StatusCounts
}

const APIStatusOverview: React.FC<APIStatusOverviewProps> = ({ counts }) => {
  return (
    <Row gutter={16}>
      <Col span={6}>
        <Card size="small">
          <Statistic
            title="已配置"
            value={counts.configured}
            suffix={`/ ${counts.total}`}
            prefix={<SettingOutlined />}
            valueStyle={{ color: '#1677ff' }}
          />
        </Card>
      </Col>
      <Col span={6}>
        <Card size="small">
          <Statistic
            title="已验证"
            value={counts.verified}
            prefix={<CheckCircleOutlined />}
            valueStyle={{ color: '#52c41a' }}
          />
        </Card>
      </Col>
      <Col span={6}>
        <Card size="small">
          <Statistic
            title="待验证"
            value={counts.pending}
            prefix={<ClockCircleOutlined />}
            valueStyle={{ color: '#faad14' }}
          />
        </Card>
      </Col>
      <Col span={6}>
        <Card size="small">
          <Statistic
            title="无效"
            value={counts.invalid}
            prefix={<CloseCircleOutlined />}
            valueStyle={{ color: counts.invalid > 0 ? '#ff4d4f' : '#999' }}
          />
        </Card>
      </Col>
    </Row>
  )
}

export default APIStatusOverview
