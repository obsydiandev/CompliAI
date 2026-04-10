"""Prompt templates for all 9 Annex IV sections.

Each template receives system metadata and (optionally) existing section content,
then returns a prompt string for the LLM.
"""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are an expert EU AI Act compliance specialist helping providers of high-risk AI systems
complete their Annex IV Technical File. You produce precise, regulatory-grade documentation
following the requirements of EU Regulation 2024/1689 (AI Act), especially Article 11 and
Annex IV. Your answers always cite the relevant article when applicable.
Write concisely, professionally, and in the same language as the user's existing content
(default: English). Do NOT invent metrics or data you are not given – instead describe
what should be documented and, where possible, give example templates.
"""

# ── Section-level prompt templates ────────────────────────────────────────────

SECTION_PROMPTS: dict[int, str] = {
    1: """\
Generate a draft for Section 1 (General Description) of the Annex IV Technical File.

AI System metadata:
- Name: {system_name}
- Description: {description}
- Intended purpose: {intended_purpose}
- Risk category: {category}
- Annex III classification: {annex_iii}

Fields to fill:
- intended_purpose: A clear, specific statement of what the system does and in which context it operates.
- responsible_persons: Name and contact details of the provider and authorised representative (Art. 11(1)).
- basic_characteristics: Key capabilities, modalities, input/output types.
- deployment_countries: EU member states where deployment is planned.

Existing content:
{existing_content}

Produce a JSON object with keys: intended_purpose, responsible_persons, basic_characteristics, deployment_countries.
For list fields return a JSON array of strings. Keep each value concise (max 300 words per field).
""",
    2: """\
Generate a draft for Section 2 (System Architecture & Technical Specifications) of the Annex IV Technical File.

AI System metadata:
- Name: {system_name}
- Description: {description}
- Intended purpose: {intended_purpose}

Fields to fill:
- system_architecture: High-level description of the overall design (Art. 11, Annex IV §2).
- algorithms_used: List of ML/AI algorithms, model types, and techniques employed.
- model_type: Primary model paradigm (e.g., transformer, ensemble, CNN).
- framework_and_tools: Libraries and frameworks used.
- hardware_requirements: Minimum compute specs for training and inference.

Existing content:
{existing_content}

Produce a JSON object with keys: system_architecture, algorithms_used (array), model_type, framework_and_tools (array), hardware_requirements.
""",
    3: """\
Generate a draft for Section 3 (Training Data & Methodology) of the Annex IV Technical File.

AI System metadata:
- Name: {system_name}
- Intended purpose: {intended_purpose}

Fields to fill:
- training_datasets: Dataset descriptions including size, format, provenance.
- data_collection_methodology: How data was collected and pre-processed (bias mitigation, balancing).
- data_governance: Data governance practices – quality assurance, access control, retention (GDPR alignment).
- validation_datasets: Validation split description.
- test_datasets: Hold-out test set description.
- known_data_limitations: Gaps, imbalances, or biases in training data.

Existing content:
{existing_content}

Produce a JSON object with keys: training_datasets, data_collection_methodology, data_governance, validation_datasets, test_datasets, known_data_limitations.
""",
    4: """\
Generate a draft for Section 4 (Performance Metrics & Benchmarks) of the Annex IV Technical File.

AI System metadata:
- Name: {system_name}
- Intended purpose: {intended_purpose}
- Risk category: {category}

Fields to fill:
- accuracy_metrics: Key performance metrics (accuracy, precision, recall, F1, AUC, etc.) and their values.
- benchmark_datasets: Standard benchmark datasets used for evaluation.
- performance_thresholds: Minimum acceptable performance thresholds for production deployment.
- known_limitations: Known failure modes, edge cases, performance degradation conditions.

Existing content:
{existing_content}

Produce a JSON object with keys: accuracy_metrics, benchmark_datasets (array), performance_thresholds, known_limitations.
""",
    5: """\
Generate a draft for Section 5 (Risk Management) of the Annex IV Technical File.

AI System metadata:
- Name: {system_name}
- Intended purpose: {intended_purpose}
- Risk category: {category}

Reference: AI Act Art. 9 (Risk management system), Art. 10 (Data governance).

Fields to fill:
- risk_identification: Catalogue of identified risks (technical, operational, societal) across the lifecycle.
- risk_assessment: Likelihood × severity matrix for each identified risk.
- mitigation_measures: Technical and organisational controls applied.
- residual_risks: Risks remaining after mitigation.
- risk_monitoring_process: Ongoing risk monitoring cadence and metrics.

Existing content:
{existing_content}

Produce a JSON object with keys: risk_identification, risk_assessment, mitigation_measures, residual_risks, risk_monitoring_process.
""",
    6: """\
Generate a draft for Section 6 (Human Oversight & Control) of the Annex IV Technical File.

AI System metadata:
- Name: {system_name}
- Intended purpose: {intended_purpose}

Reference: AI Act Art. 14 (Human oversight).

Fields to fill:
- oversight_mechanisms: Technical and procedural mechanisms enabling human oversight.
- human_intervention_points: Specific points in the process where humans can review/intervene.
- override_capabilities: How operators can correct, override, or shut down the system.
- operator_training_requirements: Training, qualifications, and competences required for operators.

Existing content:
{existing_content}

Produce a JSON object with keys: oversight_mechanisms, human_intervention_points, override_capabilities, operator_training_requirements.
""",
    7: """\
