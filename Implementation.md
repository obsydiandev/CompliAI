# CompliAI – Status Implementacji

> **Wygenerowano:** 10 Kwietnia 2026  
> **Wersja PRD:** 1.0  
> **Status ogólny:** Fazy 0–5 zaimplementowane; Faza 6 (Skalowanie) pozostaje do realizacji.

---

## Legenda statusów

| Symbol | Znaczenie |
|--------|-----------|
| ✅ | W pełni zaimplementowane |
| 🟡 | Częściowo zaimplementowane (szczegóły w sekcji) |
| ❌ | Niezaimplementowane |
| 📋 | Zaplanowane, brak implementacji |

---

## EPIK 1: Zarządzanie systemami AI i organizacją [M1–M2]

**Cel:** użytkownik może zdefiniować organizację, dodać systemy AI i przypisać role.

### User Stories

| ID | Opis | Status | Uwagi |
|----|------|--------|-------|
| E1-US1 | Rejestracja organizacji, zaproszenie użytkowników, role (admin/ml_owner/legal/viewer) | ✅ | `app/api/v1/endpoints/auth.py`, `organizations.py`, `app/models/organization.py`. Role RBAC w `deps.py`. |
| E1-US2 | Dodawanie systemu AI, metadane, kategoria ryzyka, intended purpose | ✅ | `app/api/v1/endpoints/ai_systems.py`, `app/modules/annex_iv_core/validator.py` – walidator "intended purpose". |
| E1-US3 | Dashboard z listą systemów AI, % kompletności, data ostatniej rewizji, alerty | ✅ | Frontend: `app/dashboard/page.tsx` + `app/systems/[id]/page.tsx`. Completeness engine w `completeness.py`. |

### Brakujące elementy E1
- Zaproszenia przez email nie są w pełni zintegrowane z faktycznym wysyłaniem maili (tylko logika DB).
- Widok porównywania systemów (E7-US2) zaimplementowany w portfolio – nie jako osobna funkcja E1.

---

## EPIK 2: Pełny Plik Techniczny Annex IV (Core) [M1–M3]

**Cel:** wypełnianie wszystkich 9 sekcji Annex IV i eksport PDF.

### User Stories

| ID | Opis | Status | Uwagi |
|----|------|--------|-------|
| E2-US1 | Formularze 9 sekcji Annex IV z walidacją | ✅ | `app/modules/annex_iv_core/schemas.py` (9 sekcji), frontend w `app/systems/[id]/annex-iv/`. |
| E2-US2 | Wskaźnik kompletności per sekcja, lista braków, alerty o nieaktualnych sekcjach | ✅ | `completeness.py` – silnik kompletności. Dashboard sekcji z paskiem postępu. |
| E2-US3 | Upload dowodów (pliki + URL) z metadanymi do pól Annex IV | ✅ | `app/api/v1/endpoints/evidence.py`, S3 upload, sanityzacja nazw plików, MIME validation. |
| E2-US4 | Eksport PDF (numeracja, data, wersja, lista dowodów, hash rewizji) | ✅ | `app/modules/exports/pdf.py` (WeasyPrint), endpoint `exports.py`. Markdown export obecny. |
| E2-US5 | Rewizje pliku technicznego, historia zmian, diff między wersjami | 🟡 | Model `TechnicalFileRevision` + historia rewizji. **Brakuje:** widok diff między dwiema rewizjami w UI (backend model istnieje, frontend diff view nie zaimplementowany). |

### Brakujące elementy E2
- **T1.11 Diff viewer** – backend ma model rewizji, ale frontend nie ma dedykowanego widoku porównawczego.
- **T1.16 Testy E2E** – testy jednostkowe obecne, brak pełnych testów E2E (Playwright/Cypress).
- **T4.9 Moduł PMM** – Post-Market Monitoring plan jako oddzielna strona nie istnieje (dane są w sekcji 9 Annex IV).

---

## EPIK 3: Annex-IV-Copilot (AI Asystent Dokumentacji) [M2–M4]

