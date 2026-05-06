export type MatchGrade = 'A' | 'B' | 'C' | 'D'

export type RecommendationLevel = '强烈推荐' | '推荐' | '观望' | '不推荐'

export interface Tender {
  id: string
  title: string
  sourceUrl?: string | null
  projectNumber: string
  purchaser: string
  agency: string
  budget: number
  publishDate: string
  deadline: string
  location: string
  category: string
  procurementType: string
  status: 'pending' | 'analyzing' | 'analyzed'
  matchGrade?: MatchGrade
  recommendationLevel?: RecommendationLevel
  matchScore?: number
  createdAt: string
  updatedAt: string
}

export interface MatchResult {
  grade: MatchGrade
  score: number
  reasons: string[]
  strengths: string[]
  weaknesses: string[]
}

export interface Decision {
  recommendation: RecommendationLevel
  confidence: number
  keyFactors: string[]
  riskAssessment: string
  actionItems: string[]
}

export interface AnalysisResult {
  tenderId: string
  matchResult: MatchResult
  decision: Decision
  analyzedAt: string
  rawAnalysis?: string
}

export interface TenderListParams {
  page?: number
  pageSize?: number
  keyword?: string
  status?: string
  matchGrade?: MatchGrade
  category?: string
  startDate?: string
  endDate?: string
}

export interface BatchAnalyzeParams {
  tenderIds: string[]
}

export interface BatchAnalyzeFailedItem {
  tender_id: number
  reason: string
}

export interface BatchAnalyzeResponse {
  total: number
  success: number
  failed: number
  success_ids: number[]
  failed_items: BatchAnalyzeFailedItem[]
  retryable_ids: number[]
}

export interface TenderOverview {
  total: number
  analyzed: number
  pending: number
  strong_recommended: number
}

export interface GateCheck {
  name: string
  result: 'pass' | 'fail' | 'warning'
  reason: string
  is_mandatory: boolean
  detail?: string
}

export interface ExtractionInfo {
  budget: {
    value: number | null
    confidence: number
  }
  deadline: string | null
  qualifications: string[]
  tags: string[]
  region: string | null
  contact: {
    person: string | null
    phone: string | null
    email: string | null
  }
}

export interface MatchingInfo {
  pass_gate: boolean
  score: number
  grade: MatchGrade
  recommendation: string
  gate_checks: GateCheck[]
  details?: MatchingDetails
}

export interface EvidenceAssetRef {
  id?: number
  name?: string
  asset_type?: string
  source_sheet?: string
  status?: string
  certificate_no?: string
  expiry_date?: string
}

export interface EvidenceMatch {
  dimension: string
  requirement: string
  status: 'matched' | 'missing' | 'review' | 'weak' | string
  score_delta: number
  matched_assets: EvidenceAssetRef[]
  reason: string
  is_mandatory?: boolean
}

export interface MatchingDimensionScore {
  name: string
  score: number
  weight: number
  details: string
}

export interface MatchingDetails {
  dimension_scores?: Record<string, MatchingDimensionScore>
  evidence_matches?: EvidenceMatch[]
  gate_evidence?: EvidenceMatch[]
  missing_items?: EvidenceMatch[]
  risk_items?: EvidenceMatch[]
}

export interface DecisionInfo {
  action: '投标' | '不投标' | '评估后决定'
  confidence: number
  reason: string
  risks: string[]
}

export interface FullAnalysisResult {
  tender_id: number
  title: string
  source_url: string | null
  publish_date: string | null
  extraction: ExtractionInfo
  matching: MatchingInfo
  decision: DecisionInfo | null
}
