import { useEffect, useState } from 'react'
import { Form, Input, Select, InputNumber, Button, Card, message, Space } from 'antd'
import { useNavigate, useParams } from 'react-router-dom'
import { equipmentApi } from '@/api/services/equipment'
import type { Brand } from '@/types/equipment'

const { TextArea } = Input

const EquipmentForm = () => {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [brands, setBrands] = useState<Brand[]>([])

  useEffect(() => {
    // 加载品牌列表
    equipmentApi.listBrands().then(setBrands).catch(() => {
      message.error('加载品牌列表失败')
    })

    // 编辑模式：加载装备详情
    if (id) {
      equipmentApi.get(Number(id)).then((data) => {
        form.setFieldsValue(data)
      }).catch(() => {
        message.error('加载装备详情失败')
      })
    }
  }, [id, form])

  const onFinish = async (values: Record<string, unknown>) => {
    setLoading(true)
    try {
      if (id) {
        await equipmentApi.update(Number(id), values)
        message.success('更新成功')
      } else {
        await equipmentApi.create(values as Parameters<typeof equipmentApi.create>[0])
        message.success('创建成功')
      }
      navigate('/equipment')
    } catch {
      message.error('保存失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card title={id ? '编辑装备' : '新增装备'}>
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={{ user_level: '新手', is_active: true }}
        style={{ maxWidth: 800 }}
      >
        <Form.Item
          label="装备名称"
          name="name"
          rules={[{ required: true, message: '请输入装备名称' }]}
        >
          <Input placeholder="请输入装备名称" />
        </Form.Item>

        <Space size="large">
          <Form.Item
            label="类别"
            name="category"
            rules={[{ required: true, message: '请选择类别' }]}
          >
            <Select style={{ width: 150 }}>
              <Select.Option value="鱼竿">鱼竿</Select.Option>
              <Select.Option value="渔轮">渔轮</Select.Option>
              <Select.Option value="鱼线">鱼线</Select.Option>
              <Select.Option value="拟饵">拟饵</Select.Option>
              <Select.Option value="路亚竿">路亚竿</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="品牌"
            name="brand_id"
            rules={[{ required: true, message: '请选择品牌' }]}
          >
            <Select placeholder="请选择品牌" style={{ width: 200 }}>
              {brands.map((brand) => (
                <Select.Option key={brand.brand_id} value={brand.brand_id}>
                  {brand.name_cn}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
        </Space>

        <Form.Item label="型号" name="model">
          <Input placeholder="请输入型号" style={{ width: 300 }} />
        </Form.Item>

        <Space size="large">
          <Form.Item label="最低价格" name="price_min">
            <InputNumber placeholder="最低价" min={0} addonBefore="¥" />
          </Form.Item>
          <Form.Item label="最高价格" name="price_max">
            <InputNumber placeholder="最高价" min={0} addonBefore="¥" />
          </Form.Item>
        </Space>

        <Form.Item label="描述" name="description">
          <TextArea rows={4} placeholder="请输入装备描述" />
        </Form.Item>

        <Form.Item label="特点" name="features">
          <TextArea rows={3} placeholder="请输入装备特点" />
        </Form.Item>

        <Form.Item label="适用水平" name="user_level">
          <Select style={{ width: 150 }}>
            <Select.Option value="新手">新手</Select.Option>
            <Select.Option value="进阶">进阶</Select.Option>
            <Select.Option value="高手">高手</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={loading}>
              保存
            </Button>
            <Button onClick={() => navigate('/equipment')}>
              取消
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  )
}

export default EquipmentForm
