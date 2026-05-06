import api from './api'
import type {
  CompanyAsset,
  CompanyAssetInput,
  CompanyAssetQuery,
  CompanyAssetsResponse,
  CompanyAssetSummary,
  CompanyImportPreview,
  CompanyImportResult,
  CompanyProfile,
  CompanyProfileInput,
} from '../types/company'

export const getCompanyProfile = async (): Promise<CompanyProfile> => {
  const response = await api.get<unknown, CompanyProfile>('/company/')
  return response
}

export const updateCompanyProfile = async (
  profile: CompanyProfileInput
): Promise<CompanyProfile> => {
  const response = await api.put<unknown, CompanyProfile>('/company/', profile)
  return response
}

export const resetCompanyProfile = async (): Promise<CompanyProfile> => {
  const response = await api.post<unknown, CompanyProfile>('/company/reset')
  return response
}

export const previewCompanyExcel = async (file: File): Promise<CompanyImportPreview> => {
  const formData = new FormData()
  formData.append('file', file)
  const response = await api.post<unknown, CompanyImportPreview>('/company/import-excel/preview', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 60000,
  })
  return response
}

export const confirmCompanyExcelImport = async (previewId: string): Promise<CompanyImportResult> => {
  const response = await api.post<unknown, CompanyImportResult>('/company/import-excel', {
    preview_id: previewId,
  })
  return response
}

export const getCompanyAssets = async (params: CompanyAssetQuery): Promise<CompanyAssetsResponse> => {
  const response = await api.get<unknown, CompanyAssetsResponse>('/company/assets', { params })
  return response
}

export const getCompanyAssetSummary = async (): Promise<CompanyAssetSummary> => {
  const response = await api.get<unknown, CompanyAssetSummary>('/company/assets/summary')
  return response
}

export const createCompanyAsset = async (payload: CompanyAssetInput): Promise<CompanyAsset> => {
  const response = await api.post<unknown, CompanyAsset>('/company/assets', payload)
  return response
}

export const updateCompanyAsset = async (id: number, payload: CompanyAssetInput): Promise<CompanyAsset> => {
  const response = await api.put<unknown, CompanyAsset>(`/company/assets/${id}`, payload)
  return response
}

export const deleteCompanyAsset = async (id: number, reason?: string): Promise<CompanyAsset> => {
  const response = await api.delete<unknown, CompanyAsset>(`/company/assets/${id}`, {
    data: { reason },
  })
  return response
}

export const restoreCompanyAsset = async (id: number): Promise<CompanyAsset> => {
  const response = await api.post<unknown, CompanyAsset>(`/company/assets/${id}/restore`)
  return response
}
