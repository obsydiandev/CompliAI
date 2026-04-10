import axios from 'axios'
import type {
  Token,
  User,
  Organization,
  Membership,
  AISystem,
  TechnicalFile,
  TechnicalFileRevision,
  Section,
  EvidenceAttachment,
  CompletenessResult,
  IntendedPurposeResult,
} from '@/types'

const BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api/v1'

const api = axios.create({ baseURL: BASE_URL })

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('compliai_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('compliai_token')
      window.location.href = '/auth/login'
    }
    return Promise.reject(error)
  }
)

// ----- Request/input types -----

export interface RegisterData {
  email: string
  password: string
  full_name: string
  org_name: string
}

export interface LoginData {
  username: string
  password: string
}

export interface CreateOrgData {
  name: string
  slug?: string
}

export interface InviteData {
  email: string
  role: string
}

export interface CreateSystemData {
  org_id: string
  name: string
  description?: string
  intended_purpose?: string
  category: string
  annex_iii_classification?: boolean
}

export interface CreateRevisionData {
  version?: string
  linked_commit_sha?: string
  linked_model_version?: string
  change_summary?: string
}

// ----- API namespaces -----

export const authApi = {
  register: (data: RegisterData) => api.post<Token>('/auth/register', data),
  login: (data: LoginData) =>
    api.post<Token>('/auth/login', data, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),
  me: () => api.get<User>('/auth/me'),
}

export const orgApi = {
  list: () => api.get<Organization[]>('/organizations/'),
  create: (data: CreateOrgData) => api.post<Organization>('/organizations/', data),
  get: (id: string) => api.get<Organization>(`/organizations/${id}`),
  update: (id: string, data: Partial<Organization>) =>
    api.put<Organization>(`/organizations/${id}`, data),
  invite: (id: string, data: InviteData) => api.post(`/organizations/${id}/invite`, data),
  members: (id: string) => api.get<Membership[]>(`/organizations/${id}/members`),
}

export const systemApi = {
  list: (orgId: string) => api.get<AISystem[]>(`/systems/?org_id=${orgId}`),
  create: (data: CreateSystemData) => api.post<AISystem>('/systems/', data),
  get: (id: string) => api.get<AISystem>(`/systems/${id}`),
  update: (id: string, data: Partial<AISystem>) => api.put<AISystem>(`/systems/${id}`, data),
  delete: (id: string) => api.delete(`/systems/${id}`),
  validatePurpose: (purpose: string) =>
    api.post<IntendedPurposeResult>('/systems/validate-purpose', {
      intended_purpose: purpose,
    }),
}

export const tfApi = {
  get: (systemId: string) => api.get<TechnicalFile>(`/systems/${systemId}/technical-file`),
  listRevisions: (systemId: string) =>
    api.get<TechnicalFileRevision[]>(`/systems/${systemId}/technical-file/revisions`),
  createRevision: (systemId: string, data: CreateRevisionData) =>
    api.post<TechnicalFileRevision>(`/systems/${systemId}/technical-file/revisions`, data),
  getRevision: (systemId: string, revisionId: string) =>
    api.get<TechnicalFileRevision>(
      `/systems/${systemId}/technical-file/revisions/${revisionId}`
    ),
  updateRevision: (
    systemId: string,
    revisionId: string,
    data: Partial<TechnicalFileRevision>
  ) =>
    api.put<TechnicalFileRevision>(
      `/systems/${systemId}/technical-file/revisions/${revisionId}`,
      data
    ),
}

export const sectionApi = {
  list: (systemId: string, revisionId: string) =>
    api.get<Section[]>(
      `/systems/${systemId}/technical-file/revisions/${revisionId}/sections/`
    ),
  get: (systemId: string, revisionId: string, sectionNumber: number) =>
    api.get<Section>(
      `/systems/${systemId}/technical-file/revisions/${revisionId}/sections/${sectionNumber}`
    ),
  update: (
    systemId: string,
    revisionId: string,
    sectionNumber: number,
    content: Record<string, unknown>
  ) =>
    api.put<Section>(
      `/systems/${systemId}/technical-file/revisions/${revisionId}/sections/${sectionNumber}`,
      { content }
    ),
  completeness: (systemId: string, revisionId: string) =>
    api.get<CompletenessResult>(
      `/systems/${systemId}/technical-file/revisions/${revisionId}/sections/completeness`
    ),
}

export const evidenceApi = {
  list: (revisionId: string) =>
    api.get<EvidenceAttachment[]>(`/evidence/?revision_id=${revisionId}`),
  upload: (formData: FormData) =>
    api.post<EvidenceAttachment>('/evidence/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  addUrl: (data: {
    revision_id: string
    url: string
    source?: string
    version?: string
    field_key?: string
  }) => api.post<EvidenceAttachment>('/evidence/url', data),
  delete: (id: string) => api.delete(`/evidence/${id}`),
}

export const exportApi = {
  pdf: (systemId: string, revisionId: string) =>
    api.get(
      `/systems/${systemId}/technical-file/revisions/${revisionId}/export/pdf`,
      { responseType: 'blob' }
    ),
  markdown: (systemId: string, revisionId: string) =>
    api.get<string>(
      `/systems/${systemId}/technical-file/revisions/${revisionId}/export/markdown`
    ),
}

export default api
