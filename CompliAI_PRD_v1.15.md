# CompliAI – Product Requirements Document
**Wersja:** 1.15 (Combo) | **Data:** Kwiecień 2026 | **Status:** Obowiązujący

**Ten dokument zastępuje:** v1.0, v1.1, v1.2 (wszystkie poprzednie wersje są archiwalne).

---

## Historia zmian

| Wersja | Co wniosła |
|--------|-----------|
| v1.0 | Epiki 1–8: Core Annex IV, Auth, CI/CD, Copilot, ISO 42001, Enterprise, Sprzedaż |
| v1.1 | Epiki 9–16: Cockpit, Collaboration, Evidence, Auditor, Proactive, Trust |
| v1.2 | Epiki 0+17–19: Lite Path, White-Label, BYOK/Privacy, Classifier; GTM, Kill Switch, ICP, scoring |
| **v1.15** | Korekta horyzontu czasowego: 4 miesiące do sierpnia 2026; freeze Epiki 4+5 do M9; sierpień jako strategiczny deadline; post-August upsell plan; messaging „X dni do AI Act" |

---

## CZĘŚĆ I — ORIENTACJA STRATEGICZNA

### 1.1 Okno czasowe: 4 miesiące, jeden deadline

```
DZIŚ                   M1           M2           M3      DEADLINE
Kwiecień 2026 ─────── Maj ──────── Czerwiec ── Lipiec ── 1 Sierpień 2026
     │                 │            │            │              │
  60% silnika       Launch      Pierwsi       Szczyt        AI Act
  gotowe            Lite        klienci       sprzedaży     High-Risk
                    + Classifier beta + fix    + kancelarie  enforcement
```

**1 sierpień 2026** = termin stosowania wymogów dla systemów High-Risk
(Annex III AI Act, 24 miesiące od wejścia w życie 1.08.2024).
Firmy bez Annex IV w tym dniu mają problem prawny.

**Ważna korekta komunikacyjna:**
Sierpień to deadline rejestracji i obowiązku posiadania dokumentacji —
nie data pierwszych kar (systemy nadzoru w PL/DE/FR nie są jeszcze w pełni
operacyjne). Twój messaging: „dokumentacja gotowa gdy organ się pojawi",
NIE „unikniesz kary od 1 sierpnia". To jest uczciwe i nie naraża Cię na
odpowiedzialność za fałszywe poczucie bezpieczeństwa.

### 1.2 Dwa tryby, jeden silnik

```
                    ┌─────────────────────────────────────┐
                    │            CORE ENGINE              │
                    │  Annex IV schema · LLM prompts      │
                    │  Legal rules · Evidence model       │
                    └───────────────┬─────────────────────┘
                                    │
              ┌─────────────────────┴──────────────────────┐
              │                                            │
   ┌──────────▼──────────────┐             ┌──────────────▼───────────────┐
   │  PATH A: LITE           │             │  PATH B: PRO                 │
   │  "Quick Wizard"         │             │  "Continuous Compliance"     │
   │  PRIORYTET: M1–M3 BUILD │             │  PRIORYTET: M9+ (post-Aug)   │
   │  M4–M8: SPRZEDAŻ        │             │  ZAMROŻONY do Września 2026  │
   │                         │             │                              │
   │  • Kreator 30–50 Q      │             │  • Pełne 9 sekcji Annex IV  │
   │  • AI drafts            │             │  • CI/CD integracje          │
   │  • Eksport PDF          │  ─upsell──► │  • Cloud adapters            │
   │  • Jednorazowy token    │             │  • Evidence-First            │
   │                         │             │  • SaaS subskrypcja          │
   │  Wskaźnik:              │             │  Wskaźnik:                   │
   │  "Technical File        │             │  "Audit Readiness Score"     │
   │   Completion %"         │             │  (0–100, evidence-backed)    │
   └─────────────────────────┘             └──────────────────────────────┘
   KLIENT teraz: CEO, Founder,             KLIENT po VIII: ML Lead, CTO,
   Legal, Agencja AI,                      Compliance Officer (ten sam,
   Zdesperowana firma                      który kupił Lite w lipcu)
```

### 1.3 Zasada nadrzędna: LLM jako tłumacz, nie decydent

> **Core Engine generuje dokument wyłącznie na bazie sztywnej schema Annex IV**
> (9 sekcji, zdefiniowane pola, obowiązkowe vs. opcjonalne).
> LLM przekształca input użytkownika w paragraf urzędowo-techniczny.
> LLM nigdy nie decyduje CO umieścić — tylko JAK to sformułować.
> Każde pole ma: typ, wymagalność, źródło (manual/auto), walidację.

Konsekwencja: nawet kiepskie dane → poprawna *struktura* Annex IV.
Dlatego disclaimer jest obowiązkowy architektonicznie, nie opcjonalny.

### 1.4 Zasada scorecard: „fotografia vs. film"

| | LITE | PRO |
|-|------|-----|
| Nazwa | Technical File Completion % | Audit Readiness Score (0–100) |
| Mierzy | Czy pola są wypełnione | Czy pola są wypełnione I poparte dowodami |
| Logika | Binarna: jest tekst = +% | Ważona: completion × evidence freshness × policy |
| Przekaz | „Masz gotowy plik do wydruku" | „Jesteś gotowy na kontrolę" |
| Metafora | Fotografia | Film |

**ZAKAZ:** słowo „Compliance" nigdy nie pada w UI/copy Lite.
Tylko: „Completion", „Progress", „Technical File".

