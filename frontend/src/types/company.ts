export interface CompanyProfile {
  name: string
  target_domains: string[]
  budget_range: [number, number]
  qualifications: string[]
  service_regions: string[]
  bid_history?: BidRecord[]
  asset_summary?: CompanyAssetSummary
  assets?: CompanyAsset[]
}

export interface BidRecord {
  tender_id: string
  tender_title: string
  bid_date: string
  result: 'won' | 'lost' | 'pending'
  feedback?: string
}

export interface CompanyProfileInput {
  name?: string
  target_domains?: string[]
  budget_range?: [number, number]
  qualifications?: string[]
  service_regions?: string[]
}

export interface CompanyAssetSummary {
  total_assets: number
  by_type: Record<string, number>
  by_sheet: Record<string, number>
  by_status: Record<string, number>
  valid_qualification_count: number
  expired_count: number
  expiring_soon_count: number
  top_qualifications: string[]
}

export interface CompanyAsset {
  id: number
  company_name: string
  asset_type: string
  source_sheet: string
  name: string
  category?: string
  certificate_no?: string
  issuer?: string
  issue_date?: string
  expiry_date?: string
  status?: string
  amount_wanyuan?: number
  keywords: string[]
  data: Record<string, unknown>
  import_batch_id?: string
  source_type?: 'excel_import' | 'manual' | 'manual_edit' | string
  is_deleted?: boolean
  deleted_at?: string | null
  deleted_reason?: string | null
}

export interface CompanyImportResult {
  batch_id: string
  company_name: string
  summary: CompanyAssetSummary
  warnings: string[]
}

export interface CompanyImportPreview extends CompanyImportResult {
  preview_id: string
  filename: string
  assets_sample: CompanyAsset[]
}

export interface CompanyAssetsResponse {
  total: number
  skip: number
  limit: number
  items: CompanyAsset[]
}

export interface CompanyAssetQuery {
  asset_type?: string
  status?: string
  source_sheet?: string
  keyword?: string
  include_deleted?: boolean
  skip?: number
  limit?: number
}

export interface CompanyAssetInput {
  company_name?: string
  asset_type: string
  source_sheet?: string
  name: string
  category?: string
  certificate_no?: string
  issuer?: string
  issue_date?: string
  expiry_date?: string
  status?: string
  amount_wanyuan?: number | null
  keywords?: string[]
  data?: Record<string, unknown>
  source_type?: string
}