**Cel:** AI generuje i utrzymuje drafty sekcji Annex IV.

### User Stories

| ID | Opis | Status | Uwagi |
|----|------|--------|-------|
| E3-US1 | Generowanie draftu sekcji 1-9 z metadanych (LLM, streaming) | ✅ | `app/modules/ai_assistant/draft_generator.py`, `prompt_templates.py`. Endpoint `/systems/{id}/assistant/draft`. |
| E3-US2 | Inline suggestions – "brakuje X w sekcji Y" | ✅ | `app/modules/ai_assistant/suggestions.py`. Endpoint `/assistant/suggestions`. |
| E3-US3 | Documentation Diff – analiza co zmienić po zmianie modelu | ✅ | `app/modules/ai_assistant/doc_diff.py`. Endpoint `/assistant/doc-diff`. |
| E3-US4 | Generowanie User Instructions (Art. 13) | ✅ | `app/modules/ai_assistant/user_instructions.py`. Endpoint `/assistant/user-instructions`. |
| E3-US5 | Q&A nad dokumentacją (RAG + semantic search) | ✅ | `app/modules/ai_assistant/rag.py` (pgvector). Endpoint `/assistant/qa`. |

### Brakujące elementy E3
- **T2.10 Evals jakości draftów** – brak formalnego zestawu ewaluacji jakości generowanych draftów (LLM-as-judge / human eval).
- **T2.8 Logowanie użycia LLM** – `usage_logger.py` istnieje, ale brak panelu zarządzania kosztami dla klientów.
- Cache embeddingów (`cache.py`) istnieje, ale brak kompleksowego rate-limiting per-plan.

---

## EPIK 4: Integracje z MLOps i repozytoriami kodu [M3–M6]

**Cel:** automatyczne zaciąganie metadanych z MLOps, repozytoriów i CI/CD.

### User Stories

| ID | Opis | Status | Uwagi |
|----|------|--------|-------|
| E4-US1 | GitHub OAuth, śledzenie wersji kodu, powiązanie commitów z TF-Revision | ✅ | `app/modules/integrations/github_connector.py`, OAuth flow, tagi/commity. |
| E4-US2 | MLflow + W&B connector, import metryk eksperymentów do sekcji walidacyjnych | ✅ | `mlflow_connector.py`, `wandb_connector.py`, `metadata_mapper.py`. Auto-mapowanie na pola Annex IV. |
| E4-US3 | Webhook CI/CD, klasyfikacja istotności zmian, auto-tworzenie TF-Revision draft | ✅ | `change_classifier.py`, `report_parser.py`, `app/models/deployment.py`. Endpoint webhooków. |
| E4-US4 | Upload raportów testów (CSV/JSON), auto-parsowanie metryk jako evidence | ✅ | `report_parser.py` – parsowanie CSV/JSON. |

### Brakujące elementy E4
- **GitLab** – `gitlab_connector.py` istnieje, ale integracja OAuth GitLab (flow) jest uproszczona.
- **T3.11 Testy integracyjne** – `test_integrations.py` jest obecny z mockami, ale brak testów z rzeczywistymi sandbox API.
- **T3.10 UI konfiguracji integracji** – frontend `app/systems/[id]/integrations/` istnieje, ale widok statusu połączenia (health check per connector) jest ograniczony.

---

## EPIK 5: Continuous Compliance i zarządzanie długiem [M5–M7]

**Cel:** platforma aktywnie wykrywa dryft i egzekwuje polityki compliance.

### User Stories

| ID | Opis | Status | Uwagi |
|----|------|--------|-------|
| E5-US1 | Dashboard "Compliance Health" – days since revision, unlinked deployments, missing evidence | ✅ | `app/modules/policy_engine/builtin_rules.py` (5 typów reguł), frontend `app/systems/[id]/compliance/page.tsx`. |
| E5-US2 | Shadow Mode Validation – porównanie staging vs TF, raport sekcji wymagających aktualizacji | ✅ | `app/modules/policy_engine/shadow_validator.py`. Endpoint `POST /systems/{id}/compliance/shadow-validate`. |
| E5-US3 | Edytor polityk tekstowych → automatyczne reguły | 🟡 | `rule_evaluator.py` + YAML/JSON reguły. **Brakuje:** edytor polityk tekstowych → LLM generujący regułę (T4.4). Scheduler (APScheduler/Celery) nie jest skonfigurowany. |
| E5-US4 | Automated Bias Audit przy każdym deployu | ✅ | `app/modules/policy_engine/bias_audit.py`. Endpoint `POST /systems/{id}/compliance/bias-audit`. |

