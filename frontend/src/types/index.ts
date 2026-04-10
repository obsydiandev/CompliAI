// Core API types
export interface User {
  id: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  org_id?: string;
  role: string;
  created_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: string;
  stripe_subscription_id?: string;
}

export interface AISystem {
  id: string;
  org_id: string;
  name: string;
  version: string;
  risk_level: "minimal" | "limited" | "high" | "unacceptable";
  status: "draft" | "review" | "approved" | "deployed";
  annex_iv_data?: AnnexIVData;
  created_at?: string;
  updated_at?: string;
}

// Annex IV section types
export interface GeneralInformation {
  system_name?: string;
  version?: string;
  purpose?: string;
  developer?: string;
  deployment_date?: string;
}

export interface IntendedPurpose {
  use_cases?: string[];
  target_users?: string[];
  geographic_scope?: string;
  prohibited_uses?: string;
}

export interface TechnicalSpecifications {
  model_architecture?: string;
  input_types?: string[];
  output_types?: string[];
  performance_metrics?: string;
  hardware_requirements?: string;
}

export interface TrainingData {
  data_sources?: string[];
  data_preprocessing?: string;
  data_quality_measures?: string;
  training_methodology?: string;
}

export interface TestingAndValidation {
  test_datasets?: string[];
  evaluation_metrics?: string[];
  performance_results?: string;
  known_limitations?: string;
}

export interface HumanOversight {
  oversight_mechanisms?: string;
  human_intervention_points?: string[];
  roles_responsibilities?: string;
}

export interface Cybersecurity {
  security_measures?: string;
  access_controls?: string;
  vulnerability_assessments?: string;
  incident_response?: string;
}

export interface Transparency {
  explainability_methods?: string;
  user_information?: string;
  logging_monitoring?: string;
}

export interface PostMarketMonitoring {
  monitoring_plan?: string;
  feedback_mechanisms?: string;
  update_procedures?: string;
  incident_reporting?: string;
}

export interface AnnexIVData {
  general_information?: GeneralInformation;
  intended_purpose?: IntendedPurpose;
  technical_specifications?: TechnicalSpecifications;
  training_data?: TrainingData;
  testing_and_validation?: TestingAndValidation;
  human_oversight?: HumanOversight;
  cybersecurity?: Cybersecurity;
  transparency?: Transparency;
  post_market_monitoring?: PostMarketMonitoring;
}

// Completeness
export interface SectionCompleteness {
  filled: number;
  total: number;
  pct: number;
}

export interface CompletenessResult {
  sections: Record<string, SectionCompleteness>;
  overall_pct: number;
}

// Policy engine
export interface PolicyRule {
  id: string;
  name: string;
  rule_type: string;
  conditions?: Record<string, unknown>;
  is_active: boolean;
}

export interface PolicyEvaluationResult {
  rule_id: string;
  rule_name: string;
  rule_type: string;
  passed: boolean;
  details: string;
}

// Assistant
export interface GapItem {
  section: string;
  field: string;
  priority: "high" | "medium" | "low";
  suggestion: string;
}

export interface ImpactAssessment {
  risk_level: string;
  risk_classification: string;
  affected_populations: string[];
  mitigation_measures: string[];
  fundamental_rights_impact: Record<string, string>;
  recommended_actions: string[];
  annex_iii_applicable: boolean;
  conformity_assessment_required: boolean;
}

// Auth
export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// Billing
export interface BillingSubscription {
  plan: string;
  subscription_id?: string;
  status?: string;
}

// Evidence
export interface Evidence {
  id: string;
  system_id: string;
  org_id: string;
  filename: string;
  s3_key: string;
  content_type: string;
  size: number;
  uploaded_by: string;
  created_at: string;
}

// Templates
export interface TemplateInfo {
  type: string;
  name: string;
}

// Integration
export interface DeploymentEvent {
  id: string;
  system_id: string;
  source: string;
  event_type: string;
  metadata?: Record<string, unknown>;
  created_at?: string;
}
