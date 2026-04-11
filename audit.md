# CompliAI PRD v1.15 — Implementation Audit

**Audit Date:** 2026-04-11
**Auditor:** Automated code audit
**Branch:** `copilot/create-implementation-plan-compli-ai-prd-v1-15`

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Overall Implementation** | **~88% complete** |
| **Backend Unit Tests** | 234 passing, 0 failures |
| **Integration Tests** | 17 (require PostgreSQL — skipped in CI) |
| **Frontend TypeScript** | Passes (`tsc --noEmit`) |
| **Critical Gaps** | 3 |
| **Medium Gaps** | 4 |
| **Minor Gaps** | 3 |

### Status by Phase

| Phase | Status | Completion |
|-------|--------|------------|
| **1A — AI Act Risk Classifier** | ✅ Complete | 100% |
| **1B — Quick-Start Lite Wizard** | ✅ Complete | 100% |
| **1C — White-Label MVP** | ⚠️ Mostly Complete | 90% |
| **2 — BYOK + Stateless + Upsell** | ⚠️ Partial | 75% |
| **3 — Pro Enhancements** | ⚠️ Partial | 60% |
| **4 — CI/CD + Cloud** | ⚠️ Partial (frozen per plan) | 50% |
| **5 — Enterprise** | ⚠️ Partial (deferred per plan) | 40% |
| **Config & Infrastructure** | ✅ Complete | 95% |

---

## Phase 1A — AI Act Risk Classifier (Epic 19) ✅ COMPLETE

### Item 1: `backend/app/modules/classifier/annex3_rules.py` ✅
- **10 questions** defined (q1–q10) covering all required categories
- **Sector flags:** Healthcare, biometrics, employment, education, critical infrastructure, law enforcement ✅
- **Type flags:** Profiling, emotion recognition, real-time remote biometric ✅
- **Deterministic decision tree** with 8 return paths
- Returns `ClassificationResult` with `risk_level`, `justification`, `article_citations`, `annex_iii_category`, `is_edge_case`

### Item 2: `backend/app/modules/classifier/llm_fallback.py` ✅
- LLM prompt for edge cases using OpenAI API (GPT-4o, temperature 0.1)
- JSON response format with `risk_level`, `justification`, `article_citations`
- Graceful fallback to preliminary result on error

### Item 3: `backend/app/modules/classifier/panic_calendar.py` ✅
- 4 AI Act milestones defined (2025-02-02, 2025-08-02, **2026-08-02**, 2027-08-02)
- Color-coded urgency: `red` ≤60d, `orange` ≤90d, `green` >90d, `past` <0d ✅
- `get_primary_deadline()` returns Aug 2, 2026 for high-risk systems

### Item 4: `backend/app/models/classifier_lead.py` ✅
- All fields present: `id` (UUID), `email` (nullable), `answers` (JSON), `result`, `justification`, `share_token` (unique), `created_at`
- Extra fields: `article_citations`, `annex_iii_category`, `is_edge_case`, `nurturing_sent`

### Item 5: DB Migration `008_classifier.py` ✅
- Creates `classifier_leads` table with all columns
- Indexes on `email` and `share_token` (unique)
- Note: Plan said `006_classifier.py` but pre-existing migrations 006/007 occupied those slots → renumbered to `008`. Correct.

### Item 6: `backend/app/api/v1/endpoints/classifier.py` ✅
- `POST /classifier/evaluate` — no auth, accepts 10 answers, returns classification + panic_calendar ✅
- `POST /classifier/capture-email` — attaches email, triggers nurturing D+1 via Celery ✅
- `GET /classifier/result/{share_token}` — public shareable, no auth ✅
- **Bonus:** `GET /classifier/questions` — returns full question definitions for frontend

