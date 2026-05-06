import { useState, useEffect } from 'react'
import {
  Modal,
  Card,
  Descriptions,
  Tag,
  List,
  Progress,
  Space,
  Spin,
  Button,
  Input,
  InputNumber,
  Tabs,
  message,
  Typography,
  Divider,
  Empty,
} from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
  TrophyOutlined,
  RobotOutlined,
} from '@ant-design/icons'
import type { EvidenceMatch, FullAnalysisResult, GateCheck, MatchGrade } from '../types/tender'
import { analyzeTender, getTenderAnalysis } from '../services/tender'
import { recordBidFeedback, updateBidResult } from '../services/feedback'

const { Title, Text } = Typography

const matchGradeColors: Record<MatchGrade, string> = {
  A: '#52c41a',
  B: '#1890ff',
  C: '#faad14',
  D: '#ff4d4f',
}

const formatBudget = (budget: number | null): string => {
  if (budget === null || budget === undefined) return '-'
  return `${budget.toFixed(2)} 万元`
}

const formatDate = (dateStr: string | null): string => {
  if (!dateStr) return '-'
  return dateStr.split('T')[0]
}

interface AnalysisDetailModalProps {
  tenderId: number | null
  open: boolean
  onClose: () => void
}

const AnalysisDetailModal: React.FC<AnalysisDetailModalProps> = ({
  tenderId,
  open,
  onClose,
}) => {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<FullAnalysisResult | null>(null)
  const [bidPrice, setBidPrice] = useState<number>(0)
  const [loseReason, setLoseReason] = useState('')
  const [feedbackRecordId, setFeedbackRecordId] = useState<number | null>(null)
  const [feedbackLoading, setFeedbackLoading] = useState(false)

  useEffect(() => {
    if (open && tenderId) {
      fetchAnalysis()
      setLoseReason('')
      setFeedbackRecordId(null)
    }
  }, [open, tenderId])

  const fetchAnalysis = async () => {
    if (!tenderId) return
    setLoading(true)
    try {
      const result = await getTenderAnalysis(String(tenderId))
      setData(result)
    } catch (error: unknown) {
      const status = (error as { response?: { status?: number } })?.response?.status
      if (status === 404) {
        setData(null)
        message.info('暂无分析结果，请手动点击“手动分析”')
      } else {
        message.error('获取分析结果失败')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleManualAnalyze = async () => {
    if (!tenderId) return
    setLoading(true)
    try {
      await analyzeTender(String(tenderId))
      const latest = await getTenderAnalysis(String(tenderId))
      setData(latest)
      message.success('手动分析完成')
    } catch {
      message.error('手动分析失败')
    } finally {
      setLoading(false)
    }
  }

  const renderGateCheckIcon = (result: GateCheck['result']) => {
    switch (result) {
      case 'pass':
        return <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 18 }} />
      case 'fail':
        return <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 18 }} />
      case 'warning':
        return <WarningOutlined style={{ color: '#faad14', fontSize: 18 }} />
    }
  }

  const renderGateCheckTag = (result: GateCheck['result']) => {
    const config = {
      pass: { color: 'success', text: '通过' },
      fail: { color: 'error', text: '未通过' },
      warning: { color: 'warning', text: '警告' },
    }
    const { color, text } = config[result]
    return <Tag color={color}>{text}</Tag>
  }

  const renderExtractionSection = () => {
    if (!data?.extraction) return null
    const { extraction } = data

    return (
      <Card
        title={
          <Space>
            <span>提取信息</span>
            {extraction.budget?.confidence && (
              <Tag color="blue">置信度: {(extraction.budget.confidence * 100).toFixed(0)}%</Tag>
            )}
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        <Descriptions column={2} bordered size="small">
          <Descriptions.Item label="预算金额（万元）">
            {formatBudget(extraction.budget?.value)}
          </Descriptions.Item>
          <Descriptions.Item label="投标截止日期">
            {formatDate(extraction.deadline)}
          </Descriptions.Item>
          <Descriptions.Item label="项目地区" span={2}>
            {extraction.region || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="资质要求" span={2}>
            {extraction.qualifications?.length > 0 ? (
              <Space wrap>
                {extraction.qualifications.map((qual, index) => (
                  <Tag key={index} color="blue">
                    {qual}
                  </Tag>
                ))}
              </Space>
            ) : (
              <Text type="secondary">无特殊资质要求</Text>
            )}
          </Descriptions.Item>
          <Descriptions.Item label="业务标签" span={2}>
            {extraction.tags?.length > 0 ? (
              <Space wrap>
                {extraction.tags.map((tag, index) => (
                  <Tag key={index} color="purple">
                    {tag}
                  </Tag>
                ))}
              </Space>
            ) : (
              <Text type="secondary">无标签</Text>
            )}
          </Descriptions.Item>
          <Descriptions.Item label="联系人">
            {extraction.contact?.person || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="联系电话">
            {extraction.contact?.phone || '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>
    )
  }

  const renderGateSection = () => {
    if (!data?.matching) return null
    const { matching } = data

    return (
      <Card
        title={
          <Space>
            <span>Gate 检查结果</span>
            {matching.pass_gate ? (
              <Tag color="success" icon={<CheckCircleOutlined />}>
                通过门槛
              </Tag>
            ) : (
              <Tag color="error" icon={<CloseCircleOutlined />}>
                未通过门槛
              </Tag>
            )}
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        <List
          dataSource={matching.gate_checks || []}
          renderItem={(check: GateCheck) => (
            <List.Item>
              <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                <Space>
                  {renderGateCheckIcon(check.result)}
                  <Text strong>{check.name}</Text>
                  {check.is_mandatory && <Tag color="red">必须</Tag>}
                </Space>
                <Space>
                  <Text type="secondary">{check.reason}</Text>
                  {renderGateCheckTag(check.result)}
                </Space>
              </Space>
            </List.Item>
          )}
        />
      </Card>
    )
  }

  const renderRankingSection = () => {
    if (!data?.matching) return null
    const { matching } = data

    const getScoreColor = (score: number) => {
      if (score >= 80) return '#52c41a'
      if (score >= 60) return '#1890ff'
      if (score >= 40) return '#faad14'
      return '#ff4d4f'
    }

    const dimensionScores = matching.details?.dimension_scores || {}

    return (
      <Card
        title={
          <Space>
            <TrophyOutlined />
            <span>Ranking 评分详情</span>
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div style={{ textAlign: 'center' }}>
            <Title level={2} style={{ color: matchGradeColors[matching.grade as MatchGrade], marginBottom: 0 }}>
              {matching.grade} 级
            </Title>
            <Text type="secondary">综合评分</Text>
            <div style={{ marginTop: 16 }}>
              <Progress
                type="circle"
                percent={matching.score}
                strokeColor={getScoreColor(matching.score)}
                format={(percent) => (
                  <span style={{ fontSize: 24, fontWeight: 'bold' }}>{percent?.toFixed(0)}</span>
                )}
              />
            </div>
            <div style={{ marginTop: 8 }}>
              <Tag color={matchGradeColors[matching.grade as MatchGrade]} style={{ fontSize: 14, padding: '4px 12px' }}>
                {matching.recommendation}
              </Tag>
            </div>
          </div>
          {Object.keys(dimensionScores).length > 0 && (
            <List
              dataSource={Object.entries(dimensionScores)}
              renderItem={([key, item]) => (
                <List.Item key={key}>
                  <Space direction="vertical" style={{ width: '100%' }} size={4}>
                    <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                      <Text strong>{item.name}</Text>
                      <Text>{item.score.toFixed(1)} 分 / 权重 {(item.weight * 100).toFixed(0)}%</Text>
                    </Space>
                    <Progress percent={item.score} size="small" strokeColor={getScoreColor(item.score)} />
                    <Text type="secondary">{item.details}</Text>
                  </Space>
                </List.Item>
              )}
            />
          )}
        </Space>
      </Card>
    )
  }

  const renderEvidenceStatus = (status: EvidenceMatch['status']) => {
    const config: Record<string, { color: string; text: string }> = {
      matched: { color: 'success', text: '命中' },
      missing: { color: 'error', text: '缺失' },
      review: { color: 'warning', text: '待复核' },
      weak: { color: 'warning', text: '弱命中' },
    }
    const item = config[String(status)] || { color: 'default', text: String(status || '未知') }
    return <Tag color={item.color}>{item.text}</Tag>
  }

  const renderEvidenceSection = () => {
    const details = data?.matching?.details
    if (!details) {
      return (
        <Card title="匹配证据">
          <Empty description="当前分析结果暂无结构化证据链，请重新分析该招标" />
        </Card>
      )
    }

    const evidence = [...(details.gate_evidence || []), ...(details.evidence_matches || [])]

    return (
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        <Card title="证据概览">
          <Space wrap>
            <Tag color="success">命中 {evidence.filter((item) => item.status === 'matched').length}</Tag>
            <Tag color="error">缺失 {(details.missing_items || []).length}</Tag>
            <Tag color="warning">风险/复核 {(details.risk_items || []).length}</Tag>
          </Space>
        </Card>
        <Card title="命中与缺失证据">
          <List
            dataSource={evidence}
            locale={{ emptyText: '暂无证据项' }}
            renderItem={(item) => (
              <List.Item>
                <Space direction="vertical" style={{ width: '100%' }} size={6}>
                  <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                    <Space>
                      {renderEvidenceStatus(item.status)}
                      <Text strong>{item.dimension}</Text>
                      {item.is_mandatory && <Tag color="red">必须</Tag>}
                    </Space>
                    {item.score_delta ? <Text type="secondary">+{item.score_delta}</Text> : null}
                  </Space>
                  <Text>{item.requirement || '-'}</Text>
                  <Text type="secondary">{item.reason}</Text>
                  {!!item.matched_assets?.length && (
                    <Space wrap>
                      {item.matched_assets.map((asset, index) => (
                        <Tag key={`${asset.name}-${index}`} color="blue">
                          {asset.source_sheet} / {asset.name}
                        </Tag>
                      ))}
                    </Space>
                  )}
                </Space>
              </List.Item>
            )}
          />
        </Card>
      </Space>
    )
  }

  const renderDecisionSection = () => {
    if (!data?.decision) return null
    const { decision } = data

    const actionColors = {
      '投标': 'success',
      '不投标': 'error',
      '评估后决定': 'warning',
    } as const

    return (
      <Card
        title={
          <Space>
            <RobotOutlined />
            <span>Agent 决策建议</span>
          </Space>
        }
      >
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <div style={{ textAlign: 'center' }}>
            <Tag
              color={actionColors[decision.action]}
              style={{ fontSize: 16, padding: '8px 24px', marginBottom: 8 }}
            >
              {decision.action}
            </Tag>
            <div>
              <Text type="secondary">置信度: </Text>
              <Text strong>{(decision.confidence * 100).toFixed(0)}%</Text>
            </div>
          </div>

          <Divider style={{ margin: '8px 0' }} />

          <div>
            <Text strong>决策理由：</Text>
            <div style={{ marginTop: 8, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
              <Text>{decision.reason || '暂无理由'}</Text>
            </div>
          </div>

          {decision.risks && decision.risks.length > 0 && (
            <div>
              <Text strong type="danger">
                风险点：
              </Text>
              <List
                size="small"
                dataSource={decision.risks}
                renderItem={(risk: string) => (
                  <List.Item style={{ color: '#ff4d4f' }}>
                    <WarningOutlined style={{ marginRight: 8 }} />
                    {risk}
                  </List.Item>
                )}
              />
            </div>
          )}
        </Space>
      </Card>
    )
  }

  const handleRecordBid = async () => {
    if (!tenderId || !data?.matching) {
      message.warning('当前无可提交的分析数据')
      return
    }
    setFeedbackLoading(true)
    try {
      const response = await recordBidFeedback({
        tender_id: tenderId,
        bid_price: Number(bidPrice || 0),
        score: Number(data.matching.score || 0),
        recommendation: String(data.matching.recommendation || ''),
        grade: String(data.matching.grade || 'D'),
      })
      setFeedbackRecordId(response.id)
      message.success(`投标记录已创建（ID: ${response.id}）`)
    } catch {
      message.error('投标记录创建失败')
    } finally {
      setFeedbackLoading(false)
    }
  }

  const handleUpdateBidResult = async (isWon: boolean) => {
    if (!feedbackRecordId) {
      message.warning('请先记录投标信息')
      return
    }
    setFeedbackLoading(true)
    try {
      const response = await updateBidResult(feedbackRecordId, {
        is_won: isWon,
        lose_reason: isWon ? undefined : loseReason || '未提供原因',
      })
      message.success(`投标结果已更新：${response.actual_result}`)
    } catch {
      message.error('投标结果更新失败')
    } finally {
      setFeedbackLoading(false)
    }
  }

  const renderFeedbackSection = () => {
    return (
      <Card title="反馈闭环（投标与结果）">
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Space wrap>
            <Text>投标报价：</Text>
            <InputNumber
              min={0}
              value={bidPrice}
              onChange={(value) => setBidPrice(Number(value || 0))}
              style={{ width: 200 }}
              addonAfter="元"
            />
            <Button
              type="primary"
              loading={feedbackLoading}
              onClick={handleRecordBid}
            >
              记录投标反馈
            </Button>
          </Space>
          <Space wrap>
            <Input
              placeholder="未中标原因（可选）"
              value={loseReason}
              onChange={(e) => setLoseReason(e.target.value)}
              style={{ width: 360 }}
            />
            <Button
              disabled={!feedbackRecordId}
              loading={feedbackLoading}
              onClick={() => handleUpdateBidResult(true)}
            >
              标记中标
            </Button>
            <Button
              danger
              disabled={!feedbackRecordId}
              loading={feedbackLoading}
              onClick={() => handleUpdateBidResult(false)}
            >
              标记未中标
            </Button>
          </Space>
          <Text type="secondary">
            {feedbackRecordId
              ? `当前反馈记录 ID: ${feedbackRecordId}`
              : '请先创建投标反馈记录，再更新中标结果'}
          </Text>
        </Space>
      </Card>
    )
  }

  return (
    <Modal
      title={data?.title || '分析详情'}
      open={open}
      onCancel={onClose}
      width={800}
      footer={null}
      destroyOnHidden
    >
      <Spin spinning={loading}>
        {data ? (
          <Tabs
            defaultActiveKey="extraction"
            items={[
              { key: 'extraction', label: '提取信息', children: renderExtractionSection() },
              { key: 'gate', label: 'Gate校验', children: renderGateSection() },
              { key: 'ranking', label: '评分详情', children: renderRankingSection() },
              { key: 'evidence', label: '匹配证据', children: renderEvidenceSection() },
              { key: 'decision', label: '决策建议', children: renderDecisionSection() },
              { key: 'feedback', label: '反馈闭环', children: renderFeedbackSection() },
            ]}
          />
        ) : (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Space direction="vertical" size="middle">
              <Text type="secondary">暂无分析数据</Text>
              <Button type="primary" onClick={handleManualAnalyze} loading={loading}>
                手动分析
              </Button>
            </Space>
          </div>
        )}
      </Spin>
    </Modal>
  )
}

export default AnalysisDetailModal