### Brakujące elementy E5
- **T4.4 LLM → generowanie reguł z tekstu** – frontend edytor polityk nie zamienia naturalnego języka na reguły przez LLM.
- **T4.2 Scheduler** – APScheduler/Celery nie jest skonfigurowany produkcyjnie; reguły są uruchamiane on-demand, nie periodycznie.
- **T4.10 Testy E2E** – pełne E2E "deploy → audyt biasu → alert → rewizja TF" brak.
- **Alerty email/Slack** – `alert_dispatcher.py` ma szkielet, ale faktyczna wysyłka email/Slack wymaga konfiguracji SMTP/Slack webhooks w env.

---

## EPIK 6: Zarządzanie jakością i standardy (ISO 42001) [M7–M9]

**Cel:** wsparcie przygotowania do certyfikacji ISO 42001.

### User Stories

| ID | Opis | Status | Uwagi |
|----|------|--------|-------|
| E6-US1 | Biblioteka 8+ szablonów dokumentacji per typ systemu AI | ✅ | `app/modules/annex_iv_core/templates.py` (8 typów). Frontend: `components/templates/template-picker.tsx`, `app/systems/[id]/` → Templates tab. |
| E6-US2 | Crosswalk Annex IV ↔ ISO 42001, eksport "evidence package" | ✅ | `app/modules/annex_iv_core/iso42001_crosswalk.py` (20 kontroli). Endpoint `GET /systems/{id}/iso42001` + `POST .../package`. Frontend: `app/systems/[id]/iso42001/page.tsx`. |
| E6-US3 | Generowanie AI Impact Assessment (AI IA / DPIA-style), eksport PDF | ✅ | `app/modules/ai_assistant/impact_assessment.py`. Endpoint `POST /systems/{id}/ai-ia`. |

### Brakujące elementy E6
- Eksport AI IA jako samodzielny PDF (struktura jest generowana, ale dedykowany PDF layout dla IA nie jest oddzielny od głównego eksportu TF).
- Szablony dla systemów GenAI (Large Language Models) i systemów biometrycznych są uproszczone.

---

## EPIK 7: Moduł Enterprise i wielodostępowość [M9–M12]

**Cel:** obsługa organizacji enterprise z SSO i zaawansowanymi kontrolami dostępu.

### User Stories

| ID | Opis | Status | Uwagi |
|----|------|--------|-------|
| E7-US1 | SSO SAML 2.0 / OIDC (Okta, Azure AD, Google Workspace) | 🟡 | **OIDC zaimplementowane:** `app/modules/auth_billing/sso.py` – Google, Microsoft, generic OIDC. Endpoints `GET /sso/providers`, `GET /sso/{provider}/authorize`, `POST /sso/{provider}/callback`. DB migration `005_sso.py`. Frontend: przyciski SSO na logowaniu + `/auth/sso/callback`. **Brakuje: SAML 2.0** – tylko OIDC; SAML nie jest zaimplementowany. |
| E7-US2 | Panel portfolio – lista systemów + heatmapa ryzyk + alerty zbiorcze | ✅ | Frontend: `app/dashboard/portfolio/page.tsx` z risk heatmapą, KPI, zagregowanymi alertami. |
| E7-US3 | Zbiorczy raport compliance portfolio (PDF + CSV) dla zarządu/regulatora | ✅ | `app/modules/exports/portfolio_report.py`, endpoints `GET /organizations/{org_id}/reports/portfolio/pdf` i `/csv`. Przyciski eksportu w portfolio page. |