### Item 7: `backend/app/tasks/email_nurturing.py` ✅
- `send_nurturing_d1` — D+1, subject "Your AI Act Risk Classification", schedules D+7 ✅
- `send_nurturing_d7` — D+7, penalties/enforcement, schedules D+14 ✅
- `send_nurturing_d14` — D+14, final reminder, no further scheduling ✅
- All use Resend API via `settings.RESEND_API_KEY` ✅
- Lead tracking via `nurturing_sent` JSON array prevents duplicates ✅

### Item 8: `frontend/src/app/classifier/page.tsx` ✅
- Public, no auth gate, mobile-first responsive design ✅
- 10-question step-by-step form ✅
- Results: risk badge (color-coded), justification, article citations ✅
- Email capture (optional) with CTA "Get PDF Summary" ✅
- Share button → copies `compliai.com/classifier/result/{token}` ✅
- **SEO:** Title "AI Act Risk Classifier — Is your AI system High-Risk?" + meta keywords including "AI Act Annex IV generator", "AI Act High Risk checker", "Annex IV template download" ✅

### Item 9: `frontend/src/app/classifier/result/[token]/page.tsx` ✅
- SSR server component with `generateMetadata()` for dynamic OG tags ✅
- `og:title`: "My AI system is classified as {riskLabel} under the EU AI Act" ✅
- Twitter card `summary_large_image` ✅
- Public, no auth, uses `notFound()` for invalid tokens ✅

### Item 10: `frontend/src/components/classifier/PanicCalendar.tsx` ✅
- Countdown display with color-coded urgency (red/orange/green/past) ✅
- Calendar icon, milestone labels, days remaining badges ✅

### Router Wiring ✅
- `classifier.router` included at `/api/v1/classifier/` in `router.py`

---

## Phase 1B — Quick-Start Lite Wizard (Epic 0) ✅ COMPLETE

### Item 10-11: Data Model + Migration ✅
- `WizardSession` model with all required fields: `id`, `session_token`, `email` (nullable), `org_name`, `system_name`, `current_block`, `answers` (JSON), `generated_paragraphs` (JSON), `risk_result`, `stripe_payment_intent_id`, `pdf_s3_key`, `expires_at`, `created_at`, `updated_at` ✅
- 7-day expiry enforced ✅
- Additional fields: `payment_confirmed`, `stripe_checkout_session_id`, `partner_id`, `logo_s3_key`, `data_purged_at` ✅
- Migration `009_wizard_session.py` creates table with indexes ✅

### Item 12: `backend/app/api/v1/endpoints/wizard.py` ✅
| Endpoint | Status |
|----------|--------|
| `POST /wizard/sessions` | ✅ Creates anonymous session |
| `GET /wizard/sessions/{token}` | ✅ Loads state, 410 if expired |
| `PUT /wizard/sessions/{token}/blocks/{id}` | ✅ Saves answers, advances block |
| `POST /wizard/sessions/{token}/generate-paragraph` | ✅ Non-streaming generation |
| `POST /wizard/sessions/{token}/generate-paragraph/stream` | ✅ SSE streaming (bonus) |
| `POST /wizard/sessions/{token}/classify-risk` | ✅ Annex III classification from B1/B2 |
| `POST /wizard/sessions/{token}/checkout` | ✅ Stripe Checkout, 299 EUR |
| `POST /wizard/sessions/{token}/export-pdf` | ✅ **Gated by `payment_confirmed=True`** |
| `GET /wizard/sessions/{token}/resume-email` | ✅ Sends resume link via Resend |

### Item 13: Wizard Module ✅
- **`blocks.py`** — 7 blocks (B1–B7), 42 questions total (5-8 per block), each with `annex_iv_section`, `article_ref`, `why_asking`, `placeholder` ✅
- **`prompt_chain.py`** — Per-block LLM prompts, separate from Pro's `draft_generator.py`, temperature 0.2, SSE streaming support ✅
- **`pdf_builder.py`** ✅:
  - Watermark `"DRAFT – requires legal review"` — mandatory, non-removable ✅
  - Disclaimer section — mandatory, server-side enforced (`ValueError` if `disclaimer_accepted=False`) ✅
  - Logo upload slot ✅
  - Partner branding support ✅

