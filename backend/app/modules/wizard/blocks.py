"""Wizard block definitions for the Lite Quick-Start Wizard (Epic 0).

7 blocks covering all Annex IV sections, 30–50 questions total.
Each question maps to a specific Annex IV section and field.
"""

from __future__ import annotations

from dataclasses import dataclass, field

WIZARD_DISCLAIMER = (
    "Technical File Completion % means structural completeness only — "
    "this document requires legal and ML Lead review before submission "
    "to any supervisory authority."
)


@dataclass
class WizardQuestion:
    id: str
    text: str
    type: str  # "text" | "textarea" | "select" | "boolean" | "multiselect"
    options: list[str] = field(default_factory=list)
    placeholder: str = ""
    why_asking: str = ""
    article_ref: str = ""
    annex_iv_section: int = 1
    annex_iv_field: str = ""
    required: bool = True


@dataclass
class WizardBlock:
    id: str          # "B1" … "B7"
    number: int
    title: str
    description: str
    questions: list[WizardQuestion]
    annex_iv_sections: list[int]  # which Annex IV sections this block feeds


WIZARD_BLOCKS: list[WizardBlock] = [
    # ── Block 1: System identification & intended purpose ──────────────────
    WizardBlock(
        id="B1",
        number=1,
        title="System Identification & Purpose",
        description="Basic information about your AI system and what it is designed to do.",
        annex_iv_sections=[1],
        questions=[
            WizardQuestion(
                id="B1Q1",
                text="What is the official name of your AI system?",
                type="text",
                placeholder="e.g. 'CreditScore AI v2.0'",
                why_asking="The AI Act requires a unique identifier for each system in technical documentation.",
                article_ref="Annex IV §1(a)",
                annex_iv_section=1,
                annex_iv_field="system_name",
            ),
            WizardQuestion(
                id="B1Q2",
                text="What version is this documentation for?",
                type="text",
                placeholder="e.g. 'v2.0', '2024-Q4'",
                why_asking="Version tracking is mandatory under Art. 11(2) for material changes.",
                article_ref="Art. 11(2) AI Act",
                annex_iv_section=1,
                annex_iv_field="version",
            ),
            WizardQuestion(
                id="B1Q3",
                text="Describe the intended purpose of your AI system in 2–4 sentences. "
                     "What problem does it solve and who uses it?",
                type="textarea",
                placeholder="e.g. 'This system predicts credit default risk for retail banking customers…'",
                why_asking="The intended purpose defines the scope of the Annex IV obligations. "
                           "Be specific — over-broad definitions can trigger higher-risk classification.",
                article_ref="Annex IV §1(b) + Art. 6",
                annex_iv_section=1,
                annex_iv_field="intended_purpose",
            ),
            WizardQuestion(
                id="B1Q4",
                text="Who are the end-users of this system? (e.g. bank loan officers, HR teams, patients)",
                type="text",
                placeholder="e.g. 'Loan officers at retail banks'",
                why_asking="Art. 13 requires transparency information targeted at specific user groups.",
                article_ref="Art. 13 AI Act",
                annex_iv_section=1,
                annex_iv_field="end_users",
            ),
            WizardQuestion(
                id="B1Q5",
                text="In which EU member states or countries is the system deployed?",
                type="text",
                placeholder="e.g. 'Germany, Poland, EU-wide'",
                why_asking="Territorial scope affects which national supervisory authority has jurisdiction.",
                article_ref="Art. 2 AI Act",
                annex_iv_section=1,
                annex_iv_field="deployment_countries",
            ),
        ],
    ),
    # ── Block 2: Architecture & data ───────────────────────────────────────
    WizardBlock(
        id="B2",
        number=2,
        title="Architecture, Inputs & Training Data",
        description="Describe how your AI system works and what data it uses.",
        annex_iv_sections=[2, 3],
        questions=[
            WizardQuestion(
                id="B2Q1",
                text="What type of AI/ML approach does your system use?",
                type="select",
                options=[
                    "Supervised machine learning (classification/regression)",
                    "Unsupervised learning / clustering",
                    "Deep learning / neural network",
                    "Large language model (LLM) / generative AI",
                    "Rule-based / expert system",
                    "Reinforcement learning",
                    "Hybrid (ML + rules)",
                    "Other",
                ],
                why_asking="Annex IV §2 requires a description of the system architecture and type.",
                article_ref="Annex IV §2(a)",
                annex_iv_section=2,
                annex_iv_field="architecture_type",
            ),
            WizardQuestion(
                id="B2Q2",
                text="Describe the input data your system receives (type, format, source).",
                type="textarea",
                placeholder="e.g. 'Structured tabular data: age, income, credit history from core banking system'",
                why_asking="Regulators need to understand what data the system processes to assess bias and data quality risks.",
                article_ref="Annex IV §2(b) + Art. 10",
                annex_iv_section=2,
                annex_iv_field="input_data_description",
            ),
            WizardQuestion(
                id="B2Q3",
                text="What was the training data? Describe size, source, and time period.",
                type="textarea",
                placeholder="e.g. '500,000 loan applications from 2019–2023, sourced from internal CRM'",
                why_asking="Art. 10 requires documentation of training datasets including origin, scope, and characteristics.",
                article_ref="Art. 10 + Annex IV §3",
                annex_iv_section=3,
                annex_iv_field="training_data_description",
            ),
            WizardQuestion(
                id="B2Q4",
                text="Were any data pre-processing steps applied? (e.g. normalisation, balancing, filtering)",
                type="textarea",
                placeholder="e.g. 'SMOTE oversampling for minority class; outlier removal via IQR'",
                why_asking="Data processing decisions affect model behaviour and must be documented for auditors.",
                article_ref="Annex IV §3(b)",
                annex_iv_section=3,
                annex_iv_field="data_preprocessing",
            ),
            WizardQuestion(
                id="B2Q5",
                text="Does the training data include any personal data or special categories of data "
                     "(e.g. health, ethnicity, religion)?",
                type="boolean",
                why_asking="Special category data triggers GDPR Art. 9 requirements and heightens AI Act scrutiny.",
                article_ref="GDPR Art. 9 + AI Act Art. 10(5)",
                annex_iv_section=3,
                annex_iv_field="uses_special_category_data",
            ),
            WizardQuestion(
                id="B2Q6",
                text="What steps were taken to ensure the training data is representative, "
                     "free from bias, and of sufficient quality?",
                type="textarea",
                placeholder="e.g. 'Geographic and demographic stratification; fairness audit by external firm'",
                why_asking="Art. 10(2)(f) requires documentation of data quality measures and bias mitigation.",
                article_ref="Art. 10(2)(f) AI Act",
                annex_iv_section=3,
                annex_iv_field="data_quality_measures",
            ),
            WizardQuestion(
                id="B2Q7",
                text="Where is the AI system hosted / deployed? (cloud provider, on-premise, hybrid)",
                type="text",
                placeholder="e.g. 'AWS eu-central-1 (Frankfurt), containerised in EKS'",
                why_asking="Infrastructure information supports data residency and security assessments.",
                article_ref="Annex IV §2(c)",
                annex_iv_section=2,
                annex_iv_field="infrastructure",
            ),
            WizardQuestion(
                id="B2Q8",
                text="What other software systems does the AI system integrate with or depend on?",
                type="textarea",
                placeholder="e.g. 'Core banking API, Salesforce CRM, internal identity service'",
                why_asking="Annex IV requires documentation of system dependencies and integration points.",
                article_ref="Annex IV §2(d)",
                annex_iv_section=2,
                annex_iv_field="system_integrations",
            ),
        ],
    ),
    # ── Block 3: Validation, accuracy & testing ────────────────────────────
    WizardBlock(
        id="B3",
        number=3,
        title="Validation, Accuracy & Testing",
        description="How was your model tested and what are its accuracy metrics?",
        annex_iv_sections=[4],
        questions=[
            WizardQuestion(
                id="B3Q1",
                text="What are the primary performance metrics for your system? "
                     "(e.g. accuracy, AUC-ROC, F1, precision, recall)",
                type="textarea",
                placeholder="e.g. 'AUC-ROC: 0.82 on holdout set; F1: 0.74; accuracy: 87%'",
                why_asking="Art. 15 requires documentation of accuracy, robustness, and cybersecurity levels.",
                article_ref="Art. 15 + Annex IV §4(a)",
                annex_iv_section=4,
                annex_iv_field="performance_metrics",
            ),
            WizardQuestion(
                id="B3Q2",
                text="Describe the validation methodology used to evaluate the model.",
                type="textarea",
                placeholder="e.g. 'k-fold cross-validation (k=5) + separate holdout set (20%)…'",
                why_asking="Auditors need to understand how model performance was measured and validated.",
                article_ref="Annex IV §4(b)",
                annex_iv_section=4,
                annex_iv_field="validation_methodology",
            ),
            WizardQuestion(
                id="B3Q3",
                text="Were fairness or bias tests conducted? If yes, describe the approach and results.",
                type="textarea",
                placeholder="e.g. 'Demographic parity tested across gender and age groups; max 3pp disparity'",
                why_asking="Art. 10(2)(f) and Art. 9 require bias risk identification and mitigation evidence.",
                article_ref="Art. 10(2)(f) + Art. 9 AI Act",
                annex_iv_section=4,
                annex_iv_field="bias_testing",
            ),
            WizardQuestion(
                id="B3Q4",
                text="What edge cases or failure modes have been identified and tested?",
                type="textarea",
                placeholder="e.g. 'Model performs poorly on thin-file applicants with <6 months credit history'",
                why_asking="Risk management (Art. 9) requires identification and documentation of known limitations.",
                article_ref="Art. 9(2)(b)",
                annex_iv_section=4,
                annex_iv_field="known_limitations",
            ),
            WizardQuestion(
                id="B3Q5",
                text="Have third-party audits or external testing been conducted?",
                type="textarea",
                placeholder="e.g. 'External bias audit by Fairlearn GmbH, March 2024'",
                why_asking="Third-party validation strengthens conformity assessment evidence.",
                article_ref="Art. 43 AI Act",
                annex_iv_section=4,
                annex_iv_field="third_party_testing",
                required=False,
            ),
            WizardQuestion(
                id="B3Q6",
                text="What cybersecurity measures protect the AI system from adversarial attacks?",
                type="textarea",
                placeholder="e.g. 'Input validation, adversarial robustness testing (FGSM), access controls'",
                why_asking="Art. 15(5) requires cybersecurity measures proportionate to the risk level.",
                article_ref="Art. 15(5) AI Act",
                annex_iv_section=4,
                annex_iv_field="cybersecurity_measures",
            ),
        ],
    ),
    # ── Block 4: Risk management ───────────────────────────────────────────
    WizardBlock(
        id="B4",
        number=4,
        title="Risk Management",
        description="How do you identify, assess, and mitigate risks from your AI system?",
        annex_iv_sections=[6],
        questions=[
            WizardQuestion(
                id="B4Q1",
                text="Describe the risk management process for this AI system. "
                     "Who is responsible and how often is it reviewed?",
                type="textarea",
                placeholder="e.g. 'Quarterly risk review by ML Lead + Compliance Officer using internal risk register'",
                why_asking="Art. 9 requires a continuous risk management system throughout the lifecycle.",
                article_ref="Art. 9(1) AI Act",
                annex_iv_section=6,
                annex_iv_field="risk_management_process",
            ),
            WizardQuestion(
                id="B4Q2",
                text="What are the most significant risks identified for this system? "
                     "(e.g. false negatives that deny credit to eligible applicants)",
                type="textarea",
                placeholder="e.g. 'Risk 1: Systemic bias against underrepresented groups…'",
                why_asking="Art. 9(2) requires identification and analysis of foreseeable risks.",
                article_ref="Art. 9(2) AI Act",
                annex_iv_section=6,
                annex_iv_field="identified_risks",
            ),
            WizardQuestion(
                id="B4Q3",
                text="What measures have been put in place to eliminate or reduce these risks?",
                type="textarea",
                placeholder="e.g. 'Manual review for borderline cases; appeal process; periodic retraining'",
                why_asking="Art. 9(2)(d) requires documentation of risk elimination and mitigation measures.",
                article_ref="Art. 9(2)(d) AI Act",
                annex_iv_section=6,
                annex_iv_field="risk_mitigation_measures",
            ),
            WizardQuestion(
                id="B4Q4",
                text="What residual risks remain after mitigation, and how are they monitored?",
                type="textarea",
                placeholder="e.g. 'Residual bias risk: monitored via monthly demographic parity reports'",
                why_asking="Art. 9(4) requires documentation of residual risks and how they are managed.",
                article_ref="Art. 9(4) AI Act",
                annex_iv_section=6,
                annex_iv_field="residual_risks",
            ),
            WizardQuestion(
                id="B4Q5",
                text="Has this system been tested against real-world conditions before deployment? "
                     "Describe any pre-deployment testing or pilots.",
                type="textarea",
                placeholder="e.g. 'Shadow mode pilot for 3 months; 500 real applications used for validation'",
                why_asking="Art. 9(3) requires real-world testing before deployment.",
                article_ref="Art. 9(3) AI Act",
                annex_iv_section=6,
                annex_iv_field="real_world_testing",
            ),
            WizardQuestion(
                id="B4Q6",
                text="Are there any conflict-of-interest policies for teams developing or reviewing this system?",
                type="textarea",
                placeholder="e.g. 'Model developers excluded from model approval committee'",
                why_asking="Good governance requires separation of duties in risk management.",
                article_ref="Art. 9(6) AI Act",
                annex_iv_section=6,
                annex_iv_field="conflict_of_interest_policy",
                required=False,
            ),
            WizardQuestion(
                id="B4Q7",
                text="Who is the person/team responsible for the AI system (AI system owner)?",
                type="text",
                placeholder="e.g. 'Head of Data Science — Jan Kowalski (jan@company.com)'",
                why_asking="Art. 3(23) requires identification of the provider responsible for the system.",
                article_ref="Art. 3(23) AI Act",
                annex_iv_section=6,
                annex_iv_field="system_owner",
            ),
        ],
    ),
    # ── Block 5: Human oversight ──────────────────────────────────────────
    WizardBlock(
        id="B5",
        number=5,
        title="Human Oversight & Control",
        description="How do humans monitor and control the AI system's decisions?",
        annex_iv_sections=[5],
        questions=[
            WizardQuestion(
                id="B5Q1",
                text="Can the AI system be overridden or its output rejected by a human operator?",
                type="boolean",
                why_asking="Art. 14 requires that high-risk AI systems allow human override.",
                article_ref="Art. 14(4)(e) AI Act",
                annex_iv_section=5,
                annex_iv_field="human_override_capability",
            ),
            WizardQuestion(
                id="B5Q2",
                text="Describe the human-in-the-loop process. At what point do humans review "
                     "or validate the AI's outputs?",
                type="textarea",
                placeholder="e.g. 'All high-risk decisions (>€50k credit) reviewed by senior analyst before final approval'",
                why_asking="Art. 14 requires meaningful human oversight proportionate to the risk level.",
                article_ref="Art. 14(1) AI Act",
                annex_iv_section=5,
                annex_iv_field="human_oversight_process",
            ),
            WizardQuestion(
                id="B5Q3",
                text="What training or qualifications are required for human operators of this system?",
                type="textarea",
                placeholder="e.g. 'Mandatory 4h training on AI outputs; annual certification renewal'",
                why_asking="Art. 14(5) requires operators to understand the system's capabilities and limitations.",
                article_ref="Art. 14(5) AI Act",
                annex_iv_section=5,
                annex_iv_field="operator_training",
            ),
            WizardQuestion(
                id="B5Q4",
                text="How are human operators notified when the system's confidence is low or "
                     "when it operates outside its normal parameters?",
                type="textarea",
                placeholder="e.g. 'Confidence score <70% triggers orange flag in UI; operator must add manual note'",
                why_asking="Art. 14(4)(c) requires adequate information about the system's operational status.",
                article_ref="Art. 14(4)(c) AI Act",
                annex_iv_section=5,
                annex_iv_field="low_confidence_notification",
            ),
            WizardQuestion(
                id="B5Q5",
                text="Is there a 'stop button' or emergency shutdown procedure for the system?",
                type="textarea",
                placeholder="e.g. 'Emergency kill switch available to CTO; activates manual review queue'",
                why_asking="Art. 14(4)(e) requires the ability to halt the system.",
                article_ref="Art. 14(4)(e) AI Act",
                annex_iv_section=5,
                annex_iv_field="emergency_shutdown",
            ),
        ],
    ),
    # ── Block 6: Post-market monitoring ───────────────────────────────────
    WizardBlock(
        id="B6",
        number=6,
        title="Post-Market Monitoring",
        description="How will you monitor the system after deployment?",
        annex_iv_sections=[7],
        questions=[
            WizardQuestion(
                id="B6Q1",
                text="What metrics will you monitor in production to detect model drift or "
                     "performance degradation?",
                type="textarea",
                placeholder="e.g. 'Monthly: approval rate, default rate, demographic parity index; quarterly: AUC-ROC'",
                why_asking="Art. 72 (formerly Art. 61) requires a post-market monitoring plan with specific metrics.",
                article_ref="Art. 72 AI Act",
                annex_iv_section=7,
                annex_iv_field="monitoring_metrics",
            ),
            WizardQuestion(
                id="B6Q2",
                text="How often will the model be retrained or updated?",
                type="text",
                placeholder="e.g. 'Quarterly retraining; major update if AUC drops >5%'",
                why_asking="Art. 72 requires documentation of how and when the system will be updated.",
                article_ref="Art. 72 AI Act",
                annex_iv_section=7,
                annex_iv_field="update_frequency",
            ),
            WizardQuestion(
                id="B6Q3",
                text="What is the process for reporting serious incidents involving this AI system?",
                type="textarea",
                placeholder="e.g. 'Serious incidents reported to national market surveillance authority within 15 working days'",
                why_asking="Art. 73 requires providers to report serious incidents to national authorities.",
                article_ref="Art. 73 AI Act",
                annex_iv_section=7,
                annex_iv_field="incident_reporting_process",
            ),
            WizardQuestion(
                id="B6Q4",
                text="How do affected persons (e.g. loan applicants) receive information about "
                     "AI-assisted decisions and how can they challenge them?",
                type="textarea",
                placeholder="e.g. 'Disclosure notice sent with decision letter; appeal via customer service'",
                why_asking="Art. 13 + GDPR Art. 22 give affected persons rights regarding automated decisions.",
                article_ref="Art. 13 AI Act + GDPR Art. 22",
                annex_iv_section=7,
                annex_iv_field="affected_persons_rights",
            ),
        ],
    ),
    # ── Block 7: Standards & compliance ───────────────────────────────────
    WizardBlock(
        id="B7",
        number=7,
        title="Standards, Norms & Certification",
        description="Technical standards and certifications applicable to your system.",
        annex_iv_sections=[8, 9],
        questions=[
            WizardQuestion(
                id="B7Q1",
                text="Does your system comply with any harmonised technical standards? "
                     "(e.g. ISO/IEC 42001, ISO/IEC 27001, IEC 61508)",
                type="textarea",
                placeholder="e.g. 'ISO/IEC 27001 certified (cert no. 12345); ISO/IEC 42001 in progress'",
                why_asking="Art. 8 of the AI Act grants presumption of conformity for harmonised standards.",
                article_ref="Art. 8 + Annex VIII AI Act",
                annex_iv_section=8,
                annex_iv_field="applicable_standards",
            ),
            WizardQuestion(
                id="B7Q2",
                text="Has the system been certified by a third-party notified body or "
                     "conformity assessment body?",
                type="boolean",
                why_asking="Art. 43 requires third-party conformity assessment for certain high-risk categories.",
                article_ref="Art. 43 AI Act",
                annex_iv_section=8,
                annex_iv_field="third_party_certification",
            ),
            WizardQuestion(
                id="B7Q3",
                text="What other EU regulations apply to this system? "
                     "(e.g. GDPR, MDR, Machinery Directive)",
                type="textarea",
                placeholder="e.g. 'GDPR (credit decision processing); EBA guidelines on credit risk models'",
                why_asking="Annex IV §8 requires documentation of all applicable EU legal requirements.",
                article_ref="Annex IV §8 AI Act",
                annex_iv_section=8,
                annex_iv_field="other_applicable_regulations",
            ),
            WizardQuestion(
                id="B7Q4",
                text="Enter the legal name and registered address of the provider (your company) "
                     "for the EU Declaration of Conformity.",
                type="textarea",
                placeholder="e.g. 'ACME Financial Technologies Sp. z o.o., ul. Marszałkowska 1, 00-001 Warsaw, Poland'",
                why_asking="Annex V requires the provider's legal identity in the Declaration of Conformity.",
                article_ref="Art. 47 + Annex V AI Act",
                annex_iv_section=9,
                annex_iv_field="provider_legal_name",
            ),
            WizardQuestion(
                id="B7Q5",
                text="Provide the name and contact details of your EU Authorised Representative "
                     "(required if provider is established outside the EU).",
                type="textarea",
                placeholder="e.g. 'Not applicable — provider established in Poland (EU)'",
                why_asking="Art. 22 requires non-EU providers to designate an EU Authorised Representative.",
                article_ref="Art. 22 AI Act",
                annex_iv_section=9,
                annex_iv_field="eu_authorised_representative",
                required=False,
            ),
        ],
    ),
]

WIZARD_BLOCKS_BY_ID: dict[str, WizardBlock] = {b.id: b for b in WIZARD_BLOCKS}
TOTAL_QUESTIONS: int = sum(len(b.questions) for b in WIZARD_BLOCKS)


def calculate_completion_percent(answers: dict) -> float:
    """Calculate Technical File Completion % based on answered questions.

    NOTE: This is NOT 'Compliance Score' — it measures structural completeness only.
    Per PRD v1.15 Section 1.4: use 'Technical File Completion %' in Lite, never 'Compliance'.
    """
    required_questions = [
        q for block in WIZARD_BLOCKS for q in block.questions if q.required
    ]
    if not required_questions:
        return 0.0

    answered = 0
    for block in WIZARD_BLOCKS:
        block_answers = answers.get(block.id, {})
        for q in block.questions:
            if not q.required:
                continue
            val = block_answers.get(q.id)
            if val is not None and str(val).strip():
                answered += 1

    return round(answered / len(required_questions) * 100, 1)