### Brakujące elementy E7
- **SAML 2.0** – PRD wymaga SAML 2.0, zaimplementowano tylko OIDC (wystarczające dla Okta/Azure AD przez OIDC, ale nie dla starszych implementacji SAML-only).
- **T5.8 Hardening bezpieczeństwa** – brak formalnego pen-testu i raportu OWASP Top 10.
- **T5.9 SLA + DPA** – dokumenty prawne (umowy, DPA) nie są częścią implementacji kodu.
- **T5.10 Program partnerski** – zadanie sprzedażowe, poza zakresem kodu.

---

## EPIK 8: Sprzedaż, onboarding i wzrost [M2–M18]

**Cel:** płynny onboarding nowych klientów i skuteczne kanały pozyskania.

### User Stories

| ID | Opis | Status | Uwagi |
|----|------|--------|-------|
| E8-US1 | Guided onboarding wizard 5 kroków, progres bar, sample data | ✅ | `app/onboarding/page.tsx` – 5 kroków: Welcome → AI System info → Risk Classification → Sample Data (3 gotowe szablony lub blank) → Done. |
| E8-US2 | Trial 14 dni bez karty kredytowej, lock + upgrade prompt | ✅ | `app/modules/auth_billing/` + Stripe Billing. Trial flow, lock po wygaśnięciu, upgrade prompt w `app/dashboard/billing/`. |
| E8-US3 | Wewnętrzny dashboard metryk Foundera (nie dla klientów) | ✅ | `app/api/v1/endpoints/admin.py` – `GET /admin/metrics` (superuser only). Frontend: `app/admin/metrics/page.tsx` z KPI kartami, auto-refresh co 60s. |

### Brakujące elementy E8
- **T1.19 Landing page + blog** – strona marketingowa poza repo; brak.
- **T1.20 Rekrutacja pilotowych klientów** – zadanie sprzedażowe, poza zakresem kodu.

---

## Harmonogram techniczny – podsumowanie statusu faz

### FAZA 0 – Problem Discovery

| # | Zadanie | Status | Uwagi |
|---|---------|--------|-------|
| T0.1 | 10 rozmów discovery z ML leadami / compliance | ❌ | Zadanie biznesowe, poza kodem |
| T0.2 | Analiza konkurencji | ❌ | Zadanie biznesowe, poza kodem |
| T0.3 | Definicja ICP + landing page (waitlist) | 🟡 | PRD istnieje; landing page brak |
| T0.4 | Wybór stacku, setup repo, CI/CD pipeline | ✅ | FastAPI + Next.js + PostgreSQL; repo skonfigurowane |

---

### FAZA 1 – Core MVP: Annex IV + Auth + Eksport

| # | Zadanie | Status | Uwagi |
|---|---------|--------|-------|
| T1.1 | Setup boilerplate SaaS (auth, billing, DB, hosting) | ✅ | JWT auth, Stripe, PostgreSQL, modele |
| T1.2 | Model danych: Org, User, AISystem, Role | ✅ | `app/models/` – pełny schemat |
| T1.3 | CRUD systemów AI + UI listy systemów | ✅ | `ai_systems.py` + `app/systems/` |
| T1.4 | Walidator "intended purpose" | ✅ | `app/modules/annex_iv_core/validator.py` |
| T1.5 | Model danych Annex IV: 9 sekcji jako schema | ✅ | `schemas.py` – wszystkie 9 sekcji |
| T1.6 | Formularze sekcji 1–3 | ✅ | Frontend `app/systems/[id]/annex-iv/` |
| T1.7 | Evidence attachment (upload + URL + metadane) | ✅ | `evidence.py` – S3, MIME check, hash |
| T1.8 | Testy jednostkowe + seed data | ✅ | `tests/test_completeness.py`, `test_validator.py` |
| T1.9 | Formularze sekcji 4–6 | ✅ | Frontend formularze sekcji 4–6 |
| T1.10 | Formularze sekcji 7–9 | ✅ | Frontend formularze sekcji 7–9 |
| T1.11 | TechnicalFileRevision: model + UI historii + diff | 🟡 | Model backend ✅; UI historii ✅; **diff view ❌** |
| T1.12 | Dashboard completeness | ✅ | `completeness.py` + dashboard UI |
| T1.13 | Eksport PDF (WeasyPrint, layout, podpis) | ✅ | `app/modules/exports/pdf.py` |
| T1.14 | Eksport Markdown | ✅ | Endpoint eksportu MD |
| T1.15 | Stripe Billing: plany Starter/Pro/Trial | ✅ | `billing.py` + Stripe webhooks |
| T1.16 | E2E testy flow | ❌ | Brak testów E2E (Playwright/Cypress) |
| T1.17 | Onboarding wizard | ✅ | `app/onboarding/page.tsx` – 5 kroków |
| T1.18 | Trial 14 dni + lock/upgrade | ✅ | Trial flow w billing module |
| T1.19 | Landing page + blog post | ❌ | Brak – zadanie marketingowe |
| T1.20 | Rekrutacja pilotowych klientów | ❌ | Brak – zadanie sprzedażowe |
| T1.21 | Bug fixes z pilotów | 🟡 | Ongoing |