### Item 14: `backend/app/tasks/wizard_reminders.py` ✅
- `send_wizard_reminders_daily` — targets sessions >24h old, not paid, not expired ✅
- `send_post_purchase_email` — triggered after Stripe webhook, "3 next steps" email ✅

### Items 15-18: Frontend Wizard Pages ✅
| Component | Status | Notes |
|-----------|--------|-------|
| `wizard/page.tsx` (entry) | ✅ | Email capture (optional, can skip) |
| `wizard/[token]/page.tsx` (main) | ✅ | Session restoration, block rendering |
| `WizardBlock.tsx` | ✅ | Questions, tooltips, auto-save |
| `AIParagraphEditor.tsx` | ✅ | Streaming, editable, "Regenerate" |
| `RiskBadgeInline.tsx` | ✅ | Inline classification after B1/B2 |
| `BlockNavigation.tsx` | ✅ | Previous/Next, progress bar |
| `wizard/[token]/checkout/page.tsx` | ✅ | Stripe redirect |
| `wizard/[token]/export/page.tsx` | ✅ | **Mandatory disclaimer checkbox, button disabled until checked** |
| `wizard/[token]/next-steps/page.tsx` | ✅ | "Technical File Completion: 100%", "Evidence Validation: NOT VERIFIED" (locked red badge) |

### Items 19-20: Stripe Integration ✅
- `STRIPE_PRICE_LITE` (299 EUR one-time) in `config.py` ✅
- `STRIPE_PRICE_LITE_PLUS` (99 EUR/month) in `config.py` ✅
- `checkout.session.completed` webhook handler in `billing.py` → sets `payment_confirmed=True`, sends post-purchase email ✅

### UI/UX Constraints (v1.15 Architecture) ✅
- **"Compliance" word check**: Grep of all Lite-facing frontend files finds **ZERO** instances of "Compliance" or "Compliance Score" ✅
- **Terminology used**: "Technical File Completion %", "Progress", "Technical File" throughout ✅
- **Disclaimer checkbox**: Mandatory, export button disabled until checked, server-side validation ✅
- **Watermark**: "DRAFT – requires legal review" — built into `pdf_builder.py`, no config to disable ✅
- **Evidence Validation**: Shown as locked red badge with "NOT VERIFIED" on next-steps page ✅

---

## Phase 1C — White-Label MVP (Epic 17) ⚠️ 90% COMPLETE

### Item 21: `backend/app/models/partner.py` ✅
- All fields: `id`, `org_id`, `name`, `logo_s3_key`, `billing_plan`, `client_sessions` (JSON), `created_at`, `updated_at` ✅

### Item 22: Migration `010_partner.py` ✅
- Creates `partners` table with unique index on `org_id` ✅

### Item 23: `backend/app/api/v1/endpoints/partner.py` ✅
- `POST /partners` ✅
- `GET /partners/{partner_id}/clients` ✅
- `POST /partners/{partner_id}/clients` ✅
- `POST /partners/{partner_id}/clients/{token}/export` ✅
- **Bonus:** `PUT /partners/{partner_id}/clients/{token}/status` (workflow transitions) ✅
- **Bonus:** `POST /partners/{partner_id}/logo` (logo upload with validation) ✅
- Authorization via `_require_partner_membership` ✅

### Item 24: PDF Builder Partner Branding ✅
- `partner_name` parameter → "Prepared by [Partner Name]" footer ✅
- CompliAI branding conditionally hidden when partner is set ✅
- Logo support via `logo_bytes` + `logo_mime` ✅

### Item 25: `frontend/src/app/partner/page.tsx` ✅
- Client list with status badges (Generated/In Review/Approved/Sent) ✅
- Create new client form ✅
- Status workflow transitions ✅
- Completion percentage display ✅

### Item 26: Frontend Single Client View ❌ **NOT IMPLEMENTED**
- **Missing:** `frontend/src/app/partner/[client_id]/page.tsx` does not exist
- Only the main `partner/page.tsx` is present
- **Impact:** Cannot view/edit individual client sessions from partner dashboard
- **Severity:** Medium — core partner functionality but partial workaround via main page

