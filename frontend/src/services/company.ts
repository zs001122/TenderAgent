import api from './api'
import type { CompanyProfile, CompanyProfileInput } from '../types/company'

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
