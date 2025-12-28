import { useEffect, useState } from 'react'
import { Form, Input, Select, InputNumber, Button, Card, message, Space, Divider } from 'antd'
import { useNavigate, useParams } from 'react-router-dom'
import { equipmentApi } from '@/api/services/equipment'
import type { Brand, Equipment, RodSpecs, ReelSpecs, LineSpecs, LureSpecs } from '@/types/equipment'

const { TextArea } = Input

const EquipmentForm = () => {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [brands, setBrands] = useState<Brand[]>([])
  const [category, setCategory] = useState<string>('')
  const [equipment, setEquipment] = useState<Equipment>()

  useEffect(() => {
    // 加载品牌列表
    equipmentApi.listBrands().then(setBrands).catch(() => {
      message.error('加载品牌列表失败')
    })

    // 编辑模式：加载装备详情
    if (id) {
      equipmentApi.get(Number(id)).then((data) => {
        setEquipment(data)
        setCategory(data.category)
        form.setFieldsValue(data)
      }).catch(() => {
        message.error('加载装备详情失败')
      })
    }
  }, [id, form])

  const handleCategoryChange = (value: string) => {
    setCategory(value)
    // 清空规格字段
    form.setFieldsValue({ specs: {} })
  }

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
            <Select style={{ width: 150 }} onChange={handleCategoryChange}>
              <Select.Option value="鱼竿">鱼竿</Select.Option>
              <Select.Option value="渔轮">渔轮</Select.Option>
              <Select.Option value="鱼线">鱼线</Select.Option>
              <Select.Option value="拟饵">拟饵</Select.Option>
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
            <Select.Option value="入门">入门</Select.Option>
            <Select.Option value="新手">新手</Select.Option>
            <Select.Option value="进阶">进阶</Select.Option>
            <Select.Option value="高手">高手</Select.Option>
          </Select>
        </Form.Item>

        {/* 动态规格字段 */}
        {category && (
          <>
            <Divider>技术规格</Divider>

            {category === '鱼竿' && (
              <>
                <Space size="large">
                  <Form.Item
                    label="长度(米)"
                    name={['specs', 'length']}
                    rules={[{ required: true, message: '请输入长度' }]}
                  >
                    <InputNumber placeholder="例: 2.1" min={0.5} max={10} step={0.1} />
                  </Form.Item>
                  <Form.Item
                    label="调性"
                    name={['specs', 'power']}
                    rules={[{ required: true, message: '请选择调性' }]}
                  >
                    <Select placeholder="请选择调性" style={{ width: 120 }}>
                      <Select.Option value="UL">UL</Select.Option>
                      <Select.Option value="L">L</Select.Option>
                      <Select.Option value="ML">ML</Select.Option>
                      <Select.Option value="M">M</Select.Option>
                      <Select.Option value="MH">MH</Select.Option>
                      <Select.Option value="H">H</Select.Option>
                      <Select.Option value="XH">XH</Select.Option>
                    </Select>
                  </Form.Item>
                  <Form.Item
                    label="动作"
                    name={['specs', 'action']}
                    rules={[{ required: true, message: '请选择动作' }]}
                  >
                    <Select placeholder="请选择动作" style={{ width: 120 }}>
                      <Select.Option value="Fast">Fast</Select.Option>
                      <Select.Option value="Moderate">Moderate</Select.Option>
                      <Select.Option value="Slow">Slow</Select.Option>
                    </Select>
                  </Form.Item>
                </Space>

                <Space size="large">
                  <Form.Item
                    label="重量(克)"
                    name={['specs', 'weight']}
                    rules={[{ required: true, message: '请输入重量' }]}
                  >
                    <InputNumber placeholder="例: 105" min={0} />
                  </Form.Item>
                  <Form.Item
                    label="节数"
                    name={['specs', 'sections']}
                    rules={[{ required: true, message: '请输入节数' }]}
                  >
                    <InputNumber placeholder="例: 2" min={1} max={10} />
                  </Form.Item>
                  <Form.Item
                    label="收缩长度(厘米)"
                    name={['specs', 'closed_length']}
                    rules={[{ required: true, message: '请输入收缩长度' }]}
                  >
                    <InputNumber placeholder="例: 105" min={0} />
                  </Form.Item>
                </Space>

                <Space size="large">
                  <Form.Item label="饵重范围(克)">
                    <Input.Group compact>
                      <Form.Item name={['specs', 'lure_weight_min']} noStyle>
                        <InputNumber placeholder="最小" min={0} style={{ width: 100 }} />
                      </Form.Item>
                      <Input
                        style={{
                          width: 30,
                          textAlign: 'center',
                          borderLeft: 0,
                          borderRight: 0,
                          pointerEvents: 'none',
                        }}
                        placeholder="~"
                        disabled
                      />
                      <Form.Item name={['specs', 'lure_weight_max']} noStyle>
                        <InputNumber placeholder="最大" min={0} style={{ width: 100 }} />
                      </Form.Item>
                    </Input.Group>
                  </Form.Item>
                  <Form.Item label="线重范围(磅)">
                    <Input.Group compact>
                      <Form.Item name={['specs', 'line_weight_min']} noStyle>
                        <InputNumber placeholder="最小" min={0} style={{ width: 100 }} />
                      </Form.Item>
                      <Input
                        style={{
                          width: 30,
                          textAlign: 'center',
                          borderLeft: 0,
                          borderRight: 0,
                          pointerEvents: 'none',
                        }}
                        placeholder="~"
                        disabled
                      />
                      <Form.Item name={['specs', 'line_weight_max']} noStyle>
                        <InputNumber placeholder="最大" min={0} style={{ width: 100 }} />
                      </Form.Item>
                    </Input.Group>
                  </Form.Item>
                </Space>

                <Form.Item label="导环类型" name={['specs', 'guide_type']}>
                  <Input placeholder="例: 11颗钛合金支架的富士导环" />
                </Form.Item>

                <Form.Item label="握把材质" name={['specs', 'handle_type']}>
                  <Input placeholder="例: 4A级软木" />
                </Form.Item>

                <Form.Item label="工艺描述" name={['specs', 'craft_description']}>
                  <TextArea rows={2} placeholder="请描述工艺特点" />
                </Form.Item>
              </>
            )}

            {category === '渔轮' && (
              <>
                <Space size="large">
                  <Form.Item label="齿比" name={['specs', 'gear_ratio']}>
                    <InputNumber placeholder="例: 6.3" min={1} step={0.1} />
                  </Form.Item>
                  <Form.Item label="轴承数" name={['specs', 'bearings']}>
                    <InputNumber placeholder="例: 8" min={0} />
                  </Form.Item>
                  <Form.Item label="重量(克)" name={['specs', 'weight']}>
                    <InputNumber placeholder="例: 195" min={0} />
                  </Form.Item>
                </Space>

                <Form.Item label="线容量" name={['specs', 'line_capacity']}>
                  <Input placeholder="例: 150米/PE线2号" />
                </Form.Item>

                <Form.Item label="最大拖力(公斤)" name={['specs', 'drag_max']}>
                  <InputNumber placeholder="例: 5" min={0} step={0.5} />
                </Form.Item>

                <Form.Item label="线杯材质" name={['specs', 'spool_material']}>
                  <Input placeholder="例: 铝合金" />
                </Form.Item>
              </>
            )}

            {category === '鱼线' && (
              <>
                <Space size="large">
                  <Form.Item label="直径(毫米)" name={['specs', 'diameter']}>
                    <InputNumber placeholder="例: 0.2" min={0} step={0.01} />
                  </Form.Item>
                  <Form.Item label="长度(米)" name={['specs', 'length']}>
                    <InputNumber placeholder="例: 100" min={0} />
                  </Form.Item>
                  <Form.Item label="强力(公斤)" name={['specs', 'strength']}>
                    <InputNumber placeholder="例: 5" min={0} step={0.5} />
                  </Form.Item>
                </Space>

                <Form.Item label="材质" name={['specs', 'material']}>
                  <Input placeholder="例: 尼龙" />
                </Form.Item>

                <Form.Item label="类型" name={['specs', 'type']}>
                  <Select placeholder="请选择类型" style={{ width: 150 }}>
                    <Select.Option value="尼龙">尼龙</Select.Option>
                    <Select.Option value="PE">PE</Select.Option>
                    <Select.Option value="碳素">碳素</Select.Option>
                  </Select>
                </Form.Item>

                <Form.Item label="颜色" name={['specs', 'color']}>
                  <Input placeholder="例: 透明" />
                </Form.Item>
              </>
            )}

            {category === '拟饵' && (
              <>
                <Space size="large">
                  <Form.Item label="重量(克)" name={['specs', 'weight']}>
                    <InputNumber placeholder="例: 7" min={0} step={0.5} />
                  </Form.Item>
                  <Form.Item label="长度(毫米)" name={['specs', 'length']}>
                    <InputNumber placeholder="例: 70" min={0} />
                  </Form.Item>
                  <Form.Item label="潜行深度(米)" name={['specs', 'diving_depth']}>
                    <InputNumber placeholder="例: 1.2" min={0} step={0.1} />
                  </Form.Item>
                </Space>

                <Form.Item label="类型" name={['specs', 'type']}>
                  <Select placeholder="请选择类型" style={{ width: 150 }}>
                    <Select.Option value="米诺">米诺</Select.Option>
                    <Select.Option value="摇滚">摇滚</Select.Option>
                    <Select.Option value="胖子">胖子</Select.Option>
                    <Select.Option value="铅笔">铅笔</Select.Option>
                    <Select.Option value="铁板">铁板</Select.Option>
                    <Select.Option value="VIB">VIB</Select.Option>
                  </Select>
                </Form.Item>

                <Space size="large">
                  <Form.Item label="钩数" name={['specs', 'hooks']}>
                    <InputNumber placeholder="例: 2" min={0} max={6} />
                  </Form.Item>
                  <Form.Item label="材质" name={['specs', 'material']}>
                    <Input placeholder="例: ABS塑料" />
                  </Form.Item>
                  <Form.Item label="颜色" name={['specs', 'color']}>
                    <Input placeholder="例: 红头白身" />
                  </Form.Item>
                </Space>
              </>
            )}
          </>
        )}

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