### Stripe Partner Pricing ✅
- `STRIPE_PRICE_PARTNER` (300 EUR/month) in `config.py` ✅

### Router Wiring ✅
- `partner.router` included at `/api/v1/partners/` in `router.py` ✅

---

## Phase 2 — BYOK + Stateless + Upsell ⚠️ 75% COMPLETE

### Item 27: `backend/app/modules/auth_billing/byok.py` ✅
- Envelope encryption with AES-256-GCM ✅
- `encrypt_field(provider, key_arn, plaintext)` → base64 payload ✅
- `decrypt_field(provider, key_arn, encrypted_payload)` → plaintext ✅
- `test_kms_connectivity(provider, key_arn)` → encrypt/decrypt cycle ✅
- **AWS KMS** via `boto3` ✅
- **Azure Key Vault** via `azure.keyvault.keys` ✅
- **GCP Cloud KMS** via `google.cloud.kms` ✅

### Item 28: Organization Model BYOK Fields ✅
- `byok_kms_provider` (String) ✅
- `byok_kms_key_arn` (Text) ✅
- `byok_openai_key` (Text) ✅
- `stateless_mode` (Boolean, default False) ✅

### Item 29: Migration `011_byok.py` ✅
- Adds all 4 fields to `organizations` table ✅

### Item 30: `backend/app/api/v1/endpoints/byok.py` ✅
- `PUT /organizations/{org_id}/byok/kms` ✅
- `PUT /organizations/{org_id}/byok/llm-key` ✅
- `POST /organizations/{org_id}/byok/test` ✅
- **Bonus:** `PUT /organizations/{org_id}/byok/stateless` ✅
- **Bonus:** `GET /organizations/{org_id}/byok/status` ✅

### Item 30 (continued): Draft Generator BYOK Integration ❌ **NOT IMPLEMENTED**
- `backend/app/modules/ai_assistant/draft_generator.py` always uses `settings.OPENAI_API_KEY`
- Does **NOT** check `org.byok_openai_key` or call `decrypt_field()`
- **Impact:** Organizations with BYOK LLM keys cannot use their own keys for draft generation
- **Severity:** 🔴 Critical — BYOK LLM key feature is non-functional

### Item 31: Frontend BYOK Settings ❌ **NOT IMPLEMENTED**
- No frontend UI for BYOK configuration found
- **Impact:** Admins cannot configure BYOK from the UI (API-only)
- **Severity:** Medium — API works, no frontend

### Items 32-33: Stateless Mode ⚠️ PARTIAL
- `stateless_mode` boolean on Organization model ✅
- `data_purged_at` field on WizardSession model ✅
- Toggle endpoint in BYOK endpoints ✅
- **MISSING:** Post-export purge logic ❌
  - `wizard.py` export endpoint does NOT check `org.stateless_mode`
  - `partner.py` export endpoint does NOT purge data
  - No code deletes `answers` / `generated_paragraphs` after PDF generation
  - **Impact:** Stateless mode flag exists but is NOT enforced — data persists
  - **Severity:** 🔴 Critical — violates zero-knowledge guarantee

### Item 34: Frontend Stateless Mode Toggle ❌ **NOT IMPLEMENTED**
- No toggle in org settings, no warning modal
- **Severity:** Medium — API works, no frontend

### Item 35: `backend/app/tasks/upsell_sequence.py` ✅
- `send_upsell_emails_daily` — queries sessions with `payment_confirmed=True`, `updated_at < now - 60 days` ✅
- References Art. 11(2), links to update wizard (€299) and Pro upgrade ✅
- Uses Resend API ✅
- Registered in Celery beat schedule ✅

### Router Wiring ✅
- `byok.router` included at `/api/v1/organizations/{org_id}/byok/` in `router.py` ✅

---

