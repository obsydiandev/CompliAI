export type UserRole = 'admin' | 'ml_owner' | 'legal' | 'viewer'
export type OrgPlan = 'starter' | 'pro' | 'enterprise'
export type AISystemCategory = 'high_risk' | 'limited_risk' | 'minimal_risk'
export type AISystemStatus = 'active' | 'inactive' | 'archived'
export type RevisionStatus = 'draft' | 'approved' | 'archived'
export type EvidenceType = 'file' | 'url' | 'report'
export type PolicySeverity = 'info' | 'warning' | 'blocking'

export interface User {
  id: string
  email: string
  full_name: string
  is_active: boolean
  created_at: string
}

export interface Organization {
  id: string
  name: string
  slug: string
  plan: OrgPlan
  trial_ends_at: string | null
  created_at: string
  member_count?: number
}

export interface Membership {
  user_id: string
  email: string
  full_name: string
  role: UserRole
  joined_at: string
}

export interface AISystem {
  id: string
  org_id: string
  name: string
  description: string | null
  intended_purpose: string | null
  category: AISystemCategory
  annex_iii_classification: boolean
  status: AISystemStatus
  created_by: string
  created_at: string
  updated_at: string
  completeness_score?: number | null
  last_revision_at?: string | null
}

export interface TechnicalFile {
  id: string
  ai_system_id: string
  current_revision_id: string | null
  created_at: string
  updated_at: string
}

export interface TechnicalFileRevision {
  id: string
  tf_id: string
  version: string
  author_id: string | null
  linked_commit_sha: string | null
  linked_model_version: string | null
  status: RevisionStatus
  change_summary: string | null
  created_at: string
}

export interface Section {
  id: string
  revision_id: string
  section_number: number
  content: Record<string, unknown>
  completeness_score: number
  last_updated_at: string
}

export interface EvidenceAttachment {
  id: string
  revision_id: string | null
  section_id: string | null
  field_key: string | null
  type: EvidenceType
  filename: string | null
  url: string | null
  source: string | null
  version: string | null
  file_hash: string | null
  mime_type: string | null
  size_bytes: number | null
  uploaded_at: string
}

export interface CompletenessResult {
  overall: number
  sections: Record<string, number>
  missing_by_section: Record<string, string[]>
}

export interface Token {
  access_token: string
  token_type: string
}

export interface IntendedPurposeResult {
  is_high_risk: boolean
  triggers: string[]
  warnings: string[]
}
