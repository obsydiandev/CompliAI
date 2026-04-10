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
  diffRevisions: (systemId: string, revisionId: string, otherRevisionId: string) =>
    api.get<import('@/types').RevisionDiff[]>(
      `/systems/${systemId}/technical-file/revisions/${revisionId}/diff`,
      { params: { other_revision_id: otherRevisionId } }
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

export const billingApi = {
  status: (orgId: string) =>
    api.get<import('@/types').BillingStatus>(`/billing/status/${orgId}`),
  createCheckout: (orgId: string, plan: string) =>
    api.post<{ url: string }>('/billing/checkout', { org_id: orgId, plan }),
  createPortal: (orgId: string) =>
    api.post<{ url: string }>('/billing/portal', { org_id: orgId }),
}

export const assistantApi = {
  generateDraft: (systemId: string, sectionNumber: number) =>
    api.post<import('@/types').DraftResult>(
      `/systems/${systemId}/assistant/draft/${sectionNumber}`
    ),
  streamDraftUrl: (systemId: string, sectionNumber: number) =>
    `${BASE_URL}/systems/${systemId}/assistant/stream/${sectionNumber}`,
  getSuggestions: (systemId: string, sectionNumber: number) =>
    api.post<import('@/types').SuggestionsResult>(
      `/systems/${systemId}/assistant/suggestions/${sectionNumber}`
    ),
  docDiff: (
    systemId: string,
    previousMetadata: Record<string, unknown>,
    newMetadata: Record<string, unknown>
  ) =>
    api.post<{ affected_sections: import('@/types').DocDiffItem[] }>(
      `/systems/${systemId}/assistant/doc-diff`,
      { previous_metadata: previousMetadata, new_metadata: newMetadata }
    ),
  userInstructions: (systemId: string) =>
    api.post<{ markdown: string }>(`/systems/${systemId}/assistant/user-instructions`),
  qa: (systemId: string, question: string, revisionId?: string) =>
    api.post<import('@/types').QAResult>(`/systems/${systemId}/assistant/qa`, {
      question,
      revision_id: revisionId,
    }),
  indexRevision: (systemId: string, revisionId?: string) =>
    api.post<import('@/types').IndexResult>(`/systems/${systemId}/assistant/index`, {
      revision_id: revisionId,
    }),
}

export const integrationApi = {
  list: (orgId: string) =>
    api.get<import('@/types').Integration[]>(`/organizations/${orgId}/integrations`),
  create: (
    orgId: string,
    data: { name: string; type: string; credentials?: Record<string, string>; config?: Record<string, string> },
  ) => api.post<import('@/types').Integration>(`/organizations/${orgId}/integrations`, data),
  get: (orgId: string, integrationId: string) =>
    api.get<import('@/types').Integration>(`/organizations/${orgId}/integrations/${integrationId}`),
  update: (orgId: string, integrationId: string, data: Record<string, unknown>) =>
    api.put<import('@/types').Integration>(
      `/organizations/${orgId}/integrations/${integrationId}`,
      data,
    ),
  delete: (orgId: string, integrationId: string) =>
    api.delete(`/organizations/${orgId}/integrations/${integrationId}`),
  test: (orgId: string, integrationId: string) =>
    api.post(`/organizations/${orgId}/integrations/${integrationId}/test`),
  sync: (orgId: string, integrationId: string) =>
    api.post(`/organizations/${orgId}/integrations/${integrationId}/sync`),
  listDeployments: (systemId: string) =>
    api.get<import('@/types').DeploymentEvent[]>(`/systems/${systemId}/deployments`),
  uploadTestReport: (systemId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<import('@/types').TestReportResult>(
      `/systems/${systemId}/test-reports`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
  },
}

export const policyApi = {
  listRules: (orgId: string) =>
    api.get<import('@/types').PolicyRule[]>(`/organizations/${orgId}/policies`),
  createRule: (orgId: string, data: Record<string, unknown>) =>
    api.post<import('@/types').PolicyRule>(`/organizations/${orgId}/policies`, data),
  updateRule: (orgId: string, ruleId: string, data: Record<string, unknown>) =>
    api.put<import('@/types').PolicyRule>(`/organizations/${orgId}/policies/${ruleId}`, data),
  deleteRule: (orgId: string, ruleId: string) =>
    api.delete(`/organizations/${orgId}/policies/${ruleId}`),
  seedBuiltin: (orgId: string) =>
    api.post<import('@/types').PolicyRule[]>(`/organizations/${orgId}/policies/seed-builtin`),
  health: (systemId: string) =>
    api.get<import('@/types').ComplianceHealthReport>(`/systems/${systemId}/compliance/health`),
  runChecks: (systemId: string) =>
    api.post<import('@/types').RunChecksResponse>(`/systems/${systemId}/compliance/run-checks`),
  shadowValidate: (systemId: string, newMetrics: Record<string, number>, thresholdPct = 5) =>
    api.post<import('@/types').ShadowValidationResponse>(
      `/systems/${systemId}/compliance/shadow-validate`,
      { new_metrics: newMetrics, threshold_pct: thresholdPct },
    ),
  biasAudit: (
    systemId: string,
    currentMetrics: Record<string, number>,
    previousMetrics?: Record<string, number>,
  ) =>
    api.post<import('@/types').BiasAuditResponse>(
      `/systems/${systemId}/compliance/bias-audit`,
      { current_metrics: currentMetrics, previous_metrics: previousMetrics },
    ),
  listEvents: (systemId: string, status?: string) =>
    api.get<import('@/types').ComplianceEvent[]>(
      `/systems/${systemId}/compliance/events`,
      { params: status ? { status_filter: status } : {} },
    ),
  resolveEvent: (systemId: string, eventId: string) =>
    api.put<import('@/types').ComplianceEvent>(
      `/systems/${systemId}/compliance/events/${eventId}/resolve`,
    ),
}

export const templateApi = {
  list: () => api.get<import('@/types').TemplateSummary[]>('/templates'),
  get: (templateId: string) => api.get(`/templates/${templateId}`),
  apply: (systemId: string, templateId: string, revisionId: string, overwrite = false) =>
    api.post(`/systems/${systemId}/templates/apply`, {
      template_id: templateId,
      revision_id: revisionId,
      overwrite,
    }),
  getCrosswalk: (systemId: string) =>
    api.get<import('@/types').CrosswalkEntry[]>(`/systems/${systemId}/iso42001`),
  getEvidencePackage: (systemId: string) =>
    api.post<import('@/types').EvidencePackage>(`/systems/${systemId}/iso42001/package`),
  generateAIIA: (systemId: string, useLlm = true) =>
    api.post<{ report: import('@/types').AIIAReport }>(`/systems/${systemId}/ai-ia`, {
      system_id: systemId,
      use_llm: useLlm,
    }),
}

export const ssoApi = {
  providers: () => api.get<import('@/types').SSOProvider[]>('/sso/providers'),
  authorize: (provider: string, redirectUri: string, redirectAfter = '/dashboard') =>
    api.get<{ auth_url: string; state: string }>(
      `/sso/${provider}/authorize`,
      { params: { redirect_uri: redirectUri, redirect_after: redirectAfter } },
    ),
  callback: (
    provider: string,
    body: { code: string; state: string; redirect_uri: string },
  ) => api.post<{ access_token: string; token_type: string; redirect_to: string }>(
    `/sso/${provider}/callback`,
    body,
  ),
}

export const portfolioApi = {
  downloadPdf: (orgId: string) =>
    api.get(`/organizations/${orgId}/reports/portfolio/pdf`, { responseType: 'blob' }),
  downloadCsv: (orgId: string) =>
    api.get(`/organizations/${orgId}/reports/portfolio/csv`, { responseType: 'blob' }),
}

export const adminApi = {
  metrics: () => api.get<import('@/types').FounderMetrics>('/admin/metrics'),
}

export const pmmApi = {
  get: (systemId: string) =>
    api.get<import('@/types').PMMPlan>(`/systems/${systemId}/pmm/`),
  update: (systemId: string, data: import('@/types').PMMPlanUpdate) =>
    api.put<import('@/types').PMMPlan>(`/systems/${systemId}/pmm/`, data),
  submitMetrics: (systemId: string, metrics: import('@/types').MetricEntry[]) =>
    api.post<{ recorded_entries: number; total_log_entries: number; recorded_at: string }>(
      `/systems/${systemId}/pmm/metrics`,
      { metrics },
    ),
  listMetrics: (systemId: string) =>
    api.get<import('@/types').MetricsLog>(`/systems/${systemId}/pmm/metrics`),
  summary: (systemId: string) =>
    api.get<import('@/types').PMMSummary>(`/systems/${systemId}/pmm/summary`),
}

export const llmUsageApi = {
  getOrgUsage: (orgId: string, days = 30) =>
    api.get<import('@/types').LLMUsageStats>(`/organizations/${orgId}/llm-usage`, {
      params: { days },
    }),
}

export const ruleGeneratorApi = {
  generateRule: (orgId: string, description: string, severity = 'warning') =>
    api.post<import('@/types').GeneratedRule>(
      `/organizations/${orgId}/policies/generate-rule`,
      { description, severity },
    ),
}

export const alertConfigApi = {
  get: (orgId: string) =>
    api.get<import('@/types').AlertConfig>(`/organizations/${orgId}/policies/alert-config`),
  update: (orgId: string, data: import('@/types').AlertConfig) =>
    api.put<import('@/types').AlertConfig>(
      `/organizations/${orgId}/policies/alert-config`,
      data,
    ),
}

export const apiKeyApi = {
  list: (orgId: string) =>
    api.get<import('@/types').ApiKeyRead[]>(`/organizations/${orgId}/api-keys`),
  create: (orgId: string, data: { name: string; expires_in_days?: number | null }) =>
    api.post<import('@/types').ApiKeyCreated>(`/organizations/${orgId}/api-keys`, data),
  revoke: (orgId: string, keyId: string) =>
    api.delete(`/organizations/${orgId}/api-keys/${keyId}`),
}

export const integrationHealthApi = {
  health: (orgId: string, integrationId: string) =>
    api.get<import('@/types').IntegrationHealth>(
      `/organizations/${orgId}/integrations/${integrationId}/health`,
    ),
}

export default api