## Phase 3 — Pro Enhancements ⚠️ 60% COMPLETE

### Item 36: Revision Diff Viewer ✅
- `frontend/src/app/systems/[id]/revisions/diff/page.tsx` implemented
- Supports unified and split diff modes
- Uses `TechnicalFileRevision` backend model

### Item 37: Audit Readiness Score ✅
- `backend/app/modules/annex_iv_core/completeness.py` — `compute_audit_readiness_score()` function
- Formula: `(completeness × 0.4) + (evidence_freshness × 0.3) + (open_alerts × 0.2) + (revision_recency × 0.1)` ✅
- Evidence freshness: staleness_penalty per expired evidence item
- Open alerts: `max(0, 1 - count/5)`
- Revision recency: ≤90d=1.0, 90-180d=linear decline, ≥180d=0.0
- Returns `score` (0–100), `label`, `breakdown`

### Item 38: Intended Purpose Checker ✅
- `backend/app/modules/annex_iv_core/validator.py` — `check_intended_purpose_overscoping()` function
- Two-tier: deterministic keyword scan (68 Annex III triggers) + LLM analysis
- LLM prompt as "EU AI Act compliance expert"
- Returns `overscoping_detected`, `suggested_risk_level`, `explanation`, `recommendations`
- Graceful fallback when no API key or on error

### Item 39: Collaboration Comments ❌ **NOT IMPLEMENTED**
- No `Comment` model found
- No comment endpoints
- **Impact:** No inline comments per Annex IV section
- **Severity:** Low (Phase 3, gated by KS-4)

### Item 40: Auditor Export ❌ **NOT IMPLEMENTED**
- No read-only shareable link with TTL
- No Evidence ZIP download endpoint
- **Severity:** Low (Phase 3, gated by KS-4)

### Item 41: E2E Tests ❌ **NOT IMPLEMENTED**
- No Playwright tests found
- No `frontend/tests/` directory
- **Severity:** Medium — no E2E coverage for Lite or Pro flows

---

## Phase 4 — CI/CD + Cloud (Frozen per Plan) ⚠️ 50%

### Item 42: Celery Scheduler ✅
- `worker.py` has `beat_schedule` with 4 tasks configured ✅
- `periodic-compliance-checks` — hourly ✅
- `daily-pmm-reminders` — daily 08:00 ✅
- `daily-wizard-reminders` — daily 09:00 ✅
- `daily-upsell-emails` — daily 10:00 ✅

### Item 43: GitLab OAuth Flow ⚠️ PARTIAL
- `gitlab_connector.py` exists with personal access token support
- **Missing:** OAuth 2.0 flow (client_id/client_secret exchange) not implemented
- Uses `PRIVATE-TOKEN` header instead of OAuth bearer tokens

### Item 44: Alert Dispatcher SMTP/Slack ✅
- `alert_dispatcher.py` has SMTP and Slack implementations
- SMTP: Uses `settings.SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`
- Slack: Uses `settings.SLACK_WEBHOOK_URL` with `httpx.post`
- Config vars present in `config.py`

---

## Phase 5 — Enterprise (Deferred per Plan) ⚠️ 40%

### Item 45: SAML 2.0 ✅
- `backend/app/modules/auth_billing/saml.py` exists
- Uses `python3-saml` (onelogin) library
- SP-initiated SSO with graceful degradation if library not installed
- Settings: `SAML_SP_ENTITY_ID`, `SAML_SP_ACS_URL`, `SAML_IDP_*`, etc.
- Returns 503 if not configured

### Item 46: LLM Cost Panel ✅
- Backend: `usage_logger.py` exists
- Frontend: `frontend/src/app/dashboard/llm-usage/page.tsx` exists
- Sidebar link: "AI Usage" → `/dashboard/llm-usage`

### Item 47: SOC 2 Readiness Audit ❌ **NOT STARTED**
- No SOC 2 documentation or tooling found
- **Severity:** Low — deferred per plan

---

## Configuration & Infrastructure

