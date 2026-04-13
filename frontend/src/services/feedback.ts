import api from './api'

export interface RecordBidPayload {
  tender_id: number
  bid_price: number
  score: number
  recommendation: string
  grade: string
}

export interface RecordBidResponse {
  id: number
  tender_id: number
  actual_result: string
}

export interface UpdateBidResultPayload {
  is_won: boolean
  lose_reason?: string
  notes?: string
}

export interface UpdateBidResultResponse {
  id: number
  tender_id: number
  actual_result: string
  is_won: boolean
}

export const recordBidFeedback = async (
  payload: RecordBidPayload
): Promise<RecordBidResponse> => {
  return api.post<unknown, RecordBidResponse>('/feedback/bid', payload)
}

export const updateBidResult = async (
  recordId: number,
  payload: UpdateBidResultPayload
): Promise<UpdateBidResultResponse> => {
  return api.put<unknown, UpdateBidResultResponse>(
    `/feedback/result/${recordId}`,
    payload
  )
}