**Mechanika upsell przez kontrast** (po 100% w Lite):
- ✅ `Technical File Completion: 100%`
- 🔴 `Evidence Validation: NOT VERIFIED` (locked)
- Komunikat: „Twoja dokumentacja jest kompletna strukturalnie,
  ale nie posiada automatycznego powiązania z dowodami technicznymi.
  W razie kontroli musisz ręcznie udowodnić prawdziwość każdego zapisu."

### 1.5 Segmentacja i ICP

| Segment | Profil | Motywacja | Produkt | Wartość |
|---------|--------|-----------|---------|---------|
| **LITE: Panikujący** | CEO/Founder/Legal, firma 5–50 os., deadline za pasem | Strach przed audytem, wymóg w przetargu, „muszę mieć papier" | Lite 299 EUR jednorazowo | Szybka gotówka, M1–M8 |
| **PRO: Scale-up High-Risk** | 20–200 os., własny model HR/fintech/health | Cykl życia modelu, Art. 11 ust. 2 | Pro 499–999 EUR/mies. | Retencja, M9+ |
| **PARTNER: Kancelarie** | Tech-law boutique, ISO consultants | Automatyzacja pracy doradczej | White-label 300 EUR/mies. | Kanał sprzedaży, M3+ |

> **ICP priorytet M1–M8 (jeden, nie trzy):**
> AI Scale-up 20–100 osób, własny system High-Risk, nie ma działu legal.
> Agencje: secondary — tylko organicznie.
> Kancelarie: **obowiązkowy kanał M3+ (nie opcja)** — jedyni którzy przynoszą
> lead w 24h przy zerowym zasięgu Founderskim.

### 1.6 Freeze decyzja: Epiki 4 i 5

> **CLOSED DECISION — nie podlega dyskusji przed 1 września 2026:**
> Epik 4 (MLOps integrations) i Epik 5 (Continuous Compliance)
> są całkowicie zamrożone do Września 2026.
> Uzasadnienie: klient lipiec 2026 = firma bez dokumentacji.
> Klient wrzesień 2026 = ta sama firma, której model się zmienił.
> To są różni klienci w różnych momentach — obsługa jednocześnie
> przy 4-miesięcznym oknie jest operacyjnie niemożliwa dla solo foundera.
> Build Pro zaczyna się dopiero z kasy zarobionych na Lite w lipcu.

---

## CZĘŚĆ II — MODEL BIZNESOWY

### 2.1 Plany i cennik

| Plan | Cena | Dla kogo | Co zawiera |
|------|------|----------|------------|
| **Free: Classifier** | 0 EUR | Lead magnet | Risk Classifier (10Q → High/Limited/Minimal) + Panic Calendar |
| **Lite: Single Report** | 299 EUR / raport | Panikujący, deadline-driven | 1 system, Wizard, AI drafts, PDF Annex IV, Completion %, brak rewizji |
| **Lite+: Annual** | 99 EUR/mies. | Firmy z 2–3 systemami | Do 3 systemów/rok, Wizard, eksport, alerty, brak integracji |
| **Pro** | 499–999 EUR/mies. | Scale-upy High-Risk (M9+) | Pełny Annex IV, CI/CD Etap 1, Copilot, Collaboration, Evidence, Audit Score |
| **Pro+Cloud** | 999–1 999 EUR/mies. | Korporacje ML (M12+) | Pro + AWS/Azure/GCP adapters, Secrets Vault, SLA |
| **Partner (White-label)** | 300 EUR/mies. lub 20% rev-share | Kancelarie, konsultanci (M3+) | PDF z logo klienta, multi-client panel, API |
| **Enterprise** | Custom (M12+) | Duże org. | SSO, Docker, SOC 2, DPA, dedicated support |

**Ścieżka upsell (chronologiczna):**
```
Free (Classifier) → Lite 299 EUR → Lite+ 99/mies.
  → [sierpień] upsell: „Model się zmieni?" → Pro 499/mies. → Pro+Cloud → Enterprise
```

### 2.2 Kill Switch — twarde progi

| # | Data | KPI „kontynuuj" | KPI „pivot/stop" |
|---|------|-----------------|------------------|
| **KS-1** | Koniec M2 (Maj) | ≥3 beta testerów Lite (może za free) | 0 zainteresowanych → zmień ICP lub uproszczaj |
| **KS-2** | Koniec M3 (Czerwiec) | ≥5 płacących klientów Lite | <2 płacących → stop, analiza co nie działa |
| **KS-3** | Koniec M4 (Lipiec) | ≥15 płacących klientów Lite | <8 → nie ruszaj Pro, przedłuż Lite marketing |
| **KS-4** | Koniec M6 (Wrzesień) | ≥2 klientów Pro (upsell lub nowi) | 0 Pro → wróć do Lite+, nie ruszaj integracji |
| **KS-5** | Koniec M9 | ≥1 klient Pro+Cloud lub ≥2 inbound zapytań | 0 → wytnij E14 z roadmapy |

---

## CZĘŚĆ III — ARCHITEKTURA

### 3.1 Mapa modułów

