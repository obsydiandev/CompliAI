SECTION_NAMES: dict[int, str] = {
    1: "General Description",
    2: "Design & Development",
    3: "Training, Validation & Test Data",
    4: "Validation & Testing",
    5: "Risk Management",
    6: "Lifecycle Changes",
    7: "Standards & Norms",
    8: "Human Oversight",
    9: "Post-Market Monitoring",
}

ANNEX_IV_SECTIONS: dict[int, dict[str, dict]] = {
    1: {
        "system_name": {
            "label": "System Name",
            "required": False,
            "help_text": "The commercial or internal name of the AI system.",
        },
        "system_version": {
            "label": "System Version",
            "required": False,
            "help_text": "Current version identifier of the system.",
        },
        "intended_purpose": {
            "label": "Intended Purpose",
            "required": True,
            "help_text": "A clear description of the intended purpose of the AI system, including the specific context and conditions of use.",
        },
        "use_cases": {
            "label": "Use Cases",
            "required": True,
            "help_text": "Specific use cases and applications the AI system is designed to address.",
        },
        "intended_users": {
            "label": "Intended Users",
            "required": False,
            "help_text": "The categories of users expected to interact with or be affected by the AI system.",
        },
        "geographic_scope": {
            "label": "Geographic Scope",
            "required": False,
            "help_text": "The countries or regions where the AI system is intended to be deployed.",
        },
        "operational_context": {
            "label": "Operational Context",
            "required": False,
            "help_text": "Description of the operational environment and conditions of use.",
        },
    },
    2: {
        "architecture_description": {
            "label": "Architecture Description",
            "required": True,
            "help_text": "A detailed description of the AI system architecture, including the type of AI/ML approach used.",
        },
        "algorithms_used": {
            "label": "Algorithms Used",
            "required": True,
            "help_text": "Description of the algorithms and models used in the system.",
        },
        "key_design_decisions": {
            "label": "Key Design Decisions",
            "required": False,
            "help_text": "Rationale behind key architectural and algorithmic design choices.",
        },
        "software_components": {
            "label": "Software Components",
            "required": False,
            "help_text": "List of software components, frameworks, and libraries used.",
        },
        "hardware_requirements": {
            "label": "Hardware Requirements",
            "required": False,
            "help_text": "Minimum and recommended hardware specifications for operation.",
        },
        "third_party_components": {
            "label": "Third-Party Components",
            "required": False,
            "help_text": "Third-party software, pre-trained models, or datasets incorporated.",
        },
    },
    3: {
        "training_data_description": {
            "label": "Training Data Description",
            "required": True,
            "help_text": "Description of the datasets used for training, including size, format, and content.",
        },
        "data_sources": {
            "label": "Data Sources",
            "required": True,
            "help_text": "Origin of the training data, including provenance and acquisition methods.",
        },
        "data_preprocessing": {
            "label": "Data Preprocessing",
            "required": False,
            "help_text": "Steps taken to clean, transform, or augment the training data.",
        },
        "data_quality_measures": {
            "label": "Data Quality Measures",
            "required": True,
            "help_text": "Measures taken to ensure data quality, representativeness, and absence of bias.",
        },
        "validation_data_description": {
            "label": "Validation Data Description",
            "required": False,
            "help_text": "Description of the datasets used for model validation.",
        },
        "test_data_description": {
            "label": "Test Data Description",
            "required": False,
            "help_text": "Description of the datasets used for final testing and evaluation.",
        },
        "data_governance": {
            "label": "Data Governance",
            "required": False,
            "help_text": "Data governance policies, access controls, and retention policies.",
        },
    },
    4: {
        "validation_methodology": {
            "label": "Validation Methodology",
            "required": True,
            "help_text": "Methods used to validate the system's performance and reliability.",
        },
        "performance_metrics": {
            "label": "Performance Metrics",
            "required": True,
            "help_text": "Metrics used to measure performance (e.g., accuracy, precision, recall, F1 score).",
        },
        "test_results": {
            "label": "Test Results",
            "required": True,
            "help_text": "Summary of test results including performance across different scenarios.",
        },
        "subgroup_analysis": {
            "label": "Subgroup Analysis",
            "required": False,
            "help_text": "Performance analysis across different demographic and contextual subgroups.",
        },
        "known_limitations": {
            "label": "Known Limitations",
            "required": True,
            "help_text": "Known limitations, failure modes, and edge cases of the system.",
        },
        "benchmark_comparisons": {
            "label": "Benchmark Comparisons",
            "required": False,
            "help_text": "Comparison against relevant industry benchmarks or baseline models.",
        },
    },
    5: {
        "risk_register": {
            "label": "Risk Register",
            "required": True,
            "help_text": "Comprehensive register of identified risks associated with the AI system.",
        },
        "risk_assessment_methodology": {
            "label": "Risk Assessment Methodology",
            "required": True,
            "help_text": "Methodology used to identify, assess, and prioritize risks.",
        },
        "control_measures": {
            "label": "Control Measures",
            "required": True,
            "help_text": "Technical and organisational measures implemented to mitigate identified risks.",
        },
        "residual_risks": {
            "label": "Residual Risks",
            "required": False,
            "help_text": "Risks that remain after control measures have been applied.",
        },
        "risk_acceptance_criteria": {
            "label": "Risk Acceptance Criteria",
            "required": False,
            "help_text": "Criteria used to determine acceptable levels of risk.",
        },
        "bias_assessment": {
            "label": "Bias Assessment",
            "required": False,
            "help_text": "Assessment of potential biases in the system and measures to address them.",
        },
    },
    6: {
        "change_management_plan": {
            "label": "Change Management Plan",
            "required": True,
            "help_text": "Plan for managing changes to the AI system throughout its lifecycle.",
        },
        "changelog": {
            "label": "Changelog",
            "required": True,
            "help_text": "Record of all significant changes made to the system since initial deployment.",
        },
        "version_control_approach": {
            "label": "Version Control Approach",
            "required": False,
            "help_text": "Approach to versioning the system and its components.",
        },
        "significant_change_criteria": {
            "label": "Significant Change Criteria",
            "required": False,
            "help_text": "Criteria used to determine what constitutes a significant change requiring re-assessment.",
        },
    },
    7: {
        "applicable_standards": {
            "label": "Applicable Standards",
            "required": True,
            "help_text": "List of technical standards applicable to the AI system.",
        },
        "harmonised_standards": {
            "label": "Harmonised Standards",
            "required": False,
            "help_text": "EU harmonised standards applied in the development of the system.",
        },
        "common_specifications": {
            "label": "Common Specifications",
            "required": False,
            "help_text": "Common specifications issued by the European Commission that have been applied.",
        },
        "compliance_declarations": {
            "label": "Compliance Declarations",
            "required": False,
            "help_text": "Declarations of conformity or compliance with relevant regulations and standards.",
        },
    },
    8: {
        "human_oversight_measures": {
            "label": "Human Oversight Measures",
            "required": True,
            "help_text": "Measures enabling human oversight of the AI system during operation.",
        },
        "hitl_procedures": {
            "label": "Human-in-the-Loop Procedures",
            "required": True,
            "help_text": "Procedures for human intervention in the AI decision-making process.",
        },
        "override_mechanisms": {
            "label": "Override Mechanisms",
            "required": False,
            "help_text": "Technical mechanisms allowing humans to override, stop, or reverse AI decisions.",
        },
        "transparency_measures": {
            "label": "Transparency Measures",
            "required": True,
            "help_text": "Measures ensuring transparency of the AI system's operation to users and subjects.",
        },
        "user_interface_description": {
            "label": "User Interface Description",
            "required": False,
            "help_text": "Description of user interfaces enabling human oversight and control.",
        },
        "logging_audit_trail": {
            "label": "Logging & Audit Trail",
            "required": False,
            "help_text": "Logging capabilities providing audit trails for oversight and accountability.",
        },
    },
    9: {
        "pmm_plan": {
            "label": "Post-Market Monitoring Plan",
            "required": True,
            "help_text": "Plan for monitoring the AI system's performance and compliance after deployment.",
        },
        "monitoring_metrics": {
            "label": "Monitoring Metrics",
            "required": True,
            "help_text": "Metrics and KPIs used for ongoing post-market monitoring.",
        },
        "data_collection_methods": {
            "label": "Data Collection Methods",
            "required": False,
            "help_text": "Methods used to collect post-market performance and incident data.",
        },
        "reporting_frequency": {
            "label": "Reporting Frequency",
            "required": False,
            "help_text": "Frequency of post-market monitoring reports to the notified body or authority.",
        },
        "incident_reporting_procedure": {
            "label": "Incident Reporting Procedure",
            "required": True,
            "help_text": "Procedure for reporting serious incidents and near-misses to competent authorities.",
        },
        "feedback_mechanisms": {
            "label": "Feedback Mechanisms",
            "required": False,
            "help_text": "Mechanisms for collecting feedback from users and affected persons.",
        },
    },
}