---

### FAZA 2 – Annex-IV-Copilot

| # | Zadanie | Status | Uwagi |
|---|---------|--------|-------|
| T2.1 | Architektura ai_assistant: prompt templates, streaming | ✅ | `prompt_templates.py`, streaming w draft_generator |
| T2.2 | Generowanie draftu sekcji 1-3 (LLM) | ✅ | `draft_generator.py` |
| T2.3 | Generowanie draftu sekcji 4-9 | ✅ | `draft_generator.py` – pełne pokrycie |
| T2.4 | Inline suggestions | ✅ | `suggestions.py` |
| T2.5 | Documentation Diff po zmianie modelu | ✅ | `doc_diff.py` |
| T2.6 | Generowanie User Instructions (Art. 13) | ✅ | `user_instructions.py` |
| T2.7 | Q&A nad dokumentacją (RAG + pgvector) | ✅ | `rag.py` |
| T2.8 | Logowanie użycia LLM (tokeny, koszty) | 🟡 | `usage_logger.py` istnieje; **brak panelu kosztów dla klientów** |
| T2.9 | Cache embeddingów, rate limiting, fallback | 🟡 | `cache.py` obecny; rate limiting per plan niepełne |
| T2.10 | Testy jakości draftów (evals) | ❌ | Brak formalnego eval zestawu |

---

### FAZA 3 – Integracje MLOps i Git

| # | Zadanie | Status | Uwagi |
|---|---------|--------|-------|
| T3.1 | GitHub OAuth + repo, commity, tagi | ✅ | `github_connector.py` |
| T3.2 | GitLab integration | 🟡 | `gitlab_connector.py` istnieje; **OAuth flow uproszczony** |
| T3.3 | MLflow connector | ✅ | `mlflow_connector.py` |
| T3.4 | W&B connector | ✅ | `wandb_connector.py` |
| T3.5 | Mapowanie metadanych MLOps → Annex IV | ✅ | `metadata_mapper.py` |
| T3.6 | Webhook endpoint CI/CD | ✅ | `integrations.py` – webhook endpoint |
| T3.7 | Klasyfikacja istotności zmian | ✅ | `change_classifier.py` |
| T3.8 | Auto-tworzenie TF-Revision draft przy deploy | ✅ | `app/models/deployment.py` + logika |
| T3.9 | Upload + parsowanie raportów testów | ✅ | `report_parser.py` |
| T3.10 | UI konfiguracji integracji | 🟡 | Frontend `app/systems/[id]/integrations/` istnieje; **health check per connector niepełny** |
| T3.11 | Testy integracyjne (mock API) | ✅ | `test_integrations.py` z mockami |

---

### FAZA 4 – Continuous Compliance + PMM