```
┌──────────────────────────────────────────────────────────────────────┐
│                          CompliAI Platform                           │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                     CORE ENGINE (wewnętrzne API)             │    │
│  │   annex_iv_schema · legal_rules · prompt_templates           │    │
│  │   evidence_model · classification_logic · scoring_engine     │    │
│  └───────────────────┬──────────────────────────────────────────┘    │
│                      │                                               │
│     ┌────────────────┴──────────────────────────────────┐            │
│     │                                                   │            │
│  ┌──▼───────────────────┐              ┌───────────────▼──────────┐  │
│  │  LITE PATH (Epik 0)  │              │  PRO PATH (Epiki 1–16)   │  │
│  │  BUILD: M1–M3        │              │  BUILD: M9+              │  │
│  │  SELL: M3–M8         │              │  SELL: M9+               │  │
│  └──────────────────────┘              └──────────────────────────┘  │
│                                                                      │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │ Classifier │  │ White-Label  │  │ Privacy/BYOK │  │ Auth+     │  │
│  │ (Epik 19)  │  │ (Epik 17)    │  │ (Epik 18)    │  │ Billing   │  │
│  │ M1–M2      │  │ M3–M8        │  │ M4–M12       │  │ M1        │  │
│  └────────────┘  └──────────────┘  └──────────────┘  └───────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.2 Stack technologiczny

- **Backend:** Python FastAPI + PostgreSQL + S3-compatible EU region
- **Frontend:** Next.js + TailwindCSS (mono-stack na Lite)
- **LLM:** OpenAI gpt-4o + BYOK option (Epik 18, M4)
- **Auth:** Supertokens (email-only M1, OAuth M5+)
- **Płatności:** Stripe Billing (jednorazowe M1, subskrypcje M5+)
- **Infra:** Railway EU / Render EU (start); k8s przy skalowaniu
- **Email:** Resend + Mailchimp (nurturing sequence)
- **Status:** BetterUptime (M1, przed pierwszą sprzedażą)

---

## CZĘŚĆ IV — EPIKI I USER STORIES

---

### EPIK 0: Quick-Start Wizard – Lite Path
**Priorytet:** #1 | **Build:** M1–M3 | **Sell:** M3–M8

**Cel:** CEO/Founder/Legal generuje draft Annex IV w <60 minut,
bez wiedzy o MLOps. Pierwsze źródło przychodu.

**Wizard: 7 bloków, 30–50 pytań:**
- B1 (5Q): Identyfikacja systemu i intended purpose
- B2 (8Q): Architektura, dane wejściowe, dane treningowe
- B3 (6Q): Walidacja, metryki dokładności, testy
- B4 (7Q): Zarządzanie ryzykiem (Art. 9)
- B5 (5Q): Nadzór ludzki (Art. 14), Human-in-the-Loop
- B6 (4Q): Post-market monitoring (Art. 72)
- B7 (5Q): Standardy, normy, certyfikaty

#### E0-US1: Kreator krok po kroku
Jako Founder, chcę odpowiadać na pytania w języku naturalnym i otrzymać paragraf Annex IV.
- AC: liniowy kreator 7 bloków + progress bar (Technical File Completion %)
- AC: każde pytanie: przykład + „Dlaczego pytamy?" + cytat artykułu AI Act
- AC: LLM jako tłumacz: odpowiedź → paragraf urzędowy (nie odwrotnie)
- AC: edycja wygenerowanego paragrafu przed eksportem
- AC: jeśli pole puste → placeholder tekst widoczny w drafcie (nie blokuje)
- AI: ~70%

#### E0-US2: Klasyfikacja ryzyka inline
Jako Founder, chcę wiedzieć czy mój system jest High-Risk i jakich artykułów to dotyczy.
- AC: klasyfikacja Annex III + fallback LLM dla edge-case'ów
- AC: wynik: kategoria + uzasadnienie + lista wymogów per kategoria
- AC: High-Risk → pełny Wizard (9 sekcji); Limited/Minimal → skrócony (Art. 13+52)
- AC: „Intended Purpose Checker" — flaga jeśli definicja za szeroka (ryzyko wciągnięcia w High-Risk)
- AI: ~65%

#### E0-US3: Eksport PDF + Stripe
Jako Founder, chcę zapłacić 299 EUR i otrzymać PDF gotowy do przekazania prawnikowi.
- AC: Stripe Checkout → jednorazowy token → eksport odblokowany
- AC: PDF: logo klienta (upload), numer wersji, data, watermark „DRAFT – requires legal review"
- AC: **OBOWIĄZKOWY DISCLAIMER** (checkbox przed eksportem):
  „Wskaźnik 100% oznacza wyłącznie kompletność struktury Annex IV.
  Nie stanowi potwierdzenia merytorycznej poprawności ani zgodności ze stanem faktycznym.
  Dokument wymaga weryfikacji przez prawnika i ML Leada przed złożeniem organowi nadzoru."
- AC: email post-purchase: „Twój Annex IV draft – 3 następne kroki"
  [1. przegląd prawny, 2. weryfikacja ML Lead, 3. co aktualizować po zmianie modelu]
- AC: brak możliwości eksportu bez checkbox — nie opcja, nie skip
- AI: ~75%

#### E0-US4: Zapis sesji i powrót
Jako Founder, chcę zapisać sesję i wrócić w ciągu 7 dni.
- AC: auto-save po każdym bloku; sesja email + token (bez konta)
- AC: po 7 dniach: email reminder + 3 dni grace period
- AC: zakup = konwersja sesji na konto z historią raportów
- AI: ~70%

#### E0-US5: Strona „Co dalej?" — mechanika upsell
Jako Founder po eksporcie, chcę rozumieć co daje upgrade do Pro.
- AC: ✅ `Technical File Completion: 100%`
- AC: 🔴 `Evidence Validation: NOT VERIFIED` (locked, z tooltipem)
- AC: komunikat: „Jesteś gotowy do wydruku. Nie jesteś gotowy na kontrolę."
- AC: CTA: „Twój model się zmieni. Wtedy wróć po Pro." (messaging: kontynuacja, nie presja)
- AC: countdown do następnego regularnego terminu przeglądu (opcjonalny, Art. 72)
- AI: ~80%

#### E0-US6: Tryb Partner (entry do White-Label)
Jako Konsultant, chcę generować raport dla klienta pod jego logo.
- AC: wpisanie nazwy i logo innej organizacji
- AC: PDF footer: „Prepared by [Partner Name]"
- AC: entry point do White-Label planu (Epik 17)
- AI: ~70%

---

### EPIK 19: AI Act Risk Classifier & Lead Magnet
**Priorytet:** #2 | **Build:** M1–M2 | **Cel:** zbieranie leadów, konwersja do Lite

#### E19-US1: Publiczny Classifier (10 pytań, bez rejestracji)
Jako Founder, chcę w 3 minuty wiedzieć czy mój system podlega AI Act.
- AC: formularz 10Q, bez rejestracji, mobile-friendly
- AC: wynik: High/Limited/Minimal + uzasadnienie + cytat artykułu
- AC: PDF summary po podaniu emaila (opcjonalne)
- AI: ~65%

#### E19-US2: Panic Calendar (dla High-Risk)
Jako Founder z wynikiem High-Risk, chcę widzieć countdown do deadlinu.
- AC: konkretne daty kluczowych terminów AI Act 2026
- AC: jeśli do terminu <90 dni: pomarańczowy banner; <60 dni: czerwony
- AC: messaging: „Zostało X dni do AI Act. Masz już Annex IV?"
- AC: CTA: „Wygeneruj Annex IV teraz – 299 EUR" (nie „dowiedz się więcej")
- AI: ~80%

#### E19-US3: Shareable link + SEO
- AC: shareable URL z wynikiem + OG meta dla LinkedIn
- AC: embed code (iframe) dla partnerów
- AC: SEO target: „AI Act Annex IV generator", „AI Act High Risk checker"
- AI: ~80%

#### E19-US4: Nurturing sequence
- AC: email po wyniku High-Risk: tag + automated sequence D+1, D+7, D+14
- AC: treści: edukacja + CTA; Resend/Mailchimp
- AI: ~70%

---

### EPIK 1: Zarządzanie Organizacją i Systemami AI
**Build:** M2 (uproszczona wersja dla Lite), M6 (pełna dla Pro)

#### E1-US1: Rejestracja i workspace
- AC: email-only auth M1; OAuth (Google, GitHub) M5+
- AC: workspace = organizacja; multi-member M5+
- AC: system AI = projekt z metadanymi (nazwa, wersja, kategoria ryzyka)
- AI: ~75%

#### E1-US2: Dashboard systemów (Lite)
- AC: lista systemów + status (Draft/In Progress/Exported/Needs Update)
- AC: Lite: maks. 1 system aktywny; Lite+: do 3
- AI: ~70%

---

### EPIK 2: Pełny Annex IV Core (9 sekcji)
**Build:** M9+ (Pro MVP) | **Zależy od:** Kill Switch KS-4

Pełna specyfikacja 9 sekcji Annex IV zgodnie z rozporządzeniem:
1. Ogólny opis systemu AI i jego przeznaczenie
2. Opis elementów systemu i procesu rozwoju
3. Informacje o danych treningowych i testowych
4. Walidacja i testy (Art. 10 + Art. 15)
5. Monitorowanie, działanie i kontrola
6. Opis procesów zarządzania ryzykiem (Art. 9)
7. Zmiany w systemie i post-market monitoring
8. Standardy i normy zharmonizowane
9. Deklaracja zgodności UE

#### E2-US1: Edytor sekcji Annex IV (pełny, Pro)
- AC: rich text editor per sekcja + AI Draft button
- AC: obsługa plików/artefaktów jako evidence
- AC: historia wersji (revision log) per sekcja
- AI: ~65%

#### E2-US2: Wskaźniki — ścisły podział Lite/Pro
- **Lite:** Technical File Completion % (binarny: jest tekst w sekcji = %)
  - Nigdy nie nazywamy tego „Compliance Score"
  - Max widoczna wartość w Lite: 100% Completion
- **Pro:** Audit Readiness Score (0–100)
  - Wzór: (completeness × 0.4) + (evidence_freshness × 0.3) + (open_alerts × 0.2) + (revision_recency × 0.1)
  - Tag `[Verified by Data]` per sekcja gdy evidence attached
  - Locked placeholder w Lite z komunikatem

#### E2-US3: Intended Purpose Checker
- AC: analiza definicji „Intended Purpose" pod kątem ryzyka Over-Scoping
- AC: automatyczne flagowanie zbyt szerokich definicji
- AC: sugestia węższej definicji redukującej ryzyko High-Risk classification
- AI: ~55%

---

### EPIK 3: AI Copilot i Drafting Engine
**Build:** M9+ (Pro) | **Lite:** AI drafts w Wizard (M2, uproszczone)

#### E3-US1: AI Draft (Lite — uproszczony)
- AC: per blok Wizarda: przycisk „Wygeneruj draft"
- AC: LLM jako tłumacz odpowiedzi → paragraf (nie samodzielny generator)
- AI: ~70%

#### E3-US2: Full Copilot (Pro)
- AC: Q&A z dokumentacją (RAG po schema Annex IV + wytycznych)
- AC: „Diff View": co się zmieniło w dokumencie vs. poprzednia wersja
- AC: sugestie uzupełnień na podstawie luk w sekcjach
- AC: „What-if": symulacja jak zmiana modelu wpłynie na sekcje
- AI: ~60%

---

### EPIK 4: MLOps Integrations — ZAMROŻONY DO M9
**Build:** M9+ | **Status:** FREEZE — nie ruszać przed Kill Switch KS-4

Integracje: GitHub/GitLab webhooks, CLI compliai-cli,
AWS SageMaker, Azure ML, Vertex AI, Databricks/MLflow,
Weights & Biases, DVC, Evidence auto-collection.

---

### EPIK 5: Continuous Compliance — ZAMROŻONY DO M9
**Build:** M9+ | **Status:** FREEZE — nie ruszać przed Kill Switch KS-4

Real-time drift detection, automated Technical File updates,
Change Impact Assessment (Art. 11 ust. 2), post-market alerts.

---

### EPIK 6: ISO 42001 Crosswalk
**Build:** M12+ | Mapowanie Annex IV → ISO 42001:2023

---

### EPIK 7: Enterprise (SSO, Portfolio)
**Build:** M12+ | SAML/OIDC, Okta/Azure AD, portfolio dashboardy

---

### EPIK 8: Onboarding, Growth i Retencja
**Build:** M1 (onboarding Lite), M9+ (Pro flows)

#### E8-US1: Onboarding wizard (first-use)
- AC: 5-krokowy onboarding: co to AI Act → czy dotyczy mnie → Classifier → Wizard → eksport
- AC: progress persists, można opuścić i wrócić
- AI: ~75%

#### E8-US2: Trial flow (Lite → Lite+)
- AC: po eksporcie: CTA do Lite+ annual (99 EUR/mies.) z korzyściami
- AC: jeśli użytkownik ma >1 system: automatyczny prompt do Lite+
- AI: ~70%

#### E8-US3: Founder dashboard metryk
- AC: wewnętrzny panel (tylko Ty): MRR, Churn, konwersja Classifier→Lite, konwersja Lite→Pro
- AC: alerty jeśli Kill Switch KPI zagrożone
- AI: ~80%

#### E8-US4: Upsell flow post-Sierpień (M5)
- AC: do klientów Lite którzy eksportowali >60 dni temu: email „Twój model się zmienił?"
- AC: CTA: „Zaktualizuj Annex IV" → nowy Lite token lub upgrade Pro
- AC: messaging: ciągłość i obowiązek art. 11 ust. 2, nie strach
- AI: ~75%

---

### EPIK 9: Compliance Cockpit
**Build:** M9+ (Pro) | Ścisły podział wg zasady 1.4

#### E9-US1: Audit Readiness Score (Pro only)
- AC: dynamiczny wskaźnik 0–100 z podziałem na komponenty
- AC: trend historyczny (30/60/90 dni)
- AC: lista „Top 3 actions to improve score"
- AI: ~65%

#### E9-US2: RAG-score badge i Completeness (Lite)
- AC: Lite: tylko Technical File Completion % (nie score)
- AC: po 100%: locked `Evidence Validation: NOT VERIFIED` z tooltipem i CTA
- AI: ~70%

---

### EPIK 10: Collaboration & Review Workflow
**Build:** M9+ (Pro) | Komentarze inline, review, approval flow

---

### EPIK 11: Evidence Freshness & Lineage
**Build:** M9+ (Pro) | EVIDENCED/STALE/AUTO statusy, SHA-256, immutability

---

### EPIK 12: Auditor Exports & External Sharing
**Build:** M9+ (Pro) | Read-only link z TTL, Evidence ZIP, auditor view

---

### EPIK 13: CI/CD Integration — Etap 1 (Webhooks + CLI)
**Build:** M9+ (po KS-4) | GitHub/GitLab webhooks, compliai-cli, Gate endpoint

---

### EPIK 14: Cloud Adapters — Etap 2
**Build:** M12+ (po KS-5) | AWS/Azure/GCP adapters
**CLOSED:** Nie przed Kill Switch KS-5 (≥1 klient Pro+Cloud lub ≥2 inbound)

---

### EPIK 15: Proactive Compliance Assistant
**Build:** M9+ | Regulatory alerts, full scan, chatbot, quarterly digest

---

### EPIK 16: Trust, Security & Compliance
**Build:** M1 (podstawy), M5 (DPA), M12 (SOC 2)

#### E16-US1: EU Data Residency (M1 — OBOWIĄZKOWE przed launch)
- AC: hosting wyłącznie EU region (Railway EU / AWS eu-central-1)
- AC: status page (BetterUptime) aktywny przed pierwszą sprzedażą

#### E16-US2: DPA (Data Processing Agreement)
- AC: DPA dostępne do podpisania przed pierwszą sprzedażą Pro
- AC: privacy policy PL+EN aktywne od M1

#### E16-US3: SOC 2 Type I (M12+)
- AC: readiness audit M12; Type II M15

---

### EPIK 17: White-Label & Intermediary Panel
**Build:** M3 (MVP: PDF+logo), M8 (pełne: subdomain)
**Priorytet: M3 — bo kancelarie to kanał sprzedaży, nie feature**

#### E17-US1: White-Label MVP (M3)
- AC: upload logo klienta + nazwa per projekt
- AC: PDF footer: „Prepared by [Partner Name]" (bez CompliAI branding)
- AC: multi-client panel: lista klientów + systemy + status
- AC: billing: Partner płaci CompliAI, klienci nie widzą cen CompliAI
- AI: ~70%

#### E17-US2: Partner edit workflow
- AC: Generated → Partner Reviews → Approved → Sent to Client
- AC: tryb edycji draftu przed wysłaniem (rich text per sekcja)
- AI: ~65%

#### E17-US3: White-Label Full (M8)
- AC: subdomain / CNAME per partner (partner.compliai.com lub CNAME)
- AC: upload logo + kolory + nazwa (basic brand kit)
- AI: ~65%

---

### EPIK 18: Privacy & Data Sovereignty
**Build:** M1 (SaaS default), M4 (BYOK), M5 (Stateless), M12 (Docker)

#### E18-US1: Standard SaaS EU (M1 — default)
- AC: dane zaszyfrowane w EU region; TLS 1.3; AES-256 at rest
- AI: ~70%

#### E18-US2: BYOK — Bring Your Own Key (M4)
- AC: envelope encryption z AWS KMS / Azure Key Vault / GCP KMS klienta
- AC: CompliAI nie może odszyfrować bez klucza klienta
- AI: ~60%

#### E18-US3: BYOK LLM — własny klucz API (M4)
- AC: ustawienia org: własny klucz OpenAI / Anthropic / Azure OpenAI
- AC: koszty tokenów po stronie klienta; zniżka -15% na plan Pro
- AC: odpowiedzialność za prywatność danych: klient–OpenAI/Anthropic
- AI: ~65%

#### E18-US4: Stateless / Zero-Knowledge Mode (M5)
- AC: toggle per organizacja
- AC: dane formularza purged po wygenerowaniu dokumentu
- AC: audit log: „data purged at [timestamp]"
- AC: disclaimer: brak możliwości re-generacji w Stateless Mode
- AI: ~55%

#### E18-US5: Docker / Single-Tenant (M12+)
- AC: obraz Docker w prywatnym registry CompliAI
- AC: license server: heartbeat co 24h (lub offline JWT token na 30 dni)
- AC: dokumentacja deploy: AWS ECS, Azure Container Apps, self-hosted k8s
- AC: licencja Docker: od 2 000 EUR/mies. (Enterprise only)
- **CLOSED DECISION:** NIE przed M12, NIE bez ≥2 enterprise inbound z NDA.
  Version drift + brak logów + SLA liability są zabójcze dla solo foundera.
- AI: ~60%

---

## CZĘŚĆ V — GTM (GO-TO-MARKET)

### 5.1 Faza A: Survival (Kwiecień–Czerwiec 2026)

1. **Classifier online (M1–M2):** Lead gen, SEO, viralność na LinkedIn
   Targetowane słowa kluczowe: „AI Act Annex IV generator", „AI Act High Risk checker",
   „Annex IV template download", „AI Act compliance 2026"

2. **Cold outreach LinkedIn (M2–M3):** 20 wiadomości/dzień
   Skrypt: „Widzę, że budujecie [produkt AI]. Zostało X dni do AI Act —
   Twój system może wymagać Annex IV. Zrobiłem narzędzie które generuje go
   w godzinę za 299 EUR. Chcecie testowy raport?"
   Target: CTO, Head of AI, Founder w firmach 10–100 osób z własnym AI produktem

3. **Kancelarie (M3 — OBOWIĄZKOWE):** test 50 kontaktów
   Oferta: „Macie klientów którzy pytają o AI Act. Daję Wam White-Label dostęp.
   Wy bierzecie 5 000 PLN za 'weryfikację dokumentacji AI',
   ja biorę 300 EUR/mies. za technologię."
   Jeśli <5 odpowiedzi na 50 kontaktów → zmień pitch, nie produkt

4. **Content (M2+):**
   „Przeczytałem cały Annex IV i oto 3 pułapki które zniszczą startup AI"
   „Prawnicy nie opiszą wag modelu — tu jest Twoja przewaga techniczna"
   „AI Act Timeline 2026: co grozi firmom bez dokumentacji (i kiedy faktycznie)"

### 5.2 Faza B: Peak (Lipiec 2026)

5. **„Ostatnia szansa" messaging:** countdown na landing page, banner, emaile do listy
   Hasło główne: „Zostało [X] dni do AI Act. Masz już Annex IV?"
6. **Product Hunt launch:** cel top 5 dnia — uprzednio zebrać hunter'a i 50+ upvoters
7. **Case Studies:** minimum 2 anonimowe z logo przed PH launch

### 5.3 Faza C: Post-August Upsell (Sierpień–Wrzesień 2026)

8. **Email do klientów Lite:** „Twój Annex IV jest gotowy.
   Co gdy zmienisz model? Art. 11 ust. 2 wymaga aktualizacji."
   CTA: nowy token (299 EUR) lub upgrade Pro (499/mies.)
9. **Webinaria partnerskie:** z kancelariami, „AI Act Clinic" (bezpłatne dla uczestników)
10. **AWS/Azure Marketplace:** DOPIERO po ARR 50k+ i uruchomieniu Cloud Adapters (M12+)

---

## CZĘŚĆ VI — HARMONOGRAM TECHNICZNY

### Zasada: Lite na rynek w M2, sprzedaż M3, Pro finansowany z Lite

```
M1 (Kwiecień):  Classifier + Lite MVP build
M2 (Maj):       Classifier launch + Lite launch + pierwsi klienci
M3 (Czerwiec):  Kancelarie + outreach + KS-2 check
M4 (Lipiec):    Peak sales + KS-3 check + Product Hunt
M5 (Sierpień):  Post-August upsell + White-Label full + BYOK LLM
M6 (Wrzesień):  KS-4 check → jeśli OK, START Pro build
M9+:            Pro MVP (E2,E3,E9–E13)
M12+:           Cloud Adapters, Enterprise, Docker
```

### Faza 0 — Discovery (Tygodnie 1–2, ZERO KODU)

| # | Zadanie | AI | Dni |
|---|---------|----|-----|
| T0.1 | 10 rozmów discovery: ML Lead, Compliance Officer, CEO z AI-product | ✗ | 5 |
| T0.2 | Walidacja pytań Classifiera na 5 osobach docelowych | ✗ | 3 |
| T0.3 | Setup: repo, CI/CD, Railway EU, domena, landing page (waitlist) | ◑◑ | 4 |
| T0.4 | Competitor deep-dive (eucompliai.com, Holistic AI, Credo AI) | ✗ | 2 |
| **T0.5** | **Trademark check „CompliAI" w EUIPO; warianty: AnnexAI, TechFileAI, CompliDoc** | **✗** | **2** |
| T0.6 | Disclaimer prawny — wersja zaakceptowana przez PL prawnika (PRZED M2 launch) | ✗ | 3 |

### Faza 1A — Classifier (M1, Epik 19)

| # | Zadanie | AI | Dni |
|---|---------|----|-----|
| T19.1 | Logika klasyfikacji: decision tree Annex III + LLM fallback | ◑ | 3 |
| T19.2 | Formularz 10Q + wynik + Panic Calendar + countdown | ◑◑ | 3 |
| T19.3 | Email capture + Resend + automated sequence (D+1, D+7, D+14) | ◑◑ | 2 |
| T19.4 | Share URL + OG meta + embed code | ◑◑ | 1 |
| T19.5 | SEO landing page Classifier + blog post „Am I High Risk?" | ◑◑ | 2 |

### Faza 1B — Lite MVP (M1–M2, Epik 0)

| # | Zadanie | AI | Dni | Priorytet |
|---|---------|----|-----|-----------|
| T0.A1 | Auth email-only + WizardSession model danych | ◑◑ | 3 | P1 |
| T0.A2 | Wizard UI: 7 bloków, progress bar, auto-save | ◑◑ | 4 | P1 |
| T0.A3 | Prompt chain: Answer → Annex IV paragraph (per blok) | ◑ | 4 | P1 |
| T0.A4 | Klasyfikator ryzyka inline (Annex III) | ◑◑ | 2 | P1 |
| T0.A5 | Rich text edytor paragrafów wygenerowanych przez LLM | ◑◑ | 3 | P1 |
| T0.A6 | Eksport PDF: Annex IV layout + logo upload + watermark + disclaimer checkbox | ◑◑ | 4 | P1 |
| T0.A7 | Stripe Checkout 299 EUR + webhook + email z PDF linkiem | ◑◑ | 3 | P1 |
| T0.A8 | Strona „Co dalej?" (100% Completion + locked Evidence Validation + upsell) | ◑◑ | 2 | P1 |
| T0.A9 | Stripe Lite+ Annual 99 EUR/mies. + upgrade flow | ◑◑ | 2 | P2 |
| T0.A10 | Landing page SEO + 5-krokowy onboarding wizard | ◑◑ | 3 | P1 |
| T0.A11 | E2E test: classifier → wizard → Stripe → PDF → strona Co dalej | ◑◑ | 3 | P1 |
| T0.A12 | Status page (BetterUptime) + privacy policy + DPA basic | ✗ | 2 | P1 |

### Faza 1C — White-Label MVP dla kancelarii (M3, Epik 17 — partial)

| # | Zadanie | AI | Dni |
|---|---------|----|-----|
| T17.1 | Multi-client panel (lista klientów, systemy, statusy) | ◑◑ | 3 |
| T17.2 | PDF branding: logo klienta + „Prepared by [Partner]" | ◑◑ | 2 |
| T17.3 | Partner billing: Stripe plan 300 EUR/mies. | ◑◑ | 2 |

### Faza 1D — Manualna sprzedaż (M3–M4, ZERO KODU)

LinkedIn outreach, kancelarie, beta testerzy, case studies.
Kill Switch KS-2 i KS-3 sprawdzane na koniec M3 i M4.
**Jeśli KS-2 nie spełniony (M3): stop build, analiza.**
**Jeśli KS-3 nie spełniony (M4): stop Pro build na dłużej.**

### Faza 2 — BYOK + Stateless + Upsell flow post-Aug (M4–M5)

| # | Zadanie | AI | Dni |
|---|---------|----|-----|
| T18.2 | BYOK KMS (AWS/Azure/GCP envelope encryption) | ◑ | 6 |
| T18.3 | BYOK LLM (własny klucz API per org) | ◑◑ | 4 |
| T18.4 | Stateless/Zero-Knowledge Mode | ◑ | 4 |
| T8.4 | Email upsell flow: klienci Lite >60 dni → „Twój model się zmienił?" | ◑◑ | 3 |
| T17.3 | White-Label Full: subdomain/CNAME | ◑◑ | 5 |

### Faza 3 — Pro MVP (M9+, po KS-4, Epiki E1–E3, E9–E12 core)

**WARUNEK START:** Kill Switch KS-4 spełniony (≥2 klientów Pro lub upsell).
**WAŻNE:** Model danych Pro (TechnicalFile, Evidence, Revision)
budowany DOPIERO po ≥1 płacącym kliencie Lite (unikamy miesięcy bez walidacji).

| # | Zadanie | AI | Dni |
|---|---------|----|-----|
| T_p1 | Model danych Pro: Org, AISystem, TechnicalFile, Evidence, Revision | ◑ | 5 |
| T_p2 | Formularze 9 sekcji Annex IV (pełne, nie Wizard) | ◑◑ | 8 |
| T_p3 | TechnicalFileRevision: model + historia + diff view | ◑◑ | 5 |
| T_p4 | AI Copilot full: drafty + Q&A (RAG) + „What-if" | ◑◑ | 8 |
| T_p5 | Collaboration: komentarze inline + review workflow | ◑◑ | 6 |
| T_p6 | Evidence: upload + status EVIDENCED/STALE/AUTO + freshness | ◑◑ | 5 |
| T_p7 | Audit Readiness Score (pełny wzór) + dashboard | ◑◑ | 4 |
| T_p8 | Auditor View (read-only link + TTL) + Evidence ZIP | ◑◑ | 4 |
| T_p9 | Stripe Pro plan + upgrade flow z Lite | ◑◑ | 3 |
| T_p10 | Intended Purpose Checker (over-scoping flag) | ◑ | 4 |
| T_p11 | E2E testy Pro flow | ◑◑ | 4 |

### Faza 4 — CI/CD + Cloud (M9–M12, po KS-4 i KS-5)

Epiki 4, 5, 13, 14: MLOps integrations, Continuous Compliance,
GitHub/GitLab webhooks, CLI, AWS/Azure/GCP adapters.
Szczegółowe US w oryginalnym v1.1 (archiwum).

### Faza 5 — Enterprise (M12+)

ISO 42001, SSO, Docker (po ≥2 enterprise inbound z NDA), SOC 2.

---

## CZĘŚĆ VII — RYZYKA

| Ryzyko | Pr. | Wpływ | Mitygacja |
|--------|-----|-------|-----------|
| GIGO: błędne dane → niepoprawna dok. | Wysoka | Wysoki | Disclaimer checkbox obowiązkowy architektonicznie; email „3 kroki"; watermark w Lite na zawsze |
| Fałszywe poczucie bezpieczeństwa (messaging „sierpień = kary") | Wysoka | Wysoki | Messaging: „gotowy gdy organ się pojawi" — NIE „unikniesz kary 1 sierpnia" |
| KE lub duży gracz wypuszcza darmowy generator | Wysoka | Wysoki | Integracje + Evidence-First = moat; Lite to wejście do lejka, nie produkt docelowy |
| eucompliai.com atakuje niszę przed Tobą | Wysoka | Średni | Szybki launch (M2), głębszy Annex IV schema, ICP scale-upy |
| Zero klientów M3 (KS-2) | Średnia | Krytyczny | Stop build → analiza → pivot ICP lub uproszczenie → nowy launch |
| Kancelarie odrzucają partnerstwo | Średnia | Wysoki | Test 50 kontaktów M3; jeśli <5 odpowiedzi → bezpośredni outreach CEO/CTO |
| Prawna odpowiedzialność za błędną dok. | Wysoka | Wysoki | PL prawnik akceptuje disclaimer przed M2 launch; checkbox nieusuwalne |
| Trademark kolizja z eucompliai.com | Średnia | Wysoki | T0.5 EUIPO check przed M2 |
| Burn-out / scope creep | Wysoka | Krytyczny | Kill Switch'e, FREEZE Epiki 4+5, jedna funkcja na sprint |
| Docker dla enterprise przed M12 | Wysoka | Wysoki | CLOSED DECISION: NIE przed M12 bez 2x inbound enterprise z NDA |

---

## CZĘŚĆ VIII — DECYZJE ZAMKNIĘTE

| Decyzja | Kiedy zamknięta |
|---------|-----------------|
| FREEZE Epiki 4+5 do M9 (po KS-4) | v1.15 |
| Docker NIE przed M12, NIE bez ≥2 inbound enterprise z NDA | v1.2 |
| Model danych Pro DOPIERO po ≥1 płacącym Lite | v1.2 |
| Słowo „Compliance" NIGDY w UI/copy Lite | v1.2 |
| Disclaimer + checkbox obowiązkowy architektonicznie (nie skip) | v1.15 |
| Kill Switch KS-1 do KS-5 są twarde — brak racjonalizacji | v1.15 |
| Kancelarie = obowiązkowy kanał M3 (nie opcja) | v1.15 |
| Messaging: „gotowy gdy organ się pojawi" NIE „unikniesz kary" | v1.15 |
| ICP M1–M8: jeden segment (scale-up High-Risk 20–100 os.) | v1.2 |

---

## CZĘŚĆ IX — PYTANIA OTWARTE

1. **Trademark:** wynik T0.5 (EUIPO) decyduje o nazwie — decyzja przed M2
2. **Disclaimer:** wersja zaakceptowana przez PL prawnika — przed M2 launch
3. **Stack Lite:** Next.js API routes (mono) vs FastAPI osobno? → mono na Lite (szybkość), FastAPI od Pro
4. **Pricing test:** 299 EUR vs. 199 EUR — A/B w M2 (pierwsze 2 tygodnie)
5. **Kancelarie pitch:** rev-share 20% vs. flat 300 EUR/mies. — test na pierwszych 5 partnerach

---

## CZĘŚĆ X — LEGENDA

| Symbol | Znaczenie |
|--------|-----------|
| ◑◑ | AI-coding generuje 60–80% kodu |
| ◑ | AI-coding wspiera 30–50% |
| ✗ | Nie można zautomatyzować: rozmowy, prawo, sprzedaż, decyzje |

---

*CompliAI PRD v1.15 — Kwiecień 2026*
*Zastępuje: v1.0, v1.1, v1.2*
*Następna rewizja: po Kill Switch KS-2 (Koniec M3)*
