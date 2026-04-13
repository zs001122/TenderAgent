import { useState, useEffect, useCallback, useMemo } from 'react'
import { Table, Tag, Button, Space, message, Card, Statistic, Row, Col, Input, Segmented, Grid } from 'antd'
import { EyeOutlined, PlayCircleOutlined, RedoOutlined, LinkOutlined } from '@ant-design/icons'
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table'
import type { Tender, MatchGrade, RecommendationLevel } from '../types/tender'
import { analyzeBatch, getTenders } from '../services/tender'
import AnalysisDetailModal from '../components/AnalysisDetailModal'

const matchGradeColors: Record<MatchGrade, string> = {
  A: 'success',
  B: 'processing',
  C: 'warning',
  D: 'error',
}

const recommendationColors: Record<RecommendationLevel, string> = {
  强烈推荐: 'success',
  推荐: 'processing',
  观望: 'warning',
  不推荐: 'error',
}

const formatBudget = (budget?: number | null): string => {
  if (budget === null || budget === undefined || Number.isNaN(Number(budget))) {
    return '-'
  }
  const value = Number(budget)
  return `${value.toFixed(2)} 万元`
}

const formatDate = (dateStr: string): string => {
  return dateStr ? dateStr.split('T')[0] : '-'
}

const TenderList: React.FC = () => {
  const screens = Grid.useBreakpoint()
  const isMobile = !screens.md
  const [tenders, setTenders] = useState<Tender[]>([])
  const [loading, setLoading] = useState(false)
  const [summary, setSummary] = useState({
    total: 0,
    analyzed: 0,
    pending: 0,
    strong_recommended: 0,
  })
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  })
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedTenderId, setSelectedTenderId] = useState<number | null>(null)
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [batchAnalyzing, setBatchAnalyzing] = useState(false)
  const [retrying, setRetrying] = useState(false)
  const [lastFailedIds, setLastFailedIds] = useState<string[]>([])
  const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'analyzing' | 'analyzed'>('all')
  const [keyword, setKeyword] = useState('')

  const fetchTenders = useCallback(async (page: number, pageSize: number) => {
    setLoading(true)
    try {
      const result = await getTenders({ page, pageSize })
      setTenders(result.items)
      setPagination((prev) => ({
        ...prev,
        current: result.page,
        pageSize: result.pageSize,
        total: result.total,
      }))
      if (result.summary) {
        setSummary(result.summary)
      }
    } catch {
      message.error('获取招标列表失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchTenders(pagination.current, pagination.pageSize)
  }, [fetchTenders, pagination.current, pagination.pageSize])

  const handleTableChange = (paginationConfig: TablePaginationConfig) => {
    const { current = 1, pageSize = 10 } = paginationConfig
    fetchTenders(current, pageSize)
  }

  const handleViewDetail = (record: Tender) => {
    setSelectedTenderId(Number(record.id))
    setModalOpen(true)
  }

  const handleModalClose = () => {
    setModalOpen(false)
    setSelectedTenderId(null)
  }

  const runBatchAnalyze = async (ids: string[], isRetry: boolean) => {
    if (ids.length === 0) return
    if (isRetry) {
      setRetrying(true)
    } else {
      setBatchAnalyzing(true)
    }
    try {
      const result = await analyzeBatch({ tenderIds: ids })
      const failedIds = result.retryable_ids.map((id) => String(id))
      setLastFailedIds(failedIds)
      if (result.failed > 0) {
        const firstReason = result.failed_items[0]?.reason
        message.warning(
          `批量分析完成：成功 ${result.success} 条，失败 ${result.failed} 条${firstReason ? `（示例原因：${firstReason}）` : ''}`
        )
      } else {
        message.success(`批量分析完成：成功 ${result.success} 条`)
      }
      setSelectedRowKeys([])
      await fetchTenders(pagination.current, pagination.pageSize)
    } catch {
      message.error(isRetry ? '失败重试执行失败' : '批量分析执行失败')
    } finally {
      if (isRetry) {
        setRetrying(false)
      } else {
        setBatchAnalyzing(false)
      }
    }
  }

  const handleBatchAnalyze = () => {
    const ids = selectedRowKeys.map((item) => String(item))
    runBatchAnalyze(ids, false)
  }

  const handleRetryFailed = () => {
    runBatchAnalyze(lastFailedIds, true)
  }

  const filteredTenders = useMemo(() => {
    return tenders.filter((item) => {
      const statusPass = statusFilter === 'all' ? true : item.status === statusFilter
      const keywordPass = keyword.trim()
        ? item.title.toLowerCase().includes(keyword.trim().toLowerCase())
        : true
      return statusPass && keywordPass
    })
  }, [tenders, statusFilter, keyword])

  const dashboardStats = useMemo(
    () => ({
      total: summary.total,
      analyzed: summary.analyzed,
      pending: summary.pending,
      highRecommend: summary.strong_recommended,
    }),
    [summary]
  )

  const columns: ColumnsType<Tender> = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      width: isMobile ? 200 : 300,
      render: (_: string, record: Tender) =>
        record.sourceUrl ? (
          <a href={record.sourceUrl} target="_blank" rel="noreferrer">
            {record.title} <LinkOutlined />
          </a>
        ) : (
          record.title
        ),
    },
    {
      title: '预算金额（万元）',
      dataIndex: 'budget',
      key: 'budget',
      render: (budget: number) => formatBudget(budget),
    },
    {
      title: '日期',
      key: 'dates',
      responsive: ['md'],
      render: (_, record) => (
        <div>
          <div style={{ fontSize: 12 }}>发: {formatDate(record.publishDate)}</div>
          <div style={{ fontSize: 12 }}>止: {formatDate(record.deadline)}</div>
        </div>
      ),
    },
    {
      title: '评估结果',
      key: 'evaluation',
      render: (_, record) => {
        const statusMap: Record<string, { text: string; color: string }> = {
          pending: { text: '待分析', color: 'default' },
          analyzing: { text: '分析中', color: 'processing' },
          analyzed: { text: '已分析', color: 'success' },
        }
        const statusConfig = statusMap[record.status] || { text: record.status, color: 'default' }
        return (
          <Space wrap size={[4, 4]}>
            <Tag color={record.matchGrade ? matchGradeColors[record.matchGrade] : 'default'}>
              评分 {record.matchGrade || '-'}
            </Tag>
            <Tag color={record.recommendationLevel ? recommendationColors[record.recommendationLevel] : 'default'}>
              {record.recommendationLevel || '未评估'}
            </Tag>
            <Tag color={statusConfig.color}>{statusConfig.text}</Tag>
          </Space>
        )
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 84,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            详情
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <>
      <Card
        title="招标列表看板"
        style={{ borderRadius: 16, boxShadow: '0 8px 24px rgba(14, 38, 74, 0.08)' }}
      >
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col xs={24} md={12} lg={6}>
            <Card bordered={false} style={{ borderRadius: 12, background: '#f8fbff' }}>
              <Statistic title="当前页项目数" value={dashboardStats.total} />
            </Card>
          </Col>
          <Col xs={24} md={12} lg={6}>
            <Card bordered={false} style={{ borderRadius: 12, background: '#f6ffed' }}>
              <Statistic title="已分析" value={dashboardStats.analyzed} />
            </Card>
          </Col>
          <Col xs={24} md={12} lg={6}>
            <Card bordered={false} style={{ borderRadius: 12, background: '#fffbe6' }}>
              <Statistic title="待分析" value={dashboardStats.pending} />
            </Card>
          </Col>
          <Col xs={24} md={12} lg={6}>
            <Card bordered={false} style={{ borderRadius: 12, background: '#f9f0ff' }}>
              <Statistic title="强烈推荐" value={dashboardStats.highRecommend} />
            </Card>
          </Col>
        </Row>

        <Space style={{ marginBottom: 12, width: '100%', justifyContent: 'space-between' }} wrap>
          <Space wrap>
            <Segmented
              options={[
                { label: '全部', value: 'all' },
                { label: '待分析', value: 'pending' },
                { label: '分析中', value: 'analyzing' },
                { label: '已分析', value: 'analyzed' },
              ]}
              value={statusFilter}
              onChange={(value) => setStatusFilter(value as 'all' | 'pending' | 'analyzing' | 'analyzed')}
            />
            <Input.Search
              allowClear
              placeholder="按标题搜索当前页"
              style={{ width: 260 }}
              onSearch={(value) => setKeyword(value)}
              onChange={(e) => setKeyword(e.target.value)}
            />
          </Space>
          <Space>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            disabled={selectedRowKeys.length === 0}
            loading={batchAnalyzing}
            onClick={handleBatchAnalyze}
          >
            批量分析（已选 {selectedRowKeys.length}）
          </Button>
          <Button
            icon={<RedoOutlined />}
            disabled={lastFailedIds.length === 0}
            loading={retrying}
            onClick={handleRetryFailed}
          >
            失败重试（{lastFailedIds.length}）
          </Button>
          </Space>
        </Space>
        <Table
          columns={columns}
          dataSource={filteredTenders}
          rowKey="id"
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => setSelectedRowKeys(keys),
          }}
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
          onChange={handleTableChange}
          tableLayout="fixed"
          size={isMobile ? 'small' : 'middle'}
          style={{ borderRadius: 12 }}
        />
      </Card>
      <AnalysisDetailModal
        tenderId={selectedTenderId}
        open={modalOpen}
        onClose={handleModalClose}
      />
    </>
  )
}

export default TenderList