| # | Zadanie | Status | Uwagi |
|---|---------|--------|-------|
| T4.1 | Model danych: PolicyRule + Alert + ComplianceEvent | ✅ | `004_policy_engine.py`, `app/models/policy.py` |
| T4.2 | Scheduler periodycznych checków | ❌ | Brak APScheduler/Celery – tylko on-demand |
| T4.3 | Builtin reguły (X dni bez rewizji, missing PMM plan) | ✅ | `builtin_rules.py` – 5 typów reguł |
| T4.4 | Edytor polityk tekstowych → LLM → reguły | ❌ | Brak konwersji tekst → YAML reguły przez LLM |
| T4.5 | Dashboard "Compliance Health" | ✅ | `app/systems/[id]/compliance/page.tsx` |
| T4.6 | Shadow Mode Validation | ✅ | `shadow_validator.py` |
| T4.7 | Automated Bias Audit | ✅ | `bias_audit.py` |
| T4.8 | Alerty email + webhook (Slack/Teams) | 🟡 | `alert_dispatcher.py` szkielet ✅; **SMTP/Slack webhook wymaga konfiguracji env** |
| T4.9 | Moduł PMM: plan + metryki + raporty kwartalne | 🟡 | Dane PMM w sekcji 9 Annex IV; **brak dedykowanego modułu PMM** |
| T4.10 | Testy E2E Fazy 4 | ❌ | Brak |

---

### FAZA 5 – Enterprise: SSO, portfolio, raporty zbiorcze

| # | Zadanie | Status | Uwagi |
|---|---------|--------|-------|
| T5.1 | SSO: SAML 2.0 + OIDC | 🟡 | **OIDC ✅** (Google, Microsoft, Okta); **SAML 2.0 ❌** |
| T5.2 | Biblioteka szablonów (8+ typów) | ✅ | `templates.py` – 8 typów; frontend template picker |
| T5.3 | Crosswalk Annex IV ↔ ISO 42001 | ✅ | `iso42001_crosswalk.py` – 20 kontroli |
| T5.4 | Generowanie AI Impact Assessment | ✅ | `impact_assessment.py` |
| T5.5 | Dashboard portfolio: lista + heatmapa ryzyk | ✅ | `app/dashboard/portfolio/page.tsx` |
| T5.6 | Raport zbiorczy compliance (PDF/CSV) | ✅ | `portfolio_report.py` – PDF landscape A4 + CSV |
| T5.7 | Wewnętrzny dashboard metryk Foundera | ✅ | `admin.py` + `app/admin/metrics/page.tsx` |
| T5.8 | Hardening bezpieczeństwa (pen test, OWASP) | ❌ | Brak formalnego audytu |
| T5.9 | SLA + DPA dla enterprise | ❌ | Dokumenty prawne – poza kodem |
| T5.10 | Program partnerski | ❌ | Zadanie sprzedażowe – poza kodem |

---

### FAZA 6 – Skalowanie i ekosystem (Miesiące 12–18)

| # | Zadanie | Status | Uwagi |
|---|---------|--------|-------|
| T6.1 | Connector SDK open source dla partnerów MLOps | ❌ | Nie rozpoczęte |
| T6.2 | Integracja SageMaker + Azure ML | ❌ | Nie rozpoczęte |
| T6.3 | Regulatory mapping: NIST AI RMF + Colorado AI Act | ❌ | Nie rozpoczęte |
| T6.4 | Public API v1 (dla integratorów) | ❌ | Wewnętrzne API istnieje; brak publicznej dokumentacji/wersjonowania |
| T6.5 | Listing w AWS / Azure Marketplace | ❌ | Zadanie biznesowe |
| T6.6 | Decyzja bootstrap vs. seed funding | ❌ | Decyzja biznesowa |

---

## Podsumowanie ogólne

### Statystyki per Epik