Generate a draft for Section 7 (Transparency & Explainability) of the Annex IV Technical File.

AI System metadata:
- Name: {system_name}
- Intended purpose: {intended_purpose}

Reference: AI Act Art. 13 (Transparency and provision of information to deployers).

Fields to fill:
- explainability_approach: Methods used to explain system decisions (XAI techniques: SHAP, LIME, attention, etc.).
- output_interpretation: How outputs should be interpreted, confidence levels, uncertainty.
- disclosure_mechanisms: How AI involvement is disclosed to affected persons (Art. 13(1)).
- instructions_for_use: Clear instructions for deployers on appropriate use, limitations, and misuse prevention.

Existing content:
{existing_content}

Produce a JSON object with keys: explainability_approach, output_interpretation, disclosure_mechanisms, instructions_for_use.
""",
    8: """\
Generate a draft for Section 8 (Cybersecurity & Robustness) of the Annex IV Technical File.

AI System metadata:
- Name: {system_name}
- Intended purpose: {intended_purpose}

Reference: AI Act Art. 15 (Accuracy, robustness and cybersecurity).

Fields to fill:
- security_measures: Technical controls protecting the system from unauthorised access and manipulation.
- adversarial_robustness: Measures against adversarial inputs, data poisoning, model inversion attacks.
- incident_response: Incident response and breach notification procedure.
- backup_and_recovery: Backup strategy and recovery time objectives.
- penetration_testing: Summary of security testing conducted and findings.

Existing content:
{existing_content}

Produce a JSON object with keys: security_measures, adversarial_robustness, incident_response, backup_and_recovery, penetration_testing.
""",
    9: """\
Generate a draft for Section 9 (Post-Market Monitoring & Incident Reporting) of the Annex IV Technical File.

AI System metadata:
- Name: {system_name}
- Intended purpose: {intended_purpose}

Reference: AI Act Art. 72 (Post-market monitoring), Art. 73 (Reporting of serious incidents).

Fields to fill:
- monitoring_plan: Post-market monitoring plan specifying data collection, analysis, and reporting cycle.
- performance_indicators: KPIs tracked post-deployment (drift metrics, error rates, user complaints, etc.).
- incident_reporting_process: Process for identifying, documenting, and reporting serious incidents to the market
  surveillance authority within the required timeframe (Art. 73).
- feedback_mechanisms: Channels for collecting feedback from deployers and affected persons.
- update_and_retraining_policy: Criteria and process for model updates and retraining.

Existing content:
{existing_content}

Produce a JSON object with keys: monitoring_plan, performance_indicators (array), incident_reporting_process, feedback_mechanisms, update_and_retraining_policy.
""",
}

# ── Documentation diff prompt ──────────────────────────────────────────────────

DOC_DIFF_PROMPT = """\
You are an EU AI Act compliance expert. A high-risk AI system's metadata has changed.
Analyse which sections of the Annex IV Technical File need to be updated and why.

AI System: {system_name}

Previous state:
{previous_metadata}

New state:
{new_metadata}

For each section that requires updating, provide:
1. Section number and name
2. Why it needs updating (cite the changed field)
3. A brief draft of the key changes needed

Return a JSON array of objects with keys: section_number, section_name, reason, draft_changes.
Focus only on sections genuinely affected by the changes.
"""

# ── User Instructions (Art. 13) prompt ────────────────────────────────────────

USER_INSTRUCTIONS_PROMPT = """\
Generate a plain-language "Instructions for Use" document for an EU AI Act high-risk AI system,
as required by Article 13 of EU Regulation 2024/1689.

AI System metadata:
- Name: {system_name}
- Intended purpose: {intended_purpose}
- Risk category: {category}

Section 7 content (Transparency):
{section_7_content}

Section 6 content (Human Oversight):
{section_6_content}

Section 5 content (Risk Management):
{section_5_content}

The document must cover (Art. 13(3)):
a) Identity and contact details of the provider
b) Characteristics, capabilities and limitations
c) Any known or foreseeable circumstances that may lead to risks
d) Performance metrics and relevant accuracy levels
e) Human oversight measures (Art. 14)
f) Expected lifetime and maintenance/updating measures

Write in clear, non-technical language suitable for deployers and end users.
Return a structured Markdown document with sections matching Art. 13(3) requirements.
"""

# ── Q&A system prompt ──────────────────────────────────────────────────────────

QA_SYSTEM_PROMPT = """\
You are a compliance assistant for the EU AI Act. You have access to the Technical File
sections of a high-risk AI system. Answer the user's question accurately and concisely,
citing the specific section and field where you found the information.

If the answer is not in the provided context, say so clearly and suggest which section
should contain the relevant information.
"""

QA_USER_PROMPT = """\
Context from the Technical File:
{context}

Question: {question}

Provide a precise answer with citations to the section(s) you used.
"""

# ── Inline suggestions prompt ──────────────────────────────────────────────────

SUGGESTIONS_PROMPT = """\
You are reviewing Section {section_number} ({section_name}) of an EU AI Act Annex IV Technical File.

Current content:
{current_content}

Missing required fields: {missing_fields}

For each missing field, provide a brief, actionable suggestion (1-2 sentences) explaining
what information should be added and why it is required under the AI Act.

Return a JSON object where keys are field names and values are suggestion strings.
"""