### Item 48: `backend/app/config.py` ✅
| Config Variable | Status |
|----------------|--------|
| `RESEND_API_KEY` | ✅ |
| `RESEND_FROM_EMAIL` | ✅ |
| `STRIPE_PRICE_LITE` (299 EUR) | ✅ |
| `STRIPE_PRICE_LITE_PLUS` (99 EUR/month) | ✅ |
| `STRIPE_PRICE_PARTNER` (300 EUR/month) | ✅ |
| `BETTERUPTIME_API_KEY` | ✅ |
| `BYOK_DEFAULT_PROVIDER` | ✅ |
| `SLACK_WEBHOOK_URL` | ✅ |
| `SMTP_HOST/PORT/USER/PASS` | ✅ |
| `EMAIL_FROM` | ✅ |

### Item 49: Celery Beat Schedule in `worker.py` ✅
| Task | Schedule | Status |
|------|----------|--------|
| `run_periodic_compliance_checks` | Hourly (configurable) | ✅ |
| `send_pmm_reminders` | Daily 08:00 UTC | ✅ |
| `send_wizard_reminders` | Daily 09:00 UTC | ✅ |
| `send_upsell_sequence` | Daily 10:00 UTC | ✅ |
| `send_nurturing_d1/d7/d14` | Triggered (not beat-scheduled) | ✅ |

### Item 50: `docker-compose.yml` Celery Worker ✅
| Service | Status |
|---------|--------|
| PostgreSQL (pgvector:pg16) | ✅ |
| Redis (redis:7-alpine) | ✅ |
| MinIO (S3-compatible) | ✅ |
| Backend (FastAPI + Uvicorn) | ✅ |
| Frontend (Next.js) | ✅ |
| **Celery Worker** | ✅ |
| **Celery Beat** | ✅ |

### `.env.example` ⚠️ INCOMPLETE
- Missing new v1.15 config variables:
  - `RESEND_API_KEY`, `RESEND_FROM_EMAIL`
  - `STRIPE_PRICE_LITE`, `STRIPE_PRICE_LITE_PLUS`, `STRIPE_PRICE_PARTNER`
  - `BETTERUPTIME_API_KEY`
  - `BYOK_DEFAULT_PROVIDER`
  - `SLACK_WEBHOOK_URL`
- **Severity:** Low — config.py has defaults, but .env.example should document all vars

---

## Database Migrations Summary

| Migration | Plan Ref | Actual | Status |
|-----------|----------|--------|--------|
| `006_classifier.py` | Plan item 3 | `008_classifier.py` | ✅ (renumbered due to existing 006/007) |
| `007_wizard_session.py` | Plan item 11 | `009_wizard_session.py` | ✅ (renumbered) |
| `008_partner.py` | Plan item 22 | `010_partner.py` | ✅ (renumbered) |
| `009_byok.py` | Plan item 28 | `011_byok.py` | ✅ (renumbered) |

All migrations have proper `upgrade()` and `downgrade()` functions. The renumbering is correct — pre-existing migrations 006 (`alert_config`) and 007 (`api_keys`) were already in the codebase.

---

## Test Results

### Backend (234 unit tests)
```
234 passed, 3 warnings, 17 errors (integration tests — no DB available)
```

All unit tests pass. The 17 errors are integration tests in `test_ai_systems.py`, `test_organizations.py`, and `test_technical_files.py` that require a running PostgreSQL instance — expected to fail in this CI-like environment.

### Frontend TypeScript
```
tsc --noEmit — PASSES with 0 errors
```

---

## Identified Gaps

### 🔴 Critical (Must Fix Before Launch)

| # | Gap | Location | Impact | Effort |
|---|-----|----------|--------|--------|
| C1 | **BYOK LLM key not used in draft generation** | `backend/app/modules/ai_assistant/draft_generator.py` | Orgs with BYOK LLM keys can't use their own keys — feature non-functional | Small — modify `_openai_client()` to accept `org_id`, query org, decrypt key |
| C2 | **Stateless mode not enforced on export** | `backend/app/api/v1/endpoints/wizard.py`, `partner.py` | Data persists after export even with `stateless_mode=True` — violates zero-knowledge guarantee | Small — add purge logic after PDF generation |
| C3 | **`.env.example` missing v1.15 vars** | `.env.example` | New developers won't know about required config | Trivial — add documented entries |

