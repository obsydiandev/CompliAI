import axios from "axios";
import type {
  AISystem,
  AnnexIVData,
  BillingSubscription,
  CompletenessResult,
  DeploymentEvent,
  Evidence,
  GapItem,
  ImpactAssessment,
  Organization,
  PolicyEvaluationResult,
  PolicyRule,
  TemplateInfo,
  TokenResponse,
  User,
} from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

const api = axios.create({ baseURL: BASE_URL });

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Auth
export const authApi = {
  login: (email: string, password: string) =>
    api.post<TokenResponse>("/auth/login", new URLSearchParams({ username: email, password }), {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    }),
  register: (email: string, password: string, full_name?: string) =>
    api.post<TokenResponse>("/auth/register", { email, password, full_name }),
};

// Organizations
export const orgApi = {
  create: (name: string) => api.post<Organization>("/organizations", { name }),
  get: (orgId: string) => api.get<Organization>(`/organizations/${orgId}`),
  update: (orgId: string, name: string) => api.patch<Organization>(`/organizations/${orgId}`, { name }),
};

// Systems
export const systemApi = {
  list: (orgId: string) => api.get<AISystem[]>(`/organizations/${orgId}/systems`),
  create: (orgId: string, data: Partial<AISystem>) =>
    api.post<AISystem>(`/organizations/${orgId}/systems`, data),
  get: (orgId: string, systemId: string) =>
    api.get<AISystem>(`/organizations/${orgId}/systems/${systemId}`),
  update: (orgId: string, systemId: string, data: Partial<AISystem>) =>
    api.patch<AISystem>(`/organizations/${orgId}/systems/${systemId}`, data),
  delete: (orgId: string, systemId: string) =>
    api.delete(`/organizations/${orgId}/systems/${systemId}`),
  completeness: (orgId: string, systemId: string) =>
    api.get<CompletenessResult>(`/organizations/${orgId}/systems/${systemId}/completeness`),
};

// Evidence
export const evidenceApi = {
  upload: (orgId: string, systemId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post<Evidence>(`/organizations/${orgId}/systems/${systemId}/evidence`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  list: (orgId: string, systemId: string) =>
    api.get<Evidence[]>(`/organizations/${orgId}/systems/${systemId}/evidence`),
};

// AI Assistant
export const assistantApi = {
  suggest: (orgId: string, systemId: string, section: string) =>
    api.post<{ suggestion: string }>(`/organizations/${orgId}/systems/${systemId}/assistant/suggest`, {
      section,
    }),
  gaps: (orgId: string, systemId: string) =>
    api.post<{ gaps: GapItem[] }>(`/organizations/${orgId}/systems/${systemId}/assistant/gaps`, {}),
  review: (orgId: string, systemId: string) =>
    api.post<Record<string, unknown>>(`/organizations/${orgId}/systems/${systemId}/assistant/review`, {}),
  impact: (orgId: string, systemId: string) =>
    api.post<ImpactAssessment>(`/organizations/${orgId}/systems/${systemId}/assistant/impact`, {}),
};

// Policy
export const policyApi = {
  listRules: (orgId: string) =>
    api.get<PolicyRule[]>(`/organizations/${orgId}/policy/rules`),
  createRule: (orgId: string, data: Partial<PolicyRule>) =>
    api.post<PolicyRule>(`/organizations/${orgId}/policy/rules`, data),
  deleteRule: (orgId: string, ruleId: string) =>
    api.delete(`/organizations/${orgId}/policy/rules/${ruleId}`),
  evaluate: (orgId: string, systemId: string) =>
    api.post<{ results: PolicyEvaluationResult[] }>(
      `/organizations/${orgId}/systems/${systemId}/policy/evaluate`
    ),
};

// Templates
export const templateApi = {
  list: () => api.get<{ templates: TemplateInfo[] }>("/templates"),
  get: (type: string) => api.get<{ type: string; data: AnnexIVData }>(`/templates/${type}`),
  apply: (orgId: string, systemId: string, template_type: string) =>
    api.post(`/organizations/${orgId}/systems/${systemId}/apply-template`, { template_type }),
};

// Portfolio
export const portfolioApi = {
  pdf: (orgId: string) =>
    api.get(`/organizations/${orgId}/reports/portfolio/pdf`, { responseType: "blob" }),
  csv: (orgId: string) =>
    api.get(`/organizations/${orgId}/reports/portfolio/csv`, { responseType: "blob" }),
};

// Billing
export const billingApi = {
  checkout: (orgId: string, plan: string) =>
    api.post<{ subscription_id: string; client_secret?: string }>("/billing/checkout", {
      org_id: orgId,
      plan,
    }),
  subscription: () => api.get<BillingSubscription>("/billing/subscription"),
};

// SSO
export const ssoApi = {
  providers: () => api.get<{ providers: Array<{ id: string; name: string }> }>("/sso/providers"),
  authorize: (provider: string) =>
    api.get<{ authorization_url: string }>(`/sso/${provider}/authorize`),
};

export default api;
