import api from './api'
import type { PaginatedResponse } from '../types'
import type {
  Tender,
  AnalysisResult,
  TenderListParams,
  BatchAnalyzeParams,
  BatchAnalyzeResponse,
  FullAnalysisResult,
  TenderOverview,
} from '../types/tender'

export interface TenderListResponse extends PaginatedResponse<Tender> {
  summary?: TenderOverview
}

const normalizeTender = (item: Record<string, unknown>): Tender => {
  const score = Number(item.match_score ?? item.score ?? 0)
  const grade = (item.match_grade ?? item.grade) as Tender['matchGrade']
  const recommendation = (item.recommendation ?? item.recommendation_level) as Tender['recommendationLevel']
  const rawStatus = String(item.extraction_status ?? item.status ?? '')
  const normalizedStatus: Tender['status'] =
    rawStatus === 'completed'
      ? 'analyzed'
      : rawStatus === 'processing'
      ? 'analyzing'
      : rawStatus === 'analyzed' || rawStatus === 'analyzing' || rawStatus === 'pending'
      ? rawStatus
      : 'pending'
  return {
    id: String(item.id ?? ''),
    title: String(item.title ?? '未命名项目'),
    sourceUrl: item.source_url ? String(item.source_url) : null,
    projectNumber: String(item.project_number ?? item.projectNumber ?? '-'),
    purchaser: String(item.purchaser ?? '-'),
    agency: String(item.agency ?? '-'),
    budget: Number(item.budget_amount ?? item.budget ?? 0),
    publishDate: String(item.publish_date ?? item.publishDate ?? ''),
    deadline: String(item.deadline ?? ''),
    location: String(item.region ?? item.location ?? '-'),
    category: String(item.notice_type ?? item.category ?? '-'),
    procurementType: String(item.procurement_type ?? item.procurementType ?? '-'),
    status: normalizedStatus,
    matchGrade: grade,
    recommendationLevel: recommendation,
    matchScore: Number.isFinite(score) ? score : 0,
    createdAt: String(item.created_at ?? item.createdAt ?? ''),
    updatedAt: String(item.updated_at ?? item.updatedAt ?? ''),
  }
}

export const getTenders = async (
  params: TenderListParams = {}
): Promise<TenderListResponse> => {
  const { page, pageSize, ...rest } = params
  const skip = page && pageSize ? (page - 1) * pageSize : undefined
  const limit = pageSize
  const response = await api.get<unknown, TenderListResponse>('/tenders/', {
    params: {
      ...rest,
      ...(skip !== undefined ? { skip } : {}),
      ...(limit !== undefined ? { limit } : {}),
    },
  })
  return {
    ...response,
    items: Array.isArray(response.items)
      ? (response.items as unknown as Record<string, unknown>[]).map(normalizeTender)
      : [],
    page: page ?? response.page ?? 1,
    pageSize: pageSize ?? response.pageSize ?? limit ?? 10,
    summary: response.summary,
  }
}

export const getTenderAnalysis = async (
  tenderId: string
): Promise<FullAnalysisResult> => {
  const response = await api.get<unknown, FullAnalysisResult>(
    `/tenders/${tenderId}/analysis`
  )
  return response
}

export const analyzeTender = async (tenderId: string): Promise<AnalysisResult> => {
  const response = await api.post<unknown, AnalysisResult>(
    `/tenders/${tenderId}/analyze`
  )
  return response
}

export const analyzeBatch = async (
  params: BatchAnalyzeParams
): Promise<BatchAnalyzeResponse> => {
  const tenderIds = params.tenderIds.map((id) => Number(id)).filter((id) => Number.isInteger(id) && id > 0)
  const response = await api.post<unknown, BatchAnalyzeResponse>('/tenders/analyze-batch', {
    tender_ids: tenderIds,
    tenderIds: tenderIds,
  })
  return response
}