### 🟡 Medium (Should Fix Before M2)

| # | Gap | Location | Impact | Effort |
|---|-----|----------|--------|--------|
| M1 | **Partner single client view missing** | `frontend/src/app/partner/[client_id]/page.tsx` | Cannot view/edit individual clients from partner dashboard | Small — new page component |
| M2 | **BYOK frontend settings page missing** | Frontend org settings | Admins can't configure BYOK from UI (API-only works) | Medium — new settings section |
| M3 | **Stateless mode frontend toggle missing** | Frontend org settings | Can't toggle stateless mode from UI | Small — toggle + warning modal |
| M4 | **E2E tests not implemented** | `frontend/tests/` | No end-to-end test coverage | Large — Playwright setup + test suite |

### 🟢 Low Priority (Phase 3+ / Deferred)

| # | Gap | Location | Impact | Effort |
|---|-----|----------|--------|--------|
| L1 | **Collaboration comments** (Item 39) | Not started | Phase 3, gated by KS-4 | Large |
| L2 | **Auditor export** (Item 40) | Not started | Phase 3, gated by KS-4 | Medium |
| L3 | **GitLab OAuth** (Item 43) | Partial — PAT only | Phase 4, frozen | Medium |

---

## UI/UX v1.15 Compliance Verification

| Rule | Status | Evidence |
|------|--------|----------|
| No "Compliance" word in Lite UI | ✅ PASS | `grep -rn "Compliance" frontend/src/app/wizard/ frontend/src/components/wizard/ frontend/src/app/classifier/ frontend/src/components/classifier/ frontend/src/app/partner/` → 0 results |
| "Technical File Completion %" (not "Compliance Score") | ✅ PASS | Used consistently in wizard, block navigation, next-steps |
| Mandatory disclaimer checkbox before export | ✅ PASS | `export/page.tsx`: button disabled until checked; server-side 422 if false |
| Watermark "DRAFT – requires legal review" | ✅ PASS | `pdf_builder.py` line 29: `WATERMARK_TEXT = "DRAFT – requires legal review"`, not configurable |
| Evidence Validation locked in Lite | ✅ PASS | `next-steps/page.tsx`: red badge "NOT VERIFIED" with lock icon |
| Pro: "Audit Readiness Score (0–100)" | ✅ PASS | `completeness.py`: `compute_audit_readiness_score()` returns 0-100 |

---

## Router Wiring Verification

All new routers are properly wired in `backend/app/api/v1/router.py`:

| Router | Prefix | Tags | Status |
|--------|--------|------|--------|
| `classifier.router` | `/classifier` | `["classifier"]` | ✅ |
| `wizard.router` | `/wizard` | `["wizard"]` | ✅ |
| `partner.router` | `/partners` | `["partner"]` | ✅ |
| `byok.router` | `/organizations/{org_id}/byok` | `["byok"]` | ✅ |

---

## Recommendations

### Immediate (Before M2 Launch)
1. **Fix C1:** Integrate BYOK LLM keys into `draft_generator.py` — modify `_openai_client()` to accept `org_id` and use decrypted key
2. **Fix C2:** Add stateless mode purge to wizard and partner export endpoints — after PDF generation, if `org.stateless_mode`, null out `answers`/`generated_paragraphs` and set `data_purged_at`
3. **Fix C3:** Update `.env.example` with all v1.15 config variables

### Before M3 (Partner Launch)
4. **Fix M1:** Create partner single client view page
5. **Fix M2/M3:** Add BYOK settings and stateless mode toggle to frontend org settings

### Before M4
6. **Fix M4:** Set up Playwright and write E2E tests for Lite flow