| Epik | User Stories | ✅ Kompletne | 🟡 Częściowe | ❌ Brakujące |
|------|-------------|------------|-------------|------------|
| E1 – Zarządzanie systemami | 3 | 3 | 0 | 0 |
| E2 – Plik Techniczny (Core) | 5 | 4 | 1 | 0 |
| E3 – AI Copilot | 5 | 5 | 0 | 0 |
| E4 – Integracje MLOps | 4 | 4 | 0 | 0 |
| E5 – Continuous Compliance | 4 | 3 | 1 | 0 |
| E6 – ISO 42001 / Jakość | 3 | 3 | 0 | 0 |
| E7 – Enterprise / Multi-tenancy | 3 | 2 | 1 | 0 |
| E8 – Sprzedaż / Onboarding | 3 | 3 | 0 | 0 |

### Statystyki per Faza

| Faza | Zadań | ✅ | 🟡 | ❌ |
|------|-------|---|---|---|
| F0 – Discovery | 4 | 1 | 1 | 2 |
| F1 – Core MVP | 21 | 17 | 2 | 2 |
| F2 – AI Copilot | 10 | 7 | 2 | 1 |
| F3 – Integracje | 11 | 9 | 2 | 0 |
| F4 – Compliance | 10 | 6 | 2 | 2 |
| F5 – Enterprise | 10 | 7 | 1 | 2 |
| F6 – Skalowanie | 6 | 0 | 0 | 6 |
| **ŁĄCZNIE** | **72** | **47 (65%)** | **10 (14%)** | **15 (21%)** |

---

## Krytyczne braki do zamknięcia przed launch

Poniższe elementy są **niezbędne lub istotne** dla profesjonalnego produktu SaaS:

### Priorytet 1 – Produkt (blokujące)
1. **T4.2 – Scheduler** – bez APScheduler/Celery reguły compliance nie uruchamiają się automatycznie; produkt nie spełnia obietnicy "continuous compliance".
2. **T1.16 / T4.10 – Testy E2E** – brak automatycznych testów end-to-end całego flow (UI → API → DB → eksport).
3. **T4.8 – Faktyczna wysyłka alertów** – dispatcher ma kod, ale wymaga konfiguracji SMTP i Slack webhook w środowisku produkcyjnym.

### Priorytet 2 – Enterprise (ważne)
4. **T5.1 – SAML 2.0** – część enterprise klientów (banki, ubezpieczyciele) używa SAML-only IdP. OIDC pokrywa ~80% przypadków.
5. **T5.8 – Hardening bezpieczeństwa** – audyt OWASP Top 10, pen-test, review uprawnień S3.
6. **T1.11 – Diff viewer rewizji** – kluczowa funkcja traceability; model backend istnieje, brakuje UI.

### Priorytet 3 – Wzrost (pożądane)
7. **T2.10 – Evals jakości AI** – bez systemu ewaluacji nie można kontrolować regresji jakości draftów.
8. **T4.4 – LLM → reguły z tekstu** – różnicujący feature; compliance officer pisze regułę po polsku, system generuje YAML.
9. **T1.19 – Landing page** – bez strony marketingowej brak kanału akwizycji.

---

## Stan testów

| Plik testów | Liczba testów | Status |
|-------------|--------------|--------|
| `test_completeness.py` | ~20 | ✅ Pass |
| `test_validator.py` | ~15 | ✅ Pass |
| `test_billing.py` | ~18 | ✅ Pass |
| `test_assistant.py` | ~22 | ✅ Pass |
| `test_integration.py` | ~12 | ✅ Pass |
| `test_integrations.py` | ~14 | ✅ Pass |
| `test_policy_engine.py` | ~30 | ✅ Pass |
| `test_templates.py` | ~25 | ✅ Pass |
| `test_sso.py` | 18 | ✅ Pass |
| `test_ai_systems.py` | ~8 | ✅ Pass |
| `test_organizations.py` | ~8 | ✅ Pass |
| `test_technical_files.py` | ~8 | ✅ Pass |
| **ŁĄCZNIE** | **~181** | ✅ **Wszystkie przechodzą** |
| Frontend TypeScript check | n/a | ✅ 0 błędów |
| Testy E2E (Playwright) | 0 | ❌ Brak |

---

*Dokument wygenerowany na podstawie analizy kodu w repo `obsydiandev/CompliAI` — branch `copilot/explore-codebase-analyze-compliai-prd`.*
