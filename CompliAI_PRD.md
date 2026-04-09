# CompliAI – Product Requirements Document (PRD)
**Wersja:** 1.0 | **Data:** Kwiecień 2026 | **Autor:** Solo Founder / Indie Dev

---

## 1. Streszczenie produktu

### 1.1 Problem
Dostawcy systemów AI wysokiego ryzyka w UE (AI Act, Art. 11 + Annex IV) muszą utrzymywać
kompletny, aktualny Plik Techniczny – interdyscyplinarny dokument liczący 40–120 stron,
obejmujący architekturę, dane, ryzyka, walidację, nadzór ludzki i post-market monitoring.
Tworzenie go ręcznie (Word / Excel / Confluence) jest:
- nieefektywne (tygodnie pracy przy każdej zmianie modelu),
- podatne na luki (brak powiązania z rzeczywistym stanem systemu),
- kosztowne przy audytach (nadrabianie dokumentacji „na gorąco").

### 1.2 Rozwiązanie
**CompliAI** – modularna platforma SaaS automatyzująca cykl życia dokumentacji technicznej
(Annex IV). Rdzeń stanowi model danych „Evidence-First": każda sekcja pliku technicznego
jest widokiem na realne artefakty z potoku MLOps, a nie statycznym tekstem.

### 1.3 Pozycjonowanie
- **Dla kogo:** ML Lead, Head of Compliance, Risk Officer w organizacjach rozwijających
  systemy AI high-risk (fintech, HR-tech, healthtech, edtech, automotive software).
- **Kim nie jesteśmy:** pełną platformą AI governance (jak Holistic AI) ani narzędziem
  bezpieczeństwa promptów (jak Lakera). Jesteśmy pionowym narzędziem dokumentacyjnym.
- **Kluczowy wyróżnik:** pełne pokrycie Annex IV + Continuous Compliance + integracje MLOps
  + AI Copilot generujący i utrzymujący plik techniczny.

### 1.4 Model biznesowy
Subskrypcja SaaS (roczna / miesięczna):
- Starter: ~250 EUR/mies. – 1 system AI, 3 użytkowników
- Pro: ~650 EUR/mies. – 3 systemy, 10 użytkowników, zaawansowane integracje
- Enterprise: wycena custom – nieograniczone systemy, SSO, wsparcie wdrożeniowe

---

## 2. Cele produktowe i miary sukcesu

| Cel | Miara | Target (M12) |
|-----|-------|-------------|
| Adopcja | Płacący klienci | 10 |
| Przychód | MRR | 5 000 EUR |
| Retencja | Churn miesięczny | <5% |
| Użyteczność | % kompletności Annex IV u klientów | >75% avg |
| Wdrożenie | Czas do pierwszego eksportu PDF | <2 h |

---

## 3. Architektura modułowa (wysokopoziomowa)

Produkt podzielony na 6 niezależnych modułów z czystymi interfejsami:

```
┌─────────────────────────────────────────────────────────┐
│                     CompliAI Platform                   │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  annex_iv_   │  │  ai_assistant│  │  integrations│  │
│  │  core        │  │  (Copilot,   │  │  (Git, CI,   │  │
│  │  (schema,    │  │  Q&A, diff)  │  │  MLOps)      │  │
│  │  revisions,  │  └──────────────┘  └──────────────┘  │
│  │  dowody)     │                                       │
│  └──────────────┘  ┌──────────────┐  ┌──────────────┐  │
│                    │  policy_     │  │  exports     │  │
│  ┌──────────────┐  │  engine      │  │  (PDF, MD,   │  │
│  │  auth_billing│  │  (rules,     │  │  JSON-LD)    │  │
│  │  (Auth0,     │  │  alerts,     │  └──────────────┘  │
│  │  Stripe)     │  │  blocks)     │                    │
│  └──────────────┘  └──────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

**Stack technologiczny:**
- Backend: Python (FastAPI) + PostgreSQL + S3-compatible storage
- Frontend: Next.js (React) + TailwindCSS
- LLM: OpenAI API (gpt-4o) + warstwa cache i logowania
- Auth: Auth0 / Supertokens
- Płatności: Stripe Billing
- Infra: Railway / Render (start), migracja do k8s przy skalowaniu
- Integracje: REST API + Webhooks + oficjalne SDK dla MLflow, W&B, GitHub

---

## 4. Epiki i User Stories

---

### EPIK 1: Zarządzanie systemami AI i organizacją [M1–M2]

**Cel:** użytkownik może zdefiniować organizację, dodać systemy AI i przypisać role.

#### User Stories

**E1-US1:** Jako Admin, chcę założyć konto organizacji i zaprosić użytkowników,
aby mój zespół (ML, legal, risk) miał dostęp do platformy.
- AC: rejestracja org, zaproszenie email, role: admin / ml_owner / legal / viewer
- AI-coding: boilerplate auth (Auth0), CRUD użytkowników – AI generuje 80%

**E1-US2:** Jako ML Lead, chcę dodać nowy system AI do inwentarza
i wypełnić podstawowe metadane (nazwa, opis, kategoria ryzyka, intended purpose),
aby zainicjować plik techniczny Annex IV.
- AC: formularz tworzenia systemu, walidator "intended purpose"
  (flagi szerokich definicji mogących wciągnąć w high-risk)
- AC: automatyczne przypisanie do Annex III (high-risk) jeśli spełnia kryteria

**E1-US3:** Jako Compliance Officer, chcę widzieć dashboard z listą
wszystkich systemów AI organizacji i statusem ich dokumentacji
(% kompletności Annex IV, data ostatniej rewizji, alerty),
aby monitorować dług dokumentacyjny.
- AC: lista systemów + wskaźnik completeness + ostatnia rewizja + badge alertu
- AI-coding: generowanie dashboardu + metryki – AI generuje UI, Ty piszesz logikę

---

### EPIK 2: Pełny Plik Techniczny Annex IV (Core) [M1–M3]

**Cel:** użytkownik może wypełnić wszystkie 9 sekcji Annex IV dla systemu AI
i eksportować kompletny, audit-ready plik techniczny.

**Sekcje Annex IV do odwzorowania w schema:**
1. Ogólny opis systemu i przeznaczenie (intended purpose, use cases, users)
2. Opis projektu i rozwoju (architektura, algorytmy, główne decyzje projektowe)
3. Dane treningowe, walidacyjne i testowe (datasheets for datasets)
4. Walidacja i testowanie (metryki, metodologia, wyniki dla podgrup)
5. System zarządzania ryzykiem (rejestr ryzyk, środki kontroli, ryzyko resztkowe)
6. Zmiany w cyklu życia (changelog, plan zarządzania zmianami)
7. Zastosowane normy i standardy (ISO 42001, inne)
8. Nadzór ludzki i przejrzystość (interfejsy XAI, procedury HITL, Art. 13–14)
9. Post-market monitoring (plan PMM, źródła danych, metryki, raportowanie)

#### User Stories

**E2-US1:** Jako ML Lead, chcę wypełniać każdą sekcję Annex IV w ustrukturyzowanym
formularzu (pola + rich text + tabele), aby mieć kompletny plik techniczny.
- AC: 9 sekcji z formularzami, walidacja obowiązkowych pól, inline help
  ("Dlaczego to pole jest wymagane?" linkujące do tekstu AI Act)

**E2-US2:** Jako ML Lead, chcę widzieć w każdej sekcji wskaźnik kompletności
i listę brakujących elementów, aby wiedzieć co jeszcze do zrobienia.
- AC: pasek postępu per sekcja + sekcja per plik + lista "missing fields"
- AC: alerty: "Sekcja 5 (Ryzyko) nie była aktualizowana od 30+ dni"

**E2-US3:** Jako Compliance Officer, chcę podpinać dowody (pliki, linki, raporty)
do konkretnych pól w sekcjach Annex IV, aby każdy paragraf był poparty artefaktem.
- AC: upload pliku lub podanie URL/referencji jako "evidence" dla pola
- AC: każdy dowód ma metadane: typ, źródło, data, wersja, opcjonalny hash

**E2-US4:** Jako Admin, chcę eksportować pełny plik techniczny jako PDF/Markdown,
gotowy do przekazania audytorowi lub jednostce notyfikowanej.
- AC: eksport PDF z: numeracją sekcji, datą wygenerowania, wersją pliku,
  listą podpiętych dowodów i podpisem cyfrowym (hash rewizji)
- AC: eksport Markdown dla integracji z systemami DMS
- AI-coding: generowanie layoutu PDF (WeasyPrint/Puppeteer) – AI pisze ~70%

**E2-US5:** Jako ML Lead, chcę tworzyć nowe rewizje pliku technicznego
i przeglądać historię zmian między wersjami,
aby śledzić ewolucję dokumentacji systemu.
- AC: TechnicalFileRevision z: timestampem, listą zmienionych sekcji,
  autorem, linkiem do wersji kodu/modelu (opcjonalnie)
- AC: widok diff między dwoma rewizjami (highlight changed fields)

---

### EPIK 3: Annex-IV-Copilot (AI Asystent Dokumentacji) [M2–M4]

**Cel:** AI generuje i utrzymuje drafty sekcji Annex IV na bazie metadanych,
zwalniając użytkownika z ręcznego pisania.

#### User Stories

**E3-US1:** Jako ML Lead, chcę aby system automatycznie wygenerował
draft opisu systemu (Sekcja 1) na podstawie wypełnionych metadanych
(intended purpose, architektura, users), aby zaoszczędzić czas.
- AC: przycisk "Generuj draft" per sekcja, wynik w edytowalnym polu
- AC: draft zawiera cytowania (np. "zgodnie z Art. 11 AI Act, sekcja...")
- AI-coding: prompt engineering + streaming LLM response – AI generuje ~60%

**E3-US2:** Jako Compliance Officer, chcę aby Copilot
podpowiadał brakujące elementy w każdej sekcji
i sugerował uzupełnienia językiem naturalnym,
aby uniknąć luk dokumentacyjnych.
- AC: asystent działa "inline" w formularzu – np. "Brakuje opisu
  procedury eskalacji (Art. 14). Czy chcesz, żebym wygenerował draft?"

**E3-US3:** Jako ML Lead, chcę aby Copilot generował
"Diff dokumentacyjny" po aktualizacji wersji modelu –
listę sekcji, które prawdopodobnie wymagają aktualizacji,
z gotowymi draftami zmian.
- AC: po wgraniu nowych metadanych (np. nowy dataset) – automatyczny
  "Documentation Impact Analysis": lista sekcji + AI-draft zmian

**E3-US4:** Jako Legal, chcę aby Copilot generował
instrukcję obsługi dla użytkownika końcowego (Art. 13)
na bazie danych z pliku technicznego,
napisaną prostym językiem naturalnym.
- AC: generowanie dokumentu "User Instructions" z: przeznaczeniem,
  ograniczeniami, poziomami dokładności, procedurami nadzoru ludzkiego
- AC: export PDF + wersja edytowalna

**E3-US5:** Jako ML Lead, chcę zadawać pytania do dokumentacji
w języku naturalnym ("Jakie ryzyka opisaliśmy dla modeli
używających danych biometrycznych?") i otrzymywać
odpowiedzi z referencjami do konkretnych sekcji.
- AC: semantic search + Q&A nad dokumentacją (RAG nad TF rewizjami)
- AC: odpowiedź zawiera cytowania sekcji + linki do rewizji

---

### EPIK 4: Integracje z MLOps i repozytoriami kodu [M3–M6]

**Cel:** CompliAI zaciąga metadane z rzeczywistych systemów inżynierskich,
minimalizując ręczne wprowadzanie danych.

#### User Stories

**E4-US1:** Jako ML Lead, chcę podłączyć repozytorium GitHub/GitLab,
aby CompliAI automatycznie śledził wersje kodu
i powiązał je z rewizjami pliku technicznego.
- AC: OAuth z GitHub/GitLab, wybór repo, zaciąganie tagów/commitów
- AC: przy tworzeniu TF-Revision – możliwość wybrania commit/tagu jako "kotwicy"
- AI-coding: GitHub API wrapper + OAuth flow – AI generuje ~75%

**E4-US2:** Jako ML Lead, chcę podłączyć MLflow lub Weights & Biases,
aby metryki eksperymentów (accuracy, F1, drift, bias per group)
były automatycznie importowane do sekcji walidacyjnych Annex IV.
- AC: konfiguracja połączenia (API key / self-hosted URL)
- AC: mapowanie runów MLOps na pola w sekcjach 4 (walidacja) i 5 (ryzyko)
- AC: import jednorazowy + opcjonalny auto-sync

**E4-US3:** Jako DevOps / ML Lead, chcę skonfigurować webhook z CI/CD,
aby każdy deploy modelu na produkcję automatycznie
tworzył nową rewizję dokumentacji lub alert o wymaganej aktualizacji.
- AC: endpoint webhook + logika: "czy zmiana jest 'istotna' wg konfiguracji?"
- AC: konfiguracja progów (np. zmiana F1 > 5% = istotna zmiana)
- AC: automatyczne tworzenie TF-Revision draft lub alertu

**E4-US4:** Jako ML Lead, chcę ręcznie uploadować raporty z testów
(CSV / JSON / HTML z pytest/Great Expectations),
aby podpiąć je jako dowody w sekcjach walidacyjnych.
- AC: upload pliku + auto-parsowanie kluczowych metryk (accuracy, coverage)
- AC: metadane parsowanego raportu jako evidence w sekcji 4

---

### EPIK 5: Continuous Compliance i zarządzanie długiem [M5–M7]

**Cel:** platforma aktywnie wykrywa dryft między stanem systemu
a dokumentacją i egzekwuje polityki compliance.

#### User Stories

**E5-US1:** Jako Compliance Officer, chcę widzieć
dashboard "Compliance Health" dla każdego systemu AI,
pokazujący aktualne ryzyka dokumentacyjne i dług.
- AC: metryki: "days since last TF revision", "unlinked deployments",
  "sections overdue for update", "missing evidence count"
- AC: trend historyczny + eksport raportu

**E5-US2:** Jako ML Lead, chcę aby system porównał
nową wersję modelu (shadow / staging) z aktualną dokumentacją
i wskazał sekcje wymagające aktualizacji przed deployem na produkcję.
- AC: "Shadow Mode Validation": porównanie metryk nowej wersji
  z progami zdefiniowanymi w dokumentacji
- AC: raport: "zmiana wymaga aktualizacji sekcji X, Y" lub
  "nie wykryto istotnych zmian – OK do deployu"

**E5-US3:** Jako Compliance Officer, chcę definiować polityki compliance
jako reguły tekstowe, które system zamieni na automatyczne checksy.
- AC: edytor polityk (np. "Model scoringowy musi mieć audyt biasu
  co 30 dni") → system generuje regułę w YAML/JSON
- AC: reguły uruchamiane periodycznie; naruszenia → alert / blokada

**E5-US4:** Jako ML Lead, chcę aby Automated Bias Audit
był uruchamiany automatycznie przy każdym nowym deployu modelu,
aby wykrywać dryft fairness między wersjami.
- AC: konfigurowalna lista metryk biasu per system
  (np. demographic parity, equal opportunity)
- AC: porównanie nowa_wersja vs poprzednia_wersja + raport diff
- AC: wyniki auto-podpinane jako dowody w sekcji 5 (Ryzyko) Annex IV

---

### EPIK 6: Zarządzanie jakością i standardy (ISO 42001) [M7–M9]

**Cel:** CompliAI wspiera przygotowanie do certyfikacji ISO 42001
przez dostarczenie struktury procesów i szablonów polityk AI.

#### User Stories

**E6-US1:** Jako Admin, chcę mieć dostęp do biblioteki szablonów
(polityki AI, datasheets, impact assessment, procedury eskalacji),
aby nie zaczynać dokumentacji od zera.
- AC: biblioteka szablonów per typ systemu (scoring, CV-ranking, medical, generative)
- AC: szablony edytowalne, import do sekcji Annex IV jednym kliknięciem

**E6-US2:** Jako Compliance Officer, chcę mapowanie
wymagań CompliAI (Annex IV) na wymagania ISO 42001,
aby dokumentacja służyła dwóm celom jednocześnie.
- AC: widok "crosswalk" – tabela ISO 42001 control vs sekcja Annex IV
- AC: eksport "ISO 42001 evidence package" z zaznaczonymi pokrytymi kontrolami

**E6-US3:** Jako Legal, chcę generować podstawowy raport
AI Impact Assessment (AI IA / DPIA-style) na bazie danych z pliku technicznego,
aby wspierać wewnętrzne oceny ryzyka i prawa osób.
- AC: formularz AI IA z auto-populacją z TF (system, dane, ryzyka, grupy użytkowników)
- AC: eksport raportu AI IA (PDF)

---

### EPIK 7: Moduł Enterprise i wielodostępowość [M9–M12]

**Cel:** produkt obsługuje organizacje enterprise z wieloma systemami AI,
SSO i zaawansowanymi kontrolami dostępu.

#### User Stories

**E7-US1:** Jako Admin (enterprise), chcę logować się przez SSO (SAML/OIDC),
aby CompliAI był kompatybilny z systemem tożsamości organizacji.
- AC: integracja SAML 2.0 / OIDC (Okta, Azure AD, Google Workspace)

**E7-US2:** Jako Admin, chcę zarządzać wieloma systemami AI
z jednego panelu i porównywać ich status compliance,
aby monitorować portfolio systemów AI w organizacji.
- AC: widok portfolio: lista systemów + heatmapa ryzyk + alerty zbiorcze

**E7-US3:** Jako Compliance Officer, chcę eksportować
zbiorczy raport compliance dla całego portfolio systemów AI
(np. dla zarządu lub regulatora), w formacie PDF/CSV.
- AC: raport zbiorczy: lista systemów, completeness, ryzyka, otwarte punkty

---

### EPIK 8: Sprzedaż, onboarding i wzrost [M2–M18 ciągle]

**Cel:** płynny onboarding nowych klientów i skuteczne kanały pozyskania.

#### User Stories

**E8-US1:** Jako nowy użytkownik, chcę przejść onboarding
w mniej niż 30 minut: dodać pierwszy system AI,
wypełnić kluczowe sekcje Annex IV i wygenerować pierwszy eksport.
- AC: guided onboarding (wizard 5 kroków), progres bar, sample data

**E8-US2:** Jako potencjalny klient, chcę wypróbować CompliAI
bez podawania karty kredytowej przez 14 dni,
aby ocenić wartość przed zakupem.
- AC: trial 14 dni (1 system, 3 użytkowników), po wygaśnięciu – lock + upgrade prompt

**E8-US3:** Jako Founder, chcę śledzić metryki produktowe
(aktywne organizacje, completeness, eksporty, churn) w wewnętrznym dashboardzie,
aby podejmować decyzje o priorytecie rozwoju.
- AC: wewnętrzny panel metryk (nie dla klientów)

---

## 5. Harmonogram techniczny – 18 miesięcy

### FAZA 0 – Problem Discovery (Tygodnie 1–2)

**Cel:** zwalidować problem i ICP przed pierwszą linią kodu.

| # | Zadanie | AI | Czas |
|---|---------|----|------|
| T0.1 | 10 rozmów discovery z ML leadami / compliance w fintech/HR | ✗ | 1 tyg |
| T0.2 | Analiza konkurencji: Holistic AI, Annex IV narzędzia, demo | ✗ | 3 dni |
| T0.3 | Zdefiniuj ICP + "one sentence problem" + landing page (waitlist) | ◐ | 3 dni |
| T0.4 | Wybór stacku, setup repo, CI/CD pipeline | ◑ | 2 dni |

**Output:** jasna definicja ICP, 5+ potwierdzonych "pain pointów", landing page

---

### FAZA 1 – Core MVP: Annex IV + Auth + Eksport (Miesiące 1–3)

**Cel:** działający produkt z pełnym Annex IV, auth, rolami i eksportem PDF.
Epiki: E1 + E2.

**Miesiąc 1:**

| # | Zadanie | Moduł | AI | Szac. dni |
|---|---------|-------|----|-----------|
| T1.1 | Setup boilerplate SaaS (auth, billing, DB, hosting) | auth_billing | ◑◑ | 3 |
| T1.2 | Model danych: Org, User, AISystem, Role | annex_iv_core | ◑ | 2 |
| T1.3 | CRUD systemów AI + UI listy systemów | annex_iv_core | ◑◑ | 3 |
| T1.4 | Walidator "intended purpose" (flagi high-risk triggerów) | annex_iv_core | ◑◑ | 2 |
| T1.5 | Model danych Annex IV: 9 sekcji jako schema | annex_iv_core | ◑ | 3 |
| T1.6 | Formularze sekcji 1–3 (ogólny opis, architektura, dane) | annex_iv_core | ◑◑ | 4 |
| T1.7 | Evidence attachment (upload pliku + URL + metadane) | annex_iv_core | ◑◑ | 3 |
| T1.8 | Testy jednostkowe + seed data | - | ◑ | 3 |

**Miesiąc 2:**

| # | Zadanie | Moduł | AI | Szac. dni |
|---|---------|-------|----|-----------|
| T1.9 | Formularze sekcji 4–6 (walidacja, ryzyko, changelog) | annex_iv_core | ◑◑ | 4 |
| T1.10 | Formularze sekcji 7–9 (standardy, nadzór ludzki, PMM) | annex_iv_core | ◑◑ | 4 |
| T1.11 | TechnicalFileRevision: model + UI historii + diff | annex_iv_core | ◑ | 4 |
| T1.12 | Dashboard completeness (% per sekcja, alerty) | annex_iv_core | ◑◑ | 3 |
| T1.13 | Eksport PDF (WeasyPrint/Puppeteer, layout, podpis) | exports | ◑◑ | 4 |
| T1.14 | Eksport Markdown | exports | ◑◑ | 1 |
| T1.15 | Stripe Billing: plany Starter/Pro/Trial 14 dni | auth_billing | ◑◑ | 3 |
| T1.16 | E2E testy flow: "utwórz system → Annex IV → eksport PDF" | - | ◑ | 3 |

**Miesiąc 3:**

| # | Zadanie | Moduł | AI | Szac. dni |
|---|---------|-------|----|-----------|
| T1.17 | Onboarding wizard (E8-US1) | UI | ◑◑ | 3 |
| T1.18 | Trial 14 dni + lock/upgrade flow | auth_billing | ◑◑ | 2 |
| T1.19 | Landing page + blog post "Co to jest Annex IV" | marketing | ◑◑ | 3 |
| T1.20 | Rekrutacja 2-3 pilotowych klientów (beta) | sprzedaż | ✗ | cały mies. |
| T1.21 | Bug fixes z pilotów | - | ◑ | 5 |

**Output Fazy 1:** działający produkt z pełnym Annex IV, płatnościami i eksportem.
2–3 pilotowych klientów (nawet bezpłatnych).

---

### FAZA 2 – Annex-IV-Copilot (Miesiące 3–5)

**Cel:** LLM generuje drafty sekcji, diff dokumentacyjny i Q&A.
Epik: E3.

| # | Zadanie | Moduł | AI | Szac. dni |
|---|---------|-------|----|-----------|
| T2.1 | Architektura ai_assistant: prompt templates, streaming | ai_assistant | ◑ | 3 |
| T2.2 | Generowanie draftu sekcji 1-3 z metadanych (LLM) | ai_assistant | ◑◑ | 4 |
| T2.3 | Generowanie draftu sekcji 4-9 (walidacja, ryzyko, PMM) | ai_assistant | ◑◑ | 4 |
| T2.4 | Inline suggestions: "brakuje X w sekcji Y" | ai_assistant | ◑◑ | 3 |
| T2.5 | Documentation Diff: LLM analizuje co zmienić po zmianie modelu | ai_assistant | ◑ | 4 |
| T2.6 | Generowanie User Instructions (Art. 13) | ai_assistant | ◑◑ | 3 |
| T2.7 | Q&A nad dokumentacją: RAG + semantic search (pgvector) | ai_assistant | ◑ | 5 |
| T2.8 | Logowanie użycia LLM (tokeny, koszty, prompt versioning) | ai_assistant | ◑◑ | 2 |
| T2.9 | Cache embeddingów, rate limiting, fallback | ai_assistant | ◑◑ | 2 |
| T2.10 | Testy jakości generowanych draftów (evals) | - | ◑ | 3 |

**Output Fazy 2:** CompliAI generuje drafty wszystkich sekcji Annex IV + Q&A.
Pierwsze płatne konwersje.

---

### FAZA 3 – Integracje MLOps i Git (Miesiące 4–6)

**Cel:** automatyczne zaciąganie metadanych z MLOps, repozytoriów i CI/CD.
Epik: E4.

| # | Zadanie | Moduł | AI | Szac. dni |
|---|---------|-------|----|-----------|
| T3.1 | GitHub OAuth + zaciąganie repo, commitów, tagów | integrations | ◑◑ | 4 |
| T3.2 | GitLab integration (analogiczna) | integrations | ◑◑ | 2 |
| T3.3 | MLflow connector: runy, metryki, parametry | integrations | ◑◑ | 4 |
| T3.4 | Weights & Biases connector: runy, artefakty | integrations | ◑◑ | 3 |
| T3.5 | Mapowanie metadanych MLOps → sekcje Annex IV | integrations | ◑ | 3 |
| T3.6 | Webhook endpoint dla CI/CD deploymentów | integrations | ◑◑ | 3 |
| T3.7 | Logika klasyfikacji "czy zmiana jest istotna?" | integrations | ◑ | 3 |
| T3.8 | Auto-tworzenie TF-Revision draft przy deploy | annex_iv_core | ◑◑ | 3 |
| T3.9 | Upload + parsowanie raportów testów (CSV/JSON) | integrations | ◑◑ | 3 |
| T3.10 | UI konfiguracji integracji + status połączenia | integrations | ◑◑ | 3 |
| T3.11 | Testy integracyjne (mock API MLflow, W&B, GitHub) | - | ◑◑ | 4 |

**Output Fazy 3:** CompliAI "składa się sam" z danych MLOps.
Pitch: "podłącz MLflow → Annex IV wypełnia się automatycznie".

---

### FAZA 4 – Continuous Compliance + PMM (Miesiące 6–8)

**Cel:** platforma aktywnie monitoruje dług dokumentacyjny i egzekwuje polityki.
Epik: E5.

| # | Zadanie | Moduł | AI | Szac. dni |
|---|---------|-------|----|-----------|
| T4.1 | Model danych: PolicyRule + Alert + ComplianceEvent | policy_engine | ◑ | 3 |
| T4.2 | Scheduler periodycznych checków (APScheduler/Celery) | policy_engine | ◑◑ | 3 |
| T4.3 | Wbudowane reguły: "X dni bez rewizji", "missing PMM plan" | policy_engine | ◑◑ | 4 |
| T4.4 | Edytor polityk tekstowych → generowanie reguł (LLM) | policy_engine | ◑ | 4 |
| T4.5 | Dashboard "Compliance Health" (debt metrics) | policy_engine | ◑◑ | 4 |
| T4.6 | Shadow Mode Validation: porównanie staging vs TF | policy_engine | ◑ | 5 |
| T4.7 | Automated Bias Audit: metryki fairness per deploy | policy_engine | ◑ | 5 |
| T4.8 | Alerty email + webhook (Slack/Teams) dla naruszeń | policy_engine | ◑◑ | 3 |
| T4.9 | Moduł PMM: plan + metryki + raporty kwartalne | annex_iv_core | ◑◑ | 4 |
| T4.10 | Testy E2E: "deploy → audyt biasu → alert → rewizja TF" | - | ◑ | 4 |

**Output Fazy 4:** CompliAI jest aktywnym "strażnikiem" zgodności, nie tylko repozytorium.

---

### FAZA 5 – Enterprise: SSO, portfolio, raporty zbiorcze (Miesiące 9–12)

**Cel:** obsługa organizacji enterprise z wieloma systemami AI.
Epiki: E6 + E7.

| # | Zadanie | Moduł | AI | Szac. dni |
|---|---------|-------|----|-----------|
| T5.1 | SSO: SAML 2.0 + OIDC (Okta, Azure AD) | auth_billing | ◑◑ | 5 |
| T5.2 | Biblioteka szablonów (8+ typów systemów AI) | annex_iv_core | ◑◑ | 5 |
| T5.3 | Crosswalk Annex IV ↔ ISO 42001 | annex_iv_core | ◑◑ | 4 |
| T5.4 | Generowanie AI Impact Assessment (AI IA) | ai_assistant | ◑◑ | 4 |
| T5.5 | Dashboard portfolio: lista systemów + heatmapa ryzyk | annex_iv_core | ◑◑ | 4 |
| T5.6 | Raport zbiorczy compliance (PDF/CSV) | exports | ◑◑ | 3 |
| T5.7 | Wewnętrzny dashboard metryk Foundera | - | ◑◑ | 3 |
| T5.8 | Hardening bezpieczeństwa (pen test, OWASP) | - | ◑ | 5 |
| T5.9 | SLA + DPA (Data Processing Agreement) dla enterprise | - | ✗ | 3 |
| T5.10 | Program partnerski (kancelarie, konsultanci compliance) | sprzedaż | ✗ | cały mies |

---

### FAZA 6 – Skalowanie i ekosystem (Miesiące 12–18)

**Cel:** marketplace integracji, inne reżimy regulacyjne, opcjonalnie: fundraising.

| # | Zadanie | Moduł | AI | Szac. dni |
|---|---------|-------|----|-----------|
| T6.1 | Connector SDK (open source) dla partnerów MLOps | integrations | ◑◑ | 10 |
| T6.2 | Integracja SageMaker + Azure ML | integrations | ◑◑ | 8 |
| T6.3 | Regulatory mapping: NIST AI RMF + Colorado AI Act | annex_iv_core | ◑◑ | 10 |
| T6.4 | Public API v1 (dla integratorów i enterprise) | - | ◑◑ | 10 |
| T6.5 | Listing w AWS / Azure Marketplace | sprzedaż | ✗ | 15 |
| T6.6 | Decyzja: bootstrap dalej vs. seed funding | biznes | ✗ | - |

---

## 6. Legenda

| Symbol | Znaczenie |
|--------|-----------|
| ◑◑ | AI-coding generuje 60–80% kodu (boilerplate, integracje, UI, testy) |
| ◑ | AI-coding wspiera 30–50% (logika domenowa, Ty projektujesz, AI implementuje) |
| ✗ | Nie można zautomatyzować – rozmowy, decyzje, sprzedaż, kontrakty |

---

## 7. Ryzyka i mitygacje

| Ryzyko | Prawdopodobieństwo | Wpływ | Mitygacja |
|--------|--------------------|-------|-----------|
| Mała adopcja – klienci nie doceniają wartości | Średnie | Wysoki | Discovery przed MVP; trial 14 dni; consult-led sales |
| Zmiana Annex IV (akt delegowany KE) | Niskie | Wysoki | Modułowy schema – update sekcji bez przepisywania całości |
| Konkurent (istniejący Annex IV tool) skaluje szybciej | Średnie | Średni | Fokus na niszę (fintech/HR), głębsze integracje MLOps |
| Jakość LLM-draftów nie spełnia oczekiwań | Średnie | Wysoki | Evals, user feedback loop, "draft" vs "approved" workflow |
| Dług techniczny z AI-coding | Średnie | Średni | Code review każdego AI-generated PR, testy E2E, arch. modularna |
| Nie trafiasz do decydenta (ML vs. Legal vs. Risk) | Średnie | Wysoki | Multi-persona onboarding; consult-led entry przez legal/compliance |

---

*Dokument: CompliAI PRD v1.0 | Kwiecień 2026*
