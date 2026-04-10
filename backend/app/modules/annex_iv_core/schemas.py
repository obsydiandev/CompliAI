ANNEX_IV_SECTIONS: dict[str, list[str]] = {
    "general_information": [
        "system_name",
        "version",
        "purpose",
        "developer",
        "deployment_date",
    ],
    "intended_purpose": [
        "use_cases",
        "target_users",
        "geographic_scope",
        "prohibited_uses",
    ],
    "technical_specifications": [
        "model_architecture",
        "input_types",
        "output_types",
        "performance_metrics",
        "hardware_requirements",
    ],
    "training_data": [
        "data_sources",
        "data_preprocessing",
        "data_quality_measures",
        "training_methodology",
    ],
    "testing_and_validation": [
        "test_datasets",
        "evaluation_metrics",
        "performance_results",
        "known_limitations",
    ],
    "human_oversight": [
        "oversight_mechanisms",
        "human_intervention_points",
        "roles_responsibilities",
    ],
    "cybersecurity": [
        "security_measures",
        "access_controls",
        "vulnerability_assessments",
        "incident_response",
    ],
    "transparency": [
        "explainability_methods",
        "user_information",
        "logging_monitoring",
    ],
    "post_market_monitoring": [
        "monitoring_plan",
        "feedback_mechanisms",
        "update_procedures",
        "incident_reporting",
    ],
}
