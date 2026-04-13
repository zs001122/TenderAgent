export interface CompanyProfile {
  name: string
  target_domains: string[]
  budget_range: [number, number]
  qualifications: string[]
  service_regions: string[]
  bid_history?: BidRecord[]
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
