import React, { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Badge,
  Button,
  Col,
  Descriptions,
  Drawer,
  Empty,
  Form,
  Input,
  InputNumber,
  List,
  message,
  Row,
  Select,
  Space,
  Spin,
  Statistic,
  Table,
  Tabs,
  Tag,
  Typography,
  Upload,
  DatePicker,
  Modal,
  Switch,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  CheckCircleOutlined,
  CloudUploadOutlined,
  DatabaseOutlined,
  EyeOutlined,
  EditOutlined,
  FilterOutlined,
  PlusOutlined,
  ReloadOutlined,
  SaveOutlined,
  SettingOutlined,
  StopOutlined,
  UndoOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import type {
  CompanyAsset,
  CompanyAssetInput,
  CompanyAssetQuery,
  CompanyAssetSummary,
  CompanyImportPreview,
  CompanyImportResult,
  CompanyProfile,
  CompanyProfileInput,
} from '../types/company'
import {
  confirmCompanyExcelImport,
  createCompanyAsset,
  deleteCompanyAsset,
  getCompanyAssets,
  getCompanyProfile,
  previewCompanyExcel,
  resetCompanyProfile,
  restoreCompanyAsset,
  updateCompanyAsset,
  updateCompanyProfile,
} from '../services/company'

const { Text, Title } = Typography

const TARGET_DOMAINS = ['软件开发', '大数据', 'AI/人工智能', '硬件/设备', '工程/施工', '通信/网络', '运维/服务', '安全/等保']
const QUALIFICATIONS = ['CMMI3', 'CMMI5', 'ISO27001', 'ISO9001', '高新技术企业', 'ITSS', 'CS', 'CCRC']
const SERVICE_REGIONS = ['北京市', '上海市', '广东省', '浙江省', '江苏省', '四川省', '湖北省', '山东省', '河南省', '陕西省']

const ASSET_TYPE_LABELS: Record<string, string> = {
  qualification: '资质认证',
  software_copyright: '软著',
  patent_granted: '授权专利',
  patent_pending: '审核中专利',
  personnel_certificate: '人员证书',
  project_case: '业绩',
}

const statusColor = (status?: string) => {
  if (status === '有效') return 'success'
  if (status === '过期') return 'error'
  if (status === '审核中') return 'processing'
  return 'default'
}

const CompanyProfilePage: React.FC = () => {
  const [form] = Form.useForm()
  const [assetForm] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [importing, setImporting] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [profile, setProfile] = useState<CompanyProfile | null>(null)
  const [assetSummary, setAssetSummary] = useState<CompanyAssetSummary | null>(null)
  const [preview, setPreview] = useState<CompanyImportPreview | null>(null)
  const [lastImport, setLastImport] = useState<CompanyImportResult | null>(null)
  const [assets, setAssets] = useState<CompanyAsset[]>([])
  const [assetsTotal, setAssetsTotal] = useState(0)
  const [assetLoading, setAssetLoading] = useState(false)
  const [assetQuery, setAssetQuery] = useState<CompanyAssetQuery>({ skip: 0, limit: 10 })
  const [selectedAsset, setSelectedAsset] = useState<CompanyAsset | null>(null)
  const [editingAsset, setEditingAsset] = useState<CompanyAsset | null>(null)
  const [assetDrawerOpen, setAssetDrawerOpen] = useState(false)
  const [assetSaving, setAssetSaving] = useState(false)

  useEffect(() => {
    loadProfile()
    loadAssets({ skip: 0, limit: 10 })
  }, [])

  const sourceSheetOptions = useMemo(() => {
    return Object.keys(assetSummary?.by_sheet || {}).map((sheet) => ({ label: sheet, value: sheet }))
  }, [assetSummary])

  const loadProfile = async () => {
    setLoading(true)
    try {
      const nextProfile = await getCompanyProfile()
      setProfile(nextProfile)
      setAssetSummary(nextProfile.asset_summary || null)
      form.setFieldsValue({
        name: nextProfile.name,
        target_domains: nextProfile.target_domains || [],
        budget_min: nextProfile.budget_range?.[0] || 0,
        budget_max: nextProfile.budget_range?.[1] || 1000,
        qualifications: nextProfile.qualifications || [],
        service_regions: nextProfile.service_regions || [],
      })
    } catch {
      message.error('加载资料工作台失败')
    } finally {
      setLoading(false)
    }
  }

  const loadAssets = async (query: CompanyAssetQuery = assetQuery) => {
    setAssetLoading(true)
    try {
      const response = await getCompanyAssets(query)
      setAssets(response.items)
      setAssetsTotal(response.total)
      setAssetQuery({ ...query, skip: response.skip, limit: response.limit })
    } catch {
      message.error('加载资料库失败')
    } finally {
      setAssetLoading(false)
    }
  }

  const handlePreview = async (file: File) => {
    setImporting(true)
    try {
      const result = await previewCompanyExcel(file)
      setPreview(result)
      message.success('解析完成，请确认后入库')
    } catch {
      message.error('Excel 解析失败')
    } finally {
      setImporting(false)
    }
    return false
  }

  const handleConfirmImport = async () => {
    if (!preview?.preview_id) return
    setConfirming(true)
    try {
      const result = await confirmCompanyExcelImport(preview.preview_id)
      setLastImport(result)
      setPreview(null)
      await loadProfile()
      await loadAssets({ ...assetQuery, skip: 0 })
      message.success('资料库已更新')
    } catch {
      message.error('确认入库失败，请重新上传')
    } finally {
      setConfirming(false)
    }
  }

  const handleSave = async (values: any) => {
    setSaving(true)
    try {
      const nextProfile: CompanyProfileInput = {
        name: values.name,
        target_domains: values.target_domains,
        budget_range: [values.budget_min, values.budget_max],
        qualifications: values.qualifications,
        service_regions: values.service_regions,
      }
      await updateCompanyProfile(nextProfile)
      await loadProfile()
      message.success('匹配策略已保存')
    } catch {
      message.error('保存失败')
    } finally {
      setSaving(false)
    }
  }

  const handleReset = async () => {
    try {
      await resetCompanyProfile()
      await loadProfile()
      message.success('已重置为默认配置')
    } catch {
      message.error('重置失败')
    }
  }

  const openCreateAsset = () => {
    setEditingAsset(null)
    assetForm.setFieldsValue({
      asset_type: 'qualification',
      source_sheet: '手工维护',
      status: '有效',
      keywords: [],
      data_json: '{}',
    })
    setAssetDrawerOpen(true)
  }

  const openEditAsset = (asset: CompanyAsset) => {
    setEditingAsset(asset)
    assetForm.setFieldsValue({
      ...asset,
      issue_date: asset.issue_date ? dayjs(asset.issue_date) : null,
      expiry_date: asset.expiry_date ? dayjs(asset.expiry_date) : null,
      data_json: JSON.stringify(asset.data || {}, null, 2),
    })
    setAssetDrawerOpen(true)
  }

  const normalizeAssetPayload = (values: any): CompanyAssetInput => {
    let data: Record<string, unknown> = {}
    try {
      data = values.data_json ? JSON.parse(values.data_json) : {}
    } catch {
      throw new Error('原始数据 JSON 格式不正确')
    }
    return {
      company_name: values.company_name,
      asset_type: values.asset_type,
      source_sheet: values.source_sheet || '手工维护',
      name: values.name,
      category: values.category,
      certificate_no: values.certificate_no,
      issuer: values.issuer,
      issue_date: values.issue_date ? values.issue_date.format('YYYY-MM-DD') : undefined,
      expiry_date: values.expiry_date ? values.expiry_date.format('YYYY-MM-DD') : undefined,
      status: values.status || '有效',
      amount_wanyuan: values.amount_wanyuan ?? null,
      keywords: values.keywords || [],
      data,
      source_type: editingAsset ? undefined : 'manual',
    }
  }

  const handleAssetSave = async () => {
    setAssetSaving(true)
    try {
      const values = await assetForm.validateFields()
      const payload = normalizeAssetPayload(values)
      if (editingAsset?.id) {
        await updateCompanyAsset(editingAsset.id, payload)
        message.success('资料已更新')
      } else {
        await createCompanyAsset(payload)
        message.success('资料已新增')
      }
      setAssetDrawerOpen(false)
      setEditingAsset(null)
      await loadProfile()
      await loadAssets(assetQuery)
    } catch (error) {
      message.error(error instanceof Error ? error.message : '保存资料失败')
    } finally {
      setAssetSaving(false)
    }
  }

  const handleAssetDelete = (asset: CompanyAsset) => {
    let reason = ''
    Modal.confirm({
      title: '停用资料',
      content: (
        <Input.TextArea
          rows={3}
          placeholder="可填写停用原因"
          onChange={(event) => {
            reason = event.target.value
          }}
        />
      ),
      okText: '确认停用',
      okButtonProps: { danger: true },
      cancelText: '取消',
      async onOk() {
        await deleteCompanyAsset(asset.id, reason)
        message.success('资料已停用')
        await loadProfile()
        await loadAssets(assetQuery)
      },
    })
  }

  const handleAssetRestore = async (asset: CompanyAsset) => {
    try {
      await restoreCompanyAsset(asset.id)
      message.success('资料已恢复')
      await loadProfile()
      await loadAssets(assetQuery)
    } catch {
      message.error('恢复失败')
    }
  }

  const columns: ColumnsType<CompanyAsset> = [
    {
      title: '资料名称',
      dataIndex: 'name',
      ellipsis: true,
      render: (value: string, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{value || '-'}</Text>
          <Text type="secondary">{record.certificate_no || record.category || record.source_sheet}</Text>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'asset_type',
      width: 120,
      render: (value: string) => <Tag>{ASSET_TYPE_LABELS[value] || value}</Tag>,
    },
    {
      title: '来源',
      dataIndex: 'source_sheet',
      width: 120,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 90,
      render: (value?: string) => <Badge status={statusColor(value) as any} text={value || '未知'} />,
    },
    {
      title: '来源',
      dataIndex: 'source_type',
      width: 110,
      render: (value?: string) => {
        const label = value === 'manual' ? '手工新增' : value === 'manual_edit' ? '手工编辑' : 'Excel导入'
        return <Tag color={value === 'excel_import' ? 'default' : 'purple'}>{label}</Tag>
      },
    },
    {
      title: '有效期至',
      dataIndex: 'expiry_date',
      width: 120,
      render: (value?: string) => value || '-',
    },
    {
      title: '关键词',
      dataIndex: 'keywords',
      render: (values: string[]) => (
        <Space wrap>
          {(values || []).slice(0, 3).map((item) => <Tag key={item} color="blue">{item}</Tag>)}
        </Space>
      ),
    },
    {
      title: '操作',
      width: 210,
      render: (_, record) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => setSelectedAsset(record)}>详情</Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEditAsset(record)}>编辑</Button>
          {record.is_deleted ? (
            <Button size="small" icon={<UndoOutlined />} onClick={() => handleAssetRestore(record)}>恢复</Button>
          ) : (
            <Button size="small" danger icon={<StopOutlined />} onClick={() => handleAssetDelete(record)}>停用</Button>
          )}
        </Space>
      ),
    },
  ]

  const renderOverview = () => (
    <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
      <Col xs={12} md={4}>
        <Statistic title="结构化资料" value={assetSummary?.total_assets || 0} />
      </Col>
      <Col xs={12} md={4}>
        <Statistic title="有效资质" value={assetSummary?.valid_qualification_count || 0} />
      </Col>
      <Col xs={12} md={4}>
        <Statistic title="过期资料" value={assetSummary?.expired_count || 0} valueStyle={{ color: '#cf1322' }} />
      </Col>
      <Col xs={12} md={4}>
        <Statistic title="180天临期" value={assetSummary?.expiring_soon_count || 0} valueStyle={{ color: '#d48806' }} />
      </Col>
      <Col xs={12} md={4}>
        <Statistic title="资料类型" value={Object.keys(assetSummary?.by_type || {}).length} />
      </Col>
      <Col xs={12} md={4}>
        <Statistic title="服务区域" value={profile?.service_regions?.length || 0} />
      </Col>
    </Row>
  )

  const renderImportTab = () => (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Alert
        type="info"
        showIcon
        message="导入流程已改为预览确认"
        description="上传 Excel 后先解析并展示摘要、样例资料和校验问题，确认后才会替换当前资料库。"
      />
      <Upload accept=".xlsx" maxCount={1} showUploadList={false} beforeUpload={handlePreview}>
        <Button type="primary" icon={<CloudUploadOutlined />} loading={importing}>
          上传并解析 Excel
        </Button>
      </Upload>

      {preview && (
        <div>
          <Title level={5}>导入预览：{preview.filename}</Title>
          <Row gutter={[12, 12]} style={{ marginBottom: 12 }}>
            <Col xs={12} md={6}><Statistic title="解析资料" value={preview.summary.total_assets} /></Col>
            <Col xs={12} md={6}><Statistic title="有效资质" value={preview.summary.valid_qualification_count} /></Col>
            <Col xs={12} md={6}><Statistic title="过期" value={preview.summary.expired_count} /></Col>
            <Col xs={12} md={6}><Statistic title="校验提示" value={preview.warnings.length} /></Col>
          </Row>
          {preview.warnings.length > 0 && (
            <Alert
              type="warning"
              showIcon
              message={`发现 ${preview.warnings.length} 条校验提示`}
              description={preview.warnings.slice(0, 5).join('；')}
              style={{ marginBottom: 12 }}
            />
          )}
          <Table
            size="small"
            rowKey={(record) => `${record.source_sheet}-${record.name}-${record.certificate_no}`}
            columns={columns.slice(0, 5)}
            dataSource={preview.assets_sample}
            pagination={false}
          />
          <Space style={{ marginTop: 12 }}>
            <Button type="primary" icon={<CheckCircleOutlined />} loading={confirming} onClick={handleConfirmImport}>
              确认入库并替换当前资料库
            </Button>
            <Button onClick={() => setPreview(null)}>取消</Button>
          </Space>
        </div>
      )}

      {lastImport && (
        <Alert
          type={lastImport.warnings.length ? 'warning' : 'success'}
          showIcon
          message={`最近导入完成：${lastImport.company_name || '未识别公司名'}`}
          description={`资料数 ${lastImport.summary.total_assets}，校验提示 ${lastImport.warnings.length}`}
        />
      )}
    </Space>
  )

  const renderAssetsTab = () => (
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      <Space wrap>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreateAsset}>
          新增资料
        </Button>
        <Select
          allowClear
          placeholder="资料类型"
          style={{ width: 150 }}
          value={assetQuery.asset_type}
          options={Object.entries(ASSET_TYPE_LABELS).map(([value, label]) => ({ value, label }))}
          onChange={(value) => loadAssets({ ...assetQuery, asset_type: value, skip: 0 })}
        />
        <Select
          allowClear
          placeholder="状态"
          style={{ width: 120 }}
          value={assetQuery.status}
          options={['有效', '过期', '审核中', '未知'].map((value) => ({ value, label: value }))}
          onChange={(value) => loadAssets({ ...assetQuery, status: value, skip: 0 })}
        />
        <Select
          allowClear
          placeholder="来源 Sheet"
          style={{ width: 170 }}
          value={assetQuery.source_sheet}
          options={sourceSheetOptions}
          onChange={(value) => loadAssets({ ...assetQuery, source_sheet: value, skip: 0 })}
        />
        <Input.Search
          allowClear
          placeholder="搜索名称、编号、机构、关键词"
          style={{ width: 280 }}
          onSearch={(value) => loadAssets({ ...assetQuery, keyword: value || undefined, skip: 0 })}
        />
        <Button icon={<ReloadOutlined />} onClick={() => loadAssets({ skip: 0, limit: assetQuery.limit || 10 })}>
          重置
        </Button>
        <Space>
          <Text type="secondary">显示已停用</Text>
          <Switch
            checked={!!assetQuery.include_deleted}
            onChange={(checked) => loadAssets({ ...assetQuery, include_deleted: checked, skip: 0 })}
          />
        </Space>
      </Space>
      <Table
        rowKey="id"
        loading={assetLoading}
        columns={columns}
        dataSource={assets}
        pagination={{
          total: assetsTotal,
          current: Math.floor((assetQuery.skip || 0) / (assetQuery.limit || 10)) + 1,
          pageSize: assetQuery.limit || 10,
          showSizeChanger: true,
          onChange: (page, pageSize) => loadAssets({ ...assetQuery, skip: (page - 1) * pageSize, limit: pageSize }),
        }}
      />
    </Space>
  )

  const renderStrategyTab = () => (
    <Form form={form} layout="vertical" onFinish={handleSave} style={{ maxWidth: 900 }}>
      <Row gutter={16}>
        <Col xs={24} md={12}>
          <Form.Item name="name" label="公司名称" rules={[{ required: true, message: '请输入公司名称' }]}>
            <Input placeholder="请输入公司名称" />
          </Form.Item>
        </Col>
        <Col xs={24} md={12}>
          <Form.Item name="target_domains" label="目标领域" rules={[{ required: true, message: '请选择目标领域' }]}>
            <Select mode="multiple" placeholder="请选择目标领域" options={TARGET_DOMAINS.map((value) => ({ label: value, value }))} />
          </Form.Item>
        </Col>
        <Col xs={24} md={12}>
          <Form.Item name="budget_min" label="预算下限（万元）" rules={[{ required: true, message: '请输入预算下限' }]}>
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
        <Col xs={24} md={12}>
          <Form.Item name="budget_max" label="预算上限（万元）" rules={[{ required: true, message: '请输入预算上限' }]}>
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
        <Col span={24}>
          <Form.Item name="qualifications" label="手工补充资质">
            <Select mode="tags" placeholder="请选择或输入补充资质" options={QUALIFICATIONS.map((value) => ({ label: value, value }))} />
          </Form.Item>
        </Col>
        <Col span={24}>
          <Form.Item name="service_regions" label="服务区域">
            <Select mode="multiple" placeholder="请选择服务区域" options={SERVICE_REGIONS.map((value) => ({ label: value, value }))} />
          </Form.Item>
        </Col>
      </Row>
      <Space>
        <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={saving}>保存策略</Button>
        <Button icon={<ReloadOutlined />} onClick={handleReset}>重置为默认</Button>
      </Space>
    </Form>
  )

  const renderIssuesTab = () => {
    const warnings = lastImport?.warnings || preview?.warnings || []
    const byStatus = assetSummary?.by_status || {}
    return (
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        <Row gutter={[12, 12]}>
          <Col xs={12} md={6}><Statistic title="有效" value={byStatus['有效'] || 0} /></Col>
          <Col xs={12} md={6}><Statistic title="过期" value={byStatus['过期'] || 0} valueStyle={{ color: '#cf1322' }} /></Col>
          <Col xs={12} md={6}><Statistic title="审核中" value={byStatus['审核中'] || 0} /></Col>
          <Col xs={12} md={6}><Statistic title="未知" value={byStatus['未知'] || 0} /></Col>
        </Row>
        {warnings.length ? (
          <List
            bordered
            dataSource={warnings}
            renderItem={(item) => (
              <List.Item>
                <WarningOutlined style={{ color: '#d48806', marginRight: 8 }} />
                {item}
              </List.Item>
            )}
          />
        ) : (
          <Empty description="暂无导入校验提示" />
        )}
      </Space>
    )
  }

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '100px 0' }}><Spin size="large" /></div>
  }

  return (
    <div>
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 16 }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>资料管理工作台</Title>
          <Text type="secondary">管理公司资料、导入校验和匹配策略，资料证据会直接参与招标匹配评分。</Text>
        </div>
        <Tag color="blue" icon={<DatabaseOutlined />}>{profile?.name || '未配置公司'}</Tag>
      </Space>

      {renderOverview()}

      <Tabs
        defaultActiveKey="assets"
        items={[
          { key: 'import', label: <span><CloudUploadOutlined /> 资料导入</span>, children: renderImportTab() },
          { key: 'assets', label: <span><FilterOutlined /> 资料库</span>, children: renderAssetsTab() },
          { key: 'strategy', label: <span><SettingOutlined /> 匹配策略</span>, children: renderStrategyTab() },
          { key: 'issues', label: <span><WarningOutlined /> 校验问题</span>, children: renderIssuesTab() },
        ]}
      />

      <Drawer
        title="资料详情"
        open={!!selectedAsset}
        onClose={() => setSelectedAsset(null)}
        width={560}
      >
        {selectedAsset && (
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="名称">{selectedAsset.name || '-'}</Descriptions.Item>
              <Descriptions.Item label="类型">{ASSET_TYPE_LABELS[selectedAsset.asset_type] || selectedAsset.asset_type}</Descriptions.Item>
              <Descriptions.Item label="来源 Sheet">{selectedAsset.source_sheet}</Descriptions.Item>
              <Descriptions.Item label="状态"><Tag color={statusColor(selectedAsset.status)}>{selectedAsset.status || '未知'}</Tag></Descriptions.Item>
              <Descriptions.Item label="证书编号">{selectedAsset.certificate_no || '-'}</Descriptions.Item>
              <Descriptions.Item label="发证机构">{selectedAsset.issuer || '-'}</Descriptions.Item>
              <Descriptions.Item label="发证日期">{selectedAsset.issue_date || '-'}</Descriptions.Item>
              <Descriptions.Item label="有效期至">{selectedAsset.expiry_date || '-'}</Descriptions.Item>
              <Descriptions.Item label="金额（万元）">{selectedAsset.amount_wanyuan || '-'}</Descriptions.Item>
              <Descriptions.Item label="来源类型">{selectedAsset.source_type || '-'}</Descriptions.Item>
              <Descriptions.Item label="是否停用">{selectedAsset.is_deleted ? '是' : '否'}</Descriptions.Item>
              <Descriptions.Item label="停用原因">{selectedAsset.deleted_reason || '-'}</Descriptions.Item>
            </Descriptions>
            <div>
              <Text strong>关键词</Text>
              <div style={{ marginTop: 8 }}>
                <Space wrap>
                  {(selectedAsset.keywords || []).map((item) => <Tag key={item} color="blue">{item}</Tag>)}
                </Space>
              </div>
            </div>
            <div>
              <Text strong>原始数据</Text>
              <pre style={{ marginTop: 8, padding: 12, background: '#f6f8fa', borderRadius: 6, maxHeight: 260, overflow: 'auto' }}>
                {JSON.stringify(selectedAsset.data || {}, null, 2)}
              </pre>
            </div>
          </Space>
        )}
      </Drawer>

      <Drawer
        title={editingAsset ? '编辑资料' : '新增资料'}
        open={assetDrawerOpen}
        onClose={() => setAssetDrawerOpen(false)}
        width={680}
        extra={
          <Space>
            <Button onClick={() => setAssetDrawerOpen(false)}>取消</Button>
            <Button type="primary" loading={assetSaving} onClick={handleAssetSave}>保存</Button>
          </Space>
        }
      >
        <Form form={assetForm} layout="vertical">
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="asset_type" label="资料类型" rules={[{ required: true, message: '请选择资料类型' }]}>
                <Select options={Object.entries(ASSET_TYPE_LABELS).map(([value, label]) => ({ value, label }))} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="status" label="状态">
                <Select options={['有效', '过期', '审核中', '未知'].map((value) => ({ value, label: value }))} />
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item name="name" label="资料名称" rules={[{ required: true, message: '请输入资料名称' }]}>
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="source_sheet" label="来源">
                <Input placeholder="手工维护" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="category" label="分类">
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="certificate_no" label="证书/合同编号">
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="issuer" label="发证机构/客户">
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="issue_date" label="发证/签订日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="expiry_date" label="有效期至/结束日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="amount_wanyuan" label="金额（万元）">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="company_name" label="公司名称">
                <Input placeholder={profile?.name || ''} />
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item name="keywords" label="关键词">
                <Select mode="tags" placeholder="输入关键词后回车" />
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item name="data_json" label="原始数据 JSON">
                <Input.TextArea rows={8} spellCheck={false} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Drawer>
    </div>
  )
}

export default CompanyProfilePage
