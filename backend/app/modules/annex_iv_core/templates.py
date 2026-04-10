"""Pre-filled Annex IV templates for common AI system types."""

TEMPLATES: dict[str, dict] = {
    "healthcare_diagnostic": {
        "general_information": {
            "system_name": "Healthcare Diagnostic AI System",
            "version": "1.0.0",
            "purpose": "AI-powered diagnostic assistance for medical imaging and patient data analysis to support clinical decision-making.",
            "developer": "Healthcare AI Solutions Ltd.",
            "deployment_date": "2024-01-01",
        },
        "intended_purpose": {
            "use_cases": ["Medical image analysis", "Patient risk stratification", "Clinical decision support"],
            "target_users": ["Licensed physicians", "Radiologists", "Clinical staff"],
            "geographic_scope": "European Union member states",
            "prohibited_uses": "Must not be used as sole basis for diagnosis without physician review. Not for emergency triage without human oversight.",
        },
        "technical_specifications": {
            "model_architecture": "Convolutional Neural Network (ResNet-50) with transformer attention layers for multi-modal data fusion.",
            "input_types": ["DICOM medical images", "Patient EHR data", "Lab results"],
            "output_types": ["Diagnostic probability scores", "Region-of-interest annotations", "Risk classification"],
            "performance_metrics": "AUC-ROC: 0.94, Sensitivity: 91%, Specificity: 93%, F1-Score: 0.92",
            "hardware_requirements": "NVIDIA A100 GPU, 64GB RAM, 2TB SSD storage",
        },
        "training_data": {
            "data_sources": ["Anonymized patient records from 5 EU hospitals", "Public medical imaging datasets (NIH ChestX-ray14)"],
            "data_preprocessing": "DICOM normalization, patient anonymization per GDPR, data augmentation (rotation, flipping, contrast adjustment)",
            "data_quality_measures": "IRB approval obtained, bias assessment across age/gender/ethnicity groups, expert radiologist validation",
            "training_methodology": "Supervised learning with 80/10/10 train/val/test split, 5-fold cross-validation, transfer learning from ImageNet",
        },
        "testing_and_validation": {
            "test_datasets": ["Independent validation cohort (n=5000)", "Prospective clinical trial data"],
            "evaluation_metrics": ["AUC-ROC", "Sensitivity", "Specificity", "PPV", "NPV", "Calibration"],
            "performance_results": "AUC-ROC 0.94 on holdout test set. Outperforms average radiologist on early-stage detection.",
            "known_limitations": "Performance may degrade on imaging equipment not represented in training data. Validated for adults 18+.",
        },
        "human_oversight": {
            "oversight_mechanisms": "All outputs require physician review before clinical action. Mandatory second-opinion workflow for high-risk findings.",
            "human_intervention_points": ["Pre-diagnosis review", "Uncertain prediction escalation", "Patient complaint handling"],
            "roles_responsibilities": "Radiologist: final diagnostic authority. IT Admin: system monitoring. Clinical governance team: periodic audits.",
        },
        "cybersecurity": {
            "security_measures": "End-to-end encryption (AES-256), secure API gateway, audit logging, penetration testing quarterly",
            "access_controls": "Role-based access control (RBAC), multi-factor authentication, session timeout policies",
            "vulnerability_assessments": "Annual third-party security audit, CVE monitoring, automated dependency scanning",
            "incident_response": "24-hour incident response team, GDPR breach notification procedures, system isolation protocols",
        },
        "transparency": {
            "explainability_methods": "Grad-CAM visualization for image highlights, SHAP values for feature importance, plain-language explanations",
            "user_information": "Patient information sheet provided. Clinician training materials available. System limitations clearly communicated.",
            "logging_monitoring": "All predictions logged with timestamps, model version, and input hash. Audit trail retained for 10 years.",
        },
        "post_market_monitoring": {
            "monitoring_plan": "Continuous performance monitoring with quarterly reports. Annual revalidation against clinical outcomes.",
            "feedback_mechanisms": "Clinician feedback portal, adverse event reporting system, patient complaint channel",
            "update_procedures": "Major updates require re-validation and notified body review. Minor updates follow change control process.",
            "incident_reporting": "Serious incidents reported to national competent authority within 15 days per MDR Article 87.",
        },
    },
    "financial_credit_scoring": {
        "general_information": {
            "system_name": "AI Credit Scoring System",
            "version": "2.1.0",
            "purpose": "Automated credit risk assessment for loan applications using machine learning to predict default probability.",
            "developer": "FinTech Analytics GmbH",
            "deployment_date": "2024-03-01",
        },
        "intended_purpose": {
            "use_cases": ["Personal loan assessment", "Mortgage eligibility", "Credit card applications"],
            "target_users": ["Bank loan officers", "Automated underwriting systems", "Credit analysts"],
            "geographic_scope": "Germany, Austria, Switzerland",
            "prohibited_uses": "Must not discriminate based on protected characteristics. Cannot be used for insurance premium calculation.",
        },
        "technical_specifications": {
            "model_architecture": "Gradient Boosting Machine (XGBoost) with feature engineering pipeline and calibration layer.",
            "input_types": ["Credit bureau data", "Bank transaction history", "Application form data"],
            "output_types": ["Credit score (0-1000)", "Default probability", "Risk tier classification", "Explanation report"],
            "performance_metrics": "Gini coefficient: 0.68, KS statistic: 0.45, AUC: 0.84, PSI < 0.1",
            "hardware_requirements": "Standard server infrastructure, 16 vCPUs, 32GB RAM",
        },
        "training_data": {
            "data_sources": ["Historical loan portfolio (3M+ accounts)", "Credit bureau data", "Open banking transaction data"],
            "data_preprocessing": "Missing value imputation, outlier treatment (Winsorization), WoE transformation for categorical variables",
            "data_quality_measures": "Data lineage tracking, temporal validation to prevent look-ahead bias, fairness testing across demographic groups",
            "training_methodology": "Supervised learning on 5-year historical data, time-series cross-validation, champion-challenger framework",
        },
        "testing_and_validation": {
            "test_datasets": ["Out-of-time validation (most recent 12 months)", "Stress test scenarios"],
            "evaluation_metrics": ["Gini coefficient", "KS statistic", "PSI", "Fairness metrics (demographic parity)"],
            "performance_results": "Model meets all regulatory performance thresholds. Bias testing shows no adverse impact ratios > 0.8.",
            "known_limitations": "Performance degrades during economic shocks. Requires monitoring of population stability.",
        },
        "human_oversight": {
            "oversight_mechanisms": "Borderline cases reviewed by credit officer. Adverse action notices provided to all rejected applicants.",
            "human_intervention_points": ["Score band boundaries", "Fraud flag review", "Customer dispute resolution"],
            "roles_responsibilities": "Credit risk manager: model oversight. Compliance officer: regulatory reporting. Data scientist: monitoring.",
        },
        "cybersecurity": {
            "security_measures": "ISO 27001 certified infrastructure, data at rest encryption, API rate limiting, DDoS protection",
            "access_controls": "Privileged access management, quarterly access reviews, read-only production access for analysts",
            "vulnerability_assessments": "Bi-annual penetration testing, OWASP compliance checks, vendor security assessments",
            "incident_response": "SOC 24/7 monitoring, incident playbooks, regulatory notification procedures per GDPR",
        },
        "transparency": {
            "explainability_methods": "SHAP values for top contributing factors, reason codes for adverse actions, simplified explanations for customers",
            "user_information": "Credit decision explanation letters, right to human review, right to contest automated decisions",
            "logging_monitoring": "All scoring requests logged, model version tracking, decision audit trail for 7 years",
        },
        "post_market_monitoring": {
            "monitoring_plan": "Monthly PSI monitoring, quarterly performance reports, annual model validation by independent team",
            "feedback_mechanisms": "Default outcome feedback loop, customer complaint analysis, regulatory examination support",
            "update_procedures": "Model changes require risk committee approval and SR 11-7 compliance. Emergency procedures for drift.",
            "incident_reporting": "Material model risk events reported to CRO within 24 hours and to regulator as required.",
        },
    },
    "hr_recruitment": {
        "general_information": {
            "system_name": "AI Recruitment Screening System",
            "version": "1.5.0",
            "purpose": "Automated CV screening and candidate ranking to assist HR professionals in identifying qualified candidates.",
            "developer": "TalentAI Solutions B.V.",
            "deployment_date": "2024-02-15",
        },
        "intended_purpose": {
            "use_cases": ["CV screening", "Skills matching", "Interview scheduling", "Candidate ranking"],
            "target_users": ["HR managers", "Recruiters", "Hiring managers"],
            "geographic_scope": "Netherlands, Belgium, Luxembourg",
            "prohibited_uses": "Must not be used as sole hiring decision maker. Cannot screen based on protected characteristics.",
        },
        "technical_specifications": {
            "model_architecture": "BERT-based NLP model for CV parsing with skills ontology matching and semantic similarity scoring.",
            "input_types": ["CV/Resume documents (PDF, DOCX)", "Job descriptions", "Structured application forms"],
            "output_types": ["Candidate suitability score", "Skills gap analysis", "Ranking list", "Recommendation flags"],
            "performance_metrics": "Precision@10: 0.78, Recall@10: 0.72, NDCG: 0.81, Bias audit pass rate: 98%",
            "hardware_requirements": "4 vCPUs, 16GB RAM, GPU optional for batch processing",
        },
        "training_data": {
            "data_sources": ["Anonymized historical hiring data", "Public job market datasets", "LinkedIn Skills taxonomy"],
            "data_preprocessing": "PII removal, demographic data exclusion, text normalization, language detection and translation",
            "data_quality_measures": "Bias testing across gender/age/nationality, fairness constraints in training objective, diverse annotation team",
            "training_methodology": "Fine-tuned BERT on recruitment domain, adversarial debiasing, human-in-the-loop feedback integration",
        },
        "testing_and_validation": {
            "test_datasets": ["Holdout historical dataset", "Synthetic diverse candidate pool", "A/B test against manual screening"],
            "evaluation_metrics": ["Ranking quality (NDCG)", "Disparate impact ratio", "Precision/Recall", "Time-to-hire improvement"],
            "performance_results": "20% improvement in hiring quality metrics. No adverse impact found across protected groups in blind audit.",
            "known_limitations": "May underperform for highly specialized roles with limited training examples. Requires regular bias re-auditing.",
        },
        "human_oversight": {
            "oversight_mechanisms": "All final hiring decisions made by humans. System provides recommendations, not decisions.",
            "human_intervention_points": ["Final candidate selection", "Feedback on recommendations", "Bias alert investigation"],
            "roles_responsibilities": "HR Director: system governance. Recruiter: daily operation. Ethics committee: quarterly bias review.",
        },
        "cybersecurity": {
            "security_measures": "GDPR-compliant data handling, candidate data isolation, secure file processing pipeline",
            "access_controls": "HR-only data access, candidate data pseudonymization, consent management system",
            "vulnerability_assessments": "Annual security review, secure coding practices, dependency vulnerability scanning",
            "incident_response": "Data breach procedures per GDPR Art. 33, candidate notification protocols, DPA reporting",
        },
        "transparency": {
            "explainability_methods": "Skills matching explanation, top ranking factors shown to recruiters, candidate feedback explanations",
            "user_information": "Candidates informed of AI use in screening, right to human review per GDPR Art. 22",
            "logging_monitoring": "All screening decisions logged, recruiter override tracking, monthly fairness dashboards",
        },
        "post_market_monitoring": {
            "monitoring_plan": "Quarterly bias audits, hiring outcome tracking, recruiter satisfaction surveys, model drift monitoring",
            "feedback_mechanisms": "Recruiter rating system, hiring manager feedback loop, candidate experience surveys",
            "update_procedures": "Model updates require bias re-testing. New job categories require domain adaptation validation.",
            "incident_reporting": "Discrimination complaints escalated to legal team within 24 hours. DPA notification if systemic bias found.",
        },
    },
    "autonomous_vehicle": {
        "general_information": {
            "system_name": "Autonomous Vehicle Perception System",
            "version": "3.0.0",
            "purpose": "Real-time environment perception, object detection, and path planning for Level 3 autonomous driving.",
            "developer": "AutoDrive Technologies AG",
            "deployment_date": "2024-06-01",
        },
        "intended_purpose": {
            "use_cases": ["Highway driving automation", "Parking assistance", "Emergency braking", "Lane keeping"],
            "target_users": ["Vehicle operators", "Fleet managers", "Automotive OEMs"],
            "geographic_scope": "Germany, France, Italy - major motorways only",
            "prohibited_uses": "Not for fully autonomous operation without driver supervision. Not approved for urban environments.",
        },
        "technical_specifications": {
            "model_architecture": "Multi-sensor fusion network combining LiDAR, camera, and radar with real-time inference pipeline (< 50ms latency).",
            "input_types": ["LiDAR point clouds", "RGB camera feeds (8 cameras)", "Radar data", "GPS/IMU", "HD map data"],
            "output_types": ["Object detection and tracking", "Drivable area segmentation", "Path planning trajectories", "Risk scores"],
            "performance_metrics": "mAP@0.5: 0.94, False negative rate < 0.1%, Latency: 45ms P99, System availability: 99.97%",
            "hardware_requirements": "NVIDIA DRIVE Orin SoC, dedicated safety co-processor, redundant sensor arrays",
        },
        "training_data": {
            "data_sources": ["100M+ km of driving data", "Synthetic scenarios (CARLA simulator)", "Edge case library"],
            "data_preprocessing": "Temporal synchronization, sensor calibration, ground truth annotation by certified annotators",
            "data_quality_measures": "Systematic edge case collection, weather and lighting diversity requirements, annotation quality SLAs",
            "training_methodology": "Supervised learning with simulation augmentation, adversarial testing, safety-critical scenario emphasis",
        },
        "testing_and_validation": {
            "test_datasets": ["10M km validation drives", "10,000 simulated safety-critical scenarios", "ISO 21448 SOTIF test suite"],
            "evaluation_metrics": ["Detection accuracy", "False negative rate", "System latency", "SOTIF compliance metrics"],
            "performance_results": "All ISO 21448 requirements met. 99.997% detection accuracy on pedestrians in validation testing.",
            "known_limitations": "Reduced performance in heavy snow/fog. Not validated for construction zones or non-mapped roads.",
        },
        "human_oversight": {
            "oversight_mechanisms": "Driver monitoring system, automatic handover requests, remote operations center for edge cases",
            "human_intervention_points": ["ODD boundary approach", "System confidence below threshold", "Emergency scenarios"],
            "roles_responsibilities": "Safety driver: takeover authority. Operations center: remote monitoring. Safety engineer: incident investigation.",
        },
        "cybersecurity": {
            "security_measures": "UN R155 compliant, secure OTA updates, intrusion detection system, V2X security protocols",
            "access_controls": "Hardware security module, signed software attestation, physical tamper protection",
            "vulnerability_assessments": "ISO 21434 compliance, annual penetration testing, TARA analysis",
            "incident_response": "Automatic safe-stop procedures, incident data recorder, manufacturer CSIRT notification",
        },
        "transparency": {
            "explainability_methods": "System status HMI display, takeover request explanations, post-trip reports for operators",
            "user_information": "Driver training mandatory, ODD documentation, limitations clearly displayed in vehicle",
            "logging_monitoring": "Black box data recorder (EDR), cloud telemetry, real-time safety monitoring",
        },
        "post_market_monitoring": {
            "monitoring_plan": "Continuous fleet telemetry analysis, monthly safety reports, SOTIF monitoring for edge cases",
            "feedback_mechanisms": "Driver incident reporting, OEM dealer network feedback, regulatory reporting channels",
            "update_procedures": "OTA updates with safety validation gate, regression testing requirement, type approval notifications",
            "incident_reporting": "Serious incidents reported to transport authority within 24 hours per regulations.",
        },
    },
    "content_moderation": {
        "general_information": {
            "system_name": "AI Content Moderation System",
            "version": "2.0.0",
            "purpose": "Automated detection and classification of harmful, illegal, or policy-violating content on digital platforms.",
            "developer": "SafeContent AI Ltd.",
            "deployment_date": "2024-01-15",
        },
        "intended_purpose": {
            "use_cases": ["Hate speech detection", "CSAM detection", "Spam filtering", "Misinformation flagging"],
            "target_users": ["Platform trust and safety teams", "Content moderators", "Policy enforcement teams"],
            "geographic_scope": "European Union - DSA compliance",
            "prohibited_uses": "Must not suppress legitimate political speech. Cannot be used for mass surveillance.",
        },
        "technical_specifications": {
            "model_architecture": "Multi-modal transformer (text + image) with classification heads per content policy category.",
            "input_types": ["Text posts", "Images", "Video thumbnails", "User metadata"],
            "output_types": ["Content classification", "Violation probability scores", "Recommended action", "Confidence level"],
            "performance_metrics": "Precision: 0.92, Recall: 0.89, F1: 0.905, False positive rate: 3.2%",
            "hardware_requirements": "Kubernetes cluster, GPU nodes for inference, 100k+ requests/minute capacity",
        },
        "training_data": {
            "data_sources": ["Labeled moderation decisions (anonymized)", "Public hate speech datasets", "Synthetic adversarial examples"],
            "data_preprocessing": "Content hashing for CSAM (PhotoDNA), multilingual support, cultural context annotation",
            "data_quality_measures": "Diverse annotator pools, inter-annotator agreement requirements, trauma-informed annotation practices",
            "training_methodology": "Active learning with human-in-the-loop, few-shot learning for new policy categories, continual learning",
        },
        "testing_and_validation": {
            "test_datasets": ["Held-out moderation queue samples", "Red team adversarial test set", "Cultural diversity test set"],
            "evaluation_metrics": ["Precision/Recall by category", "False positive rate", "Demographic fairness metrics", "Appeals success rate"],
            "performance_results": "Meets DSA transparency report requirements. Appeals rate < 0.5%. Cultural bias testing passed.",
            "known_limitations": "Lower accuracy for low-resource languages. Context-dependent content requires human review.",
        },
        "human_oversight": {
            "oversight_mechanisms": "Human review queue for high-impact decisions, mandatory human review for account suspensions",
            "human_intervention_points": ["Account-level actions", "Appeals processing", "Edge case content", "New violation types"],
            "roles_responsibilities": "Trust & Safety lead: policy decisions. Senior moderators: appeals. Data scientists: model monitoring.",
        },
        "cybersecurity": {
            "security_measures": "Moderator mental health protections, content blurring for harmful material, secure data handling",
            "access_controls": "Need-to-know access to harmful content, psychologist support requirements, session limits",
            "vulnerability_assessments": "Adversarial robustness testing, prompt injection prevention, evasion attack testing",
            "incident_response": "Viral harmful content rapid response (<1 hour), NCMEC reporting for CSAM, law enforcement cooperation",
        },
        "transparency": {
            "explainability_methods": "Policy violation reason codes, plain language explanations for users, appeals explanation system",
            "user_information": "Community standards published, content decision notifications, right to appeal documented",
            "logging_monitoring": "All moderation decisions logged, DSA transparency reporting, bias monitoring dashboards",
        },
        "post_market_monitoring": {
            "monitoring_plan": "Real-time accuracy monitoring, weekly bias reports, DSA semi-annual transparency reports",
            "feedback_mechanisms": "User appeals analysis, moderator feedback system, civil society consultation",
            "update_procedures": "Policy updates require model retraining. New categories require labeled data collection.",
            "incident_reporting": "Systemic failures reported to Digital Services Coordinator per DSA Article 24.",
        },
    },
    "predictive_maintenance": {
        "general_information": {
            "system_name": "Industrial IoT Predictive Maintenance AI",
            "version": "1.2.0",
            "purpose": "Predict equipment failures and maintenance needs for industrial machinery using sensor data analysis.",
            "developer": "IndustrialAI Systems GmbH",
            "deployment_date": "2024-04-01",
        },
        "intended_purpose": {
            "use_cases": ["Equipment failure prediction", "Maintenance scheduling", "Asset health monitoring", "Anomaly detection"],
            "target_users": ["Plant operators", "Maintenance engineers", "Operations managers"],
            "geographic_scope": "Industrial facilities across EU",
            "prohibited_uses": "Not for safety-critical systems without additional validation. Not a replacement for mandatory safety inspections.",
        },
        "technical_specifications": {
            "model_architecture": "LSTM-based time series model with attention mechanism for multi-variate sensor data, anomaly detection via VAE.",
            "input_types": ["Vibration sensor data", "Temperature readings", "Pressure gauges", "RPM data", "Historical maintenance records"],
            "output_types": ["Failure probability (0-100%)", "Time-to-failure estimate", "Anomaly alerts", "Recommended maintenance actions"],
            "performance_metrics": "Precision: 0.87, Recall: 0.91, RMSE: 2.3 days, False alarm rate: 8%",
            "hardware_requirements": "Edge computing nodes (8GB RAM), cloud backend for training, MQTT for real-time data",
        },
        "training_data": {
            "data_sources": ["3 years of sensor data from 500+ machines", "Maintenance logs", "Equipment manufacturer specifications"],
            "data_preprocessing": "Time series normalization, missing data imputation, feature extraction (FFT, statistical features)",
            "data_quality_measures": "Sensor calibration requirements, data quality SLAs, domain expert validation of labels",
            "training_methodology": "Supervised + unsupervised combined approach, per-equipment-type models, transfer learning across similar machines",
        },
        "testing_and_validation": {
            "test_datasets": ["6-month holdout period", "Simulated failure scenarios", "Cross-site validation"],
            "evaluation_metrics": ["F1 score", "False alarm rate", "Days before failure prediction accuracy", "Cost savings metric"],
            "performance_results": "87% of failures predicted with average 5 days advance warning. 40% reduction in unplanned downtime.",
            "known_limitations": "Performance varies by equipment age and type. Requires 3 months minimum data for new equipment.",
        },
        "human_oversight": {
            "oversight_mechanisms": "Engineer review of all high-severity alerts, maintenance manager approval for work orders",
            "human_intervention_points": ["Critical failure alerts", "Maintenance budget decisions", "Model recommendation review"],
            "roles_responsibilities": "Maintenance manager: final scheduling authority. Site engineer: alert investigation. IT: system health.",
        },
        "cybersecurity": {
            "security_measures": "OT/IT network segregation, encrypted sensor data transmission, IEC 62443 compliance",
            "access_controls": "Role-based access, plant network segmentation, VPN for remote access",
            "vulnerability_assessments": "Annual OT security assessment, firmware security review, network penetration testing",
            "incident_response": "Plant safety team integration, automatic alert escalation, vendor notification procedures",
        },
        "transparency": {
            "explainability_methods": "Sensor contribution visualization, trend charts, natural language alert descriptions",
            "user_information": "Operator training program, system confidence indicators displayed, limitation notices",
            "logging_monitoring": "All predictions and outcomes logged for model improvement, audit trails for maintenance decisions",
        },
        "post_market_monitoring": {
            "monitoring_plan": "Weekly model performance review, quarterly accuracy assessments, annual model retraining evaluation",
            "feedback_mechanisms": "Maintenance outcome feedback loop, engineer feedback portal, false alarm tracking",
            "update_procedures": "Model updates deployed during planned maintenance windows, A/B testing for major changes",
            "incident_reporting": "Equipment failure not predicted by system triggers root cause analysis and model review.",
        },
    },
    "legal_document_analysis": {
        "general_information": {
            "system_name": "Legal Document Analysis AI",
            "version": "1.0.0",
            "purpose": "Automated analysis of legal documents for clause identification, risk flagging, and contract review assistance.",
            "developer": "LegalTech AI S.A.",
            "deployment_date": "2024-05-01",
        },
        "intended_purpose": {
            "use_cases": ["Contract review", "Due diligence support", "Clause extraction", "Risk identification", "Regulatory compliance checking"],
            "target_users": ["Lawyers", "Legal paralegals", "Compliance officers", "Corporate counsel"],
            "geographic_scope": "European Union member states",
            "prohibited_uses": "Not for rendering legal advice to end clients. Not a replacement for qualified legal counsel.",
        },
        "technical_specifications": {
            "model_architecture": "Legal-BERT fine-tuned on EU legal corpus with named entity recognition and clause classification heads.",
            "input_types": ["PDF contracts", "Word documents", "Plain text legal documents", "Structured data extracts"],
            "output_types": ["Clause classifications", "Risk flags", "Entity extractions", "Summary reports", "Comparison analysis"],
            "performance_metrics": "Clause classification F1: 0.91, Risk detection recall: 0.94, Entity extraction precision: 0.89",
            "hardware_requirements": "8 vCPUs, 32GB RAM, optional GPU for batch processing",
        },
        "training_data": {
            "data_sources": ["EUR-Lex legal corpus", "Anonymized contract library (100k+ documents)", "Legal annotation expert datasets"],
            "data_preprocessing": "PDF text extraction, table parsing, section structure identification, confidentiality redaction",
            "data_quality_measures": "Expert legal annotation, jurisdiction-specific review, multi-language validation (23 EU languages)",
            "training_methodology": "Domain-adaptive pre-training on legal corpus, fine-tuning with expert-labeled contracts",
        },
        "testing_and_validation": {
            "test_datasets": ["Held-out contract corpus", "Lawyer blind comparison study", "Cross-jurisdiction test set"],
            "evaluation_metrics": ["Clause F1 score", "Risk identification recall", "Lawyer agreement rate", "Time savings"],
            "performance_results": "91% agreement with expert lawyers on clause classification. 45% reduction in review time in pilot.",
            "known_limitations": "Accuracy varies by legal jurisdiction. Complex or unusual clause structures may be misclassified.",
        },
        "human_oversight": {
            "oversight_mechanisms": "All outputs are recommendations requiring lawyer review. No autonomous legal actions.",
            "human_intervention_points": ["Final contract approval", "High-risk clause handling", "Novel legal issues", "Client advice"],
            "roles_responsibilities": "Partner lawyer: final sign-off authority. Associate: AI-assisted review. Compliance: periodic audits.",
        },
        "cybersecurity": {
            "security_measures": "Legal professional privilege protection, document encryption, secure deletion, attorney-client confidentiality",
            "access_controls": "Matter-based access control, client data isolation, IP restriction for sensitive matters",
            "vulnerability_assessments": "Legal data security standards compliance, annual security review, secure document handling",
            "incident_response": "Confidentiality breach procedures, bar association notification, client incident notification",
        },
        "transparency": {
            "explainability_methods": "Highlighted document sections, confidence scores, reasoning explanations for flagged risks",
            "user_information": "Lawyers informed of AI assistance, limitations disclosed to clients per bar association requirements",
            "logging_monitoring": "All document analyses logged for billing and audit, matter-level access logs, quality monitoring",
        },
        "post_market_monitoring": {
            "monitoring_plan": "Monthly accuracy sampling, user satisfaction surveys, comparative performance vs. manual review",
            "feedback_mechanisms": "Lawyer correction capture, accuracy reporting portal, legal team feedback sessions",
            "update_procedures": "Legal corpus updates with new legislation, model fine-tuning for new contract types",
            "incident_reporting": "Significant misclassifications reported to product team, systematic issues to bar association as needed.",
        },
    },
    "education_adaptive": {
        "general_information": {
            "system_name": "Adaptive Learning AI Platform",
            "version": "1.3.0",
            "purpose": "Personalized educational content delivery and learning path optimization for K-12 and higher education students.",
            "developer": "EduAI Technologies S.r.l.",
            "deployment_date": "2024-09-01",
        },
        "intended_purpose": {
            "use_cases": ["Personalized learning paths", "Knowledge gap identification", "Adaptive assessments", "Progress tracking"],
            "target_users": ["Students (age 10+)", "Teachers", "Educational administrators"],
            "geographic_scope": "Italy, Spain, Portugal - secondary and higher education",
            "prohibited_uses": "Must not be used to profile students for non-educational purposes. No biometric data processing.",
        },
        "technical_specifications": {
            "model_architecture": "Knowledge tracing model (Deep Knowledge Tracing) with collaborative filtering for content recommendations.",
            "input_types": ["Student response data", "Time-on-task metrics", "Assessment results", "Curriculum standards"],
            "output_types": ["Next content recommendations", "Mastery probability per concept", "Learning analytics", "Teacher alerts"],
            "performance_metrics": "AUC for knowledge tracing: 0.82, Learning outcome improvement: +15%, Engagement retention: +23%",
            "hardware_requirements": "Cloud SaaS, scales automatically, COPPA/GDPR-K compliant infrastructure",
        },
        "training_data": {
            "data_sources": ["Anonymized student interaction logs (5M+ sessions)", "Curriculum mapping databases", "Educational content metadata"],
            "data_preprocessing": "Student ID pseudonymization, parental consent verification, age-appropriate content filtering",
            "data_quality_measures": "Pedagogical expert validation, curriculum alignment checking, equity testing across demographics",
            "training_methodology": "Federated learning to preserve privacy, knowledge graph integration, teacher feedback incorporation",
        },
        "testing_and_validation": {
            "test_datasets": ["Randomized controlled trial data", "Cross-school validation set", "Long-term outcome study"],
            "evaluation_metrics": ["Knowledge tracing AUC", "Learning gain measures", "Equity metrics across demographics", "Teacher satisfaction"],
            "performance_results": "Statistically significant learning improvements in RCT. Equity analysis shows equal benefits across demographics.",
            "known_limitations": "Requires minimum 2 weeks of student data for personalization. Less effective for highly irregular learners.",
        },
        "human_oversight": {
            "oversight_mechanisms": "Teachers maintain curriculum control, can override all recommendations, parental visibility portal",
            "human_intervention_points": ["Learning plan modifications", "Alert investigation", "Content appropriateness review", "Grade decisions"],
            "roles_responsibilities": "Teacher: pedagogical authority. School admin: system configuration. Parent: data access rights.",
        },
        "cybersecurity": {
            "security_measures": "GDPR and COPPA compliance, student data encryption, secure school network integration",
            "access_controls": "Student data accessible only to authorized school staff, parental consent management, FERPA compliance",
            "vulnerability_assessments": "EdTech security standards, annual penetration testing, student data protection impact assessment",
            "incident_response": "School data breach procedures, parental notification within 72 hours, DPA reporting",
        },
        "transparency": {
            "explainability_methods": "Student-friendly progress explanations, teacher dashboards with learning rationale, parent reports",
            "user_information": "Student and parent informed consent, data usage explained in age-appropriate language",
            "logging_monitoring": "Learning session logging, teacher interaction tracking, automated anomaly detection for student wellbeing",
        },
        "post_market_monitoring": {
            "monitoring_plan": "Per-term learning outcome analysis, equity monitoring reports, teacher and student satisfaction surveys",
            "feedback_mechanisms": "Teacher feedback portal, student feedback mechanisms, parent communication channel, school board reports",
            "update_procedures": "Curriculum updates aligned with national standards updates. Model retraining each academic year.",
            "incident_reporting": "Student wellbeing concerns escalated to school counselors immediately. Data incidents per GDPR timeline.",
        },
    },
}


def get_template(template_type: str) -> dict | None:
    return TEMPLATES.get(template_type)


def list_template_types() -> list[str]:
    return list(TEMPLATES.keys())
