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

// ── Billing ───────────────────────────────────────────────────────────────────

export interface BillingStatus {
  org_id: string
  plan: OrgPlan
  stripe_subscription_status: string | null
  has_active_subscription: boolean
  trial_active: boolean
  trial_ends_at: string | null
  trial_days_remaining: number | null
  has_billing_access: boolean
}

// ── AI Assistant ──────────────────────────────────────────────────────────────

export interface DraftResult {
  section_number: number
  draft: Record<string, unknown>
}

export interface SuggestionsResult {
  section_number: number
  missing_fields: string[]
  suggestions: Record<string, string>
}

export interface DocDiffItem {
  section_number: number
  section_name: string
  reason: string
  draft_changes: string
}

export interface QAResult {
  answer: string
  citations: Array<{
    section_number: number
    section_name: string
    excerpt: string
  }>
}

export interface IndexResult {
  indexed_sections: number
  revision_id: string
}

// ── Integrations ──────────────────────────────────────────────────────────────

export type IntegrationType = 'github' | 'gitlab' | 'mlflow' | 'wandb' | 'webhook' | 'ci_cd'
export type IntegrationStatus = 'connected' | 'disconnected' | 'error'

export interface Integration {
  id: string
  org_id: string
  name: string
  type: IntegrationType
  config: Record<string, unknown> | null
  status: IntegrationStatus
  last_sync_at: string | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface DeploymentEvent {
  id: string
  ai_system_id: string
  integration_id: string | null
  source: string
  event_type: string
  version: string | null
  commit_sha: string | null
  model_version: string | null
  is_significant: boolean
  significance_reason: string | null
  tf_revision_id: string | null
  triggered_at: string
}

export interface WebhookResult {
  event_id: string
  is_significant: boolean
  significance_reason: string
  revision_created: { revision_id: string; version: string } | null
}

export interface TestReportResult {
  filename: string
  report: {
    format: string
    total: number
    passed: number
    failed: number
    skipped: number
    pass_rate: number | null
    metrics: Record<string, unknown>
    raw_summary: string
  }
  annex_iv_section4_suggestion: Record<string, string>
}

// ── Policy Engine (Epic 5) ────────────────────────────────────────────────────

export type PolicySeverity2 = 'info' | 'warning' | 'blocking'
export type PolicyRuleType = 'builtin' | 'custom'
export type ComplianceEventStatus = 'open' | 'resolved' | 'snoozed'

export interface PolicyRule {
  id: string
  org_id: string
  ai_system_id: string | null
  name: string
  description: string | null
  rule_type: PolicyRuleType
  condition: Record<string, unknown>
  severity: PolicySeverity2
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ComplianceEvent {
  id: string
  rule_id: string
  ai_system_id: string
  status: ComplianceEventStatus
  details: Record<string, unknown> | null
  triggered_at: string
  resolved_at: string | null
}

export interface SectionDebt {
  section_number: number
  section_name: string
  completeness: number
  missing_fields: string[]
  days_since_update: number | null
}

export interface ComplianceHealthReport {
  ai_system_id: string
  system_name: string
  days_since_last_revision: number | null
  overall_completeness: number
  open_violations: number
  unlinked_deployments: number
  missing_evidence_count: number
  section_debt: SectionDebt[]
  open_events: ComplianceEvent[]
}

export interface RunChecksResponse {
  evaluated: number
  violations: number
  events_created: number
  results: Array<{
    rule_id: string
    rule_name: string
    violated: boolean
    detail: string
    event_id?: string
  }>
}

export interface ShadowValidationResponse {
  ok: boolean
  summary: string
  sections_requiring_update: number[]
  details: Array<Record<string, unknown>>
}

export interface BiasAuditResponse {
  ok: boolean
  summary: string
  metrics: Array<{
    metric: string
    previous: number | null
    current: number
    delta: number | null
    status: string
    message: string
  }>
  section5_evidence: Record<string, unknown>
}

// ── Templates & ISO 42001 (Epic 6) ───────────────────────────────────────────

export interface TemplateSummary {
  id: string
  name: string
  description: string
  system_type: string
  tags: string[]
  sections_count: number
}

export interface CrosswalkEntry {
  iso_clause: string
  iso_title: string
  annex_iv_sections: number[]
  coverage: 'full' | 'partial' | 'supplementary'
  notes: string
}

export interface EvidencePackage {
  total_controls: number
  fully_covered: number
  partially_covered: number
  not_covered: number
  covered_clauses: string[]
  partial_clauses: string[]
  not_covered_clauses: string[]
  coverage_pct: number
}

export interface AIIAReport {
  title: string
  system_name: string
  risk_category: string
  annex_iii_applicable: boolean
  sections: Record<string, Record<string, unknown>>
}

// ── SSO (Epic 7) ───────────────────────────────────────────────────────────

export interface SSOProvider {
  provider: string
  label: string
  enabled: boolean
}

// ── Admin / Founder Metrics (Epic 8) ──────────────────────────────────────

export interface PlanBreakdown {
  starter: number
  pro: number
  enterprise: number
}

export interface OrgMetrics {
  total: number
  active_trials: number
  paid: number
  plan_breakdown: PlanBreakdown
}

export interface SystemMetrics {
  total: number
  high_risk: number
  limited_risk: number
  minimal_risk: number
  avg_completeness_pct: number
}

export interface ComplianceMetricsAdmin {
  total_open_violations: number
  systems_at_risk: number
}

export interface GrowthMetrics {
  new_orgs_last_30d: number
  new_systems_last_30d: number
}

export interface FounderMetrics {
  generated_at: string
  orgs: OrgMetrics
  systems: SystemMetrics
  compliance: ComplianceMetricsAdmin
  growth: GrowthMetrics
}

// ── Revision Diff (T1.11) ─────────────────────────────────────────────────

export interface RevisionDiff {
  section_number: number
  changed_fields: string[]
  old_values: Record<string, unknown>
  new_values: Record<string, unknown>
}

// ── PMM Module (T4.9) ─────────────────────────────────────────────────────

export interface PMMPlan {
  system_id: string
  system_name: string
  content: Record<string, unknown>
  completeness: number
  missing_required_fields: string[]
  last_updated_at: string | null
  all_fields: string[]
}

export interface PMMPlanUpdate {
  pmm_plan?: string
  monitoring_metrics?: string[]
  data_collection_methods?: string
  reporting_frequency?: string
  incident_reporting_procedure?: string
  feedback_mechanisms?: string
  monitoring_sources?: string[]
  review_schedule?: string
}

export interface MetricEntry {
  metric_name: string
  value: number
  unit?: string
  notes?: string
  recorded_at?: string
}

export interface MetricLogEntry {
  recorded_at: string
  submitted_by: string
  metrics: Array<{ metric_name: string; value: number; unit?: string; notes?: string }>
}

export interface MetricsLog {
  system_id: string
  total_entries: number
  entries: MetricLogEntry[]
}

export interface PMMSummary {
  completeness: number
  missing_fields: string[]
  has_plan: boolean
  has_metrics: boolean
  has_incident_procedure: boolean
  last_section_updated_at: string | null
}

// ── LLM Usage (T2.8) ─────────────────────────────────────────────────────

export interface LLMUsageSummary {
  total_calls: number
  successful_calls: number
  failed_calls: number
  total_prompt_tokens: number
  total_completion_tokens: number
  total_tokens: number
  total_cost_usd: number
}

export interface LLMFeatureStat {
  calls: number
  tokens: number
  cost_usd: number
}

export interface LLMUsageStats {
  org_id: string
  period_days: number
  period_start: string
  period_end: string
  summary: LLMUsageSummary
  by_feature: Record<string, LLMFeatureStat>
  by_model: Record<string, LLMFeatureStat>
}

// ── Rule Generator (T4.4) ─────────────────────────────────────────────────

export interface GeneratedRule {
  suggested_name: string
  condition: Record<string, unknown>
  description: string
}
