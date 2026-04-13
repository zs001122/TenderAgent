import React, { useEffect, useState } from 'react'
import {
  Card,
  Form,
  Input,
  InputNumber,
  Select,
  Button,
  Space,
  message,
  Spin,
  Row,
  Col,
  Statistic,
  Typography,
  Divider,
  Tag,
} from 'antd'
import { SaveOutlined, ReloadOutlined, ApartmentOutlined, SafetyCertificateOutlined } from '@ant-design/icons'
import type { CompanyProfileInput } from '../types/company'
import { getCompanyProfile, updateCompanyProfile, resetCompanyProfile } from '../services/company'

const TARGET_DOMAINS = [
  '软件开发',
  '大数据',
  'AI/人工智能',
  '硬件/设备',
  '工程/施工',
  '通信/网络',
  '运维/服务',
]

const QUALIFICATIONS = [
  'CMMI3',
  'CMMI5',
  'ISO27001',
  'ISO9001',
  '高新技术企业',
  'ITSS',
  'CS',
  'CCRC',
]

const SERVICE_REGIONS = [
  '北京市',
  '上海市',
  '广东省',
  '浙江省',
  '江苏省',
  '四川省',
  '湖北省',
  '山东省',
  '河南省',
  '陕西省',
]

const CompanyProfilePage: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [profileSnapshot, setProfileSnapshot] = useState<CompanyProfileInput | null>(null)

  useEffect(() => {
    loadProfile()
  }, [])

  const loadProfile = async () => {
    setLoading(true)
    try {
      const profile = await getCompanyProfile()
      form.setFieldsValue({
        name: profile.name,
        target_domains: profile.target_domains || [],
        budget_min: profile.budget_range?.[0] || 0,
        budget_max: profile.budget_range?.[1] || 1000,
        qualifications: profile.qualifications || [],
        service_regions: profile.service_regions || [],
      })
      setProfileSnapshot(profile)
    } catch (error) {
      message.error('加载公司画像失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (values: any) => {
    setSaving(true)
    try {
      const profile: CompanyProfileInput = {
        name: values.name,
        target_domains: values.target_domains,
        budget_range: [values.budget_min, values.budget_max],
        qualifications: values.qualifications,
        service_regions: values.service_regions,
      }
      await updateCompanyProfile(profile)
      setProfileSnapshot(profile)
      message.success('保存成功')
    } catch (error) {
      message.error('保存失败')
    } finally {
      setSaving(false)
    }
  }

  const handleReset = async () => {
    try {
      await resetCompanyProfile()
      message.success('已重置为默认配置')
      loadProfile()
    } catch (error) {
      message.error('重置失败')
    }
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <Row gutter={16}>
      <Col xs={24} xl={17}>
        <Card
          title="公司画像配置"
          extra={<Tag color="blue">策略输入</Tag>}
          style={{ borderRadius: 16, boxShadow: '0 8px 24px rgba(14, 38, 74, 0.08)' }}
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSave}
            style={{ maxWidth: 860 }}
          >
            <Card
              bordered={false}
              style={{ background: '#f8fbff', borderRadius: 12, marginBottom: 12 }}
              title={
                <Space>
                  <ApartmentOutlined />
                  基础信息
                </Space>
              }
            >
              <Form.Item
                name="name"
                label="公司名称"
                rules={[{ required: true, message: '请输入公司名称' }]}
              >
                <Input placeholder="请输入公司名称" />
              </Form.Item>
              <Form.Item
                name="target_domains"
                label="目标领域"
                rules={[{ required: true, message: '请选择目标领域' }]}
              >
                <Select
                  mode="multiple"
                  placeholder="请选择目标领域"
                  options={TARGET_DOMAINS.map((d) => ({ label: d, value: d }))}
                />
              </Form.Item>
            </Card>

            <Card
              bordered={false}
              style={{ background: '#f6ffed', borderRadius: 12, marginBottom: 12 }}
              title={
                <Space>
                  <SafetyCertificateOutlined />
                  预算与资质
                </Space>
              }
            >
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="budget_min"
                    label="预算范围（最小值，万元）"
                    rules={[{ required: true, message: '请输入最小预算' }]}
                  >
                    <InputNumber
                      min={0}
                      style={{ width: '100%' }}
                      placeholder="最小预算"
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="budget_max"
                    label="预算范围（最大值，万元）"
                    rules={[{ required: true, message: '请输入最大预算' }]}
                  >
                    <InputNumber
                      min={0}
                      style={{ width: '100%' }}
                      placeholder="最大预算"
                    />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item
                name="qualifications"
                label="资质证书"
                tooltip="公司拥有的资质证书，用于匹配招标要求"
              >
                <Select
                  mode="tags"
                  placeholder="请选择或输入资质证书"
                  options={QUALIFICATIONS.map((q) => ({ label: q, value: q }))}
                />
              </Form.Item>
            </Card>

            <Card
              bordered={false}
              style={{ background: '#fffbe6', borderRadius: 12, marginBottom: 12 }}
              title="服务能力覆盖"
            >
              <Form.Item
                name="service_regions"
                label="服务区域"
                tooltip="公司可提供服务的区域"
              >
                <Select
                  mode="multiple"
                  placeholder="请选择服务区域"
                  options={SERVICE_REGIONS.map((r) => ({ label: r, value: r }))}
                />
              </Form.Item>
            </Card>

            <Form.Item>
              <Space>
                <Button
                  type="primary"
                  htmlType="submit"
                  icon={<SaveOutlined />}
                  loading={saving}
                >
                  保存配置
                </Button>
                <Button icon={<ReloadOutlined />} onClick={handleReset}>
                  重置为默认
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Card>
      </Col>
      <Col xs={24} xl={7}>
        <Card
          title="画像摘要"
          style={{ borderRadius: 16, boxShadow: '0 8px 24px rgba(14, 38, 74, 0.08)' }}
        >
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Statistic title="目标领域数" value={profileSnapshot?.target_domains?.length || 0} />
            <Statistic title="资质证书数" value={profileSnapshot?.qualifications?.length || 0} />
            <Statistic title="服务区域数" value={profileSnapshot?.service_regions?.length || 0} />
            <Divider style={{ margin: 0 }} />
            <Typography.Text type="secondary">
              配置会直接影响 Gate 门槛与匹配评分，建议优先确保资质与服务区域准确。
            </Typography.Text>
          </Space>
        </Card>
      </Col>
    </Row>
  )
}

export default CompanyProfilePage
