import pytest


@pytest.fixture
def empty_system():
    return {}


@pytest.fixture
def full_system():
    return {
        "general_information": {
            "system_name": "Test AI System",
            "version": "1.0.0",
            "purpose": "Testing purpose for compliance documentation",
            "developer": "Test Developer",
            "deployment_date": "2024-01-01",
        },
        "intended_purpose": {
            "use_cases": ["classification", "prediction"],
            "target_users": ["analysts"],
            "geographic_scope": "EU",
            "prohibited_uses": "No prohibited uses defined",
        },
        "technical_specifications": {
            "model_architecture": "Random Forest classifier with 100 estimators",
            "input_types": ["tabular data"],
            "output_types": ["binary classification"],
            "performance_metrics": "Accuracy: 0.92, F1: 0.89",
            "hardware_requirements": "4 vCPUs, 8GB RAM",
        },
        "training_data": {
            "data_sources": ["internal database"],
            "data_preprocessing": "Normalization and feature engineering",
            "data_quality_measures": "Manual review by domain experts",
            "training_methodology": "Supervised learning with cross-validation",
        },
        "testing_and_validation": {
            "test_datasets": ["holdout set 20%"],
            "evaluation_metrics": ["accuracy", "F1", "AUC"],
            "performance_results": "AUC: 0.94, Precision: 0.91",
            "known_limitations": "Reduced accuracy for rare edge cases",
        },
        "human_oversight": {
            "oversight_mechanisms": "Weekly review by risk team",
            "human_intervention_points": ["high-risk predictions"],
            "roles_responsibilities": "Data scientist: model owner, Manager: approval",
        },
        "cybersecurity": {
            "security_measures": "AES-256 encryption, secure API",
            "access_controls": "RBAC with MFA",
            "vulnerability_assessments": "Annual pen testing",
            "incident_response": "24h response team with defined playbooks",
        },
        "transparency": {
            "explainability_methods": "SHAP values for all predictions",
            "user_information": "User documentation and training materials",
            "logging_monitoring": "All predictions logged with audit trail",
        },
        "post_market_monitoring": {
            "monitoring_plan": "Monthly performance review and drift detection",
            "feedback_mechanisms": "User feedback portal and error reporting",
            "update_procedures": "Quarterly model updates with validation",
            "incident_reporting": "Incidents reported within 15 days",
        },
    }
